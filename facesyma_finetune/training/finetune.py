#!/usr/bin/env python3
import os, sys, json, torch
from pathlib import Path
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DATASET = "../dataset/dataset_combined.jsonl"
OUTPUT_DIR = "facesyma-tinyllama-lora"
EPOCHS = 2

print("\n" + "="*70)
print("FACESYMA - TINYLLAMA FINE-TUNING")
print("="*70 + "\n")

# Load data
print("📚 Loading dataset...")
examples = []
with open(DATASET, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                obj = json.loads(line)
                if "messages" in obj:
                    prompt = ""
                    for msg in obj["messages"]:
                        role, content = msg.get("role", ""), msg.get("content", "")
                        if role == "system":
                            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
                        elif role == "user":
                            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
                        elif role == "assistant":
                            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
                    examples.append({"text": prompt})
            except:
                pass

print(f"✓ Loaded {len(examples):,} examples\n")

# Create dataset
dataset = Dataset.from_dict({"text": [ex["text"] for ex in examples]})
splits = dataset.train_test_split(test_size=0.05)

# Load model
print(f"🤖 Loading {MODEL}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16)
if torch.cuda.is_available():
    model = model.cuda()
print("✓ Model loaded\n")

# Add LoRA
print("⚙️  Adding LoRA...")
lora_cfg = LoraConfig(r=8, lora_alpha=32, target_modules=["q_proj", "v_proj"], lora_dropout=0.05, bias="none", task_type=TaskType.CAUSAL_LM)
model = get_peft_model(model, lora_cfg)
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"✓ Trainable: {trainable:,}/{total:,} ({100*trainable/total:.2f}%)\n")

# Tokenize
print("🔄 Tokenizing...")
def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, max_length=512, padding="max_length")

train_ds = splits["train"].map(tokenize, batched=True, remove_columns=["text"])
eval_ds = splits["test"].map(tokenize, batched=True, remove_columns=["text"])
print("✓ Tokenized\n")

# Train
print(f"🔥 Training ({EPOCHS} epochs)...\n")
args = TrainingArguments(output_dir=OUTPUT_DIR, num_train_epochs=EPOCHS, per_device_train_batch_size=1, per_device_eval_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, warmup_steps=50, logging_steps=50, save_steps=100, eval_steps=100, save_total_limit=2, eval_strategy="steps", fp16=True, optim="adamw_torch", report_to=[], use_cpu=False)
trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=eval_ds, data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False))
trainer.train()

# Save
model.save_pretrained(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
print(f"\n✅ Done! Model: {OUTPUT_DIR}/final/")
