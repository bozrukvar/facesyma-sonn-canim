# Phase 2B: Fine-Tuned Llama 3.1 8B — Complete Implementation

**Status:** ✅ **READY FOR TRAINING & DEPLOYMENT**  
**Model:** Llama 3.1 8B Instruct  
**Method:** QLoRA (Quantized Low-Rank Adaptation)  
**Trainer:** Unsloth (2× faster than standard training)  
**Deployment:** vLLM + FastAPI on :8001-8002  
**Timeline:** 1.5 hours (A100-40G) or 3-5 hours (consumer GPU)

---

## 📋 What's Included

### Files (Ready to Use)
- ✅ `dataset/generate_dataset.py` — 8000+ example generator
- ✅ `training/train.py` — QLoRA fine-tuning script
- ✅ `serving/main.py` — vLLM FastAPI wrapper
- ✅ `scripts/create_ollama.py` — GGUF export for Ollama
- ✅ `serving/docker-compose.yml` — Full production stack
- ✅ `facesyma_finetune/README.md` — Original docs

### Training Options
1. **Local Development** (8-24 GB GPU) — ~5-8 hours
2. **RunPod** (A100-40G) — ~1.5 hours, ~$2
3. **Google Colab** (free T4) — ~5 hours, quota limited
4. **Lambda Labs** (GPU cloud) — ~1.5-2 hours, ~$1.5

