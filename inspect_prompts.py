import json
import os
from mcqa_enhancement import (
    SYSTEM_PROMPT, 
    load_caption_lookup, 
    parse_mcqa_item, 
    build_user_prompt,
    CSV_INPUT_FILE,
    JSON_INPUT_FILE
)

def main():
    """
    Script to inspect the prompt structure for the first two items
    using logic imported directly from mcqa_enhancement.py
    """
    print("--- Prompt Inspection Script ---")
    
    # 1. Load data using existing functions
    if not os.path.exists(CSV_INPUT_FILE) or not os.path.exists(JSON_INPUT_FILE):
        print("Error: Data files not found. Make sure you are in the Qwen3 directory.")
        return

    caption_dict = load_caption_lookup(CSV_INPUT_FILE)
    
    with open(JSON_INPUT_FILE, 'r') as f:
        mcqa_data = json.load(f)
    
    # 2. Inspect first 2 items
    for i in range(min(2, len(mcqa_data))):
        item = mcqa_data[i]
        print(f"\n{'='*80}")
        print(f"EXAMPLE {i+1} (ID: {item.get('id', 'N/A')})")
        print(f"{'='*80}")
        
        # Get caption
        image_path = item.get('image', '')
        caption = caption_dict.get(image_path.lower(), "NO CAPTION FOUND")
        
        # Parse item
        parsed = parse_mcqa_item(item)
        if not parsed:
            print("Failed to parse this item using parse_mcqa_item().")
            continue
            
        question_text, answer_text, options, _ = parsed
        
        # Build user prompt
        user_prompt = build_user_prompt(caption, question_text, answer_text, options)
        
        # Construct full Qwen chat template
        full_prompt = (
            f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
            f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )
        
        print("\n--- FULL CONSTRUCTED PROMPT ---")
        print(full_prompt)
        print("-" * 80)

if __name__ == "__main__":
    main()




