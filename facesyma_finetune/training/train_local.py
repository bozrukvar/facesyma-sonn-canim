#!/usr/bin/env python3
"""
training/train_local.py
=======================
Optimized for Local GPU (4GB VRAM) - Windows Compatible

Uses 16-bit training (instead of 4-bit) to avoid bitsandbytes/triton issues on Windows.

Estimated memory: 3.5-4.0 GB
Training time: 4-6 hours per epoch
"""

import os
import sys
import json
import argparse
from pathlib import Path

# ── Environment Setup ──────────────────────────────────────────────────────
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

print(f"\n{'='*70}")
print(f"FACESYMA PHASE 2B - LOCAL GPU TRAINING (16-bit)")
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
    from unsloth import FastLanguageModel
    print("✓ Unsloth loaded\n")
except Exception as e:
    print(f"ERROR loading Unsloth: {e}")
    sys.exit(1)

from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer

# ── Constants ──────────────────────────────────────────────────────────────
BASE_MODEL = "unsloth/Meta-Llama-3.1-8B-Instruct"  # Full precision (not 4-bit)
OUTPUT_DIR = "facesyma-llama3.1-8b-lora-local"
MAX_SEQ_LEN = 1024
BATCH_SIZE = 1
GRAD_ACCUM = 8
LORA_R = 8


def load_model():
    """Load Llama 3.1 8B (16-bit)"""
    print(f"[1/4] Loading base model (16-bit)...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=torch.float16,  # 16-bit instead of 4-bit
        load_in_4bit=False,   # Disable 4-bit quantization
    )

    print(f"✓ Model loaded")
    return model, tokenizer


def add_lora(model):
    """Add LoRA adapters"""
    print(f"\n[2/4] Adding LoRA adapters...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        use_rslora=False,
    )

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"✓ LoRA added (r={LORA_R})")
    print(f"  Trainable: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)")

    return model


def load_data(dataset_path):
    """Load JSONL dataset"""
    print(f"\n[3/4] Loading dataset...")

    if not Path(dataset_path).exists():
        print(f"ERROR: {dataset_path} not found")
        sys.exit(1)

    dataset = load_dataset("json", data_files=dataset_path, split="train")
    print(f"✓ Loaded {len(dataset)} examples")

    return dataset


def train(model, tokenizer, dataset, output_dir, epochs=3):
    """Fine-tune with 16-bit training"""
    print(f"\n[4/4] Starting training...")
    print(f"  Output: {output_dir}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Grad accum: {GRAD_ACCUM}")
    print(f"  Max seq: {MAX_SEQ_LEN}")
    print(f"  LoRA rank: {LORA_R}")
    print(f"  Estimated time: 4-6 hours per epoch\n")

    training_args = TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        warmup_steps=50,
        num_train_epochs=epochs,
        learning_rate=2e-4,
        fp16=True,  # 16-bit floating point
        bf16=False,
        logging_steps=10,
        optim="adamw_torch",  # Use torch optimizer (more compatible)
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir=output_dir,
        report_to="none",
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,
        max_grad_norm=1.0,
        dataloader_num_workers=0,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="messages",
        max_seq_length=MAX_SEQ_LEN,
        dataset_kwargs={
            "add_special_tokens": False,
            "append_concat_token": False,
        },
        packing=True,
        args=training_args,
    )

    try:
        print("Training started. You can stop with Ctrl+C.\n")
        trainer.train()
        print("\n✓ Training completed!")
        return True
    except KeyboardInterrupt:
        print("\n⚠ Training interrupted")
        return False
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print("\n❌ Out of memory")
            print("Try reducing: MAX_SEQ_LEN, GRAD_ACCUM, or BATCH_SIZE")
            sys.exit(1)
        else:
            raise


def main():
    parser = argparse.ArgumentParser()
    _addarg = parser.add_argument
    _addarg("--dataset", required=True, help="Path to JSONL dataset")
    _addarg("--epochs", type=int, default=3, help="Number of epochs")
    _addarg("--output", default=OUTPUT_DIR, help="Output directory")

    args = parser.parse_args()

    # Load and train
    model, tokenizer = load_model()
    model = add_lora(model)
    dataset = load_data(args.dataset)
    success = train(model, tokenizer, dataset, args.output, args.epochs)

    if success:
        print(f"\n{'='*70}")
        print(f"✅ ALL DONE!")
        print(f"{'='*70}")
        print(f"\nModel saved: {args.output}")
        print(f"\nNext steps:")
        print(f"  1. Copy to: facesyma_finetune/serving/models/")
        print(f"  2. Deploy: docker-compose up")


if __name__ == "__main__":
    main()
