# Manual Setup Steps (If Auto Setup Takes Too Long)

If `setup_local_gpu.py` is running slowly or you want to do it manually:

## Step 1: Open Command Prompt

Press `Win + R`, type `cmd`, press Enter

```bash
cd C:\Users\asus.LAPTOP-V8BS7MTO\Desktop\facesyma-sonn-canim
```

## Step 2: Create Virtual Environment (2 minutes)

```bash
python -m venv venv_gpu
venv_gpu\Scripts\activate.bat
```

Expected output:
```
(venv_gpu) C:\Users\...>
```

## Step 3: Upgrade pip (2 minutes)

```bash
python -m pip install --upgrade pip setuptools wheel
```

## Step 4: Install PyTorch with CUDA 11.8 (10-20 minutes)

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**This is slow** — it downloads 2-3 GB

Verify:
```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

Expected:
```
2.x.x+cu118
True
```

## Step 5: Install Unsloth (10-30 minutes)

**Option A: From Git (Recommended)**
```bash
python -m pip install "unsloth[cu118-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git"
```

**Option B: From PyPI (Faster Fallback)**
```bash
python -m pip install unsloth
```

## Step 6: Install Other Dependencies (5 minutes)

```bash
python -m pip install transformers==4.46.0 datasets==3.0.1 trl==0.11.4 peft==0.13.2 accelerate==1.0.1 bitsandbytes==0.44.1
```

## Step 7: Verify Everything

```bash
python -c "from unsloth import FastLanguageModel; print('✓ Unsloth ready'); import torch; print(f'✓ PyTorch {torch.__version__}')"
```

Expected:
```
✓ Unsloth ready
✓ PyTorch 2.x.x+cu118
```

## Step 8: Start Training

```bash
cd facesyma_finetune\training
python train_4gb.py --dataset ../dataset/dataset_combined.jsonl --epochs 3
```

---

## Total Time Estimate

| Step | Time |
|------|------|
| venv | 2 min |
| pip upgrade | 2 min |
| PyTorch | 10-20 min |
| Unsloth | 10-30 min |
| Other deps | 5 min |
| **Total Setup** | **30-60 min** |
| **Training** | **9-15 hours** |
| **Total** | **10-16 hours** |

---

## If Stuck

Check this guide: `PHASE_2B_LOCAL_GPU_GUIDE.md`