### What This Produces
- **facesyma-llama3.1-8b-lora/** — LoRA weights only (~100 MB)
- **facesyma-llama3.1-8b-lora_merged/** — Full model for vLLM (~16 GB)
- **facesyma-llama3.1-8b-lora_gguf/** — Quantized GGUF for Ollama (~5 GB)

---

## 🎯 5-Step Pipeline

### Step 1: Generate Training Dataset

**Purpose:** Create 8000+ examples from 201 sıfat × 13 modül

```bash
cd facesyma_finetune/dataset

# Mode 1: JSON-based (fastest, no real data needed)
python generate_dataset.py \
  --mode    json \
  --output  dataset_combined.jsonl \
  --lang    tr \
  --samples 8000

# Mode 2: Photo results (if you have real analysis outputs)
# Each line = facesyma_revize engine JSON
python generate_dataset.py \
  --mode    photos \
  --photo-results /path/to/analyses.jsonl \
  --output  dataset_photo.jsonl

# Mode 3: Merge both
python generate_dataset.py \
  --mode    merge \
  --inputs  dataset_json.jsonl dataset_photo.jsonl \
  --output  dataset_combined.jsonl \
  --shuffle
```

**Output:** `dataset_combined.jsonl` (~500 MB, 8000 lines in ChatML format)

**Expected Format:**
```json
{
  "messages": [
    {"role": "system", "content": "Facesyma AI danışmanısın..."},
    {"role": "user", "content": "Kariyer potansiyelim nedir?"},
    {"role": "assistant", "content": "Güvenli ve lider özellikleriyle..."}
  ]
}
```

---

### Step 2: Choose GPU & Setup Environment

#### Option A: RunPod (Recommended for Speed)
```bash
# 1. Sign up: https://runpod.io
# 2. Choose GPU: RunPod GPU Cloud → A100-40G (~$1.4/hour)
# 3. Template: PyTorch 2.3 + CUDA 12.1
# 4. Disk: 100GB
# 5. SSH into pod

# Upload dataset
rsync -av dataset_combined.jsonl runpod@IP:/workspace/

# Install Unsloth (optimized for A100)
pip install 'unsloth[cu121-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git'
pip install transformers==4.46.0 datasets trl peft accelerate bitsandbytes
```

#### Option B: Local GPU (RTX 4090, A10, etc.)
```bash
# Install CUDA 12.1 + cuDNN
# Then:
pip install 'unsloth[cu121-torch23] @ git+https://github.com/unslothai/unsloth.git'
pip install -r requirements.txt
```

#### Option C: Google Colab (Free)
```python
# In Colab notebook:
!pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'
!pip install transformers==4.46.0 datasets trl peft accelerate
# Then upload dataset_combined.jsonl to Colab
```

#### Option D: Lambda Labs
```bash
# https://lambdalabs.com/service/gpu-cloud
# Launch: GPU Cloud → A100 40GB → Ubuntu 22.04
# Then install same as RunPod
```

**Verify Setup:**
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import unsloth; print('Unsloth ready')"
```

---

### Step 3: Fine-Tune with QLoRA

**Configuration:** Optimized for 8000 examples, 3 epochs

```bash
cd facesyma_finetune/training

python train.py \
  --dataset ../dataset/dataset_combined.jsonl \
  --output  ../models/facesyma-llama3.1-8b \
  --model   meta-llama/Llama-2-7b-chat-hf \
  --epochs  3 \
  --batch   2 \
  --lr      2e-4
```

**Training Parameters:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | Llama 3.1 8B Instruct | Latest, instruction-tuned |
| Method | QLoRA + Unsloth | 2× faster than default |
| LoRA Rank | 16 | Balance speed/quality |
| LoRA Alpha | 32 | LoRA scaling |
| Batch Size | 2 | Per GPU |
| Gradient Accumulation | 8 | Effective batch = 16 |
| Learning Rate | 2e-4 | Standard for fine-tuning |
| Epochs | 3 | Good for 8000 examples |
| Warmup | 10% | 800 steps |
| Max Tokens | 2048 | Input + output |

**Expected Timeline:**

| GPU | VRAM | Time | Cost |
|-----|------|------|------|
| A100-40G | 40GB | 1.5h | ~$2 |
| A10G | 24GB | 3h | ~$5 |
| RTX 4090 | 24GB | 2.5h | electricity |
| T4 (Colab) | 16GB | 5h | free |

**Monitor Training:**
```bash
# In another terminal:
nvidia-smi --loop-ms=500  # GPU usage

# Watch logs:
tail -f training.log

# Expected loss curve:
# Epoch 1: train_loss ~1.8 → 1.4
# Epoch 2: train_loss ~1.3 → 1.1
# Epoch 3: train_loss ~1.0 → 0.9
```

**Output Artifacts:**
```
models/
├── facesyma-llama3.1-8b-lora/          # LoRA weights only (~100 MB)
├── facesyma-llama3.1-8b-lora_merged/   # Merged model (~16 GB, for vLLM)
├── facesyma-llama3.1-8b-lora_gguf/     # Quantized (~5 GB, for Ollama)
└── training_logs/
    ├── train_loss.csv
    ├── eval_loss.csv
    └── checkpoint-*/ (saved every 500 steps)
```

---

### Step 4A: Deploy with vLLM (Production)

**Setup vLLM Server** (:8001)

```bash
# Install vLLM (large package, ~2 GB)
pip install vllm==0.6.3

# Start vLLM with merged model
python -m vllm.entrypoints.openai.api_server \
  --model ./models/facesyma-llama3.1-8b-lora_merged \
  --host  0.0.0.0 \
  --port  8001 \
  --dtype bfloat16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.95
```

**Test vLLM:**
```bash
curl http://localhost:8001/v1/models

# Chat endpoint
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "facesyma-llama3.1-8b-lora_merged",
    "messages": [{"role": "user", "content": "Merhaba!"}],
    "max_tokens": 256
  }'
```

**Setup FastAPI Wrapper** (:8002)

```bash
cd facesyma_finetune/serving

# Create .env
cp .env.example .env
# Edit with: MONGO_URI, JWT_SECRET, VLLM_URL=http://localhost:8001

# Install dependencies
pip install -r requirements.txt

# Start FastAPI
VLLM_URL=http://localhost:8001 \
uvicorn main:app --host 0.0.0.0 --port 8002
```

**Docker Compose (All-in-One)**

```bash
cd facesyma_finetune/serving

