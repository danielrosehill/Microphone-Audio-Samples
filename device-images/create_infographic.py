#!/usr/bin/env python3
"""
Create a visually appealing infographic showing microphones ranked by WER.
Features colored backgrounds with WER prominently displayed in center.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Paths
BASE_DIR = Path(__file__).parent.parent
RESULTS_FILE = BASE_DIR / "evaluation_results.json"
ORIGINALS_DIR = Path(__file__).parent / "originals"

# Image mapping
SAMPLE_IMAGES = {
    1: "cm564.png", 2: "q2u.png", 3: "h390.png", 4: "oneplus.png", 5: "oneplus.png",
    6: "atr4697.png", 7: "atr4697.png", 8: "jabra510.png", 9: "c925.png",
    10: "maono-elf.png", 11: "yealinkbh72.png", 12: "yealinkbh72.png",
    13: "atr4750.png", 14: "oneplus.png", 15: "oneplus.png",
}

DISPLAY_NAMES = {
    4: "OnePlus Nord 3 (HQ)", 5: "OnePlus Nord 3 (MP3)", 6: "ATR4697 (Close)",
    7: "ATR4697 (Far)", 11: "Yealink BH72 (Dongle)", 12: "Yealink BH72 (BT)",
    14: "OnePlus Nord 3 (Noisy)", 15: "OnePlus Nord 3 (Quiet)",
}

# Color scheme - gradient from green (best) to red (worst)
def get_wer_color(wer, min_wer, max_wer):
    """Get color based on WER value - green to red gradient."""
    if max_wer == min_wer:
        ratio = 0.5
    else:
        ratio = (wer - min_wer) / (max_wer - min_wer)

    # Green (good) to Yellow to Red (bad)
    if ratio < 0.5:
        r = int(255 * (ratio * 2))
        g = 200
        b = 80
    else:
        r = 255
        g = int(200 * (1 - (ratio - 0.5) * 2))
        b = 80

    return (r, g, b)


def get_font(size, bold=False):
    """Try to load a nice font."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    for path in font_paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_samples():
    """Load sample data from evaluation results."""
    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)

    samples = []
    for result in results["detailed_results"]:
        sample_id = result["sample_id"]
        mic = result["microphone"]

        wer_percent = None
        for t in result["transcriptions"]:
            if t["service"] == "openai_whisper_1":
                wer_percent = round(t["wer"] * 100, 2)
                break

        if wer_percent is None:
            continue

        name = DISPLAY_NAMES.get(sample_id, f"{mic['manufacturer']} {mic['model']}")

        samples.append({
            "image": SAMPLE_IMAGES.get(sample_id, "placeholder.png"),
            "sample_id": sample_id,
            "name": name,
            "category": mic.get("category", "desktop"),
            "wer": wer_percent
        })

    return samples, results.get("summary", {})


def load_thumbnail(image_name, size=80):
    """Load and resize a microphone thumbnail."""
    img_path = ORIGINALS_DIR / image_name
    if not img_path.exists():
        return None
    try:
        thumb = Image.open(img_path).convert("RGBA")
        # Resize maintaining aspect ratio
        thumb.thumbnail((size, size), Image.Resampling.LANCZOS)
        return thumb
    except Exception:
        return None


