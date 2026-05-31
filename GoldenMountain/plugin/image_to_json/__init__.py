"""Image to JSON — extract structured data from images via OCR + LLM."""

from .converter import ImageToJSONConverter
from .validator import validate_image_type
from .ocr import extract_text
from .llm_parser import keyword_parse, subjective_parse

__all__ = [
    "ImageToJSONConverter",
    "validate_image_type",
    "extract_text",
    "keyword_parse",   # Method 1: title + keywords → structured fields
    "subjective_parse", # Method 2: title only → LLM decides attributes
]
