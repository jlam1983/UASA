"""OCR extraction using Tesseract."""

import subprocess
from pathlib import Path


def extract_text(image_path: str) -> str:
    """Extract raw text from image using Tesseract OCR.

    Requires Tesseract to be installed on the system.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        result = subprocess.run(
            ["tesseract", str(image_path), "stdout", "--psm", "6"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        raise ImportError("Tesseract not installed. Install from: https://github.com/tesseract-ocr/tesseract")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Tesseract OCR failed: {e.stderr}")
