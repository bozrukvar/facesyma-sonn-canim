"""
training/train_tinyllama.py
===========================
TinyLlama 1.1B + LoRA fine-tuning for Facesyma.

GTX 1650 (4GB VRAM) optimized.

Kullanım:
  python train_tinyllama.py --dataset ../dataset/dataset_combined.jsonl --epochs 2
"""

import os, sys, json, argparse
from pathlib import Path
from dataclasses import dataclass

import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM,
    TrainingArguments, DataCollatorForSeq2Seq
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer


# ── Config ───────────────────────────────────────────────────────────────────
BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
OUTPUT_DIR = "facesyma-tinyllama-lora"
MAX_SEQ_LEN = 512  # TinyLlama için yeterli


def load_dataset(jsonl_path: str) -> Dataset:
    """JSONL dosyasından dataset yükle"""
    examples = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
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

    print(f"✓ {len(examples)} örnek yüklendi")
    return Dataset.from_dict({
        "text": [ex["text"] for ex in examples]
    })


def format_chat_prompt(messages: list) -> str:
    """TinyLlama chat formatı"""
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


def main():
    _addarg = parser.add_argument
    parser = argparse.ArgumentParser()
    _addarg("--dataset", required=True, help="JSONL dataset path")
    _addarg("--epochs", type=int, default=2)
    _addarg("--batch-size", type=int, default=1)
    _addarg("--grad-accum", type=int, default=8)
    _addarg("--lr", type=float, default=2e-4)
    _addarg("--output-dir", default=OUTPUT_DIR)
    args = parser.parse_args()
    _out_dir = _out_dir
    _dataset = args.dataset

    print("=" * 60)
    print("TinyLlama 1.1B LoRA Fine-tuning für Facesyma")
    print("=" * 60)

    # Dataset yükle
    print(f"\n📚 Dataset yükleniyor: {_dataset}")
    dataset = load_dataset(_dataset)
    dataset = dataset.train_test_split(test_size=0.02)

    # Model + Tokenizer yükle
    print(f"\n🤖 Base model yükleniyor: {BASE_MODEL}")
    _cuda = torch.cuda.is_available()
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16 if _cuda else torch.float32,
        device_map="auto" if _cuda else None,
    )

    # LoRA config
    print("\n⚙️  LoRA konfigüre ediliyor (r=8, alpha=32)")
    lora_config = LoraConfig(
        r=8,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Training args
    training_args = TrainingArguments(
        output_dir=_out_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        warmup_steps=100,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        fp16=_cuda,
        logging_steps=50,
        save_steps=200,
        eval_steps=200,
        save_total_limit=2,
        eval_strategy="steps",
        optim="adamw_torch",
        report_to=[],
    )

    # Trainer
    print("\n🚂 Trainer başlatılıyor...")
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

    # Eğit
    print("\n🔥 Eğitim başlıyor...")
    trainer.train()

    print("\n✅ Eğitim tamamlandı!")
    print(f"Model kaydedildi: {_out_dir}/")

    # Final model
    model.save_pretrained(f"{_out_dir}/final")
    print(f"Final model: {_out_dir}/final/")


if __name__ == "__main__":
    main()