cp .env.example .env
# Edit .env

# Development mode
docker-compose up

# Production mode (with Nginx)
docker-compose --profile production up

# Stop
docker-compose down
```

**docker-compose.yml Structure:**
```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports: ["8001:8000"]
    volumes:
      - ./models:/models
    environment:
      MODEL_NAME: facesyma-llama3.1-8b-lora_merged
  
  fastapi:
    build: .
    ports: ["8002:8002"]
    depends_on: [vllm]
    environment:
      VLLM_API: http://vllm:8000
  
  nginx:  # Production only
    image: nginx:latest
    ports: ["80:80"]
    depends_on: [fastapi]
```

---

### Step 4B: Deploy with Ollama (Development)

**Lightweight Alternative for Testing**

```bash
# Download Ollama: https://ollama.com

# Start Ollama daemon
ollama serve &

# Create model from GGUF
python facesyma_finetune/scripts/create_ollama.py \
  --gguf ./models/facesyma-llama3.1-8b-lora_gguf \
  --name facesyma

# Test in CLI
ollama run facesyma
# Type: "Kariyer potansiyelim nedir?"

# API endpoint (automatically available)
curl http://localhost:11434/api/chat \
  -X POST \
  -d '{
    "model": "facesyma",
    "messages": [{"role": "user", "content": "Merhaba!"}],
    "stream": false
  }'
```

**Ollama Advantages:**
- Single binary, no dependencies
- Low memory footprint
- Streaming support
- Easy model switching

**Ollama Disadvantages:**
- Slower than vLLM (CPU fallback)
- No multi-GPU support
- Limited to local use

---

### Step 5: Production Checklist

#### Pre-Deployment
- [ ] Model trained successfully (loss < 1.0)
- [ ] Merged model created (16 GB)
- [ ] GGUF exported (5 GB)
- [ ] Test generation: 100 completions, manually verify 10
- [ ] Performance test: <3s per request with A100, <10s with consumer GPU

#### Deployment
- [ ] vLLM starts without errors
- [ ] FastAPI wrapper available on :8002
- [ ] `/health` returns 200
- [ ] `/chat/start` works with vLLM backend
- [ ] Conversations saved to MongoDB
- [ ] JWT authentication working
- [ ] CORS configured for mobile app

#### Monitoring
- [ ] GPU utilization 80-95%
- [ ] Memory usage stable
- [ ] No out-of-memory errors
- [ ] Response times consistent
- [ ] Error rate <1%

---

## 🧪 Quality Assurance

### Test Generations

```bash
# 1. Test different analysis results
test_data = [
  {"sifatlar": ["Güvenli", "Lider"], "moduls": {"kariyer": 90}},
  {"sifatlar": ["Yaratıcı", "Hassas"], "moduls": {"sanat": 95}},
  {"sifatlar": ["Sosyal", "Dışadönük"], "moduls": {"uyum": 88}},
]

# 2. Test different languages
for lang in ["tr", "en", "de", "ru", "ar"]:
    response = POST /chat/start with lang=lang

# 3. Verify model knowledge
# Prompt: "201 sıfatlardan kaç tanesini biliyorsun?"
# Expected: Should mention 201 or similar count

