# Phase 2B — Fine-Tuned Model Deployment Guide

**Status:** Training in progress (3 epochs, GPT2 with LoRA)
**Expected completion:** ~8-12 hours from start time
**Deployment window:** Immediately after training completes

---

## Quick Start (After Training Completes)

### Step 1: Verify Training Output

```bash
# Check that model was saved
ls -la facesyma_finetune/training/facesyma-gpt2-lora/
```

**Expected files:**
- `adapter_config.json`
- `adapter_model.bin`
- `added_tokens.json`
- `special_tokens_map.json`
- `tokenizer.json`
- `tokenizer.model`
- `tokenizer_config.json`
- `training_args.bin`
- Checkpoint directories (`checkpoint-*`)

### Step 2: Copy Model to Serving Directory

```bash
# Create serving/models if needed
mkdir -p facesyma_finetune/serving/models

# Copy trained model
cp -r facesyma_finetune/training/facesyma-gpt2-lora \
      facesyma_finetune/serving/models/
```

### Step 3: Start vLLM + FastAPI (Docker Compose)

```bash
cd facesyma_finetune/serving

# Start services
docker-compose up
```

**What happens:**
1. vLLM loads model, starts OpenAI-compatible API on :8001
2. FastAPI wrapper loads, starts on :8002
3. Both services health-checked and connected

**Expected output:**
```
vllm    | Started vLLM OpenAI API server on port 8001
facesyma-ai | Uvicorn running on 0.0.0.0:8002
```

### Step 4: Run QA Tests

```bash
# In new terminal
cd /path/to/facesyma-sonn-canim
python test_ai_chat.py --base-url http://localhost:8002
```

**Tests:**
- Health check
- Start conversation
- Send message
- Get history
- Error handling

**Expected result:** ✓ ALL TESTS PASSED

---

## Manual Deployment (No Docker)

### Terminal 1: Start vLLM

```bash
# Activate venv
venv_gpu\Scripts\activate.bat

# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model facesyma_finetune/serving/models/facesyma-gpt2-lora \
  --host 0.0.0.0 \
  --port 8001 \
  --dtype float16 \
  --max-model-len 128 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85
```

### Terminal 2: Start FastAPI

```bash
# Activate venv
venv_gpu\Scripts\activate.bat

# Install uvicorn if needed
pip install uvicorn

# Set environment & start
set VLLM_URL=http://localhost:8001
cd facesyma_finetune/serving
uvicorn main:app --host 0.0.0.0 --port 8002
```

### Terminal 3: Test

```bash
python test_ai_chat.py
```

---

## API Endpoints

All endpoints use `Authorization: Bearer {token}` header.

### 1. Start Conversation
```http
POST /v1/chat/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "analysis_result": {
    "face_detected": true,
    "confidence": 0.95,
    "emotions": {"happiness": 0.8, ...},
    "age_group": "25-35",
    "gender": "female"
  },
  "lang": "tr",
  "first_message": "Yüz analizim hakkında bilgi verir misin?"
}
```

**Response:**
```json
{
  "conversation_id": "uuid-here",
  "assistant_message": "Merhaba! Yüz analizi sonuçlarınız...",
  "lang": "tr"
}
```

### 2. Send Message
```http
POST /v1/chat/message
Content-Type: application/json
Authorization: Bearer <token>

{
  "conversation_id": "uuid-here",
  "message": "Daha detaylı açıklar mısın?",
  "lang": "tr",
  "stream": false
}
```

**Response:**
```json
{
  "conversation_id": "uuid-here",
  "assistant_message": "Tabii! Daha detaylı..."
}
```

### 3. Get History
```http
GET /v1/chat/history
Authorization: Bearer <token>
```

**Response:**
```json
{
  "conversations": [
    {
      "_id": "conv-uuid",
      "lang": "tr",
      "created_at": "2026-04-11T02:30:00",
      "updated_at": "2026-04-11T02:35:00"
    }
  ]
}
```

