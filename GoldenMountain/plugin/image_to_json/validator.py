"""Image type validator."""

import imghdr
from pathlib import Path


SUPPORTED_TYPES = {"jpeg", "jpg", "png", "bmp", "webp", "tiff", "gif"}


def validate_image_type(file_path: str) -> str:
    """Validate image file type by extension and content.

    Returns the detected image type (e.g. 'png', 'jpeg').
    Raises ValueError if unsupported.
    """
    path = Path(file_path)

    # Check extension
    ext = path.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported image extension: {ext}")

    # Check magic bytes
    detected = imghdr.what(file_path)
    if detected is None:
        raise ValueError(f"Cannot detect valid image type for: {file_path}")

    if detected not in SUPPORTED_TYPES:
        raise ValueError(f"Detected type '{detected}' not in supported list")

    return detected
