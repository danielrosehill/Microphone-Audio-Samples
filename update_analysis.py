#!/usr/bin/env python3
"""
Update analysis for new samples - generate spectrograms and regenerate charts.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import pandas as pd
from pathlib import Path
from scipy import stats

# Paths
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"
SPECTROGRAMS_DIR = BASE_DIR / "spectrograms"
METADATA_FILE = BASE_DIR / "metadata.json"
EVAL_FILE = BASE_DIR / "evaluation_results.json"
FEATURES_FILE = SPECTROGRAMS_DIR / "audio_features.csv"

# Load data
with open(METADATA_FILE) as f:
    metadata = json.load(f)

with open(EVAL_FILE) as f:
    eval_results = json.load(f)

# Create sample info lookup
sample_info = {}
for sample in metadata["samples"]:
    sample_id = sample["id"]
    mic = sample["microphone"]
    sample_info[sample_id] = {
        "name": f"{mic['manufacturer']} {mic['model']}",
        "type": mic.get("type", "Unknown"),
        "category": mic.get("category", "unknown"),
    }

# Get WER for each sample
wer_lookup = {}
for result in eval_results["detailed_results"]:
    sid = result["sample_id"]
    for t in result["transcriptions"]:
        if t["service"] == "openai_whisper_1":
            wer_lookup[sid] = t["wer"] * 100  # Convert to percentage

def extract_audio_features(audio_path):
    """Extract audio features for correlation analysis."""
    y, sr = librosa.load(audio_path, sr=None)

    # Spectral features
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]

    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    # RMS energy
    rms = librosa.feature.rms(y=y)[0]

    # MFCCs
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    features = {
        'spectral_centroid_mean': np.mean(spectral_centroid),
        'spectral_centroid_std': np.std(spectral_centroid),
        'spectral_rolloff_mean': np.mean(spectral_rolloff),
        'spectral_rolloff_std': np.std(spectral_rolloff),
        'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
        'spectral_bandwidth_std': np.std(spectral_bandwidth),
        'spectral_contrast_mean': np.mean(spectral_contrast),
        'spectral_flatness_mean': np.mean(spectral_flatness),
        'zero_crossing_rate_mean': np.mean(zcr),
        'zero_crossing_rate_std': np.std(zcr),
        'rms_mean': np.mean(rms),
        'rms_std': np.std(rms),
    }

    # Add MFCCs
    for i in range(13):
        features[f'mfcc_{i}_mean'] = np.mean(mfccs[i])
        features[f'mfcc_{i}_std'] = np.std(mfccs[i])

    # Speech-specific ratios
    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    # Harmonic content (speech fundamental F0 range 85-255 Hz)
    speech_fund_mask = (freqs >= 85) & (freqs <= 255)
    speech_fund_energy = np.mean(stft[speech_fund_mask, :]) if np.any(speech_fund_mask) else 0
    total_energy = np.mean(stft)

    # Formant range (300-3400 Hz for speech)
    formant_mask = (freqs >= 300) & (freqs <= 3400)
    formant_energy = np.mean(stft[formant_mask, :]) if np.any(formant_mask) else 0

    # High frequency content (above 4000 Hz)
    high_freq_mask = freqs > 4000
    high_freq_energy = np.mean(stft[high_freq_mask, :]) if np.any(high_freq_mask) else 0

    features['harmonic_ratio'] = np.mean(librosa.effects.harmonic(y)) / (np.mean(np.abs(y)) + 1e-10)
    features['speech_fundamental_ratio'] = speech_fund_energy / (total_energy + 1e-10)
    features['speech_formant_ratio'] = formant_energy / (total_energy + 1e-10)
    features['high_freq_ratio'] = high_freq_energy / (total_energy + 1e-10)
    features['speech_clarity_ratio'] = formant_energy / (high_freq_energy + formant_energy + 1e-10)

    return features

def generate_spectrogram(sample_id, audio_path, output_path):
    """Generate spectrogram for a sample."""
    y, sr = librosa.load(audio_path, sr=None)

    # Create figure with two subplots
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # Mel spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_db = librosa.power_to_db(S, ref=np.max)

    img1 = librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel',
                                    ax=axes[0], fmax=8000)
    axes[0].set_title(f'Mel Spectrogram - Sample {sample_id}: {sample_info[sample_id]["name"]}',
                      fontsize=14, fontweight='bold')
    fig.colorbar(img1, ax=axes[0], format='%+2.0f dB')

    # MFCC
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    img2 = librosa.display.specshow(mfccs, sr=sr, x_axis='time', ax=axes[1])
    axes[1].set_title('MFCCs', fontsize=12)
    axes[1].set_ylabel('MFCC Coefficients')
    fig.colorbar(img2, ax=axes[1])

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated: {output_path.name}")

def generate_ranked_chart():
    """Generate spectrograms ranked by WER chart."""
    # Sort samples by WER
    ranked = sorted(wer_lookup.items(), key=lambda x: x[1])

    n_samples = len(ranked)
    cols = 4
    rows = (n_samples + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(20, 5*rows))
    axes = axes.flatten()

    for idx, (sample_id, wer_val) in enumerate(ranked):
        ax = axes[idx]
        audio_path = SAMPLES_DIR / f"{sample_id}.wav"
        if not audio_path.exists():
            audio_path = SAMPLES_DIR / f"{sample_id}.mp3"

        if audio_path.exists():
            y, sr = librosa.load(audio_path, sr=None)
            S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=64, fmax=8000)
            S_db = librosa.power_to_db(S, ref=np.max)

            librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='mel',
                                     ax=ax, fmax=8000)

            info = sample_info.get(sample_id, {"name": f"Sample {sample_id}", "category": "unknown"})
            ax.set_title(f"#{idx+1}: {info['name']}\nWER: {wer_val:.2f}% ({info['category']})",
                        fontsize=9)
        else:
            ax.set_visible(False)

    # Hide unused axes
    for idx in range(n_samples, len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle('All Samples Ranked by Word Error Rate (Best to Worst)',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_path = SPECTROGRAMS_DIR / "spectrograms_ranked_by_wer.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated: {output_path.name}")

def generate_correlation_chart():
    """Generate correlation analysis chart."""
    # Load features
    df = pd.read_csv(FEATURES_FILE)

    # Key features for correlation
    feature_cols = ['spectral_centroid_mean', 'spectral_rolloff_mean', 'spectral_bandwidth_mean',
                    'spectral_flatness_mean', 'zero_crossing_rate_mean', 'rms_mean',
                    'harmonic_ratio', 'speech_clarity_ratio', 'speech_formant_ratio']

    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    axes = axes.flatten()

    correlations = {}
    for idx, feature in enumerate(feature_cols):
        ax = axes[idx]
        x = df[feature]
        y = df['wer']

        ax.scatter(x, y, c=range(len(df)), cmap='viridis', s=100, alpha=0.7)

        # Add regression line
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, p(x_line), 'r--', alpha=0.8)

        # Calculate correlation
        r, pval = stats.pearsonr(x, y)
        correlations[feature] = {'r': r, 'p': pval}

        ax.set_xlabel(feature.replace('_', ' ').title())
        ax.set_ylabel('WER (%)')
        ax.set_title(f'r={r:.3f}, p={pval:.3f}')

    plt.suptitle('Audio Feature Correlations with Word Error Rate',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = SPECTROGRAMS_DIR / "correlation_analysis.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Generated: {output_path.name}")

    # Save correlations
    with open(SPECTROGRAMS_DIR / "correlations.json", 'w') as f:
        json.dump(correlations, f, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update analysis for new samples")
    parser.add_argument("--samples", type=str, help="Comma-separated sample IDs to process")
    args = parser.parse_args()

    print("=" * 60)
    print("Updating Analysis")
    print("=" * 60)

    # Determine which samples to process
    if args.samples:
        sample_ids = [int(s.strip()) for s in args.samples.split(",")]
    else:
        sample_ids = list(wer_lookup.keys())

    # Load existing features or create new
    if FEATURES_FILE.exists():
        df = pd.read_csv(FEATURES_FILE)
    else:
        df = pd.DataFrame()

    # Process each sample
    for sample_id in sample_ids:
        # Try both .wav and .mp3 extensions
        audio_path = SAMPLES_DIR / f"{sample_id}.wav"
        if not audio_path.exists():
            audio_path = SAMPLES_DIR / f"{sample_id}.mp3"
        if not audio_path.exists():
            print(f"Skipping sample {sample_id}: file not found")
            continue

        print(f"\nProcessing sample {sample_id}: {sample_info.get(sample_id, {}).get('name', 'Unknown')}")

        # Generate spectrogram
        manufacturer = sample_info[sample_id]["name"].split()[0].lower()
        spec_path = SPECTROGRAMS_DIR / f"spectrogram_{sample_id:02d}_{manufacturer}.png"
        generate_spectrogram(sample_id, audio_path, spec_path)

        # Extract features
        print("  Extracting audio features...")
        features = extract_audio_features(audio_path)
        features['sample_id'] = sample_id
        features['microphone'] = sample_info[sample_id]["name"]
        features['mic_type'] = sample_info[sample_id]["type"]
        features['category'] = sample_info[sample_id]["category"]
        features['wer'] = wer_lookup.get(sample_id, 0)

        # Update dataframe
        if sample_id in df['sample_id'].values if 'sample_id' in df.columns else False:
            df = df[df['sample_id'] != sample_id]
        df = pd.concat([df, pd.DataFrame([features])], ignore_index=True)

    # Sort by sample_id and save
    df = df.sort_values('sample_id').reset_index(drop=True)
    df.to_csv(FEATURES_FILE, index=False)
    print(f"\nSaved features to: {FEATURES_FILE}")

    # Regenerate charts
    print("\nRegenerating charts...")
    generate_ranked_chart()
    generate_correlation_chart()

    print("\nDone!")

if __name__ == "__main__":
    main()
