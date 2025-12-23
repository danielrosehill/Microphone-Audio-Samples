#!/usr/bin/env python3
"""
Create composite grid images of microphone device photos with overlay cards
showing name, type, and WER (Word Error Rate).

WER data is loaded dynamically from evaluation_results.json for consistency.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

# Configuration
IMAGES_PER_ROW = 3
CELL_WIDTH = 400
CELL_HEIGHT = 350
CARD_HEIGHT = 80
PADDING = 20
FONT_SIZE_TITLE = 20
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_WER = 16

# Paths
BASE_DIR = Path(__file__).parent.parent
RESULTS_FILE = BASE_DIR / "evaluation_results.json"

# Image mapping for samples (sample_id -> image filename)
SAMPLE_IMAGES = {
    1: "cm564.png",
    2: "q2u.png",
    3: "h390.png",
    4: "oneplus.png",
    5: "oneplus.png",
    6: "atr4697.png",
    7: "atr4697.png",
    8: "jabra510.png",
    9: "c925.png",
    10: "maono-elf.png",
    11: "yealinkbh72.png",
    12: "yealinkbh72.png",
    13: "atr4750.png",
    14: "oneplus.png",
    15: "oneplus.png",
}

# Display name overrides for clarity (sample_id -> custom name)
DISPLAY_NAMES = {
    4: "OnePlus Nord 3 (HQ)",
    5: "OnePlus Nord 3 (MP3)",
    6: "ATR4697 (Close)",
    7: "ATR4697 (Far)",
    11: "Yealink BH72 (Dongle)",
    12: "Yealink BH72 (BT)",
    14: "OnePlus Nord 3 (Noisy)",
    15: "OnePlus Nord 3 (Quiet)",
}

# Type overrides for display
TYPE_OVERRIDES = {
    4: "HQ Voice Recording",
    5: "MP3 via Voicenotes",
    6: "Boundary ~30cm",
    7: "Boundary ~80cm",
    11: "Via USB Dongle",
    12: "Via Bluetooth",
    14: "Ambient Noise",
    15: "Quiet Environment",
}


def load_samples_from_results():
    """Load sample data from evaluation_results.json."""
    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)

    samples = []
    for result in results["detailed_results"]:
        sample_id = result["sample_id"]
        mic = result["microphone"]

        # Get WER from transcriptions
        wer_percent = None
        for t in result["transcriptions"]:
            if t["service"] == "openai_whisper_1":
                wer_percent = round(t["wer"] * 100, 2)
                break

        if wer_percent is None:
            continue  # Skip samples without WER data

        # Build display name
        name = DISPLAY_NAMES.get(sample_id, f"{mic['manufacturer']} {mic['model']}")

        # Build type
        mic_type = TYPE_OVERRIDES.get(sample_id, mic.get("type", "Unknown"))

        samples.append({
            "image": SAMPLE_IMAGES.get(sample_id, "placeholder.png"),
            "sample_id": sample_id,
            "name": name,
            "type": mic_type,
            "category": mic.get("category", "desktop"),
            "wer": wer_percent
        })

    return samples, results.get("summary", {})

# Category colors
CATEGORY_COLORS = {
    "desktop": (70, 130, 180),      # Steel blue
    "headset": (60, 179, 113),      # Medium sea green
    "mobile": (255, 140, 0),        # Dark orange
    "lavalier": (147, 112, 219),    # Medium purple
}

def get_font(size, bold=False):
    """Try to load a nice font, fall back to default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def load_and_resize_image(path, target_width, target_height):
    """Load image and resize to fit within target dimensions, maintaining aspect ratio."""
    img = Image.open(path)
    img = img.convert("RGBA")

    # Calculate scaling to fit within target dimensions
    width_ratio = target_width / img.width
    height_ratio = (target_height - CARD_HEIGHT) / img.height
    scale = min(width_ratio, height_ratio)

    new_width = int(img.width * scale)
    new_height = int(img.height * scale)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return img


