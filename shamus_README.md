# 🚀 Qwen3 Docker: Simplified Guide

Use these commands to avoid name conflicts, "module not found" errors, and session crashes.

---

### 1. Start the Background Container
Run this once from `/raid/scratch/shamus/Qwen3`. It creates a permanent environment named `qwen3`.

```bash
# Force remove any old/buggy containers first
docker rm -f qwen3 2>/dev/null

# Start a fresh, permanent container
docker run --gpus all -d -it \
  --name qwen3 \
  -v $(pwd):/workspace \
  -p 8000:8000 \
  qwen3-vllm:latest
```

### 2. Enter the Container (Bug-Free)
Whenever you want to work, just use this simple command:
```bash
docker exec -it qwen3 bash
```

---

### 3. Persistent Sessions (TMUX)
To run long inference scripts without them dying when you disconnect, follow this exact order:

1. **On the Host (DGX):** Create a tmux session.
   ```bash
   tmux new -s inference
   ```
2. **Inside Tmux:** Enter the container and run.
   ```bash
   docker exec -it qwen3 bash
   python mcqa_enhancement.py
   ```
3. **To Detach:** Press `Ctrl + B` then `D`.
4. **To Return:** `tmux attach -t inference`

---

### 🚑 Troubleshooting & Cleanup

**"Conflict: Name already in use"**
```bash
docker rm -f qwen3
```

**"Module not found" or code not updating**
```bash
# Clear Python cache inside /workspace
rm -rf __pycache__
find . -name "*.pyc" -delete
```

**Check if GPU is visible inside Docker**
```bash
docker exec -it qwen3 nvidia-smi
```

---

### 📁 Dataset Summary (Reference)
- **Total Items**: 9,625
- **IIYI_chinese**: 9,287 (96.5%)
- **pubmed_english**: 338 (3.5%)
- **Location**: `data/ClinicalContext_MCQA.json`
