# MCQA Enhancement Pipeline

## Overview

This pipeline enhances the dermatology VQA benchmark by expanding multiple-choice questions from 4 options to 8 options using Qwen2.5-72B-Instruct. The system intelligently identifies diagnosis questions and generates medically valid distractor options while maintaining the integrity of the original correct answer.

## Features

- **Automatic Caption Matching**: Links MCQA questions with their original image captions from the textbook dataset
- **Smart Question Detection**: Identifies diagnosis questions vs. other question types (e.g., treatment, morphology)
- **Resumable Processing**: Saves progress after each batch, allowing interruption and restart
- **Comprehensive Logging**: Tracks enhanced items, skipped questions, and errors
- **Batch Processing**: Efficient GPU utilization with configurable batch sizes
- **Case-Insensitive Matching**: Handles filename variations between JSON and CSV data

## File Structure

```
Qwen3/
├── mcqa_enhancement.py              # Main pipeline script
├── test_mcqa_enhancement.py         # Test suite (no model loading)
├── test_small_run.py                # Setup script for small test run
├── data/
│   ├── ClinicalContext_MCQA.json    # Input: Original 4-option questions
│   ├── textbook_IIYI_PubMed.csv     # Input: Image captions
│   └── enhanced_ClinicalContext_MCQA.json  # Output: Enhanced 8-option questions
├── progress.json                     # Resumable state
├── skipped_questions.jsonl          # Non-diagnosis questions (SKIP)
└── enhancement_errors.log           # Error tracking and debug info
```

## Installation

1. **Environment Setup** (already done):
```bash
source .venv/bin/activate
```

2. **Verify Dependencies**:
```bash
python -c "import torch, transformers, pandas; print('✓ All dependencies installed')"
```

## Usage

### Step 1: Run Tests

Verify the pipeline without loading the model:

```bash
python test_mcqa_enhancement.py
```

Expected output: All 5 tests should pass ✓

### Step 2: Small Test Run (Optional)

Test with 2 items using the actual model:

```bash
# Setup test files
python test_small_run.py

# Run test (will load model and process 2 items)
python mcqa_enhancement_test_run.py

# Review output
cat data/enhanced_ClinicalContext_MCQA_test.json
```

### Step 3: Full Pipeline

Process all MCQA items:

```bash
python mcqa_enhancement.py
```

**Note**: This will take significant time (hours to days) depending on:
- Number of items: 9,625 MCQA questions
- Batch size: 4 items per batch (configurable)
- GPU availability and model loading time

### Resuming After Interruption

The pipeline automatically resumes from where it stopped:

```bash
# Simply run again - it will skip already processed items
python mcqa_enhancement.py
```

Progress is saved in `progress.json` after each batch.

## Configuration

Edit these constants in `mcqa_enhancement.py`:

```python
BATCH_SIZE = 4              # Items per batch (adjust based on GPU memory)
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"  # Model to use
```

## Output Format

### Enhanced MCQA Item

```json
{
  "id": "21898_5",
  "image": "Images/education/21898_5.png",
  "source": "IIYI_chinese",
  "disease": "pyoderma",
  "conversations": [
    {
      "from": "human",
      "value": "<image>\nA 2-year-old male child presents with a 4-day history of a painful rash and intermittent fevers for one week. Examination reveals scattered crusted papules and pustules. Laboratory testing shows a white blood cell count of 11,000/µL with 72% neutrophils. Which of the following is the most likely diagnosis?\nOptions:\nA) Impetigo (pyoderma)\nB) Kaposi varicelliform eruption\nC) Varicella (chickenpox)\nD) Eczema herpeticum\nE) Bullous impetigo\nF) Staphylococcal scalded skin syndrome\nG) Herpes simplex infection\nH) Erythema multiforme"
    },
    {
      "from": "gpt",
      "value": "A) Impetigo (pyoderma)"
    }
  ]
}
```

### Skipped Questions

Non-diagnosis questions are logged to `skipped_questions.jsonl`:

```json
{"id": "5134_6", "image": "Images/education/5134_6.png", ...}
```

These questions ask about morphology, treatment, or other aspects rather than diagnosis.

## Monitoring Progress

### Check Progress

```bash
# View progress file
cat progress.json

# Count processed items
python -c "import json; print(len(json.load(open('progress.json'))['processed_ids']))"

# Count skipped questions
wc -l skipped_questions.jsonl

# View recent errors
tail -n 50 enhancement_errors.log
```

### Real-time Monitoring

```bash
# In one terminal, run the pipeline
python mcqa_enhancement.py

# In another terminal, monitor logs
tail -f enhancement_errors.log
```

## Workflow Details

### 1. Data Loading
- Loads 9,625 MCQA items from JSON
- Loads 97,866 captions from CSV
- Creates case-insensitive lookup dictionary

### 2. Caption Matching
- Matches JSON `image` field with CSV `filename` field
- Example: `"Images/education/21898_5.png"` → `"images/education/21898_5.png"`
- Handles case variations automatically

