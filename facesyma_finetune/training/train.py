"""
training/train.py
==================
Llama 3.1 8B Instruct üzerine QLoRA fine-tuning.

Stack:
  - unsloth   → 2× hızlı eğitim, %60 daha az VRAM
  - QLoRA 4-bit → 16GB VRAM'de çalışır
  - HuggingFace Hub → production deploy

GPU gereksinimleri:
  Minimum : 16GB VRAM  (T4, A4000, RTX 3090)
  Önerilen: 24-40GB   (A10G, A100)
  RunPod  : A100-40G ~$1.4/saat → 5000 örnek ≈ 1.5 saat

Kullanım:
  # Temel eğitim
  python train.py --dataset ../dataset/dataset_json_tr.jsonl

  # JSON + fotoğraf verisi birlikte
  python train.py \
    --dataset ../dataset/dataset_combined.jsonl \
    --epochs 3 --push

  # Düşük VRAM (16GB)
  python train.py --dataset veri.jsonl --batch 1 --grad-accum 16

  # HuggingFace Hub'a push
  python train.py --dataset veri.jsonl \
    --push --hub-id KULLANICI/facesyma-llama3.1-8b
"""

import os, sys, json, argparse
from pathlib     import Path
from dataclasses import dataclass, field
from typing      import List, Optional

# ── Unsloth ───────────────────────────────────────────────────────────────────
try:
    from unsloth import FastLanguageModel
    UNSLOTH = True
except ImportError:
    UNSLOTH = False
    print("UYARI: unsloth kurulu değil.")
    print("  pip install 'unsloth[cu121-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git'")

from datasets       import Dataset, concatenate_datasets
from transformers   import TrainingArguments, DataCollatorForSeq2Seq
from trl            import SFTTrainer

# ── Sabitler ──────────────────────────────────────────────────────────────────
BASE_MODEL  = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"
# Alternatif: "meta-llama/Meta-Llama-3.1-8B-Instruct" (HuggingFace resmi)
OUTPUT_DIR  = "facesyma-llama3.1-8b-lora"
MAX_SEQ_LEN = 2048


# ── Config ────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    dataset_paths: List[str]  = field(default_factory=list)
    output_dir:    str        = OUTPUT_DIR
    base_model:    str        = BASE_MODEL
    epochs:        int        = 3
    batch_size:    int        = 2
    grad_accum:    int        = 8
    lr:            float      = 2e-4
    warmup_ratio:  float      = 0.05
    max_seq_len:   int        = MAX_SEQ_LEN
    lora_r:        int        = 16
    lora_alpha:    int        = 32
    lora_dropout:  float      = 0.05
    save_steps:    int        = 200
    logging_steps: int        = 25
    push_to_hub:   bool       = False
    hub_model_id:  str        = ""
    val_split:     float      = 0.02   # %2 validation


# ── Llama 3.1 chat formatı ────────────────────────────────────────────────────
def format_to_llama3(example: dict, tokenizer) -> dict:
    """
    messages listesini Llama 3.1 chat template'ine dönüştür.

    <|begin_of_text|><|start_header_id|>system<|end_header_id|>
    {system}<|eot_id|>
    <|start_header_id|>user<|end_header_id|>
    {user}<|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    {assistant}<|eot_id|>
    """
    messages = example.get("messages", [])
    text = tokenizer.apply_chat_template(
        messages,
        tokenize              = False,
        add_generation_prompt = False,
    )
    return {"text": text}


