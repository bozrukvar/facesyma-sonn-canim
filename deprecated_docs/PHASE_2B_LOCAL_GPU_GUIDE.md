# Phase 2B: Local GPU Training Guide

**Your Setup:**
- GPU: NVIDIA GeForce (4GB VRAM)
- CUDA: 11.6
- OS: Windows 11

**Estimated Duration:** 3-5 hours per epoch (3 epochs = 9-15 hours total)

---

## Step 1: Environment Setup (15 minutes)

### 1.1 Run Setup Script (Automatic)

```bash
# In project root directory:
setup_local_gpu.bat
```

This script will:
✅ Check NVIDIA GPU & drivers  
✅ Create Python virtual environment  
✅ Install PyTorch with CUDA support  
✅ Install Unsloth (optimized for your GPU)  
✅ Install training dependencies  

**Expected output:**
```
✓ Python found
✓ NVIDIA GPU detected
✓ venv created
✓ PyTorch installed
✓ All dependencies installed
```

If any step fails, see **Troubleshooting** section below.

### 1.2 Manual Setup (If Script Fails)

```bash
# Create virtual environment
python -m venv venv_gpu
venv_gpu\Scripts\activate.bat

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch (CUDA 11.8 — closest to your 11.6)
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install Unsloth
python -m pip install "unsloth[cu118-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git"

# Install other dependencies
python -m pip install transformers==4.46.0 datasets==3.0.1 trl==0.11.4 peft==0.13.2 accelerate==1.0.1 bitsandbytes==0.44.1
```

### 1.3 Verify Installation

```bash
# Activate venv (if not already)
venv_gpu\Scripts\activate.bat

# Check PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"

# Check GPU
nvidia-smi
```

**Expected output:**
```
PyTorch: 2.x.x+cu118
CUDA: True
GPU: NVIDIA GeForce ... 4096 MB
```

---

## Step 2: Prepare for Training (5 minutes)

### 2.1 Check Dataset

```bash
cd facesyma_finetune
dir dataset\dataset_combined.jsonl
```

**Expected:**
```
Volume ... Directory of facesyma_finetune\dataset

04/10/2026  03:01     5,242,880  dataset_combined.jsonl
```

If file doesn't exist, go back and run Step 1 from **Quick Start** to generate it.

### 2.2 Check Training Script

```bash
dir training\train_4gb.py
```

Should show the file exists (5.5 KB).

---

## Step 3: Start Training (9-15 hours)

### 3.1 Run Training

```bash
# Make sure venv is activated
venv_gpu\Scripts\activate.bat

# Navigate to training directory
cd facesyma_finetune\training

# Start training
python train_4gb.py --dataset ../dataset/dataset_combined.jsonl --epochs 3
```

### 3.2 Monitor Training

You should see:
```
======================================================================
FACESYMA PHASE 2B - Local GPU Training (4GB)
======================================================================

✓ PyTorch 2.0.1+cu118
✓ CUDA available: True
✓ GPU: NVIDIA GeForce ...
✓ Memory: 4.00 GB

[1/4] Loading base model (quantized 4-bit)...
✓ Model loaded: unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit

[2/4] Adding LoRA adapters...
✓ LoRA added (r=8)
  Trainable: 221,184 / 8,030,261,248 (0.0%)

[3/4] Loading dataset: ../dataset/dataset_combined.jsonl
✓ Loaded 8000 examples

[4/4] Starting training (3 epochs)...
  Output: facesyma-llama3.1-8b-lora-4gb
  Batch size: 1 (per device)
  Grad accum: 8 (effective batch = 8)
  Max seq: 1024
  LoRA rank: 8
  Estimated time: 3-5 hours per epoch

Training started. You can stop with Ctrl+C.

loss: 2.1234 | step: 10/2400
loss: 1.8765 | step: 20/2400
...
```

### 3.3 Monitor GPU Usage

In another terminal, run:
```bash
# Check GPU memory every second
:monitor
cls
nvidia-smi
timeout /t 1 /nobreak
goto monitor
```

**Expected GPU memory:**
- Start: ~3.5-4.0 GB used
- During training: ~3.8-4.0 GB (near max, which is OK)
- If exceeds 4 GB: Will get OOM error (see Troubleshooting)

### 3.4 Training Timeline

```
Epoch 1/3:
  Steps: 0 → 800 (8000 examples ÷ effective batch 8 ÷ gradient steps)
  Time: 3-5 hours
  Loss: ~2.5 → ~1.5

Epoch 2/3:
  Steps: 800 → 1600
  Time: 3-5 hours
  Loss: ~1.4 → ~0.9

Epoch 3/3:
  Steps: 1600 → 2400
  Time: 3-5 hours
  Loss: ~0.8 → ~0.5

Total: ~9-15 hours
```

---

## Step 4: After Training Completes (30 minutes)

