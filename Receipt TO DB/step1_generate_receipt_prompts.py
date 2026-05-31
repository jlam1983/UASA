"""
Receipt JSON Format Generator & Optimizer with Ollama
- Step 1: Use first receipt to generate initial JSON schema
- Step 2: Use next 9 receipts to optimize and standardize the schema
- Step 3: Produce final optimized JSON schema
- All prompts saved to prompts_record.txt
"""

import pandas as pd
import json
import os
import ollama
import re

# ============================================================
# Configuration
# ============================================================
OLLAMA_MODEL = "qwen3:8b"
PROMPTS_FILE = "prompts_record.txt"
SCHEMA_FILE = "optimized_json_schema.json"

# Load the CSV
df = pd.read_csv('receipts_output.csv')
# Keep only unique filenames (first occurrence)
unique_df = df.drop_duplicates(subset='filename').reset_index(drop=True)

# Get first 10 unique receipts
first_10_receipts = unique_df.head(10)
receipts_texts = first_10_receipts['raw_text'].tolist()
receipts_filenames = first_10_receipts['filename'].tolist()

client = ollama.Client("http://localhost:11434")

# ============================================================
# Helper Functions
# ============================================================

def save_prompt(prompt_name, prompt_content):
    """Append prompt to the record file"""
    with open(PROMPTS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"PROMPT: {prompt_name}\n")
        f.write(f"{'='*80}\n\n")
        f.write(prompt_content)
        f.write("\n\n")

def call_ollama(prompt, system_prompt=None):
    """Call Ollama chat API and return response"""
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': prompt})

    response = client.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        options={"temperature": 0.1, "num_predict": 2000}
    )
    return response['message']['content']

def extract_json_from_response(text):
    """Extract JSON from response, handling markdown code blocks"""
    # Try to find JSON in code blocks first
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to parse the whole text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object/array pattern
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return None

def clean_json_response(text):
    """Remove markdown formatting from response"""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

# ============================================================
# Workflow Step 1: Generate Initial Schema from First Receipt
# ============================================================

print("=" * 60)
print("STEP 1: Generate Initial Schema from First Receipt")
print("=" * 60)
print(f"\nReceipt: {receipts_filenames[0]}")

receipt_0 = receipts_texts[0]

initial_prompt = f'''You are an expert receipt data extraction assistant. Your task is to analyze the following receipt and design a JSON schema that captures ALL information present in this receipt.

### RECEIPT CONTENT:
{receipt_0}

### YOUR TASK:
1. Analyze the receipt content carefully
2. Design a comprehensive JSON schema that captures ALL fields present in this receipt
3. The schema should be detailed and capture every piece of information
4. Consider field types (string, number, array, object) appropriately
5. For each field, provide a clear name and describe what data it should contain
6. If there are line items, design an items array structure
7. Also suggest transformation rules (e.g., remove currency symbols, normalize dates)

### OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanation) in this format:
{{
  "schema": {{ ... your schema design ... }},
  "transformations": {{ ... suggested data transformations ... }},
  "reasoning": "brief explanation of your schema design choices"
}}

IMPORTANT: This schema will be used to extract data from similar receipts. Make it comprehensive yet practical.
'''

print("\nCalling Ollama (qwen3:8b) to analyze first receipt...")
save_prompt("01_INITIAL_SCHEMA_PROMPT", initial_prompt)

try:
    initial_response = call_ollama(initial_prompt)
    print(f"\nResponse received ({len(initial_response)} chars)")
    save_prompt("01_INITIAL_SCHEMA_RESPONSE", initial_response)

    initial_result = extract_json_from_response(initial_response)
    if initial_result:
        print("[OK] Successfully parsed JSON schema")
        initial_schema = initial_result.get('schema', initial_result)
    else:
        print("[WARN] Could not parse JSON, using default schema")
        initial_schema = {
            "merchant": {"name": "string", "address": "string", "tax_id": "string"},
            "transaction": {"date": "string", "time": "string", "receipt_number": "string"},
            "items": [{"description": "string", "quantity": "number", "unit_price": "number", "line_total": "number"}],
            "summary": {"subtotal": "number", "tax_amount": "number", "total_amount": "number"},
            "payment": {"method": "string", "amount_tendered": "number", "change_due": "number"}
        }
except Exception as e:
    print(f"Error calling Ollama: {e}")
    initial_schema = {
        "merchant": {"name": "string", "address": "string", "tax_id": "string"},
        "transaction": {"date": "string", "time": "string", "receipt_number": "string"},
        "items": [{"description": "string", "quantity": "number", "unit_price": "number", "line_total": "number"}],
        "summary": {"subtotal": "number", "tax_amount": "number", "total_amount": "number"},
        "payment": {"method": "string", "amount_tendered": "number", "change_due": "number"}
    }

print(f"\nInitial Schema: {json.dumps(initial_schema, indent=2)[:500]}...")

# ============================================================
# Workflow Step 2: Optimize Schema with Next 9 Receipts
# ============================================================

print("\n" + "=" * 60)
print("STEP 2: Optimize Schema with 9 Additional Receipts")
print("=" * 60)

# Build receipts content for optimization prompt
receipts_content = ""
for i in range(1, 10):
    receipts_content += f'\n--- RECEIPT {i} ({receipts_filenames[i]}) ---\n{receipts_texts[i][:1500]}\n'