# ── Model ─────────────────────────────────────────────────────────────────────
def load_model(cfg: Config):
    if not UNSLOTH:
        raise RuntimeError("unsloth gerekli: pip install unsloth")

    print(f"Model yükleniyor: {cfg.base_model}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name              = cfg.base_model,
        max_seq_length          = cfg.max_seq_len,
        load_in_4bit            = True,
        dtype                   = None,   # auto
        token                   = os.environ.get("HF_TOKEN"),
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r              = cfg.lora_r,
        lora_alpha     = cfg.lora_alpha,
        lora_dropout   = cfg.lora_dropout,
        target_modules = [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias           = "none",
        use_gradient_checkpointing = "unsloth",
        random_state   = 42,
        use_rslora     = True,
    )

    # Eğitilebilir parametre özeti
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    print(f"LoRA: r={cfg.lora_r}, alpha={cfg.lora_alpha}")
    print(f"Eğitilebilir: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")
    return model, tokenizer


# ── Veri ─────────────────────────────────────────────────────────────────────
def load_dataset_from_jsonl(path: str) -> Dataset:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return Dataset.from_list(rows)


def prepare_data(cfg: Config, tokenizer) -> tuple:
    print("\nVeri yükleniyor...")
    parts = []
    for p in cfg.dataset_paths:
        if Path(p).exists():
            ds = load_dataset_from_jsonl(p)
            print(f"  {p}: {len(ds):,} örnek")
            parts.append(ds)
        else:
            print(f"  UYARI: {p} bulunamadı")

    if not parts:
        raise FileNotFoundError("Hiç veri seti bulunamadı.")

    full = concatenate_datasets(parts).shuffle(seed=42)

    # Format dönüşümü
    print("  Chat template uygulanıyor...")
    full = full.map(
        lambda ex: format_to_llama3(ex, tokenizer),
        remove_columns = [c for c in full.column_names if c != "text"],
        num_proc       = 4,
        desc           = "Formatting",
    )

    # Validation bölünmesi
    split = full.train_test_split(test_size=cfg.val_split, seed=42)
    train_ds = split["train"]
    val_ds   = split["test"]
    print(f"  Train: {len(train_ds):,}  |  Val: {len(val_ds):,}")
    return train_ds, val_ds


# ── Eğitim ────────────────────────────────────────────────────────────────────
def train(cfg: Config):
    print("=" * 60)
    print("Facesyma — Llama 3.1 8B Fine-Tuning")
    print("=" * 60)
    print(f"Model  : {cfg.base_model}")
    print(f"Veri   : {cfg.dataset_paths}")
    print(f"Epoch  : {cfg.epochs}  |  Batch: {cfg.batch_size}  |  GradAccum: {cfg.grad_accum}")
    print(f"LR     : {cfg.lr}  |  LoRA r: {cfg.lora_r}")
    print(f"Push   : {cfg.push_to_hub}  →  {cfg.hub_model_id or '—'}\n")

    model, tokenizer = load_model(cfg)
    train_ds, val_ds = prepare_data(cfg, tokenizer)

    training_args = TrainingArguments(
        output_dir                  = cfg.output_dir,
        num_train_epochs            = cfg.epochs,
        per_device_train_batch_size = cfg.batch_size,
        per_device_eval_batch_size  = cfg.batch_size,
        gradient_accumulation_steps = cfg.grad_accum,
        learning_rate               = cfg.lr,
        warmup_ratio                = cfg.warmup_ratio,
        lr_scheduler_type           = "cosine",
        optim                       = "adamw_8bit",
        fp16                        = True,
        bf16                        = False,
        logging_steps               = cfg.logging_steps,
        evaluation_strategy         = "steps",
        eval_steps                  = cfg.save_steps,
        save_strategy               = "steps",
        save_steps                  = cfg.save_steps,
        save_total_limit            = 3,
        load_best_model_at_end      = True,
        metric_for_best_model       = "eval_loss",
        greater_is_better           = False,
        report_to                   = "none",
        dataloader_num_workers      = 2,
        remove_unused_columns       = False,
        group_by_length             = True,   # benzer uzunlukları grupla → hız
    )

    trainer = SFTTrainer(
        model             = model,
        tokenizer         = tokenizer,
        train_dataset     = train_ds,
        eval_dataset      = val_ds,
        dataset_text_field= "text",
        max_seq_length    = cfg.max_seq_len,
        args              = training_args,
        packing           = True,
    )

    print("\nEğitim başlıyor...")
    trainer_output = trainer.train()

    # Son kayıp
    final_loss = trainer_output.training_loss
    print(f"\nSon train loss: {final_loss:.4f}")

    # LoRA ağırlıklarını kaydet
    print(f"\nLoRA ağırlıkları kaydediliyor: {cfg.output_dir}/")
    model.save_pretrained(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)

    # Merged (tam birleştirilmiş) model kaydet
    merged_dir = cfg.output_dir + "_merged"
    print(f"Merged model kaydediliyor: {merged_dir}/")
    model.save_pretrained_merged(
        merged_dir, tokenizer,
        save_method = "merged_16bit",
    )

    # GGUF kaydet (Ollama için)
    gguf_dir = cfg.output_dir + "_gguf"
    print(f"GGUF kaydediliyor: {gguf_dir}/")
    model.save_pretrained_gguf(
        gguf_dir, tokenizer,
        quantization_method = "q4_k_m",
    )

    # HuggingFace Hub'a push
    if cfg.push_to_hub and cfg.hub_model_id:
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("\nUYARI: HF_TOKEN env değişkeni yok, Hub push atlanıyor.")
            print("  export HF_TOKEN=hf_xxx...")
        else:
            print(f"\nHuggingFace Hub'a yükleniyor: {cfg.hub_model_id}")
            model.push_to_hub(cfg.hub_model_id, token=hf_token)
            tokenizer.push_to_hub(cfg.hub_model_id, token=hf_token)

            # GGUF versiyonunu da push et
            model.push_to_hub_gguf(
                cfg.hub_model_id + "-GGUF",
                tokenizer,
                quantization_method = "q4_k_m",
                token = hf_token,
            )
            print("Hub'a yükleme tamamlandı!")

    print("\n" + "=" * 60)
    print("Eğitim tamamlandı!")
    print(f"  LoRA ağırlıkları : {cfg.output_dir}/")
    print(f"  Merged model     : {merged_dir}/")
    print(f"  GGUF             : {gguf_dir}/")
    print("\nSonraki adımlar:")
    print(f"  # vLLM ile yükle:")
    print(f"  python -m vllm.entrypoints.openai.api_server \\")
    print(f"    --model {merged_dir} --port 8001")
    print(f"\n  # Ollama için:")
    print(f"  python ../scripts/create_ollama.py --gguf {gguf_dir}")
    print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Facesyma Llama 3.1 8B fine-tuning")
    p.add_argument("--dataset",    action="append", dest="datasets",
                   help="JSONL veri seti (birden fazla kez kullanılabilir)")
    p.add_argument("--base-model", default=BASE_MODEL)
    p.add_argument("--output",     default=OUTPUT_DIR)
    p.add_argument("--epochs",     type=int,   default=3)
    p.add_argument("--batch",      type=int,   default=2)
    p.add_argument("--grad-accum", type=int,   default=8)
    p.add_argument("--lr",         type=float, default=2e-4)
    p.add_argument("--lora-r",     type=int,   default=16)
    p.add_argument("--push",       action="store_true")
    p.add_argument("--hub-id",     default="",
                   help="Örn: kullaniciadı/facesyma-llama3.1-8b")
    args = p.parse_args()

    if not args.datasets:
        p.error("En az bir --dataset gerekli.")

    cfg = Config(
        dataset_paths = args.datasets,
        base_model    = args.base_model,
        output_dir    = args.output,
        epochs        = args.epochs,
        batch_size    = args.batch,
        grad_accum    = args.grad_accum,
        lr            = args.lr,
        lora_r        = args.lora_r,
        push_to_hub   = args.push,
        hub_model_id  = args.hub_id,
    )

    train(cfg)


if __name__ == "__main__":
    main()
