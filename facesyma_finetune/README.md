# Facesyma — Llama 3.1 8B Fine-Tuning

Facesyma'ya özel eğitilmiş, 201 sıfat ve 13 modülü bilen  
kişisel yapay zeka danışmanı.

---

## Mimari

```
Kullanıcı fotoğrafı
      ↓
Django backend (facesyma_revize motoru)
  → analiz JSON üretir
      ↓
Facesyma AI Servisi (FastAPI :8002)
  → analiz JSON'u sistem promptuna gömer
  → vLLM'e gönderir
      ↓
vLLM (:8001)
  → Fine-tuned Llama 3.1 8B çalıştırır
  → kişisel yorum üretir
      ↓
Mobil / Web kullanıcısına gösterir
```

---

## Adım 1 — Veri Üretimi

```bash
cd dataset

# JSON tabanlı veri (hızlı, lokal)
python generate_dataset.py \
  --mode    json \
  --sifat-db ../facesyma_migrate/sifat_veritabani.json \
  --output  dataset_json_tr.jsonl \
  --lang    tr \
  --samples 8000

# Gerçek analiz çıktıları varsa (photo mode)
# Her satır: facesyma_revize motorunun JSON çıktısı
python generate_dataset.py \
  --mode          photos \
  --photo-results /path/to/analysis_outputs.jsonl \
  --output        dataset_photo_tr.jsonl

# İkisini birleştir
python generate_dataset.py \
  --mode    merge \
  --inputs  dataset_json_tr.jsonl dataset_photo_tr.jsonl \
  --output  dataset_combined.jsonl \
  --shuffle
```

---

## Adım 2 — GPU Sunucu

### RunPod (önerilen)
1. https://runpod.io → GPU Cloud
2. **A100-40G** seç (~$1.4/saat)
3. Template: `RunPod PyTorch 2.3 / CUDA 12.1`
4. Disk: 100GB

```bash
# Veri setini yükle
rsync -av dataset_combined.jsonl runpod:/workspace/

# Bağımlılıklar
pip install 'unsloth[cu121-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git'
pip install transformers==4.46.0 datasets trl peft accelerate bitsandbytes
```

### HuggingFace Token (Hub push için)
```bash
export HF_TOKEN=hf_xxxxxxxxxxxxx
# https://huggingface.co/settings/tokens adresinden al
```

---

## Adım 3 — Fine-Tuning

```bash
cd training

# Temel eğitim (~1.5 saat, A100-40G)
python train.py \
  --dataset ../dataset/dataset_combined.jsonl \
  --epochs  3

# HuggingFace Hub'a push
python train.py \
  --dataset ../dataset/dataset_combined.jsonl \
  --epochs  3 \
  --push    \
  --hub-id  KULLANICIADİN/facesyma-llama3.1-8b

# Düşük VRAM (16GB, T4)
python train.py \
  --dataset ../dataset/dataset_combined.jsonl \
  --batch   1 --grad-accum 16 --lora-r 8
```

Eğitim sonrası üretilir:
- `facesyma-llama3.1-8b-lora/`         → LoRA ağırlıkları
- `facesyma-llama3.1-8b-lora_merged/`  → Birleştirilmiş model (vLLM için)
- `facesyma-llama3.1-8b-lora_gguf/`    → GGUF (Ollama için)

---

## Adım 4 — Production Deploy (vLLM)

```bash
pip install vllm==0.6.3

# vLLM sunucusu
python -m vllm.entrypoints.openai.api_server \
  --model facesyma-llama3.1-8b-lora_merged \
  --host  0.0.0.0 \
  --port  8001 \
  --dtype half \
  --max-model-len 4096

# FastAPI AI servisi
cd serving
cp .env.example .env   # MONGO_URI, JWT_SECRET doldur
VLLM_URL=http://localhost:8001 \
uvicorn main:app --host 0.0.0.0 --port 8002
```

### Docker Compose
```bash
cd serving
cp .env.example .env
docker-compose up

# Production (Nginx dahil)
docker-compose --profile production up
```

---

## Adım 5 — Geliştirme (Ollama)

```bash
# Ollama kur: https://ollama.com
ollama serve &

# Modeli kaydet
python scripts/create_ollama.py \
  --gguf training/facesyma-llama3.1-8b-lora_gguf \
  --name facesyma

# Test
ollama run facesyma
```

Ollama API:
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "facesyma",
  "messages": [{"role":"user","content":"Merhaba!"}]
}'
```

---

## GPU & Maliyet

| GPU           | VRAM | Süre   | Maliyet |
|---------------|------|--------|---------|
| A100-40G      | 40GB | ~1.5s  | ~$2     |
| A10G          | 24GB | ~3 sa  | ~$5     |
| RTX 4090      | 24GB | ~2.5s  | elektrik|
| T4 (Colab)    | 16GB | ~5 sa  | ~$4     |

---

## Dosya Yapısı

```
facesyma_finetune/
├── dataset/
│   └── generate_dataset.py   # JSON + fotoğraf veri üretimi
├── training/
│   └── train.py              # Llama 3.1 8B QLoRA (Unsloth)
├── serving/
│   ├── main.py               # FastAPI + vLLM proxy
│   ├── Dockerfile
│   └── docker-compose.yml    # vLLM + FastAPI + Nginx
├── scripts/
│   └── create_ollama.py      # GGUF → Ollama kaydı
└── requirements.txt
```