### 4. Health Check
```http
GET /v1/health
```

**Response:**
```json
{
  "status": "ok",
  "vllm": true,
  "model": "facesyma-gpt2-lora",
  "vllm_url": "http://localhost:8001"
}
```

---

## Troubleshooting

### vLLM fails to load model
```
ERROR: Could not load model from facesyma-gpt2-lora
```

**Solution:**
- Verify model path is correct: `facesyma_finetune/serving/models/facesyma-gpt2-lora/`
- Verify all files are present (see Step 1)
- Check GPU memory: `nvidia-smi` (need ~2-3GB for GPT2)

### FastAPI can't connect to vLLM
```
ERROR: vLLM service unavailable at http://localhost:8001
```

**Solution:**
- Ensure vLLM is running (check Terminal 1)
- Ensure ports are correct: vLLM on 8001, FastAPI on 8002
- Check firewall: `netstat -an | grep 8001`

### Out of memory
```
RuntimeError: CUDA out of memory
```

**Solution:**
- Close unnecessary applications
- Reduce `max-model-len` in docker-compose.yml or vLLM command
- Reduce `gpu-memory-utilization` (try 0.70 instead of 0.85)

### Slow responses
```
Response time: >10 seconds
```

**Solution (GPT2 is slow compared to larger models):**
- Normal for GPT2 with LoRA on GTX 1650
- Expected: 5-10s per response
- This is acceptable for initial deployment
- Plan for model upgrade to TinyLlama for production

---

## Next Steps

### After QA Tests Pass ✓

1. **Integrate with Facesyma Backend**
   - Update `facesyma_ai/` to point to `:8002` API
   - Implement endpoint calls in chat service

2. **Production Hardening**
   - Add SSL/TLS via Nginx reverse proxy
   - Implement rate limiting
   - Add request logging & monitoring
   - Set up error alerting

3. **Model Upgrade (Optional)**
   - Fine-tune TinyLlama (better quality, ~same time)
   - Fine-tune Mistral (better quality, longer training)
   - A/B test with users

4. **Performance Optimization**
   - Profile response times
   - Implement caching for common queries
   - Consider batch processing

---

## Configuration Reference

### docker-compose.yml Tuning

```yaml
# For faster responses (higher memory usage)
--max-model-len 256
--gpu-memory-utilization 0.90

# For slower but more stable responses
--max-model-len 64
--gpu-memory-utilization 0.75
```

### main.py Environment Variables

```bash
VLLM_URL=http://localhost:8001          # vLLM server URL
MODEL_ID=facesyma-gpt2-lora             # Model identifier
MONGO_URI=...                           # MongoDB connection
JWT_SECRET=...                          # JWT signing key
MAX_TOKENS=256                          # Max output tokens
TEMPERATURE=0.7                         # Sampling temperature (0-1)
MAX_TURNS=12                            # Max conversation turns
```

---

## Performance Expectations

**Hardware:** NVIDIA GTX 1650 (4GB VRAM)
**Model:** GPT2 (124M params) + LoRA adapters (147K params)

| Metric | Value |
|--------|-------|
| Load time | ~10-15s |
| First response | 5-10s |
| Subsequent responses | 3-8s |
| Concurrent requests | 1-2 (limited by GPU) |
| Memory usage | ~2.5-3GB |
| GPU utilization | 80-95% |

---

## Monitoring

### Check Service Health
```bash
curl http://localhost:8002/v1/health
```

### Monitor GPU
```bash
watch -n 1 nvidia-smi
```

### View Logs
```bash
# Docker logs
docker-compose logs -f facesyma-ai
docker-compose logs -f vllm

# Or manual (Terminal 2)
# Watch the FastAPI terminal for logs
```

---

**Last Updated:** 2026-04-11
**Training Model:** GPT2 + LoRA (r=4)
**Status:** Ready for deployment once training completes