### 4.1 Verify Model Output

```bash
dir facesyma-llama3.1-8b-lora-4gb
```

Should contain:
```
adapter_config.json
adapter_model.bin
special_tokens_map.json
tokenizer_config.json
tokenizer.model
tokenizer.json
```

### 4.2 Copy to Serving Directory

```bash
# Copy model to serving directory (for vLLM deployment)
copy facesyma-llama3.1-8b-lora-4gb ..\serving\models\facesyma-llama3.1-8b-lora-4gb
```

Or manually copy the folder.

### 4.3 Merge Model (Optional, for vLLM)

To use the model with vLLM, you need to merge LoRA weights with the base model.

```bash
cd ..
python merge_model.py \
  --lora-model training/facesyma-llama3.1-8b-lora-4gb \
  --output serving/models/facesyma-llama3.1-8b-lora-merged
```

(Merge script will be created in next section)

---

## Step 5: Deploy Model (Next Phase)

Once training is complete, deploy vLLM:

```bash
cd facesyma_finetune\serving

# Start services
docker-compose up
```

This starts:
- vLLM on :8001 (model server)
- FastAPI on :8002 (AI Chat API)

---

## 🚨 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'unsloth'"

**Solution:**
```bash
venv_gpu\Scripts\activate.bat
python -m pip install "unsloth[cu118-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git"
```

If still fails, try without git:
```bash
python -m pip install unsloth
```

---

### Issue: "CUDA out of memory"

**Your GPU has only 4GB, so memory is tight. Try:**

1. **Reduce sequence length:**
   Edit `train_4gb.py`, line 30:
   ```python
   MAX_SEQ_LEN = 512  # Down from 1024
   ```

2. **Reduce LoRA rank:**
   Edit `train_4gb.py`, line 31:
   ```python
   LORA_R = 4  # Down from 8
   ```

3. **Check if other programs use GPU:**
   ```bash
   nvidia-smi
   ```
   Close Chrome, games, or other GPU-using apps.

4. **Run on Windows in Safe Mode** (frees ~500MB)

---

### Issue: "NVIDIA GPU not detected"

**Solution:**
```bash
# Update drivers: https://www.nvidia.com/Download/driverDetails.aspx
nvidia-smi --query-gpu=name --format=csv,noheader

# Reinstall PyTorch with CUDA:
python -m pip uninstall torch -y
python -m pip install torch --index-url https://download.pytorch.org/whl/cu118
```

---

### Issue: Training is too slow

**Expected:** 3-5 hours per epoch on 4GB GPU

If much slower (>6 hours per epoch):
- Check GPU utilization: `nvidia-smi` should show 80-95% GPU
- Close other programs
- Disable Windows updates during training
- Consider moving to RunPod (faster, $2 for 3 epochs)

---

### Issue: "CUDA 11.6 not compatible with PyTorch CUDA 11.8"

**This is OK** — 11.8 is forward-compatible. It will work fine.

If you get errors, install CUDA 12.1 instead:
```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 📊 Performance Expectations

| Metric | Value |
|--------|-------|
| **GPU Memory Used** | 3.8-4.0 GB (near max) |
| **Batch Size** | 1 (per GPU) |
| **Effective Batch** | 8 (with gradient accum) |
| **Steps per Epoch** | 800 (8000 examples ÷ 10) |
| **Time per Epoch** | 3-5 hours |
| **Total Time (3 epochs)** | 9-15 hours |
| **GPU Utilization** | 80-95% |
| **Loss Trajectory** | 2.5 → 1.5 → 0.9 → 0.5 |

---

## ✅ Checklist

- [ ] Virtual environment created (`venv_gpu`)
- [ ] PyTorch installed & CUDA detected
- [ ] Unsloth installed successfully
- [ ] Dataset exists (`dataset_combined.jsonl`)
- [ ] Training script ready (`train_4gb.py`)
- [ ] GPU has free VRAM (check `nvidia-smi`)
- [ ] Ready to train

Once all checked, run:
```bash
venv_gpu\Scripts\activate.bat
cd facesyma_finetune\training
python train_4gb.py --dataset ../dataset/dataset_combined.jsonl --epochs 3
```

---

## 📞 Support

**Common Questions:**

Q: Can I use my CPU instead?
A: No, CPU training would take 50+ hours. You need GPU.

Q: Can I interrupt training and resume?
A: Yes, training saves checkpoints every 100 steps. Interrupting is safe.

Q: Should I leave my computer on for 15 hours?
A: Yes, but prevent sleep: Settings → Power → Never sleep on plugged in

Q: Can I train while gaming?
A: No, gaming will cause CUDA errors. Close all GPU programs.

Q: How much does local training cost?
A: Just electricity (~30-50 cents for 15 hours)

---

**Next Step:** Run `setup_local_gpu.bat` and start training! 🚀

