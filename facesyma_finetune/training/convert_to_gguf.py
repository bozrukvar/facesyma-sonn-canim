"""
Merge LoRA + base model → convert to GGUF
"""
import os
import sys
from pathlib import Path

BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
LORA_PATH = "facesyma-tinyllama-lora/final"
OUTPUT_DIR = "facesyma-tinyllama-merged"
GGUF_PATH = "facesyma-tinyllama-q4.gguf"

print("\n" + "="*70)
print("MERGING LORA + BASE MODEL")
print("="*70 + "\n")

# Step 1: Merge LoRA
print("1️⃣ Merging LoRA with base model...")
try:
    from peft import AutoPeftModelForCausalLM
    from transformers import AutoTokenizer
    import torch

    print(f"   Loading PEFT model: {LORA_PATH}")
    model = AutoPeftModelForCausalLM.from_pretrained(LORA_PATH, device_map="auto", torch_dtype=torch.float16)

    print(f"   Merging and unloading...")
    merged = model.merge_and_unload()

    print(f"   Saving merged model: {OUTPUT_DIR}/")
    merged.save_pretrained(OUTPUT_DIR)

    tokenizer = AutoTokenizer.from_pretrained(LORA_PATH)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("✅ Merge complete!\n")

except Exception as e:
    print(f"❌ Merge failed: {e}\n")
    sys.exit(1)

print(f"✅ Merged model saved to: {OUTPUT_DIR}/")
print(f"\nNext steps:")
print(f"1. pip install llama-cpp-python")
print(f"2. python -m llama_cpp.llama_cpp_python.scripts.convert_model_to_gguf {OUTPUT_DIR}")
print(f"   --outtype q4_k_m --outfile {GGUF_PATH}")
