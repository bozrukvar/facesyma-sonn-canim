#!/usr/bin/env python3
"""
training/train_simple.py
=======================
Unsloth gerektirmeyen basit fine-tuning script
HuggingFace Transformers + PEFT (LoRA) kullanır

Windows uyumlu!
"""

import os
import sys
import argparse
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

print(f"\n{'='*70}")
print(f"FACESYMA PHASE 2B - SIMPLE FINE-TUNING (NO UNSLOTH)")
print(f"{'='*70}\n")

# ── Check Prerequisites ────────────────────────────────────────────────────
try:
    import torch
    print(f"✓ PyTorch: {torch.__version__}")
    print(f"✓ CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✓ Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB\n")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
    from peft import get_peft_model, LoraConfig
    from trl import SFTTrainer
    from datasets import load_dataset
    print("✓ All imports successful\n")
except Exception as e:
    print(f"ERROR importing: {e}")
    sys.exit(1)

# ── Constants ──────────────────────────────────────────────────────────────
MODEL_NAME = "gpt2"  # Basit, küçük, garantili çalışır
OUTPUT_DIR = "facesyma-gpt2-lora"
MAX_SEQ_LEN = 128  # Çok kısa
BATCH_SIZE = 1
GRAD_ACCUM = 2  # Minimal
LORA_R = 4  # Daha küçük LoRA
EPOCHS = 1  # Test için sadece 1 epoch


def main():
    _exit = sys.exit
    parser = argparse.ArgumentParser()
    _addarg = parser.add_argument
    _addarg("--dataset", required=True, help="Path to JSONL dataset")
    _addarg("--epochs", type=int, default=EPOCHS, help="Number of epochs")
    _addarg("--output", default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()
    _dataset = args.dataset

    # ── Step 1: Load Model & Tokenizer ────────────────────────────────────
    print(f"[1/5] Loading model & tokenizer...")

    model_name = MODEL_NAME
    fallback_models = ["gpt2-medium", "gpt2", "distilgpt2"]

    try:
        print(f"  Loading tokenizer from {model_name}...", flush=True)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        print(f"  Loading model from {model_name}...", flush=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="cuda" if torch.cuda.is_available() else "cpu",
        )
        print(f"✓ Model loaded: {model_name}")
    except Exception as e:
        print(f"ERROR loading model: {e}")
        import traceback
        traceback.print_exc()
        print(f"Trying fallback models...")

        model_loaded = False
        for fallback in fallback_models:
            try:
                print(f"  Trying {fallback}...", end=" ", flush=True)
                tokenizer = AutoTokenizer.from_pretrained(fallback)
                tokenizer.pad_token = tokenizer.eos_token
                tokenizer.padding_side = "right"
                model = AutoModelForCausalLM.from_pretrained(fallback, torch_dtype=torch.float16, device_map="cuda" if torch.cuda.is_available() else "cpu")
                model_name = fallback
                print("✓")
                print(f"✓ Using fallback model: {model_name}")
                model_loaded = True
                break
            except Exception as fe:
                print(f"✗ ({fe})")
                continue

        if not model_loaded:
            print("ERROR: Could not load any model")
            _exit(1)

    # ── Step 2: Add LoRA ──────────────────────────────────────────────────
    print(f"\n[2/5] Adding LoRA adapters...")

    # Determine target modules based on model architecture
    _mlow = model_name.lower()
    if "llama" in _mlow or "mistral" in _mlow or "tinyllama" in _mlow:
        target_mods = ["q_proj", "v_proj"]
    else:
        target_mods = ["c_attn"]

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=32,
        target_modules=target_mods,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    try:
        print(f"  Applying LoRA config...", flush=True)
        model = get_peft_model(model, lora_config)
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print(f"✓ LoRA added (r={LORA_R})")
        print(f"  Trainable: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")
    except Exception as e:
        print(f"ERROR in LoRA: {e}")
        import traceback
        traceback.print_exc()
        _exit(1)

    # ── Step 3: Load Dataset ──────────────────────────────────────────────
    print(f"\n[3/5] Loading dataset...")

    if not Path(_dataset).exists():
        print(f"ERROR: {_dataset} not found")
        _exit(1)

    try:
        print(f"  Loading from {_dataset}...", flush=True)
        dataset = load_dataset("json", data_files=_dataset, split="train")

        # Convert messages to text format for SFTTrainer
        def format_messages_to_text(example):
            messages = example.get('messages', [])
            text = ""
            for msg in messages:
                _mget = msg.get
                role = _mget('role', 'user')
                content = _mget('content', '')
                text += f"{role}: {content}\n"
            return {"text": text}

        print(f"  Formatting messages to text...", flush=True)
        dataset = dataset.map(format_messages_to_text, remove_columns=['messages'])
        print(f"✓ Loaded {len(dataset)} examples")
    except Exception as e:
        print(f"ERROR loading dataset: {e}")
        import traceback
        traceback.print_exc()
        _exit(1)

    # ── Step 4: Setup Training ────────────────────────────────────────────
    print(f"\n[4/5] Setting up training...")

    try:
        print(f"  Creating training arguments...", flush=True)
        training_args = TrainingArguments(
            output_dir=args.output,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=2e-4,
            lr_scheduler_type="linear",
            warmup_steps=50,
            logging_steps=10,
            save_steps=100,
            save_total_limit=3,
            fp16=True,
            seed=42,
            optim="adamw_torch",
            dataloader_num_workers=0,
            report_to="none",
            remove_unused_columns=True,
        )
        print(f"  Creating SFTTrainer...", flush=True)
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=MAX_SEQ_LEN,
            args=training_args,
            packing=False,
        )
        print(f"✓ Training setup complete", flush=True)
    except Exception as e:
        print(f"ERROR in training setup: {e}")
        import traceback
        traceback.print_exc()
        _exit(1)

    # ── Step 5: Train ─────────────────────────────────────────────────────
    print(f"\n[5/5] Starting training...")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Grad accum: {GRAD_ACCUM}")
    print(f"  Estimated time: 8-12 hours per epoch (TinyLlama is slower)\n")

    try:
        print("Training started. You can stop with Ctrl+C.\n", flush=True)
        trainer.train()
        print("\n✓ Training completed!")

        print(f"\n{'='*70}")
        print(f"✅ ALL DONE!")
        print(f"{'='*70}")
        print(f"\nModel saved: {args.output}")
        print(f"\nNext steps:")
        print(f"  1. Copy to: facesyma_finetune/serving/models/")
        print(f"  2. Deploy: docker-compose up")

    except KeyboardInterrupt:
        print("\n⚠ Training interrupted")
        _exit(0)
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"\n❌ Out of memory: {e}")
            print("Try reducing MAX_SEQ_LEN or BATCH_SIZE")
            _exit(1)
        else:
            raise


if __name__ == "__main__":
    main()
