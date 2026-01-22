"""
Small test run with 2 items to verify the full pipeline.
"""
import json
import os
import shutil

# Backup original files if they exist
backup_files = {
    'progress.json': 'progress.json.backup',
    'data/enhanced_ClinicalContext_MCQA.json': 'data/enhanced_ClinicalContext_MCQA.json.backup',
    'skipped_questions.jsonl': 'skipped_questions.jsonl.backup',
    'enhancement_errors.log': 'enhancement_errors.log.backup'
}

print("Creating backups of existing files...")
for original, backup in backup_files.items():
    if os.path.exists(original):
        shutil.copy(original, backup)
        print(f"  ✓ Backed up {original} -> {backup}")

# Load original JSON
print("\nLoading original MCQA data...")
with open('data/ClinicalContext_MCQA.json', 'r') as f:
    original_data = json.load(f)

# Create a test file with just 2 items
test_data = original_data[:2]
test_file = 'data/ClinicalContext_MCQA_test.json'

print(f"Creating test file with {len(test_data)} items...")
with open(test_file, 'w') as f:
    json.dump(test_data, f, indent=2)

print(f"✓ Created {test_file}")

# Modify the main script temporarily
print("\nModifying mcqa_enhancement.py for test run...")
with open('mcqa_enhancement.py', 'r') as f:
    content = f.read()

# Replace file paths
test_content = content.replace(
    "JSON_INPUT_FILE = 'data/ClinicalContext_MCQA.json'",
    "JSON_INPUT_FILE = 'data/ClinicalContext_MCQA_test.json'"
)
test_content = test_content.replace(
    "JSON_OUTPUT_FILE = 'data/enhanced_ClinicalContext_MCQA.json'",
    "JSON_OUTPUT_FILE = 'data/enhanced_ClinicalContext_MCQA_test.json'"
)
test_content = test_content.replace(
    "PROGRESS_FILE = 'progress.json'",
    "PROGRESS_FILE = 'progress_test.json'"
)
test_content = test_content.replace(
    "SKIPPED_FILE = 'skipped_questions.jsonl'",
    "SKIPPED_FILE = 'skipped_questions_test.jsonl'"
)
test_content = test_content.replace(
    "ERROR_LOG_FILE = 'enhancement_errors.log'",
    "ERROR_LOG_FILE = 'enhancement_errors_test.log'"
)

with open('mcqa_enhancement_test_run.py', 'w') as f:
    f.write(test_content)

print("✓ Created mcqa_enhancement_test_run.py")

print("\n" + "=" * 80)
print("Test setup complete!")
print("=" * 80)
print("\nTo run the test:")
print("  python mcqa_enhancement_test_run.py")
print("\nThis will process 2 items and create test output files.")
print("Original files are backed up with .backup extension.")
print("\nAfter testing, you can:")
print("1. Review the test output in data/enhanced_ClinicalContext_MCQA_test.json")
print("2. Run the full pipeline with: python mcqa_enhancement.py")
print("3. Restore backups if needed")

