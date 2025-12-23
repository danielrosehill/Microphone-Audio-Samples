#!/usr/bin/env python3
"""
Microphone Audio Quality and STT Accuracy Evaluation

This script evaluates:
1. Audio quality metrics (SNR, loudness, dynamic range, etc.)
2. Speech-to-text accuracy using local Whisper and OpenAI Whisper
3. Word Error Rate (WER) comparison across microphones
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from datetime import datetime
import requests
import wave
import struct
import math

# Load .env file if present
from dotenv import load_dotenv
load_dotenv()

# For WER calculation
from jiwer import wer, cer

# Constants
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"
METADATA_FILE = BASE_DIR / "metadata.json"
REFERENCE_TEXT_FILE = BASE_DIR / "text" / "coffee.txt"
RESULTS_FILE = BASE_DIR / "evaluation_results.json"

# OpenAI-only evaluation for methodological consistency
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


@dataclass
class AudioMetrics:
    """Audio quality metrics for a sample."""
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: Optional[int]
    codec: str
    bitrate_kbps: Optional[float]
    peak_amplitude_db: float
    rms_level_db: float
    estimated_snr_db: Optional[float]
    dynamic_range_db: float
    silence_ratio: float  # Percentage of audio that is near-silent
    clipping_ratio: float  # Percentage of samples at max amplitude


@dataclass
class TranscriptionResult:
    """Result from a transcription service."""
    service: str
    text: str
    wer: float
    cer: float
    processing_time_seconds: Optional[float] = None
    run_date: Optional[str] = None


@dataclass
class SampleEvaluation:
    """Complete evaluation for a single sample."""
    sample_id: int
    filename: str
    microphone: dict
    audio_metrics: AudioMetrics
    transcriptions: list[TranscriptionResult]
    audio_quality_score: float  # Composite score 0-100


def get_reference_text() -> str:
    """Load and normalize the reference text."""
    with open(REFERENCE_TEXT_FILE, "r") as f:
        text = f.read()
    # Normalize: lowercase, collapse whitespace
    text = " ".join(text.lower().split())
    return text


def analyze_audio_with_ffprobe(filepath: Path) -> dict:
    """Get audio metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(filepath)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def analyze_audio_levels(filepath: Path) -> dict:
    """Analyze audio levels using ffmpeg."""
    cmd = [
        "ffmpeg", "-i", str(filepath), "-af",
        "volumedetect", "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr

    levels = {}
    for line in stderr.split("\n"):
        if "max_volume" in line:
            levels["peak_db"] = float(line.split(":")[1].strip().replace(" dB", ""))
        elif "mean_volume" in line:
            levels["mean_db"] = float(line.split(":")[1].strip().replace(" dB", ""))

    return levels


def estimate_noise_floor(filepath: Path) -> float:
    """Estimate noise floor by analyzing quietest segments."""
    # Use ffmpeg to get audio statistics
    cmd = [
        "ffmpeg", "-i", str(filepath), "-af",
        "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse RMS levels from output
    rms_values = []
    for line in result.stderr.split("\n"):
        if "RMS_level" in line:
            try:
                val = float(line.split("=")[1])
                if val > -100:  # Filter out -inf values
                    rms_values.append(val)
            except (ValueError, IndexError):
                pass

    if rms_values:
        # Noise floor is approximately the 10th percentile of RMS values
        rms_values.sort()
        idx = max(0, int(len(rms_values) * 0.1))
        return rms_values[idx]
    return -60.0  # Default noise floor estimate


def analyze_audio_metrics(filepath: Path) -> AudioMetrics:
    """Analyze all audio quality metrics for a sample."""
    probe_data = analyze_audio_with_ffprobe(filepath)
    levels = analyze_audio_levels(filepath)

    # Extract stream info
    audio_stream = None
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break

    format_info = probe_data.get("format", {})

    duration = float(format_info.get("duration", 0))
    sample_rate = int(audio_stream.get("sample_rate", 0)) if audio_stream else 0
    channels = int(audio_stream.get("channels", 0)) if audio_stream else 0
    codec = audio_stream.get("codec_name", "unknown") if audio_stream else "unknown"

    # Bit depth (if available)
    bit_depth = None
    if audio_stream:
        bits = audio_stream.get("bits_per_sample") or audio_stream.get("bits_per_raw_sample")
        if bits:
            bit_depth = int(bits)

    # Bitrate
    bitrate_kbps = None
    if format_info.get("bit_rate"):
        bitrate_kbps = float(format_info["bit_rate"]) / 1000

    # Audio levels
    peak_db = levels.get("peak_db", 0)
    mean_db = levels.get("mean_db", -20)

    # Estimate SNR
    noise_floor = estimate_noise_floor(filepath)
    estimated_snr = mean_db - noise_floor if noise_floor else None

    # Dynamic range
    dynamic_range = abs(peak_db - noise_floor) if noise_floor else abs(peak_db - mean_db)

    # Silence and clipping ratios (simplified estimates)
    silence_ratio = max(0, min(1, (noise_floor + 60) / 60)) if noise_floor else 0.1
    clipping_ratio = max(0, min(1, (peak_db + 1) / 3)) if peak_db > -3 else 0

    return AudioMetrics(
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        codec=codec,
        bitrate_kbps=bitrate_kbps,
        peak_amplitude_db=peak_db,
        rms_level_db=mean_db,
        estimated_snr_db=estimated_snr,
        dynamic_range_db=dynamic_range,
        silence_ratio=silence_ratio,
        clipping_ratio=clipping_ratio
    )


def calculate_audio_quality_score(metrics: AudioMetrics) -> float:
    """
    Calculate a composite audio quality score (0-100).

    Factors considered:
    - Sample rate (higher is better, up to 48kHz)
    - Bit depth (16-bit minimum, 24-bit preferred)
    - SNR (higher is better)
    - Dynamic range (balanced is better)
    - Clipping (less is better)
    - RMS level (optimal around -18 to -12 dB)
    """
    score = 0.0

    # Sample rate score (max 15 points)
    if metrics.sample_rate >= 48000:
        score += 15
    elif metrics.sample_rate >= 44100:
        score += 12
    elif metrics.sample_rate >= 22050:
        score += 8
    else:
        score += 5

    # Bit depth score (max 10 points)
    if metrics.bit_depth:
        if metrics.bit_depth >= 24:
            score += 10
        elif metrics.bit_depth >= 16:
            score += 8
        else:
            score += 5
    else:
        score += 6  # Unknown, assume decent

    # SNR score (max 25 points)
    if metrics.estimated_snr_db:
        snr = metrics.estimated_snr_db
        if snr >= 40:
            score += 25
        elif snr >= 30:
            score += 20
        elif snr >= 20:
            score += 15
        elif snr >= 10:
            score += 10
        else:
            score += 5
    else:
        score += 12  # Unknown

    # RMS level score (max 20 points) - optimal around -18 to -12 dB
    rms = metrics.rms_level_db
    if -20 <= rms <= -10:
        score += 20
    elif -25 <= rms <= -8:
        score += 15
    elif -30 <= rms <= -6:
        score += 10
    else:
        score += 5

    # Clipping penalty (max 15 points)
    clipping_score = 15 * (1 - metrics.clipping_ratio)
    score += clipping_score

    # Dynamic range score (max 15 points)
    dr = metrics.dynamic_range_db
    if 30 <= dr <= 60:
        score += 15
    elif 20 <= dr <= 70:
        score += 12
    elif 15 <= dr <= 80:
        score += 8
    else:
        score += 5

    return min(100, max(0, score))


def transcribe_with_openai(filepath: Path) -> tuple[str, float]:
    """Transcribe using OpenAI Whisper API."""
    import time

    if not OPENAI_API_KEY:
        return "", 0.0

    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    with open(filepath, "rb") as f:
        files = {"file": (filepath.name, f, "audio/wav")}
        data = {"model": "whisper-1", "language": "en"}

        start = time.time()
        response = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            return result.get("text", ""), elapsed
        else:
            print(f"  OpenAI error: {response.status_code} - {response.text}")
            return "", elapsed


def normalize_text(text: str) -> str:
    """Normalize text for WER comparison."""
    # Lowercase, remove punctuation, collapse whitespace
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = " ".join(text.split())
    return text


def evaluate_sample(sample: dict, reference_text: str) -> SampleEvaluation:
    """Evaluate a single audio sample."""
    filepath = BASE_DIR / sample["filename"]
    print(f"\nEvaluating sample {sample['id']}: {sample['microphone']['manufacturer']} {sample['microphone']['model']}")

    # Analyze audio quality
    print("  Analyzing audio metrics...")
    audio_metrics = analyze_audio_metrics(filepath)
    audio_quality_score = calculate_audio_quality_score(audio_metrics)

    transcriptions = []
    normalized_reference = normalize_text(reference_text)

    run_date = datetime.now().strftime("%Y-%m-%d")

    # OpenAI Whisper transcription (single source for methodological consistency)
    if OPENAI_API_KEY:
        print("  Transcribing with OpenAI Whisper...")
        openai_text, openai_time = transcribe_with_openai(filepath)
        if openai_text:
            normalized_openai = normalize_text(openai_text)
            openai_wer = wer(normalized_reference, normalized_openai)
            openai_cer = cer(normalized_reference, normalized_openai)
            transcriptions.append(TranscriptionResult(
                service="openai_whisper_1",
                text=openai_text,
                wer=openai_wer,
                cer=openai_cer,
                processing_time_seconds=openai_time,
                run_date=run_date
            ))
            print(f"    WER: {openai_wer:.2%}, CER: {openai_cer:.2%}")
    else:
        print("  Skipping OpenAI (no API key)")

    return SampleEvaluation(
        sample_id=sample["id"],
        filename=sample["filename"],
        microphone=sample["microphone"],
        audio_metrics=audio_metrics,
        transcriptions=transcriptions,
        audio_quality_score=audio_quality_score
    )


def generate_report(evaluations: list[SampleEvaluation], reference_text: str) -> dict:
    """Generate a comprehensive evaluation report."""

    # Sort by audio quality score
    by_quality = sorted(evaluations, key=lambda e: e.audio_quality_score, reverse=True)

    # Sort by OpenAI WER (lower is better) - single source for methodological consistency
    by_wer = sorted(
        [e for e in evaluations if any(t.service == "openai_whisper_1" for t in e.transcriptions)],
        key=lambda e: next(t.wer for t in e.transcriptions if t.service == "openai_whisper_1")
    )

    # Category analysis using OpenAI WER
    categories = {}
    for e in evaluations:
        cat = e.microphone.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"samples": [], "avg_quality": 0, "avg_wer": 0}
        categories[cat]["samples"].append(e.sample_id)

    for cat, data in categories.items():
        cat_evals = [e for e in evaluations if e.microphone.get("category") == cat]
        data["avg_quality"] = sum(e.audio_quality_score for e in cat_evals) / len(cat_evals)
        wers = [
            next((t.wer for t in e.transcriptions if t.service == "openai_whisper_1"), None)
            for e in cat_evals
        ]
        wers = [w for w in wers if w is not None]
        data["avg_wer"] = sum(wers) / len(wers) if wers else None

    # Get evaluation date from first transcription
    eval_date = None
    for e in evaluations:
        for t in e.transcriptions:
            if t.run_date:
                eval_date = t.run_date
                break
        if eval_date:
            break

    report = {
        "summary": {
            "total_samples": len(evaluations),
            "reference_text_words": len(reference_text.split()),
            "transcription_service": "OpenAI Whisper API (whisper-1)",
            "evaluation_date": eval_date or datetime.now().strftime("%Y-%m-%d"),
            "methodology": "Single transcription service for all samples to ensure methodological consistency"
        },
        "rankings": {
            "by_audio_quality": [
                {
                    "rank": i + 1,
                    "sample_id": e.sample_id,
                    "microphone": f"{e.microphone['manufacturer']} {e.microphone['model']}",
                    "category": e.microphone.get("category"),
                    "score": round(e.audio_quality_score, 1)
                }
                for i, e in enumerate(by_quality)
            ],
            "by_wer": [
                {
                    "rank": i + 1,
                    "sample_id": e.sample_id,
                    "microphone": f"{e.microphone['manufacturer']} {e.microphone['model']}",
                    "category": e.microphone.get("category"),
                    "wer_percent": round(next(t.wer for t in e.transcriptions if t.service == "openai_whisper_1") * 100, 2)
                }
                for i, e in enumerate(by_wer)
            ]
        },
        "category_analysis": categories,
        "detailed_results": [
            {
                "sample_id": e.sample_id,
                "filename": e.filename,
                "microphone": e.microphone,
                "audio_metrics": asdict(e.audio_metrics),
                "audio_quality_score": round(e.audio_quality_score, 1),
                "transcriptions": [asdict(t) for t in e.transcriptions]
            }
            for e in evaluations
        ]
    }

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate microphone audio samples for STT accuracy")
    parser.add_argument("--samples", type=str, help="Comma-separated list of sample IDs to evaluate (e.g., '13,14,15')")
    parser.add_argument("--merge", action="store_true", help="Merge results with existing evaluation_results.json")
    args = parser.parse_args()

    print("=" * 60)
    print("Microphone Audio Quality & STT Accuracy Evaluation")
    print("=" * 60)

    # Load metadata
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)

    # Load reference text
    reference_text = get_reference_text()
    print(f"\nReference text: {len(reference_text.split())} words")
    print(f"OpenAI API: {'Available' if OPENAI_API_KEY else 'Not configured'}")

    # Filter samples if specified
    samples_to_evaluate = metadata["samples"]
    if args.samples:
        sample_ids = [int(s.strip()) for s in args.samples.split(",")]
        samples_to_evaluate = [s for s in metadata["samples"] if s["id"] in sample_ids]
        print(f"Evaluating samples: {sample_ids}")

    # Load existing results if merging
    existing_detailed_results = []
    if args.merge and RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r") as f:
            existing_report = json.load(f)
            existing_detailed_results = existing_report.get("detailed_results", [])
            # Remove samples we're about to re-evaluate
            if args.samples:
                sample_ids = [int(s.strip()) for s in args.samples.split(",")]
                existing_detailed_results = [r for r in existing_detailed_results if r["sample_id"] not in sample_ids]

    # Evaluate each sample
    evaluations = []
    for sample in samples_to_evaluate:
        filepath = BASE_DIR / sample["filename"]
        if filepath.exists():
            eval_result = evaluate_sample(sample, reference_text)
            evaluations.append(eval_result)
        else:
            print(f"\nSkipping sample {sample['id']}: File not found - {sample['filename']}")

    # Convert existing results to SampleEvaluation objects for merging
    if args.merge and existing_detailed_results:
        for result in existing_detailed_results:
            metrics = AudioMetrics(**result["audio_metrics"])
            transcriptions = [
                TranscriptionResult(**t) for t in result["transcriptions"]
            ]
            existing_eval = SampleEvaluation(
                sample_id=result["sample_id"],
                filename=result["filename"],
                microphone=result["microphone"],
                audio_metrics=metrics,
                transcriptions=transcriptions,
                audio_quality_score=result["audio_quality_score"]
            )
            evaluations.append(existing_eval)
        # Sort by sample_id
        evaluations.sort(key=lambda e: e.sample_id)

    # Generate report
    print("\n" + "=" * 60)
    print("Generating report...")
    report = generate_report(evaluations, reference_text)

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Results saved to: {RESULTS_FILE}")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"\nTranscription: {report['summary']['transcription_service']}")
    print(f"Evaluation Date: {report['summary']['evaluation_date']}")

    print("\n📊 AUDIO QUALITY RANKING (by composite score):")
    print("-" * 50)
    for item in report["rankings"]["by_audio_quality"][:5]:
        print(f"  #{item['rank']}: {item['microphone']} ({item['category']}) - Score: {item['score']}")

    print("\n🎯 STT ACCURACY RANKING (OpenAI Whisper - by WER):")
    print("-" * 50)
    for item in report["rankings"]["by_wer"][:5]:
        print(f"  #{item['rank']}: {item['microphone']} ({item['category']}) - WER: {item['wer_percent']:.2f}%")

    print("\n📁 CATEGORY ANALYSIS:")
    print("-" * 50)
    for cat, data in report["category_analysis"].items():
        wer_str = f"{data['avg_wer']*100:.2f}%" if data['avg_wer'] else "N/A"
        print(f"  {cat}: Avg Quality={data['avg_quality']:.1f}, Avg WER={wer_str}")


if __name__ == "__main__":
    main()
