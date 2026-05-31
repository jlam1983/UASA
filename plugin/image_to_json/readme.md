# Image to JSON

Extract structured data from images → one JSON row.

## Pipeline

```
Image File → Validate Type → OCR Extract → LLM Retrieve → JSON Row
```

---

## Two LLM Retrieval Methods

### Method 1 — Keyword Parse (`keyword_parse`)

Give LLM the **title** + a list of **attribute names** (keywords). LLM maps each keyword to its value in the text.

```python
from plugin.image_to_json import ImageToJSONConverter, keyword_parse

# Via converter
conv = ImageToJSONConverter()
result = conv.process("invoice.png", title="Invoice", keywords=["vendor", "total", "date"], use_llm=True)

# Direct
fields, confidence = keyword_parse(title="Invoice", keywords=["vendor", "total"], text="Acme Corp... $1,234...")
```

**You control the attribute names.** LLM just finds the values.

---

### Method 2 — Subjective Parse (`subjective_parse`)

Give LLM the **title only**. LLM reads the text, decides what attributes are relevant, and **names them itself**.

```python
from plugin.image_to_json import ImageToJSONConverter, subjective_parse

# Via converter
result = conv.process("receipt.png", title="Receipt", use_llm=True)

# Direct
fields, confidence = subjective_parse(title="Receipt", text="Starbucks... $4.50... 2024-01-15")
```

**LLM controls the attribute names.** It chooses what to extract and how to name it.

---

## Usage

```python
from plugin.image_to_json import ImageToJSONConverter

conv = ImageToJSONConverter()

# OCR only (no LLM)
result = conv.process("receipt.png", use_llm=False)
# {"source_file": "receipt.png", "image_type": "png", "extracted_text": "...", "fields": {"text": "..."}, "confidence": 1.0}

# Keyword parse — you name the fields
result = conv.process("invoice.png", title="Invoice", keywords=["vendor", "invoice_no", "total"], use_llm=True)

# Subjective parse — LLM names the fields
result = conv.process("receipt.png", title="Receipt", use_llm=True)
```

## Output Format

```json
{
  "source_file": "receipt.png",
  "image_type": "png",
  "extracted_text": "raw OCR text...",
  "fields": { ... },
  "confidence": 1.0
}
```

---

## Project Structure

```
plugin/
└── image_to_json/
    ├── __init__.py
    ├── readme.md
    ├── converter.py      # ImageToJSONConverter (main entry)
    ├── validator.py       # Step 1: validate image type
    ├── ocr.py             # Step 2: extract text via Tesseract
    ├── llm_parser.py      # Step 3: keyword_parse + subjective_parse
    └── test_case.py
```