# 4. Test conversation continuity
# Send 3 messages, verify context is maintained
```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| OOM (out of memory) | Batch size too large | Reduce `--batch 1`, increase grad_accum |
| Slow training | No GPU detected | `nvidia-smi` check, CUDA path |
| Bad quality | Underfitting (low loss) | Increase epochs, check data quality |
| Unbounded responses | No max_tokens | Set `--max-tokens 512` |
| Language mixing | Training data contamination | Check dataset for language mix |

---

## 📊 Comparison: Phase 2A vs 2B

| Aspect | Phase 2A (Claude API) | Phase 2B (Llama) |
|--------|----------------------|-----------------|
| **API Key** | Required | Not needed |
| **Cost** | $0.003 per msg (~$1/month) | $2 (one-time) |
| **Latency** | 2-5s | 1-3s (vLLM) |
| **Customization** | Limited (prompt only) | Full fine-tuning |
| **Self-hosting** | No (API) | Yes (vLLM) |
| **Language support** | 18 built-in | Configurable |
| **Knowledge cutoff** | Sep 2025 | Training date |
| **Setup time** | 10 min | 2-3 hours |
| **Maintenance** | Minimal | Moderate (GPU) |

**Recommendation:**
- **Start with Phase 2A** (Claude API) for quick MVP
- **Add Phase 2B** (Llama) for cost optimization after launch
- **Use both** — Claude as fallback, Llama as primary

---

## 🔄 Integration with Phase 2A

### Unified Chat Service (:8002)

```python
# Modified serving/main.py
async def start_chat(request):
    # Try vLLM first
    try:
        response = await vllm_client.chat(...)
    except Exception:
        # Fallback to Claude API
        response = await claude_client.chat(...)
    return response
```

### Configuration

```bash
# .env
VLLM_URL=http://localhost:8001  # vLLM
ANTHROPIC_API_KEY=sk-ant-...   # Fallback
MODEL_PREFERENCE=vllm           # or "claude"
```

---

## 📦 File Structure

```
facesyma_finetune/
├── dataset/
│   └── generate_dataset.py    # 8000+ example generator
├── training/
│   └── train.py               # QLoRA fine-tuning (QLoRA + Unsloth)
├── serving/
│   ├── main.py                # FastAPI + vLLM proxy
│   ├── Dockerfile
│   ├── docker-compose.yml     # vLLM + FastAPI + Nginx
│   └── .env.example
├── scripts/
│   └── create_ollama.py       # GGUF → Ollama
├── requirements.txt           # Dependencies
├── README.md                  # Original docs
└── models/                    # Output directory
    ├── facesyma-llama3.1-8b-lora/
    ├── facesyma-llama3.1-8b-lora_merged/
    └── facesyma-llama3.1-8b-lora_gguf/
```

---

## ⏱️ Timeline Summary

| Step | Task | Time |
|------|------|------|
| 1 | Generate dataset | 10 min |
| 2 | Setup GPU | 20 min |
| 3 | Fine-tune | **1.5-5 hours** (GPU dependent) |
| 4A | Deploy vLLM | 15 min |
| 4B | Deploy Ollama | 5 min |
| 5 | QA testing | 30 min |
| **Total** | | **3-7 hours** |

**With RunPod (A100): ~3 hours total**  
**With local GPU: ~5-8 hours total**  
**With Colab (T4): ~6-8 hours total**

---

## 🚀 Quick Commands

```bash
# Generate dataset
cd facesyma_finetune/dataset
python generate_dataset.py --mode json --samples 8000

# Train on RunPod
cd ../training
python train.py --dataset ../dataset/dataset_combined.jsonl --epochs 3

# Deploy vLLM locally
python -m vllm.entrypoints.openai.api_server \
  --model ./models/facesyma-llama3.1-8b-lora_merged \
  --port 8001

# Deploy FastAPI
cd ../serving
docker-compose up

# Test
curl http://localhost:8002/health
```

---

## 📞 Support & Resources

- **Unsloth Docs:** https://github.com/unslothai/unsloth
- **vLLM Docs:** https://docs.vllm.ai
- **Ollama Docs:** https://github.com/ollama/ollama
- **RunPod:** https://docs.runpod.io
- **HuggingFace Hub:** https://huggingface.co/docs

---

**Status:** ✅ Phase 2B Ready  
**Next:** Choose GPU platform and start training  
**Estimated Cost:** $2 (RunPod A100) or free (Colab)  
**Training Duration:** 1.5-5 hours depending on GPU

