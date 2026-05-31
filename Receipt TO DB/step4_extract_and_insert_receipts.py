"""
Step 4: LLM Receipt Extraction & Database Insertion
Uses Ollama LLAVA model to extract receipt data
Inserts into SQLite database (skips if filename already exists)
"""

import sqlite3
import pandas as pd
import json
import os
import ollama
import re
from datetime import datetime

# Configuration
DATABASE_PATH = "buysel.db"
RECEIPTS_CSV = "receipts_output.csv"
IMAGE_FOLDER = "JReceiptLora/Receipt"
OLLAMA_MODEL = "llava"

# Extraction prompt from prompts_record.txt (FINAL_EXTRACTION_PROMPT)
EXTRACTION_PROMPT = """You are an expert receipt data extraction assistant. Extract structured information from the receipt image and return it as clean JSON.

### EXTRACTION RULES:
1. Output ONLY valid JSON - no markdown, no explanatory text
2. Use null for missing fields - do NOT guess or fabricate data
3. Transform data appropriately:
   - Remove currency symbols ($, €, £, etc.) from amounts
   - Normalize dates to YYYY-MM-DD format
   - Normalize times to HH:MM format
   - Convert all numeric values to numbers (not strings)
4. For line items: only include items with a verifiable description AND total
5. If a line item row is blank or incomplete, SKIP it
6. merchant.tax_id may be labeled as "TAX ID", "EIN", "VAT", "GST", or similar

### STANDARDIZED JSON SCHEMA:
{
  "merchant": {
    "name": "string - store/merchant name (e.g., WAL*MART, Trader Joe's)",
    "address": "string - street address, city, state, zip (combined)",
    "phone": "string - phone number if present",
    "tax_id": "string - tax identification number if visible"
  },
  "transaction": {
    "date": "string - date in YYYY-MM-DD format",
    "time": "string - time in HH:MM format (24-hour)",
    "receipt_number": "string - receipt/transaction ID",
    "clerk": "string - cashier name if present"
  },
  "items": [
    {
      "description": "string - item name/description",
      "quantity": number - quantity purchased,
      "unit_price": number - price per unit,
      "line_total": number - total for this line item
    }
  ],
  "summary": {
    "subtotal": number - subtotal before tax,
    "tax_amount": number - total tax,
    "total_amount": number - grand total,
    "tax_breakdown": [
      {"type": "string - tax type (sales, VAT, etc.)", "rate": number, "amount": number}
    ]
  },
  "payment": {
    "method": "string - CASH, DEBIT, CREDIT, etc.",
    "amount_tendered": number - amount paid,
    "change_due": number - change given back
  }
}

### OUTPUT REQUIREMENTS:
- Return ONLY the JSON object, no markdown, no explanation
- All monetary values as numbers (not strings)
- Date as YYYY-MM-DD, time as HH:MM
"""

client = ollama.Client("http://localhost:11434")

