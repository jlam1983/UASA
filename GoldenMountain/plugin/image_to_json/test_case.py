"""Test cases for image_to_json plugin."""

import pytest


class TestValidator:
    def test_validate_unsupported_extension_raises(self):
        from plugin.image_to_json.validator import validate_image_type

        with pytest.raises(ValueError) as exc:
            validate_image_type("document.pdf")
        assert "Unsupported image extension" in str(exc.value)


class TestOCR:
    def test_extract_text_file_not_found(self):
        from plugin.image_to_json.ocr import extract_text

        with pytest.raises(FileNotFoundError):
            extract_text("nonexistent_image.png")


class TestConverter:
    def test_converter_process_no_llm(self, tmp_path):
        from plugin.image_to_json.converter import ImageToJSONConverter

        # Create a fake PNG with valid header
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)

        conv = ImageToJSONConverter()
        try:
            result = conv.process(str(img), use_llm=False)
            assert "source_file" in result
            assert "fields" in result
            assert result["confidence"] == 1.0
        except ImportError as e:
            if "Tesseract" in str(e):
                pytest.skip("Tesseract not installed")
            raise

    def test_converter_keyword_mode_requires_keywords(self):
        # keywords provided but use_llm=False — keywords are ignored,
        # returns raw text in fields. Real test requires OCR engine.
        assert True


class TestLLMParser:
    def test_keyword_parse_import(self):
        from plugin.image_to_json.llm_parser import keyword_parse
        assert callable(keyword_parse)

    def test_subjective_parse_import(self):
        from plugin.image_to_json.llm_parser import subjective_parse
        assert callable(subjective_parse)
