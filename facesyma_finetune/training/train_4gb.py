#!/usr/bin/env python3
"""
training/train_4gb.py
=====================
Optimized for 4GB VRAM GPUs (GeForce, GTX, RTX consumer cards)

Settings tuned for maximum memory efficiency:
  - Batch size: 1
  - Gradient accumulation: 8 (effective batch = 8)
  - LoRA rank: 8 (smaller, still effective)
  - Max sequence: 1024 (reduced from 2048)
  - Flash attention: Enabled
  - Gradient checkpointing: Enabled

Estimated memory: 3.5-4.0 GB (fits in 4GB)
Training time: 3-5 hours per epoch
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# ── Environment Setup ──────────────────────────────────────────────────────
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Use first GPU
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ── Imports ────────────────────────────────────────────────────────────────
try:
    import torch
    print(f"✓ PyTorch {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✓ Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
except ImportError:
    print("ERROR: PyTorch not installed")
    sys.exit(1)

try:
    from unsloth import FastLanguageModel
except ImportError:
    print("ERROR: unsloth not installed")
    print("Install: pip install 'unsloth[cu118-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git'")
    sys.exit(1)

from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer


# ── Constants ──────────────────────────────────────────────────────────────
BASE_MODEL = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
OUTPUT_DIR = "facesyma-llama3.1-8b-lora-4gb"
MAX_SEQ_LEN = 1024  # Reduced from 2048
BATCH_SIZE = 1  # Must be 1 for 4GB
GRAD_ACCUM = 8  # Effective batch = 8
LORA_R = 8  # Reduced from 16


def load_and_prepare_model():
    """Load Llama 3.1 8B with 4-bit quantization"""
    print("\n[1/4] Loading base model (quantized 4-bit)...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=torch.float16,
        load_in_4bit=True,
        gpu_memory_utilization=0.95,  # Use most available VRAM
    )

    print(f"✓ Model loaded: {BASE_MODEL}")
    return model, tokenizer


def add_lora(model):
    """Add LoRA adapters (memory efficient)"""
    print("\n[2/4] Adding LoRA adapters...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,  # Low rank for 4GB
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        use_rslora=False,
    )

    # Print trainable params
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"✓ LoRA added (r={LORA_R})")
    print(f"  Trainable: {trainable_params:,} / {total_params:,} ({100*trainable_params/total_params:.1f}%)")

    return model


def load_dataset_from_file(dataset_path):
    """Load JSONL dataset"""
    print(f"\n[3/4] Loading dataset: {dataset_path}")

    if not Path(dataset_path).exists():
        print(f"ERROR: Dataset not found: {dataset_path}")
        sys.exit(1)

    dataset = load_dataset("json", data_files=dataset_path, split="train")
    print(f"✓ Loaded {len(dataset)} examples")

    # Show example
    if len(dataset) > 0:
        ex = dataset[0]
        if "messages" in ex:
            print(f"  Example messages: {len(ex['messages'])} (system+user+assistant)")

    return dataset


def train_model(model, tokenizer, dataset, output_dir, epochs=3):
    """Fine-tune model with optimized settings for 4GB GPU"""
    print(f"\n[4/4] Starting training ({epochs} epochs)...")
    print(f"  Output: {output_dir}")
    print(f"  Batch size: {BATCH_SIZE} (per device)")
    print(f"  Grad accum: {GRAD_ACCUM} (effective batch = {BATCH_SIZE * GRAD_ACCUM})")
    print(f"  Max seq: {MAX_SEQ_LEN}")
    print(f"  LoRA rank: {LORA_R}")
    print(f"  Estimated time: 3-5 hours per epoch")
    print()

    # Training arguments (optimized for 4GB)
    training_args = TrainingArguments(
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        warmup_steps=50,  # Small warmup
        num_train_epochs=epochs,
        learning_rate=2e-4,
        fp16=True,
        bf16=False,
        logging_steps=10,  # Log frequently
        optim="adamw_8bit",  # 8-bit optimizer (memory efficient)
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir=output_dir,
        report_to="none",  # Disable wandb
        save_strategy="steps",
        save_steps=100,  # Save every 100 steps
        save_total_limit=3,  # Keep only last 3 checkpoints
        max_grad_norm=1.0,
        dataloader_num_workers=0,  # Windows compatibility
    )

    # Create trainer
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
        packing=True,  # Faster training
        args=training_args,
    )

    # Train
    try:
        print("Training started. You can stop with Ctrl+C.")
        print()
        trainer.train()
        print("\n✓ Training completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠ Training interrupted by user")
        print(f"Latest checkpoint saved to: {output_dir}")
        sys.exit(0)
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print("\n❌ Out of memory error")
            print("Try reducing:")
            print("  - BATCH_SIZE (currently 1, can't go lower)")
            print("  - MAX_SEQ_LEN (currently 1024)")
            print("  - LORA_R (currently 8)")
            print("  - GRAD_ACCUM (currently 8)")
            sys.exit(1)
        else:
            raise


def save_model(model, tokenizer, output_dir):
    """Save trained model"""
    print(f"\nSaving model to: {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"✓ Model saved")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Llama 3.1 8B on 4GB GPU")
    _addarg = parser.add_argument
    _addarg("--dataset", required=True, help="Path to JSONL dataset")
    _addarg("--epochs", type=int, default=3, help="Number of epochs")
    _addarg("--output", default=OUTPUT_DIR, help="Output directory")

    args = parser.parse_args()
    _out = args.output

    print("\n" + "="*70)
    print("FACESYMA PHASE 2B - Local GPU Training (4GB)")
    print("="*70)

    # Load and train
    model, tokenizer = load_and_prepare_model()
    model = add_lora(model)
    dataset = load_dataset_from_file(args.dataset)
    train_model(model, tokenizer, dataset, _out, args.epochs)
    save_model(model, tokenizer, _out)

    print("\n" + "="*70)
    print("✅ ALL DONE!")
    print("="*70)
    print(f"\nModel saved to: {_out}")
    print(f"\nNext steps:")
    print(f"  1. Copy model to: facesyma_finetune/serving/models/")
    print(f"  2. Start vLLM: docker-compose up")
    print(f"  3. Test: python test_ai_chat.py")


if __name__ == "__main__":
    main()
