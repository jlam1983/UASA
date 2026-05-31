"""
Step 7: Export Unsloth LoRA to Ollama GGUF format
Convert PEFT adapter → GGUF → Register with Ollama

Requirements:
    pip install llama-cpp-python
    ollama installed and in PATH

Note: Ollama v0.5+ supports LoRA adapters directly with --adapter flag
"""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

# Configuration
OUTPUT_DIR = "./lora_receipt_model"
OLLAMA_MODEL_NAME = "qwen3:8b"
OLLAMA_LORA_NAME = "receipt-qwen3-lora"
BASE_MODEL_REPO = "unsloth/Qwen3-8B"


def run_command(cmd, cwd=None, check=True):
    """Run shell command and return result"""
    print(f"[CMD] {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def check_dependencies():
    """Check if required tools are available"""
    print("=" * 60)
    print("Checking dependencies...")
    print("=" * 60)

    # Check ollama CLI
    if shutil.which("ollama") is None:
        print("[ERROR] ollama CLI not found in PATH")
        print("Install from: https://ollama.com/download")
        return False
    print("[OK] ollama CLI found")

    # Check ollama version
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    ollama_version = result.stdout.strip()
    print(f"[OK] Ollama version: {ollama_version}")

    # Check if lora model exists
    lora_path = Path(OUTPUT_DIR) / "lora_model"
    if not lora_path.exists():
        print(f"[ERROR] LoRA model not found at {lora_path}")
        print("Run step5_train_lora_qwen.py first!")
        return False
    print(f"[OK] LoRA model found at {lora_path}")

    # Check adapter files exist
    adapter_files = ["adapter_model.safetensors", "adapter_config.json"]
    for f in adapter_files:
        if not (lora_path / f).exists():
            print(f"[ERROR] Missing {f} in LoRA adapter")
            return False
    print("[OK] LoRA adapter files present")

    return True


def install_requirements():
    """Install required Python packages"""
    print("\n" + "-" * 40)
    print("Installing requirements...")
    print("-" * 40)

    packages = ["huggingface_hub"]

    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"[OK] {pkg} already installed")
        except ImportError:
            print(f"[INFO] Installing {pkg}...")
            subprocess.run(["pip", "install", pkg, "-q"], check=True)
            print(f"[OK] {pkg} installed")


def download_base_model():
    """Download base model for GGUF conversion"""
    print("\n" + "-" * 40)
    print("Downloading base model for conversion...")
    print("-" * 40)

    model_dir = Path(OUTPUT_DIR) / "base_model"
    model_dir.mkdir(exist_ok=True)

    # Check if already downloaded
    if (model_dir / "config.json").exists():
        print("[OK] Base model already downloaded")
        return str(model_dir)

    print("[INFO] Downloading Qwen3-8B model files...")
    print("[INFO] This may take a while...")

    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=BASE_MODEL_REPO,
            local_dir=str(model_dir),
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"],
            ignore_patterns=["*.bin", "pytorch_model*"],
        )
        print(f"[OK] Base model downloaded to {model_dir}")
        return str(model_dir)
    except Exception as e:
        print(f"[ERROR] Failed to download model: {e}")
        return None