def create_infographic(samples, summary, output_path):
    """Create the infographic with colored WER backgrounds and thumbnails."""
    # Sort by WER (best first)
    samples = sorted(samples, key=lambda x: x["wer"])

    # Layout configuration
    cols = 3
    rows = (len(samples) + cols - 1) // cols
    cell_width = 400
    cell_height = 280
    title_height = 100
    footer_height = 80
    thumb_size = 70

    img_width = cols * cell_width
    img_height = title_height + (rows * cell_height) + footer_height

    # Create canvas
    img = Image.new("RGBA", (img_width, img_height), (30, 30, 40, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = get_font(36, bold=True)
    font_subtitle = get_font(18)
    font_name = get_font(16, bold=True)
    font_wer = get_font(48, bold=True)
    font_rank = get_font(24, bold=True)
    font_footer = get_font(14)

    # Draw title
    title = "Microphone STT Benchmark"
    subtitle = "Word Error Rate (WER) - Lower is Better"

    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((img_width - (bbox[2] - bbox[0])) // 2, 20), title, fill=(255, 255, 255), font=font_title)

    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    draw.text(((img_width - (bbox[2] - bbox[0])) // 2, 65), subtitle, fill=(180, 180, 180), font=font_subtitle)

    # Get WER range for color scaling
    wers = [s["wer"] for s in samples]
    min_wer, max_wer = min(wers), max(wers)

    # Draw cells
    for i, sample in enumerate(samples):
        row = i // cols
        col = i % cols

        x = col * cell_width
        y = title_height + row * cell_height

        # Get color for this WER
        bg_color = get_wer_color(sample["wer"], min_wer, max_wer)

        # Draw cell background
        margin = 8
        draw.rectangle(
            [(x + margin, y + margin), (x + cell_width - margin, y + cell_height - margin)],
            fill=bg_color
        )

        # Draw rank badge (top left)
        rank = i + 1
        badge_size = 36
        badge_x = x + margin + 10
        badge_y = y + margin + 10
        draw.ellipse(
            [(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)],
            fill=(0, 0, 0, 180)
        )
        rank_text = f"#{rank}"
        bbox = draw.textbbox((0, 0), rank_text, font=font_rank)
        draw.text(
            (badge_x + (badge_size - (bbox[2] - bbox[0])) // 2, badge_y + 5),
            rank_text, fill=(255, 255, 255), font=font_rank
        )

        # Draw thumbnail (below rank badge, left side)
        thumb = load_thumbnail(sample["image"], thumb_size)
        if thumb:
            thumb_x = x + margin + 15
            thumb_y = y + margin + 55
            # Add white background for thumbnail
            thumb_bg = Image.new("RGBA", (thumb_size + 10, thumb_size + 10), (255, 255, 255, 220))
            img.paste(thumb_bg, (thumb_x - 5, thumb_y - 5), thumb_bg)
            # Center thumbnail in its space
            paste_x = thumb_x + (thumb_size - thumb.width) // 2
            paste_y = thumb_y + (thumb_size - thumb.height) // 2
            img.paste(thumb, (paste_x, paste_y), thumb)

        # Draw WER prominently (offset right to accommodate thumbnail)
        wer_text = f"{sample['wer']:.1f}%"
        bbox = draw.textbbox((0, 0), wer_text, font=font_wer)
        # Shift WER text to the right to not overlap thumbnail
        wer_x = x + thumb_size + 60 + (cell_width - thumb_size - 60 - (bbox[2] - bbox[0])) // 2
        wer_y = y + cell_height // 2 - 30

        # WER text shadow
        draw.text((wer_x + 2, wer_y + 2), wer_text, fill=(0, 0, 0, 100), font=font_wer)
        draw.text((wer_x, wer_y), wer_text, fill=(255, 255, 255), font=font_wer)

        # Draw microphone name at bottom
        name = sample["name"]
        if len(name) > 25:
            name = name[:22] + "..."
        bbox = draw.textbbox((0, 0), name, font=font_name)
        name_x = x + (cell_width - (bbox[2] - bbox[0])) // 2
        name_y = y + cell_height - margin - 35

        # Name background
        draw.rectangle(
            [(name_x - 8, name_y - 4), (name_x + (bbox[2] - bbox[0]) + 8, name_y + 24)],
            fill=(0, 0, 0, 150)
        )
        draw.text((name_x, name_y), name, fill=(255, 255, 255), font=font_name)

        # Category indicator (top right)
        cat_colors = {
            "desktop": (70, 130, 180),
            "headset": (60, 179, 113),
            "mobile": (255, 140, 0),
            "lavalier": (147, 112, 219),
        }
        cat_color = cat_colors.get(sample["category"], (100, 100, 100))
        cat_text = sample["category"].upper()
        bbox = draw.textbbox((0, 0), cat_text, font=font_footer)
        cat_x = x + cell_width - margin - (bbox[2] - bbox[0]) - 15
        cat_y = y + margin + 15
        draw.rectangle(
            [(cat_x - 5, cat_y - 2), (cat_x + (bbox[2] - bbox[0]) + 5, cat_y + 18)],
            fill=cat_color
        )
        draw.text((cat_x, cat_y), cat_text, fill=(255, 255, 255), font=font_footer)

    # Draw footer
    footer_y = title_height + rows * cell_height
    draw.rectangle([(0, footer_y), (img_width, img_height)], fill=(25, 25, 35))

    eval_date = summary.get("evaluation_date", "2025-12-23")
    num_samples = summary.get("total_samples", len(samples))

    footer_text = f"OpenAI Whisper API | {num_samples} samples | {eval_date} | danielrosehill.com"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    draw.text(
        ((img_width - (bbox[2] - bbox[0])) // 2, footer_y + 30),
        footer_text, fill=(150, 150, 150), font=font_footer
    )

    # Save (convert to RGB for compatibility)
    img_rgb = img.convert("RGB")
    img_rgb.save(output_path, quality=95)
    print(f"Created: {output_path}")
    return img_rgb


def main():
    print("Loading samples...")
    samples, summary = load_samples()
    print(f"Loaded {len(samples)} samples")

    # Create output directory
    eval_date = summary.get("evaluation_date", "unknown")
    output_dir = Path(__file__).parent / "composites" / f"eval-{eval_date.replace('-', '')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create infographic
    infographic_path = output_dir / "infographic-wer-ranked.png"
    create_infographic(samples, summary, infographic_path)

    print(f"\nInfographic saved to: {infographic_path}")


if __name__ == "__main__":
    main()
