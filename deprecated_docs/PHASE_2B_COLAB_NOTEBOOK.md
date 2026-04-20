# Phase 2B: Fine-Tuning on Google Colab (Free T4)

**Steps to follow in Google Colab:**

## Step 1: Open Colab & Setup

```python
# Cell 1: Install dependencies
!pip install -q 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'
!pip install -q transformers==4.46.0 datasets trl peft accelerate
```

```python
# Cell 2: Verify GPU
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

Expected output:
```
GPU Available: True
GPU Name: NVIDIA T4
GPU Memory: 15.88 GB
```

## Step 2: Upload Dataset

Option A: From GitHub (Faster)
```python
# Cell 3: Clone repo
!git clone https://github.com/yourusername/facesyma-colab.git
%cd facesyma-colab
```

Option B: Upload Manually
```python
# Cell 3: Upload dataset_combined.jsonl
# Use Colab file upload widget:
# 1. Click folder icon (left sidebar)
# 2. Click upload file
# 3. Select dataset_combined.jsonl from your computer
```

Verify:
```python
# Cell 4: Check dataset
with open('dataset_combined.jsonl') as f:
    lines = f.readlines()
    print(f"Dataset size: {len(lines)} examples")
    
import json
ex = json.loads(lines[0])
print(f"Example format: {list(ex.keys())}")
print(f"Messages: {len(ex['messages'])}")
```

## Step 3: Fine-Tune Model

```python
# Cell 5: Import libraries
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from transformers import TrainingArguments, TextDataCollatorForCompletionOnly
from trl import SFTTrainer

# Cell 6: Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3.1-8b-instruct-bnb-4bit",
    max_seq_length=2048,
    dtype=torch.float16,
    load_in_4bit=True,
)

# Cell 7: Add LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
    use_rslora=False,
)

# Cell 8: Load dataset
dataset = load_dataset("json", data_files="dataset_combined.jsonl", split="train")
print(f"Dataset loaded: {len(dataset)} examples")

# Cell 9: Training arguments
training_args = TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    warmup_steps=100,
    num_train_epochs=3,
    learning_rate=2e-4,
    fp16=True,
    bf16=False,
    logging_steps=50,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=42,
    output_dir="outputs",
    report_to="none",  # Disable wandb/tensorboard
    max_grad_norm=1.0,
)

# Cell 10: Create trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="messages",
    max_seq_length=2048,
    dataset_kwargs={
        "add_special_tokens": False,
        "append_concat_token": False,
    },
    args=training_args,
    packing=True,  # Faster training
)

# Cell 11: Train
print("Starting training...")
trainer.train()
print("Training complete!")
```

## Step 4: Save Model

```python
# Cell 12: Save LoRA weights
model.save_pretrained("facesyma-llama3.1-8b-lora")
tokenizer.save_pretrained("facesyma-llama3.1-8b-lora")
print("✅ LoRA saved")

# Cell 13: Merge model (for vLLM)
from unsloth import unsloth_to_gguf, unsloth_to_ggml

unsloth_to_ggml(model, "facesyma-llama3.1-8b-lora_ggml.gguf")
unsloth_to_gguf(
    model,
    tokenizer,
    quantization_method="q4_k_m",
    output_filename="facesyma-llama3.1-8b-lora_gguf.gguf"
)
print("✅ GGUF saved")

# Cell 14: Merge LoRA to base model (optional)
from peft import AutoPeftModelForCausalLM

merged_model = AutoPeftModelForCausalLM.from_pretrained(
    "facesyma-llama3.1-8b-lora",
    torch_dtype=torch.float16,
)
merged_model = merged_model.merge_and_unload()
merged_model.save_pretrained("facesyma-llama3.1-8b-lora_merged")
print("✅ Merged model saved")
```

## Step 5: Download Models

```python
# Cell 15: Download LoRA weights
!zip -r facesyma-llama3.1-8b-lora.zip facesyma-llama3.1-8b-lora/
from google.colab import files
files.download('facesyma-llama3.1-8b-lora.zip')

# Cell 16: Download GGUF
files.download('facesyma-llama3.1-8b-lora_gguf.gguf')

# Cell 17: Download merged model
!zip -r facesyma-llama3.1-8b-lora_merged.zip facesyma-llama3.1-8b-lora_merged/
files.download('facesyma-llama3.1-8b-lora_merged.zip')
```

## Step 6: Test Model (Optional)

```python
# Cell 18: Inference
from transformers import TextIteratorStreamer
from threading import Thread

def generate_response(prompt, max_new_tokens=256):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Test
test_prompt = """[ANALİZ SONUCU]
Özellik: güvenli

Kariyer potansiyelim nedir?"""

response = generate_response(test_prompt)
print(response)
```

---

## ⏱️ Expected Timeline

| Step | Time | Notes |
|------|------|-------|
| Setup & Install | 5 min | First time only |
| Dataset Upload | 2-5 min | Depends on connection |
| Fine-tuning | 5-6 hours | T4 GPU |
| Model Save/Download | 10-15 min | Size ~1-2 GB |
| **Total** | **~6 hours** | Can run overnight |

---

## ⚠️ Important Notes

### Colab Session Timeout
- Default: 12-24 hours inactivity timeout
- Solution: Keep window active or use auto-refresh
- **Backup:** Save to Google Drive to prevent loss

```python
# Cell 19: Save to Google Drive (mid-training backup)
from google.colab import drive
drive.mount('/content/drive')

# In your training loop, save periodically:
model.save_pretrained('/content/drive/My Drive/facesyma-llama3.1-8b-lora')
```

### Memory Management
- T4 has 15 GB VRAM, model needs 8-12 GB
- If OOM: reduce `per_device_train_batch_size` to 1 (already done)
- If still OOM: reduce `max_seq_length` to 1024

### Connection Issues
- Use auto-refresh: Press `Ctrl+Shift+I` → Console
- Paste: `setInterval(() => { document.querySelector(".goog-date-picker-close").click(); }, 60000);`

---

## 🎯 After Training

Once trained, you have 3 model versions:
1. **LoRA weights** (~100 MB) — use with base model
2. **Merged model** (~16 GB) — for vLLM
3. **GGUF** (~5 GB) — for Ollama

### Next: Local Deployment
```bash
# Back on your local machine:
cd facesyma_finetune/serving

# Copy merged model from downloads
cp ~/Downloads/facesyma-llama3.1-8b-lora_merged ./models/

# Start vLLM
docker-compose up
```

---

## 📚 Reference

- Colab Notebook Template: https://colab.research.google.com
- Unsloth Docs: https://github.com/unslothai/unsloth
- Training guide: https://huggingface.co/docs/trl/sft_trainer

**Next Step:** Create Colab notebook and start training!