### 3. Question Parsing
- Extracts question text, options, and answer from conversations
- Validates format (must have "Options:" separator)
- Parses 4 original options (A-D)

### 4. LLM Prompting
The system uses the prompt defined in lines 42-83 of the original file:

```
You are curating and enhancing a dermatology VQA benchmark (Derm1M).
You are given the following inputs:
caption: {Origin_caption}
question: {Question}
answer (correct diagnosis): {Answer}
original_options: {Origin_option}
...
```

### 5. Response Handling
- **`<SKIP>`**: Non-diagnosis question → logged to `skipped_questions.jsonl`
- **8 options (A-H)**: Valid response → updates JSON with enhanced options
- **Invalid**: Error logged, item skipped

### 6. Progress Tracking
- Saves processed IDs after each batch
- Allows resumption from any point
- Prevents duplicate processing

## Error Handling

### Common Issues

1. **Missing Caption**
   - Error: "No caption found for {image_path}"
   - Action: Item skipped, logged to errors
   - Cause: Image not in CSV dataset

2. **Malformed Options**
   - Error: "Expected 4 options, found {n}"
   - Action: Item skipped
   - Cause: Non-standard question format

3. **Invalid LLM Response**
   - Error: "Expected 8 options, found {n}"
   - Action: Item skipped, response logged
   - Cause: Model didn't follow format

4. **GPU Out of Memory**
   - Solution: Reduce `BATCH_SIZE` in configuration
   - Try: 2 or 1 for very large models

### Debugging

```bash
# View all errors
cat enhancement_errors.log

# Search for specific item
grep "21898_5" enhancement_errors.log

# Count error types
grep "Error:" enhancement_errors.log | sort | uniq -c
```

## Performance

### Expected Timeline

- **Model Loading**: 5-10 minutes (first time)
- **Per Batch (4 items)**: ~30-60 seconds
- **Total Batches**: ~2,406 batches (9,625 items ÷ 4)
- **Estimated Total Time**: 20-40 hours (with GPU)

### Optimization Tips

1. **Increase Batch Size**: If GPU memory allows
   ```python
   BATCH_SIZE = 8  # or higher
   ```

2. **Use Multiple GPUs**: Modify `device_map` in model loading

3. **Run in Background**: Use screen or tmux
   ```bash
   screen -S mcqa
   python mcqa_enhancement.py
   # Ctrl+A, D to detach
   ```

## Quality Assurance

### Validation Checks

The pipeline automatically validates:
- ✓ Exactly 8 options generated (A-H)
- ✓ Correct answer appears in new options
- ✓ Options properly formatted
- ✓ No duplicate processing

### Manual Review

After completion, review samples:

```bash
# View first enhanced item
python -c "import json; print(json.dumps(json.load(open('data/enhanced_ClinicalContext_MCQA.json'))[0], indent=2))"

# Count total enhanced items
python -c "import json; print(len(json.load(open('data/enhanced_ClinicalContext_MCQA.json'))))"
```

## Troubleshooting

### Pipeline Won't Start

```bash
# Check if model is accessible
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen2.5-72B-Instruct')"

# Verify data files exist
ls -lh data/ClinicalContext_MCQA.json data/textbook_IIYI_PubMed.csv
```

### Pipeline Stuck

```bash
# Check if process is running
ps aux | grep mcqa_enhancement

# Check GPU usage
nvidia-smi

# View last log entries
tail -n 20 enhancement_errors.log
```

### Reset and Start Over

```bash
# Remove progress and output files
rm progress.json
rm data/enhanced_ClinicalContext_MCQA.json
rm skipped_questions.jsonl
rm enhancement_errors.log

# Start fresh
python mcqa_enhancement.py
```

## Statistics

After completion, generate statistics:

```bash
python -c "
import json

# Load results
with open('data/enhanced_ClinicalContext_MCQA.json') as f:
    enhanced = json.load(f)

# Count skipped
with open('skipped_questions.jsonl') as f:
    skipped = sum(1 for _ in f)

# Load progress
with open('progress.json') as f:
    progress = json.load(f)
    total_processed = len(progress['processed_ids'])

print(f'Enhanced: {len(enhanced)}')
print(f'Skipped: {skipped}')
print(f'Total Processed: {total_processed}')
print(f'Success Rate: {len(enhanced)/total_processed*100:.1f}%')
"
```

## Citation

If you use this enhanced dataset, please cite:

```bibtex
@misc{qwen3-mcqa-enhancement,
  title={Enhanced Dermatology VQA Benchmark with 8-Option Multiple Choice Questions},
  author={Your Name},
  year={2026},
  note={Generated using Qwen2.5-72B-Instruct}
}
```

## Support

For issues or questions:
1. Check `enhancement_errors.log` for detailed error messages
2. Review the test suite output: `python test_mcqa_enhancement.py`
3. Verify data integrity with the test scripts

## License

This pipeline follows the same license as the Qwen3 repository (Apache 2.0).

