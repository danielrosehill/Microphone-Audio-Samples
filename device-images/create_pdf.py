#!/usr/bin/env python3
"""
Create a PDF compilation of all microphone benchmark graphics.
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import json

BASE_DIR = Path(__file__).parent.parent
RESULTS_FILE = BASE_DIR / "evaluation_results.json"


def create_pdf():
    # Load summary for date
    with open(RESULTS_FILE, "r") as f:
        results = json.load(f)
    summary = results.get("summary", {})
    eval_date = summary.get("evaluation_date", "unknown")

    # Paths
    composites_dir = Path(__file__).parent / "composites" / f"eval-{eval_date.replace('-', '')}"
    output_pdf = composites_dir / "microphone-stt-benchmark.pdf"

    # Images to include
    images = [
        composites_dir / "infographic-wer-ranked.png",
        composites_dir / "microphones-ranked-by-wer.png",
        composites_dir / "microphones-by-category.png",
        composites_dir / "microphones-grid.png",
    ]

    # Create PDF in portrait orientation
    c = canvas.Canvas(str(output_pdf), pagesize=A4)
    page_width, page_height = A4

    for img_path in images:
        if not img_path.exists():
            print(f"Skipping missing image: {img_path}")
            continue

        # Load image to get dimensions
        pil_img = Image.open(img_path)
        img_width, img_height = pil_img.size

        # Scale to fit page with margins
        margin = 40
        available_width = page_width - 2 * margin
        available_height = page_height - 2 * margin

        scale = min(available_width / img_width, available_height / img_height)
        scaled_width = img_width * scale
        scaled_height = img_height * scale

        # Center on page
        x = (page_width - scaled_width) / 2
        y = (page_height - scaled_height) / 2

        # Draw image
        c.drawImage(str(img_path), x, y, width=scaled_width, height=scaled_height)

        # Add page
        c.showPage()

    c.save()
    print(f"Created PDF: {output_pdf}")


if __name__ == "__main__":
    create_pdf()
