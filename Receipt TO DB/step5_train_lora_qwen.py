"""
Step 5: Train LoRA on Qwen3-8B using UnSLoth
Fine-tune on receipt extraction data from buysel.db
"""
import os
# CRITICAL: Env vars MUST be at the very top, before any unsloth imports
os.environ['UNSLOTH_DISABLE_FUSED_CROSS_ENTROPY'] = '1'
os.environ['UNSLOTH_FORCE_FALLBACK'] = '1'
os.environ["UNSLOTH_IS_PRESENT"] = "1"
os.environ["UNSLOTH_DISABLE_AUTO_UPDATES"] = "1"

import torch
from unsloth import FastLanguageModel  # Unsloth patches trl on import
from trl import SFTTrainer, SFTConfig   # Use trl's trainer (patched by unsloth)
from datasets import Dataset
# etc...
import sqlite3
import json
import os
from datetime import datetime
# Check and install dependencies
def install_if_missing(package, import_name=None):
    import_name = import_name or package
    try:
        __import__(import_name)
    except ImportError:
        import subprocess
        subprocess.run(['pip', 'install', package, '-q'], check=True)

install_if_missing('torch')
install_if_missing('unsloth')
install_if_missing('unsloth[kbit]')
install_if_missing('triton')

import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import Dataset

# Configuration
DATABASE_PATH = "buysel.db"
OUTPUT_DIR = "./lora_receipt_model"
MAX_SEQ_LENGTH = 1024
LOAD_IN_4BIT = True

def load_receipts_from_db():
    """Load receipt data from SQLite database"""
    print("=" * 60)
    print("Loading receipt data from database")
    print("=" * 60)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    receipts = []

    # Load all receipts with their items and tax info
    cursor.execute("""
        SELECT
            r.receipt_number, r.merchant_name, r.merchant_address, r.merchant_phone,
            r.merchant_tax_id, r.transaction_date, r.transaction_time, r.clerk,
            r.subtotal, r.tax_amount, r.total_amount,
            r.payment_method, r.amount_tendered, r.change_due
        FROM receipts r
    """)

    for row in cursor.fetchall():
        receipt_number = row[0]

        # Load items for this receipt
        cursor.execute("""
            SELECT description, quantity, unit_price, line_total
            FROM receipt_items WHERE receipt_id = (
                SELECT id FROM receipts WHERE receipt_number = ?
            )
        """, (receipt_number,))
        items = cursor.fetchall()

        # Load tax breakdown for this receipt
        cursor.execute("""
            SELECT tax_type, tax_rate, tax_amount FROM receipt_tax_breakdown
            WHERE receipt_id = (
                SELECT id FROM receipts WHERE receipt_number = ?
            )
        """, (receipt_number,))
        taxes = cursor.fetchall()

        receipt = {
            "receipt_number": receipt_number,
            "merchant": {
                "name": row[1],
                "address": row[2],
                "phone": row[3],
                "tax_id": row[4]
            },
            "transaction": {
                "date": row[5],
                "time": row[6],
                "clerk": row[7]
            },
            "summary": {
                "subtotal": row[8],
                "tax_amount": row[9],
                "total_amount": row[10]
            },
            "payment": {
                "method": row[11],
                "amount_tendered": row[12],
                "change_due": row[13]
            },
            "items": [
                {
                    "description": item[0],
                    "quantity": item[1],
                    "unit_price": item[2],
                    "line_total": item[3]
                } for item in items
            ],
            "tax_breakdown": [
                {
                    "type": tax[0],
                    "rate": tax[1],
                    "amount": tax[2]
                } for tax in taxes
            ]
        }
        receipts.append(receipt)

    conn.close()
    print(f"[OK] Loaded {len(receipts)} receipts from database")
    return receipts