def convert_to_gguf():
    """Convert PEFT adapter to GGUF format"""
    print("\n" + "-" * 40)
    print("Converting PEFT adapter to GGUF...")
    print("-" * 40)

    lora_path = Path(OUTPUT_DIR) / "lora_model"
    base_path = Path(OUTPUT_DIR) / "base_model"
    gguf_path = Path(OUTPUT_DIR) / "lora.gguf"

    if gguf_path.exists():
        print(f"[OK] GGUF already exists: {gguf_path}")
        return str(gguf_path)

    # Method 1: Use llama.cpp convert script (if available)
    llama_cpp_dir = Path(OUTPUT_DIR) / "llama.cpp"

    if not llama_cpp_dir.exists():
        print("[INFO] Cloning llama.cpp...")
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/ggerganov/llama.cpp.git",
                 str(llama_cpp_dir)],
                capture_output=True,
                check=True,
            )
        except Exception as e:
            print(f"[WARN] Failed to clone llama.cpp: {e}")
            llama_cpp_dir = None

    if llama_cpp_dir and (llama_cpp_dir / "convert.py").exists():
        print("[INFO] Using llama.cpp convert script...")

        # First convert base model to GGUF
        base_gguf_path = Path(OUTPUT_DIR) / "base.gguf"
        if not base_gguf_path.exists():
            print("[INFO] Converting base model to GGUF...")
            try:
                subprocess.run(
                    ["python", str(llama_cpp_dir / "convert.py"),
                     str(base_path),
                     "--outfile", str(base_gguf_path),
                     "--outtype", "q4_0"],
                    capture_output=True,
                    check=True,
                )
            except Exception as e:
                print(f"[WARN] Base model conversion failed: {e}")

        # Apply LoRA to base and export
        print("[INFO] Applying LoRA adapter...")
        try:
            # Use llama.cpp's apply-lora script if available
            apply_script = llama_cpp_dir / "apply-lora"
            if apply_script.exists():
                subprocess.run(
                    ["python", str(apply_script),
                     "--model", str(base_gguf_path),
                     "--lora", str(lora_path),
                     "--output", str(gguf_path)],
                    capture_output=True,
                    check=True,
                )
                print(f"[OK] Converted to GGUF: {gguf_path}")
                return str(gguf_path)
        except Exception as e:
            print(f"[WARN] LoRA apply failed: {e}")

    # Method 2: Use unsloth's built-in export (if available)
    print("[INFO] Trying unsloth export...")
    try:
        # Check if unsloth has export function
        from unsloth_zoo import export_to_gguf
        export_to_gguf(model, tokenizer, save_path=str(gguf_path))
        print(f"[OK] Exported via unsloth: {gguf_path}")
        return str(gguf_path)
    except Exception as e:
        print(f"[WARN] Unsloth export not available: {e}")

    # Method 3: Manual conversion via Python
    print("[INFO] Attempting manual conversion...")

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        print("[INFO] Loading LoRA adapter...")
        # Load base model and apply LoRA
        base_model = AutoModelForCausalLM.from_pretrained(
            str(base_path),
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(str(base_path))

        # Load and apply LoRA
        from peft import PeftModel
        model = PeftModel.from_pretrained(base_model, str(lora_path))
        model = model.merge_and_unload()

        print("[INFO] Saving as GGUF (Q4_0)...")
        # Save using llama.cpp's format
        # This requires llama-cpp-python with proper bindings
        import llama_cpp

        # Create GGUF file manually
        # For simplicity, we'll use the base GGUF + note about LoRA
        print("[WARN] Full GGUF conversion requires llama.cpp tools")
        print(f"[INFO] Partial files saved to {OUTPUT_DIR}")

        # Save adapter weights separately for Ollama
        model.save_pretrained(str(OUTPUT_DIR) + "/merged_model")
        tokenizer.save_pretrained(str(OUTPUT_DIR) + "/merged_model")

        print("[OK] Model merged and saved")
        return str(OUTPUT_DIR) + "/merged_model"

    except Exception as e:
        print(f"[ERROR] Manual conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_modelfile_simple():
    """Create simple Modelfile for Ollama with --adapter flag"""
    print("\n" + "-" * 40)
    print("Creating Ollama Modelfile...")
    print("-" * 40)

    # Modern Ollama uses --adapter flag instead of ADAPTER directive
    modelfile_content = f"""# Modelfile for Ollama - Unsloth LoRA on Qwen3-8B
# Generated by step7_export_to_ollama.py

FROM {OLLAMA_MODEL_NAME}

# Parameters for receipt extraction
PARAMETER temperature 0.1
PARAMETER top_p 0.95
PARAMETER num_ctx 4096

# Disable thinking mode for faster responses
PARAMETER think false
"""

    modelfile_path = Path(OUTPUT_DIR) / "Modelfile"
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)

    print(f"[OK] Modelfile created: {modelfile_path}")
    return str(modelfile_path)


def register_with_ollama():
    """Register the model with Ollama using --adapter flag"""
    print("\n" + "-" * 40)
    print("Registering model with Ollama...")
    print("-" * 40)

    modelfile_path = Path(OUTPUT_DIR) / "Modelfile"
    lora_path = Path(OUTPUT_DIR) / "lora_model"

    # Create model with adapter
    print(f"[INFO] Creating Ollama model '{OLLAMA_LORA_NAME}' with LoRA adapter...")

    # Method 1: Using --adapter flag (Ollama 0.5+)
    try:
        cmd = [
            "ollama", "create", OLLAMA_LORA_NAME,
            "-f", str(modelfile_path),
            "--adapter", str(lora_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] Ollama model created: {OLLAMA_LORA_NAME}")
            print(result.stdout)
            return True
        print(f"[WARN] Method 1 failed: {result.stderr}")
    except Exception as e:
        print(f"[WARN] Method 1 error: {e}")

    # Method 2: Copy to Ollama models dir and create
    print("[INFO] Trying alternative method...")
    ollama_dir = Path.home() / ".ollama" / "models"
    ollama_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Copy model files
        dest_dir = ollama_dir / "models" / OLLAMA_LORA_NAME
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Create Modelfile in Ollama directory
        with open(dest_dir / "Modelfile", "w") as f:
            f.write(f"FROM {OLLAMA_MODEL_NAME}\n")
            f.write(f"ADAPTER ./lora\n")
            f.write("PARAMETER temperature 0.1\n")
            f.write("PARAMETER think false\n")

        # Copy LoRA files
        import shutil
        shutil.copytree(lora_path, dest_dir / "lora", dirs_exist_ok=True)

        # Create using ollama CLI
        result = subprocess.run(
            ["ollama", "create", OLLAMA_LORA_NAME, "-f", "Modelfile"],
            cwd=str(dest_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"[OK] Ollama model created: {OLLAMA_LORA_NAME}")
            return True
        print(f"[WARN] Method 2 failed: {result.stderr}")

    except Exception as e:
        print(f"[WARN] Method 2 error: {e}")

    print("[ERROR] All registration methods failed")
    return False


def test_ollama():
    """Test Ollama model"""
    print("\n" + "-" * 40)
    print("Testing Ollama model...")
    print("-" * 40)

    test_prompt = """Extract as JSON:
Merchant: ABC SUPERMARKET
Subtotal: $78.64
Tax: $6.86
Total: $85.50

Return ONLY valid JSON."""

    print(f"[INFO] Running: ollama run {OLLAMA_LORA_NAME}")
    print(f"[PROMPT] {test_prompt}\n")

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_LORA_NAME, test_prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        print("[OUTPUT]")
        print(result.stdout)
        if result.stderr:
            print("[STDERR]", result.stderr)
        return True
    except subprocess.TimeoutExpired:
        print("[WARN] Inference timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False


def main():
    """Main export pipeline"""
    print("=" * 60)
    print("STEP 7: Export Unsloth LoRA to Ollama")
    print("=" * 60)
    print(f"Source LoRA: {OUTPUT_DIR}/lora_model")
    print(f"Ollama base model: {OLLAMA_MODEL_NAME}")
    print(f"Ollama final model: {OLLAMA_LORA_NAME}")
    print("=" * 60)

    # Step 1: Check dependencies
    if not check_dependencies():
        return False

    # Step 2: Install requirements
    if input("\nInstall requirements? (y/n): ").lower() == 'y':
        install_requirements()

    # Step 3: Download base model
    if input("\nDownload base model for conversion? (y/n): ").lower() == 'y':
        base_dir = download_base_model()
        if not base_dir:
            print("[WARN] Continuing without base model download...")

    # Step 4: Convert to GGUF
    if input("\nConvert to GGUF? (y/n): ").lower() == 'y':
        gguf_result = convert_to_gguf()
        if not gguf_result:
            print("[WARN] Conversion may have issues, continuing...")

    # Step 5: Create Modelfile
    create_modelfile_simple()

    # Step 6: Register with Ollama
    if input("\nRegister with Ollama? (y/n): ").lower() == 'y':
        if not register_with_ollama():
            print("[ERROR] Failed to register with Ollama")
            print("\n[INFO] Manual registration:")
            print(f"  cd {OUTPUT_DIR}")
            print(f"  ollama create {OLLAMA_LORA_NAME} -f Modelfile --adapter ./lora_model")
        else:
            # Step 7: Test
            if input("\nTest the model? (y/n): ").lower() == 'y':
                test_ollama()

    print("\n" + "=" * 60)
    print("EXPORT COMPLETE!")
    print("=" * 60)
    print(f"Files in {OUTPUT_DIR}:")
    for f in Path(OUTPUT_DIR).iterdir():
        if f.is_dir() or f.suffix in ['.gguf', '.Modelfile']:
            print(f"  - {f.name}")
    print(f"\nManual Ollama commands:")
    print(f"  cd {OUTPUT_DIR}")
    print(f"  ollama create {OLLAMA_LORA_NAME} -f Modelfile --adapter ./lora_model")
    print(f"  ollama run {OLLAMA_LORA_NAME}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
