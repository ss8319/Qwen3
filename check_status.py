#!/usr/bin/env python3
"""
Quick status checker for MCQA enhancement pipeline.
Shows progress, statistics, and next steps.
"""
import json
import os
from datetime import datetime

def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_section(text):
    print(f"\n{text}")
    print("-" * 80)

def check_files():
    """Check which files exist."""
    print_header("File Status")
    
    files = {
        'Input JSON': 'data/ClinicalContext_MCQA.json',
        'Input CSV': 'data/textbook_IIYI_PubMed.csv',
        'Output JSON': 'data/enhanced_ClinicalContext_MCQA.json',
        'Progress': 'progress.json',
        'Skipped': 'skipped_questions.jsonl',
        'Error Log': 'enhancement_errors.log'
    }
    
    for name, path in files.items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            print(f"✓ {name:15} {path:45} ({size_str}, modified {mtime.strftime('%Y-%m-%d %H:%M')})")
        else:
            print(f"✗ {name:15} {path:45} (not found)")

def check_progress():
    """Check processing progress."""
    print_header("Processing Progress")
    
    # Load input data
    try:
        with open('data/ClinicalContext_MCQA.json', 'r') as f:
            total_items = len(json.load(f))
        print(f"Total MCQA items: {total_items}")
    except:
        print("✗ Cannot load input JSON")
        return
    
    # Load progress
    processed_count = 0
    if os.path.exists('progress.json'):
        try:
            with open('progress.json', 'r') as f:
                progress = json.load(f)
                processed_count = len(progress.get('processed_ids', []))
            print(f"Processed items: {processed_count}")
        except:
            print("✗ Cannot load progress.json")
    else:
        print("Processed items: 0 (not started)")
    
    # Load enhanced output
    enhanced_count = 0
    if os.path.exists('data/enhanced_ClinicalContext_MCQA.json'):
        try:
            with open('data/enhanced_ClinicalContext_MCQA.json', 'r') as f:
                enhanced_count = len(json.load(f))
            print(f"Enhanced items: {enhanced_count}")
        except:
            print("✗ Cannot load output JSON")
    else:
        print("Enhanced items: 0")
    
    # Load skipped
    skipped_count = 0
    if os.path.exists('skipped_questions.jsonl'):
        try:
            with open('skipped_questions.jsonl', 'r') as f:
                skipped_count = sum(1 for _ in f)
            print(f"Skipped items: {skipped_count}")
        except:
            print("✗ Cannot load skipped.jsonl")
    else:
        print("Skipped items: 0")
    
    # Calculate statistics
    if processed_count > 0:
        progress_pct = (processed_count / total_items) * 100
        print(f"\nProgress: {progress_pct:.1f}% ({processed_count}/{total_items})")
        
        if enhanced_count > 0:
            success_rate = (enhanced_count / processed_count) * 100
            print(f"Success rate: {success_rate:.1f}% ({enhanced_count}/{processed_count} enhanced)")
        
        remaining = total_items - processed_count
        if remaining > 0:
            print(f"Remaining: {remaining} items")
            
            # Estimate time
            batch_size = 4
            batches_remaining = (remaining + batch_size - 1) // batch_size
            seconds_per_batch = 45  # Conservative estimate
            hours_remaining = (batches_remaining * seconds_per_batch) / 3600
            print(f"Estimated time remaining: {hours_remaining:.1f} hours ({batches_remaining} batches)")

def check_errors():
    """Check recent errors."""
    print_header("Recent Errors")
    
    if not os.path.exists('enhancement_errors.log'):
        print("No error log found (good!)")
        return
    
    try:
        with open('enhancement_errors.log', 'r') as f:
            lines = f.readlines()
        
        if len(lines) == 0:
            print("No errors logged (good!)")
            return
        
        # Count error types
        error_lines = [l for l in lines if 'ERROR' in l]
        warning_lines = [l for l in lines if 'WARNING' in l]
        
        print(f"Total log lines: {len(lines)}")
        print(f"Errors: {len(error_lines)}")
        print(f"Warnings: {len(warning_lines)}")
        
        if len(error_lines) > 0:
            print("\nLast 5 errors:")
            for line in error_lines[-5:]:
                print(f"  {line.strip()}")
    except:
        print("✗ Cannot read error log")

def show_next_steps():
    """Show recommended next steps."""
    print_header("Next Steps")
    
    if not os.path.exists('progress.json'):
        print("🚀 Pipeline not started yet. Recommended steps:")
        print("\n1. Run tests:")
        print("   python test_mcqa_enhancement.py")
        print("\n2. Small test run (2 items):")
        print("   python test_small_run.py")
        print("   python mcqa_enhancement_test_run.py")
        print("\n3. Start full pipeline:")
        print("   python mcqa_enhancement.py")
    else:
        try:
            with open('progress.json', 'r') as f:
                progress = json.load(f)
                processed = len(progress.get('processed_ids', []))
            
            with open('data/ClinicalContext_MCQA.json', 'r') as f:
                total = len(json.load(f))
            
            if processed >= total:
                print("✅ Pipeline complete!")
                print("\nView results:")
                print("   cat data/enhanced_ClinicalContext_MCQA.json")
                print("\nGenerate statistics:")
                print("   python -c \"import json; print(len(json.load(open('data/enhanced_ClinicalContext_MCQA.json'))))\"")
            else:
                print("⏳ Pipeline in progress. To continue:")
                print("\n1. Resume processing:")
                print("   python mcqa_enhancement.py")
                print("\n2. Monitor progress:")
                print("   tail -f enhancement_errors.log")
                print("\n3. Check status again:")
                print("   python check_status.py")
        except:
            print("✗ Cannot determine status")

def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MCQA Enhancement Pipeline Status" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    
    check_files()
    check_progress()
    check_errors()
    show_next_steps()
    
    print("\n" + "=" * 80)
    print("For detailed documentation, see: MCQA_ENHANCEMENT_README.md")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