def create_cell(image_path, mic_data, cell_width, cell_height):
    """Create a single cell with image and overlay card."""
    # Create cell canvas
    cell = Image.new("RGBA", (cell_width, cell_height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(cell)

    # Load and position the image
    img = load_and_resize_image(image_path, cell_width - 2*PADDING, cell_height - CARD_HEIGHT - PADDING)

    # Center the image horizontally
    x_offset = (cell_width - img.width) // 2
    y_offset = PADDING
    cell.paste(img, (x_offset, y_offset), img if img.mode == "RGBA" else None)

    # Draw the overlay card at bottom
    card_y = cell_height - CARD_HEIGHT
    category_color = CATEGORY_COLORS.get(mic_data["category"], (100, 100, 100))

    # Card background with gradient effect
    draw.rectangle(
        [(0, card_y), (cell_width, cell_height)],
        fill=category_color + (240,)
    )

    # Draw a subtle border at top of card
    draw.line([(0, card_y), (cell_width, card_y)], fill=(255, 255, 255, 200), width=2)

    # Load fonts
    font_title = get_font(FONT_SIZE_TITLE, bold=True)
    font_subtitle = get_font(FONT_SIZE_SUBTITLE)
    font_wer = get_font(FONT_SIZE_WER, bold=True)

    # Draw mic name (centered)
    name = mic_data["name"]
    bbox = draw.textbbox((0, 0), name, font=font_title)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((cell_width - text_width) // 2, card_y + 8),
        name,
        fill=(255, 255, 255),
        font=font_title
    )

    # Draw type (centered, below name)
    mic_type = mic_data["type"]
    bbox = draw.textbbox((0, 0), mic_type, font=font_subtitle)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((cell_width - text_width) // 2, card_y + 32),
        mic_type,
        fill=(255, 255, 255, 220),
        font=font_subtitle
    )

    # Draw WER badge (bottom right)
    wer_text = f"WER: {mic_data['wer']:.1f}%"
    bbox = draw.textbbox((0, 0), wer_text, font=font_wer)
    text_width = bbox[2] - bbox[0]

    # WER badge background
    badge_padding = 6
    badge_x = cell_width - text_width - badge_padding * 2 - 10
    badge_y = card_y + 50
    draw.rounded_rectangle(
        [(badge_x, badge_y), (cell_width - 10, badge_y + 24)],
        radius=4,
        fill=(0, 0, 0, 150)
    )
    draw.text(
        (badge_x + badge_padding, badge_y + 3),
        wer_text,
        fill=(255, 255, 255),
        font=font_wer
    )

    return cell


def create_composite(samples, output_path, title=None, summary=None):
    """Create a composite image with all samples in specified order."""
    if summary is None:
        summary = {}
    num_samples = len(samples)
    rows = (num_samples + IMAGES_PER_ROW - 1) // IMAGES_PER_ROW

    title_height = 60 if title else 0
    footer_height = 80
    border_width = 2
    composite_width = IMAGES_PER_ROW * CELL_WIDTH + (IMAGES_PER_ROW - 1) * border_width
    grid_height = rows * CELL_HEIGHT
    composite_height = grid_height + title_height + footer_height

    composite = Image.new("RGB", (composite_width, composite_height), (245, 245, 245))
    draw = ImageDraw.Draw(composite)

    # Draw title if provided
    if title:
        font_title = get_font(28, bold=True)
        bbox = draw.textbbox((0, 0), title, font=font_title)
        text_width = bbox[2] - bbox[0]
        draw.text(
            ((composite_width - text_width) // 2, 15),
            title,
            fill=(50, 50, 50),
            font=font_title
        )

    # Create and place each cell
    originals_dir = Path(__file__).parent / "originals"

    for i, sample in enumerate(samples):
        row = i // IMAGES_PER_ROW
        col = i % IMAGES_PER_ROW

        image_path = originals_dir / sample["image"]
        if not image_path.exists():
            print(f"Warning: Image not found: {image_path}")
            continue

        cell = create_cell(image_path, sample, CELL_WIDTH, CELL_HEIGHT)

        x = col * (CELL_WIDTH + border_width)
        y = row * CELL_HEIGHT + title_height

        composite.paste(cell, (x, y))

    # Draw vertical borders between columns
    border_color = (180, 180, 180)
    for col in range(1, IMAGES_PER_ROW):
        x = col * CELL_WIDTH + (col - 1) * border_width + border_width // 2
        draw.line([(x, title_height), (x, title_height + grid_height)], fill=border_color, width=border_width)

    # Draw footer with notes
    footer_y = title_height + grid_height
    draw.rectangle([(0, footer_y), (composite_width, composite_height)], fill=(240, 240, 240))
    draw.line([(0, footer_y), (composite_width, footer_y)], fill=(200, 200, 200), width=1)

    font_footer = get_font(13)
    font_footer_bold = get_font(13, bold=True)

    # Get footer text from summary or use defaults
    eval_date = summary.get("evaluation_date", "December 2025")
    num_samples = summary.get("total_samples", len(samples))
    methodology = summary.get("methodology", "Single evaluation using OpenAI Whisper API")

    footer_text_1 = f"Methodology: {methodology}"
    footer_text_2 = f"Experiment: Daniel Rosehill | Date: {eval_date} | {num_samples} samples"

    bbox1 = draw.textbbox((0, 0), footer_text_1, font=font_footer)
    bbox2 = draw.textbbox((0, 0), footer_text_2, font=font_footer)

    draw.text(
        ((composite_width - (bbox1[2] - bbox1[0])) // 2, footer_y + 18),
        footer_text_1,
        fill=(80, 80, 80),
        font=font_footer
    )
    draw.text(
        ((composite_width - (bbox2[2] - bbox2[0])) // 2, footer_y + 42),
        footer_text_2,
        fill=(100, 100, 100),
        font=font_footer
    )

    # Save
    composite = composite.convert("RGB")
    composite.save(output_path, quality=95)
    print(f"Created: {output_path}")


def main():
    # Load samples dynamically from evaluation results
    print("Loading samples from evaluation_results.json...")
    samples, summary = load_samples_from_results()
    print(f"Loaded {len(samples)} samples")

    # Create composites directory with date subfolder
    eval_date = summary.get("evaluation_date", "unknown")
    composites_dir = Path(__file__).parent / "composites" / f"eval-{eval_date.replace('-', '')}"
    composites_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create alphabetical grid composite
    alphabetical = sorted(samples, key=lambda x: x["name"].lower())
    create_composite(
        alphabetical,
        composites_dir / "microphones-grid.png",
        title="Microphone STT Benchmark",
        summary=summary
    )

    # 2. Create WER-ranked composite (best to worst)
    ranked_best_to_worst = sorted(samples, key=lambda x: x["wer"])
    create_composite(
        ranked_best_to_worst,
        composites_dir / "microphones-ranked-by-wer.png",
        title="Microphones Ranked by WER (Best to Worst)",
        summary=summary
    )

    # 3. Create category-grouped composite
    by_category = sorted(samples, key=lambda x: (x["category"], x["wer"]))
    create_composite(
        by_category,
        composites_dir / "microphones-by-category.png",
        title="Microphones Grouped by Category",
        summary=summary
    )

    print(f"\nAll composites saved to: {composites_dir}")


if __name__ == "__main__":
    main()
