# MCQA Enhancement - Quick Start Guide

## 🎯 Goal
Enhance dermatology VQA benchmark: **4 options → 8 options** using Qwen2.5-72B

## 📋 Prerequisites
- ✅ Environment setup complete (`.venv/` with all dependencies)
- ✅ GPU available for model inference
- ✅ Input files in place:
  - `data/ClinicalContext_MCQA.json` (9,625 items)
  - `data/textbook_IIYI_PubMed.csv` (97,866 captions)

## 🚀 Three-Step Process

### Step 1: Verify Setup (2 minutes)
```bash
source .venv/bin/activate
python test_mcqa_enhancement.py
```
**Expected**: All 5 tests pass ✓

### Step 2: Test Run (5-10 minutes)
```bash
python test_small_run.py
python mcqa_enhancement_test_run.py
```
**Expected**: 2 items processed successfully

### Step 3: Full Pipeline (20-40 hours)
```bash
# Recommended: Use screen/tmux for long-running process
screen -S mcqa
python mcqa_enhancement.py
# Press Ctrl+A, D to detach
```

## 📊 Monitor Progress

### Check Status
```bash
python check_status.py
```

### View Logs
```bash
tail -f enhancement_errors.log
```

### Count Processed
```bash
python -c "import json; print(len(json.load(open('progress.json'))['processed_ids']))"
```

## 📁 Output Files

| File | Description |
|------|-------------|
| `data/enhanced_ClinicalContext_MCQA.json` | Enhanced questions (8 options) |
| `skipped_questions.jsonl` | Non-diagnosis questions |
| `progress.json` | Resumable state |
| `enhancement_errors.log` | Error tracking |

## 🔄 Resume After Interruption

Just run again - it automatically resumes:
```bash
python mcqa_enhancement.py
```

## ⚙️ Configuration

Edit `mcqa_enhancement.py` to adjust:
```python
BATCH_SIZE = 4  # Increase if you have more GPU memory
```

## 📖 Full Documentation

- **User Guide**: `MCQA_ENHANCEMENT_README.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **Original Spec**: `spec.md`

## 🆘 Troubleshooting

### Pipeline won't start
```bash
# Check GPU
nvidia-smi

# Verify model access
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-72B-Instruct')"
```

### Out of memory
Reduce batch size in `mcqa_enhancement.py`:
```python
BATCH_SIZE = 2  # or 1
```

### Reset everything
```bash
rm progress.json data/enhanced_ClinicalContext_MCQA.json skipped_questions.jsonl enhancement_errors.log
python mcqa_enhancement.py
```

## ✅ Success Criteria

After completion:
- Enhanced items: ~7,000-8,000 (diagnosis questions)
- Skipped items: ~1,500-2,500 (non-diagnosis)
- Total processed: 9,625 (all items)

## 🎉 Quick Commands

```bash
# Activate environment
source .venv/bin/activate

# Run tests
python test_mcqa_enhancement.py

# Check status
python check_status.py

# Start pipeline
python mcqa_enhancement.py

# Monitor
tail -f enhancement_errors.log
```

---

**Ready to start?** Run: `python test_mcqa_enhancement.py`

