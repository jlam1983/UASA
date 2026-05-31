"""LLM-based field extraction from text — two retrieval methods."""

import json
import os


def _call_llm(prompt: str, model: str = "claude-3-5-sonnet") -> str:
    """Call LLM and return response text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set")

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response.content[0].text.strip()
    # Strip markdown code blocks
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])
    return content


def keyword_parse(title: str, keywords: list[str], text: str, model: str = "claude-3-5-sonnet") -> tuple[dict, float]:
    """Extract values using user-provided keywords.

    LLM maps each keyword to the corresponding value found in the text.

    Args:
        title: Subject/title of the document (e.g. "Invoice", "Receipt")
        keywords: List of attribute names to extract (e.g. ["vendor", "total", "date"])
        text: Raw OCR text

    Returns:
        Tuple of (extracted_fields, confidence)
    """
    keyword_list = ", ".join(keywords)
    prompt = f"""You are given a {title} document.
Extract the values for each of the following keywords from the text below.
Return ONLY a valid JSON object. Use the keyword as the field name.

Keywords: {keyword_list}

Text:
{text}

Rules:
- If a keyword's value is not found in the text, use null
- Keep the original keyword names exactly as provided
- Return ONLY the JSON object, no explanation"""

    content = _call_llm(prompt, model)
    fields = json.loads(content)
    return fields, 1.0


def subjective_parse(title: str, text: str, model: str = "claude-3-5-sonnet") -> tuple[dict, float]:
    """Extract values based on the document title — LLM decides what is relevant.

    LLM reads the text, understands the document subject, and decides
    which attributes are important and what to name them.

    Args:
        title: Subject/title of the document (e.g. "Invoice", "Receipt", "Business Card")
        text: Raw OCR text

    Returns:
        Tuple of (extracted_fields with LLM-chosen names, confidence)
    """
    prompt = f"""You are given a {title} document.
Read the text and extract all relevant information.
Decide what attributes are meaningful for this type of document.
Name the attributes yourself based on what they represent.
Return a clean JSON object with your chosen attribute names as keys.

Text:
{text}

Rules:
- Choose 5-10 of the most important attributes
- Name attributes clearly (e.g. "vendor_name", "total_amount", "issue_date")
- Return ONLY the JSON object, no explanation"""

    content = _call_llm(prompt, model)
    fields = json.loads(content)
    return fields, 1.0
