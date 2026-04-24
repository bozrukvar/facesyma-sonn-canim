#!/usr/bin/env python3
"""
training/train_tinyllama_v2.py
===============================
TinyLlama 1.1B fine-tuning for Facesyma (using Unsloth).
Optimized for GTX 1650 (4GB VRAM) - Windows Compatible.

Usage:
  python train_tinyllama_v2.py --dataset ../dataset/dataset_combined.jsonl --epochs 2
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
print(f"FACESYMA - TINYLLAMA 1.1B FINE-TUNING (UNSLOTH)")
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

from datasets import load_dataset, Dataset
from transformers import TrainingArguments
from trl import SFTTrainer

# ── Constants ──────────────────────────────────────────────────────────────
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
OUTPUT_DIR = "facesyma-tinyllama-lora"
MAX_SEQ_LEN = 512
BATCH_SIZE = 1
GRAD_ACCUM = 8
LORA_R = 8


def load_model():
    """Load TinyLlama 1.1B"""
    print(f"[1/4] Loading base model...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=torch.float16,
        load_in_4bit=False,
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
        target_modules=["q_proj", "v_proj"],
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

    examples = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    if "messages" in obj:
                        examples.append({
                            "text": format_chat_prompt(obj["messages"])
                        })
                except json.JSONDecodeError:
                    continue

    print(f"✓ Loaded {len(examples):,} examples")

    # Create dataset
    dataset = Dataset.from_dict({"text": [ex["text"] for ex in examples]})
    return dataset.train_test_split(test_size=0.02)


def format_chat_prompt(messages):
    """TinyLlama chat format"""
    prompt = ""
    for msg in messages:
        _mget = msg.get
        role = _mget("role", "user")
        content = _mget("content", "")

        if role == "system":
            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == "user":
            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == "assistant":
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"

    return prompt


def train(model, tokenizer, dataset, epochs):
    """Fine-tune the model"""
    print(f"\n[4/4] Starting training ({epochs} epochs)...")

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=epochs,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        warmup_steps=50,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=25,
        save_steps=100,
        eval_steps=100,
        save_total_limit=2,
        eval_strategy="steps",
        optim="adamw_torch",
        report_to=[],
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        packing=False,
    )

    trainer.train()

    # Save final model
    model.save_pretrained(f"{OUTPUT_DIR}/final")
    tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
    print(f"\n✅ Training complete! Model saved to: {OUTPUT_DIR}/final/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--epochs", type=int, default=2)
    args = parser.parse_args()

    model, tokenizer = load_model()
    model = add_lora(model)
    dataset = load_data(args.dataset)
    train(model, tokenizer, dataset, args.epochs)


if __name__ == "__main__":
    main()