def format_instruction_dataset(receipts):
    """Format receipts into instruction-tuning dataset"""
    dataset = []

    for receipt in receipts:
        if not receipt['merchant']['name']:
            continue

        # Build items text
        items_text_val = ""
        if receipt.get('items'):
            item_parts = []
            for item in receipt.get('items', []):
                if item.get('description'):
                    item_parts.append(
                        f"  - {item['description']}: "
                        f"qty={item['quantity']}, price={item['unit_price']}, total={item['line_total']}"
                    )
            if item_parts:
                items_text_val = "\n- Items:\n" + "\n".join(item_parts)

        # Build tax text
        tax_text_val = ""
        if receipt.get('tax_breakdown'):
            tax_parts = []
            for tax in receipt.get('tax_breakdown', []):
                if tax.get('type'):
                    tax_parts.append(
                        f"  - {tax['type']}: rate={tax['rate']}, amount={tax['amount']}"
                    )
            if tax_parts:
                tax_text_val = "\n- Tax breakdown:\n" + "\n".join(tax_parts)

        # Build input text
        m = receipt['merchant']
        t = receipt['transaction']
        s = receipt['summary']
        p = receipt['payment']

        input_parts = [
            'Extract receipt data and return as JSON.',
            '',
            f"Merchant: {m['name'] or 'N/A'}",
            f"Address: {m['address'] or 'N/A'}",
            f"Phone: {m['phone'] or 'N/A'}",
            f"Tax ID: {m['tax_id'] or 'N/A'}",
            f"Date: {t['date'] or 'N/A'}",
            f"Time: {t['time'] or 'N/A'}",
            f"Clerk: {t['clerk'] or 'N/A'}",
            f"Payment: {p['method'] or 'N/A'} {p['amount_tendered'] or ''} / Change: {p['change_due'] or 'N/A'}",
            f"Subtotal: {s['subtotal']}",
            f"Tax: {s['tax_amount']}",
            f"Total: {s['total_amount']}",
            items_text_val,
            tax_text_val
        ]

        input_text = "\n".join(input_parts)

        output_data = {
            "merchant": m,
            "transaction": t,
            "items": receipt.get('items', []),
            "summary": s,
            "payment": p
        }
        output_text = json.dumps(output_data, indent=2)

        dataset.append({
            "instruction": "Extract structured data from this receipt and return as JSON.",
            "input": input_text,
            "output": output_text
        })

    print(f"[OK] Formatted {len(dataset)} training examples")
    return dataset

def train_lora():
    """Main training function using UnSLoth"""
    print("=" * 60)
    print("STEP 5: Train LoRA on Qwen3-8B")
    print("=" * 60)

    # Check GPU
    if not torch.cuda.is_available():
        print("[ERROR] CUDA not available. Training requires GPU.")
        return False

    print(f"[OK] GPU: {torch.cuda.get_device_name(0)}")
    print(f"[OK] CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

    # Load data from database
    receipts = load_receipts_from_db()

    if len(receipts) < 3:
        print("[ERROR] Need at least 3 receipts to train. Add more data first.")
        return False

    # Format dataset
    formatted_data = format_instruction_dataset(receipts)

    # Pre-format dataset into a "text" column
    ds = Dataset.from_list(formatted_data)

    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs = examples["input"]
        outputs = examples["output"]
        texts = []
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            text = (
                f"<|im_start|>user\n{instruction}\n{input_text}<|im_end|>\n"
                f"<|im_start|>assistant\n{output}<|im_end|>\n"
            )
            texts.append(text)
        return {"text": texts}

    ds = ds.map(formatting_prompts_func, batched=True)

    # Load model with UnSLoth
    print("\n" + "-" * 40)
    print("Loading Qwen3-8B with UnSLoth...")
    print("-" * 40)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen3-8B",
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=LOAD_IN_4BIT,
    )

    # Add LoRA adapters
    print("[OK] Adding LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=4,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        processing_class=tokenizer,
        args=SFTConfig(
            output_dir=OUTPUT_DIR,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            warmup_steps=5,
            num_train_epochs=3,
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            report_to="none",
            save_steps=100,
            save_total_limit=2,
            max_length=256,              # REDUCE: was 1024
            packing=True,
            unsloth_num_chunks=16,         # KEY: Force chunking for low memory
            gradient_checkpointing=True,
        ),
    )

    # Train
    print("\n" + "-" * 40)
    print("Starting training...")
    print("-" * 40)

    trainer.train()

    # Save model
    print("\n" + "-" * 40)
    print("Saving LoRA adapter...")
    print("-" * 40)

    model.save_pretrained(f"{OUTPUT_DIR}/lora_model")
    tokenizer.save_pretrained(f"{OUTPUT_DIR}/lora_model")

    print(f"\n[OK] Training complete!")
    print(f"[OK] Model saved to: {OUTPUT_DIR}/lora_model")

    # Cleanup
    del model
    del trainer
    torch.cuda.empty_cache()

    return True

if __name__ == "__main__":
    success = train_lora()
    if not success:
        exit(1)