optimization_prompt = f'''You are an expert in data schema optimization. A preliminary JSON schema has been created from the first receipt. Now you need to optimize and standardize it using 9 additional receipts of varying formats.

### PRELIMINARY SCHEMA (from first receipt):
{json.dumps(initial_schema, indent=2)}

### ADDITIONAL RECEIPTS TO ANALYZE:
{receipts_content}

### YOUR TASK:
1. Review the preliminary schema against all 9 receipts
2. Identify what fields are MISSING from the schema that appear in these receipts
3. Identify what fields in the schema are NOT USEFUL (not found consistently)
4. Suggest STANDARDIZED field names that work across different receipt formats
5. Optimize the schema structure for maximum compatibility
6. Consider edge cases: missing fields, varying formats, different currencies, etc.

### OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanation):
{{
  "optimized_schema": {{ ... refined schema ... }},
  "added_fields": [... list of new fields added with rationale ...],
  "removed_fields": [... fields removed and why ...],
  "standardization_rules": {{ ... field name mappings ... }},
  "transformation_rules": {{ ... data cleaning rules ... }},
  "compatibility_notes": "notes on handling various receipt formats"
}}

IMPORTANT: The goal is a STANDARDIZED, UNIVERSAL schema that works well across all receipt types.
'''

print("\nCalling Ollama (qwen3:8b) to optimize schema with 9 receipts...")
save_prompt("02_SCHEMA_OPTIMIZATION_PROMPT", optimization_prompt)

try:
    optimization_response = call_ollama(optimization_prompt)
    print(f"\nResponse received ({len(optimization_response)} chars)")
    save_prompt("02_SCHEMA_OPTIMIZATION_RESPONSE", optimization_response)

    optimization_result = extract_json_from_response(optimization_response)
    if optimization_result:
        print("[OK] Successfully parsed optimization result")
        optimized_schema = optimization_result.get('optimized_schema', optimization_result)
    else:
        print("[WARN] Could not parse JSON, using refined default schema")
        optimized_schema = initial_schema
except Exception as e:
    print(f"Error calling Ollama: {e}")
    optimized_schema = initial_schema

print(f"\nOptimized Schema: {json.dumps(optimized_schema, indent=2)[:500]}...")

# ============================================================
# Workflow Step 3: Generate Final Production Schema
# ============================================================

print("\n" + "=" * 60)
print("STEP 3: Generate Final Production Schema")
print("=" * 60)

final_prompt = f'''You are an expert in standardizing JSON schemas for receipt extraction. Given the current schema and optimization results, create a FINAL clean, standardized JSON schema for receipt data extraction.

### CURRENT SCHEMA:
{json.dumps(optimized_schema, indent=2)}

### YOUR TASK:
1. Clean up and finalize the schema
2. Remove any redundancy or duplications
3. Ensure all field names are consistent (camelCase recommended)
4. Add reasonable default values where appropriate
5. Document the schema clearly

### OUTPUT FORMAT:
Return ONLY valid JSON (no markdown):
{{
  "merchant": {{
    "name": "string - store/merchant name",
    "address": "string - full address combined",
    "phone": "string - phone number if present",
    "tax_id": "string - tax identification if present"
  }},
  "transaction": {{
    "date": "string - date in YYYY-MM-DD format",
    "time": "string - time in HH:MM 24hr format",
    "receipt_number": "string - transaction/receipt ID",
    "clerk": "string - cashier name if present"
  }},
  "items": [
    {{
      "description": "string - item name/description",
      "quantity": number - quantity purchased",
      "unit_price": number - price per unit",
      "line_total": number - total for this line"
    }}
  ],
  "summary": {{
    "subtotal": number - subtotal before tax",
    "tax_amount": number - total tax amount",
    "total_amount": number - grand total",
    "tax_breakdown": [{{ "type": "string", "rate": number, "amount": number }}]
  }},
  "payment": {{
    "method": "string - CASH/DEBIT/CREDIT/etc",
    "amount_tendered": number - amount paid",
    "change_due": number - change given"
  }}
}}

IMPORTANT: Return ONLY the JSON schema, nothing else.
'''

print("\nCalling Ollama (qwen3:8b) to generate final production schema...")
save_prompt("03_FINAL_SCHEMA_PROMPT", final_prompt)

try:
    final_response = call_ollama(final_prompt)
    print(f"\nResponse received ({len(final_response)} chars)")
    save_prompt("03_FINAL_SCHEMA_RESPONSE", final_response)

    final_result = extract_json_from_response(final_response)
    if final_result:
        print("[OK] Successfully parsed final schema")
        final_schema = final_result
    else:
        print("[WARN] Could not parse JSON, using current schema")
        final_schema = optimized_schema
except Exception as e:
    print(f"Error calling Ollama: {e}")
    final_schema = optimized_schema

# ============================================================
# Save Final Schema
# ============================================================

print("\n" + "=" * 60)
print("FINAL OPTIMIZED JSON SCHEMA")
print("=" * 60)
print(json.dumps(final_schema, indent=2))

with open(SCHEMA_FILE, 'w', encoding='utf-8') as f:
    json.dump(final_schema, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Schema saved to: {SCHEMA_FILE}")
print(f"[OK] All prompts saved to: {PROMPTS_FILE}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("WORKFLOW SUMMARY")
print("=" * 60)
print(f"""
Step 1: Analyzed first receipt ({receipts_filenames[0]}) to generate initial schema
Step 2: Used 9 additional receipts to optimize and standardize the schema
Step 3: Generated final production-ready JSON schema

Files created:
  - {SCHEMA_FILE} - The optimized JSON schema
  - {PROMPTS_FILE} - All prompts and responses for record

Receipts processed:
  - {receipts_filenames[0]}
  - {receipts_filenames[1]} to {receipts_filenames[9]}
""")

print("Done!")