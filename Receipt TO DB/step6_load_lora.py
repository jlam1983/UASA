"""
Step 6: Load trained LoRA and run inference on Qwen3-8B
"""
import os
os.environ["UNSLOTH_FORCE_FALLBACK"] = "1"
os.environ["UNSLOTH_IS_PRESENT"] = "1"
os.environ["UNSLOTH_DISABLE_AUTO_UPDATES"] = "1"

import torch
from unsloth import FastLanguageModel

# Configuration
OUTPUT_DIR = "lora_receipt_model"
MAX_SEQ_LENGTH = 1024

def load_lora_model():
    """Load base model + trained LoRA adapters"""
    print("=" * 60)
    print("Loading Qwen3-8B + trained LoRA")
    print("=" * 60)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen3-8B",
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )

    # Load trained LoRA adapters
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
    model.load_adapter(f"{OUTPUT_DIR}/lora_model", "lora_model")  # FIXED

    # Inference mode
    FastLanguageModel.for_inference(model)

    print("[OK] LoRA model loaded and ready for inference")
    return model, tokenizer


def extract_receipt(image_path: str) -> str:
    """
    Placeholder: OCR → extracted text from receipt image.
    Replace with your OCR pipeline.
    """
    return """
Merchant: ABC SUPERMARKET
Address: 123 Main Street, Springfield IL 62701
Phone: (555) 123-4567
Tax ID: 12-3456789
Date: 2026-01-15
Time: 14:32
Clerk: John
Payment: CREDIT $85.50 / Change: $14.50
Subtotal: $78.64
Tax: $6.86
Total: $85.50

Items:
  - Milk 2% 1gal: qty=1, price=$4.99, total=$4.99
  - Whole Wheat Bread: qty=2, price=$3.49, total=$6.98
  - Banana: qty=6, price=$0.59, total=$3.54
  - Organic Eggs 12ct: qty=1, price=$5.99, total=$5.99
  - Chicken Breast 2lb: qty=1, price=$12.99, total=$12.99
  -矿泉水 2L: qty=3, price=$1.99, total=$5.97

Tax breakdown:
  - State Tax: rate=0.0625, amount=$4.91
  - County Tax: rate=0.01, amount=$0.79
"""


def run_inference(model, tokenizer, receipt_text: str):
    """Run inference using the fine-tuned LoRA model"""
    prompt = f"""Extract structured data from this receipt and return as JSON.

{receipt_text}

Return only the JSON output."""

    messages = [
        {"role": "user", "content": prompt}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=False,
        think=False,
    )
    inputs = tokenizer([text], return_tensors="pt").to("cuda")

    outputs = model.generate(
        **inputs,
        max_new_tokens=1024,
        temperature=0.1,
        top_p=0.95,
        do_sample=False,
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract assistant response (after the last assistant turn)
    if "<|im_end|>" in response:
        response = response.split("<|im_end|>")[-1]
    if "<|im_start|>assistant" in response:
        response = response.split("<|im_start|>assistant")[-1]

    return response.strip()


def main():
    model, tokenizer = load_lora_model()

    # Sample receipt (replace with real OCR output)
    sample_receipt = extract_receipt("sample_receipt.jpg")

    print("\n" + "=" * 60)
    print("Running inference on sample receipt...")
    print("=" * 60)
    print("\n--- Input receipt text ---\n")
    print(sample_receipt)

    print("\n--- Model output ---\n")
    result = run_inference(model, tokenizer, sample_receipt)
    print(result)

    print("\n[OK] Inference complete!")


if __name__ == "__main__":
    main()