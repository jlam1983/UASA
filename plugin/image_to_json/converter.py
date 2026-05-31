"""Image to JSON converter — main entry point."""

from pathlib import Path

from .validator import validate_image_type
from .ocr import extract_text
from .llm_parser import keyword_parse, subjective_parse


class ImageToJSONConverter:
    """Convert a single image to one JSON row using OCR + LLM."""

    def process(
        self,
        image_path: str,
        *,
        title: str = "",
        keywords: list[str] | None = None,
        use_llm: bool = False,
    ) -> dict:
        """Process one image and return one JSON row.

        Args:
            image_path: Path to the image file
            title: Document title/subject (e.g. "Invoice", "Receipt")
            keywords: List of attribute names to extract (for keyword_parse)
            use_llm: Whether to use LLM parsing (otherwise returns raw OCR text)

        Steps:
            1. Validate image type
            2. OCR extract raw text
            3. LLM parse (keyword or subjective)
            4. Return JSON row
        """
        path = Path(image_path)

        # Step 1: Validate
        image_type = validate_image_type(str(path))

        # Step 2: OCR
        raw_text = extract_text(str(path))

        # Step 3: LLM parse
        if use_llm and keywords:
            # Method 1: user provides title + keywords → LLM maps keywords to values
            fields, confidence = keyword_parse(title, keywords, raw_text)
        elif use_llm:
            # Method 2: user provides title only → LLM decides what is relevant
            fields, confidence = subjective_parse(title, raw_text)
        else:
            fields = {"text": raw_text}
            confidence = 1.0

        # Step 4: Build result row
        return {
            "source_file": path.name,
            "image_type": image_type,
            "extracted_text": raw_text,
            "fields": fields,
            "confidence": confidence,
        }