def get_existing_filenames():
    """Get set of filenames already in database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT receipt_number FROM receipts")
    existing = set(row[0] for row in cursor.fetchall())
    conn.close()
    return existing

def clean_json_response(text):
    """Remove markdown formatting from LLM response"""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def extract_json_from_response(text):
    """Extract JSON from response"""
    cleaned = clean_json_response(text)

    # Try to find JSON object/array pattern
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try parsing the whole thing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    return None

def extract_receipt_with_ollama(image_path):
    """Extract receipt data from image using Ollama LLAVA"""
    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': EXTRACTION_PROMPT,
                    'images': [image_path]
                }
            ],
            options={"temperature": 0.1, "num_predict": 1000}
        )

        raw_output = response['message']['content']
        result = extract_json_from_response(raw_output)
        return result, raw_output

    except Exception as e:
        print(f"[ERROR] Ollama error: {e}")
        return None, str(e)

def insert_receipt(receipt_data, filename):
    """Insert receipt data into SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Extract data from JSON
        merchant = receipt_data.get('merchant', {})
        transaction = receipt_data.get('transaction', {})
        summary = receipt_data.get('summary', {})
        payment = receipt_data.get('payment', {})
        items = receipt_data.get('items', [])
        tax_breakdown = summary.get('tax_breakdown', [])

        # Insert main receipt record
        cursor.execute("""
            INSERT INTO receipts (
                receipt_number, merchant_name, merchant_address, merchant_phone,
                merchant_tax_id, transaction_date, transaction_time, clerk,
                subtotal, tax_amount, total_amount,
                payment_method, amount_tendered, change_due
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            merchant.get('name'),
            merchant.get('address'),
            merchant.get('phone'),
            merchant.get('tax_id'),
            transaction.get('date'),
            transaction.get('time'),
            transaction.get('clerk'),
            summary.get('subtotal'),
            summary.get('tax_amount'),
            summary.get('total_amount'),
            payment.get('method'),
            payment.get('amount_tendered'),
            payment.get('change_due')
        ))

        receipt_id = cursor.lastrowid

        # Insert line items
        for item in items:
            cursor.execute("""
                INSERT INTO receipt_items (receipt_id, description, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?)
            """, (
                receipt_id,
                item.get('description'),
                item.get('quantity'),
                item.get('unit_price'),
                item.get('line_total')
            ))

        # Insert tax breakdown
        for tax in tax_breakdown:
            cursor.execute("""
                INSERT INTO receipt_tax_breakdown (receipt_id, tax_type, tax_rate, tax_amount)
                VALUES (?, ?, ?, ?)
            """, (
                receipt_id,
                tax.get('type'),
                tax.get('rate'),
                tax.get('amount')
            ))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Insert failed: {e}")
        return False
    finally:
        conn.close()

def process_receipts():
    """Main processing function"""
    print("=" * 60)
    print("STEP 4: LLM Receipt Extraction & Database Insertion")
    print("=" * 60)

    # Check database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"[ERROR] Database not found: {DATABASE_PATH}")
        print("Please run init_sqlite_db.py first.")
        return

    # Check receipts CSV exists
    if not os.path.exists(RECEIPTS_CSV):
        print(f"[ERROR] Receipts CSV not found: {RECEIPTS_CSV}")
        return

    # Check image folder exists
    if not os.path.exists(IMAGE_FOLDER):
        print(f"[ERROR] Image folder not found: {IMAGE_FOLDER}")
        return

    # Get existing filenames in database
    existing_filenames = get_existing_filenames()
    print(f"[INFO] Existing receipts in database: {len(existing_filenames)}")

    # Load receipts CSV
    df = pd.read_csv(RECEIPTS_CSV)
    unique_df = df.drop_duplicates(subset='filename').reset_index(drop=True)
    print(f"[INFO] Total unique receipts in CSV: {len(unique_df)}")

    # Filter to unprocessed receipts
    unprocessed = unique_df[~unique_df['filename'].isin(existing_filenames)]
    print(f"[INFO] New receipts to process: {len(unprocessed)}")

    if unprocessed.empty:
        print("[INFO] No new receipts to process. All done!")
        return

    # Process each unprocessed receipt
    success_count = 0
    error_count = 0

    print("\n" + "-" * 40)
    print(f"Processing {len(unprocessed)} receipts...")
    print("-" * 40)

    for idx, row in unprocessed.iterrows():
        filename = row['filename']
        image_path = os.path.join(IMAGE_FOLDER, filename)

        print(f"\n[{idx+1}/{len(unprocessed)}] Processing: {filename}")

        # Check if image exists
        if not os.path.exists(image_path):
            print(f"  [SKIP] Image not found: {image_path}")
            error_count += 1
            continue

        # Extract data with LLM
        print(f"  [LLM] Calling Ollama LLAVA...")
        result, raw_output = extract_receipt_with_ollama(image_path)

        if result is None:
            print(f"  [ERROR] Failed to extract data")
            # Save raw output for debugging
            error_log = f"error_{filename}.txt"
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"Filename: {filename}\n\n")
                f.write(f"Raw Output:\n{raw_output}")
            print(f"  [DEBUG] Saved error log to: {error_log}")
            error_count += 1
            continue

        # Insert into database
        if insert_receipt(result, filename):
            print(f"  [OK] Inserted into database")
            success_count += 1
        else:
            print(f"  [ERROR] Failed to insert")
            error_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total in DB: {len(get_existing_filenames())}")

if __name__ == "__main__":
    process_receipts()