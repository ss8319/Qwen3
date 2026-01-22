import pandas as pd
from vllm import LLM, SamplingParams
import json
import os
import re
import logging
import time
from typing import Dict, List, Optional
from tqdm import tqdm

# Settings
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"
JSON_INPUT_FILE = 'data/ClinicalContext_MCQA.json'
CSV_INPUT_FILE = 'data/textbook_IIYI_PubMed.csv'
JSON_OUTPUT_FILE = 'data/enhanced_ClinicalContext_MCQA_vllm.json'

# Load Instructions (same as before)
try:
    from mcqa_enhancement import (
        SYSTEM_PROMPT, 
        load_caption_lookup, 
        parse_mcqa_item, 
        build_user_prompt, 
        parse_llm_response, 
        update_conversation_value,
        find_correct_option # Import the new robust helper
    )
except ImportError:
    print("Error: Could not import from mcqa_enhancement.py. Make sure it's in the same directory.")
    exit(1)

def main():
    print(f"Starting vLLM enhancement script on model: {MODEL_NAME}")
    
    # 1. Load Data
    print("Loading data...")
    caption_dict = load_caption_lookup(CSV_INPUT_FILE)
    if not os.path.exists(JSON_INPUT_FILE):
        print(f"Error: {JSON_INPUT_FILE} not found.")
        return
        
    with open(JSON_INPUT_FILE, 'r') as f:
        mcqa_data = json.load(f)
    print(f"Loaded {len(mcqa_data)} items from JSON.")

    # Apply test limit
    N_TEST = 20
    if len(mcqa_data) > N_TEST:
        print(f"Test Mode: Limiting to first {N_TEST} items")
        mcqa_data = mcqa_data[:N_TEST]

    # 2. Initialize vLLM 
    print("Initializing vLLM engine (this may take a minute)...")
    try:
        llm = LLM(
            model=MODEL_NAME, 
            tensor_parallel_size=1, # Single GPU
            gpu_memory_utilization=0.90,
            trust_remote_code=True
        )
    except Exception as e:
        print(f"Failed to initialize vLLM: {e}")
        return
    
    # Default inference config (Greedy decoding)
    sampling_params = SamplingParams(
        temperature=0.0, # Greedy
        max_tokens=512,
        stop=["<|endoftext|>", "<|im_end|>"]
    )

    # 3. Prepare Prompts
    print("Preparing prompts...")
    prompts = []
    items_to_process = []
    
    for item in mcqa_data:
        image_path = item['image']
        caption = caption_dict.get(image_path.lower(), "")
        if not caption: 
            print(f"Warning: No caption for {image_path}")
            continue
        
        parsed = parse_mcqa_item(item)
        if not parsed: continue
        
        q, a, opts, _ = parsed
        user_prompt = build_user_prompt(caption, q, a, opts)
        
        # Format for Qwen Chat Template
        full_prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
        prompts.append(full_prompt)
        items_to_process.append((item, parsed))

    if not prompts:
        print("No items to process. Exiting.")
        return

    # 4. Run Inference
    print(f"Generating responses for {len(prompts)} items...")
    start_time = time.time()
    outputs = llm.generate(prompts, sampling_params)
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / len(prompts)
    print(f"Inference completed in {total_time:.2f}s | Avg time per QA: {avg_time:.2f}s")

    # 5. Save Results
    print("Saving results...")
    final_results = []
    for (item, parsed), output in zip(items_to_process, outputs):
        response = output.outputs[0].text
        new_opts = parse_llm_response(response)
        
        if new_opts:
            # Robustly find the new label for the correct answer
            original_answer = parsed[1] # answer_text from parse_mcqa_item
            new_gpt_value = find_correct_option(new_opts, original_answer)
            
            if new_gpt_value:
                item_copy = item.copy()
                item_copy['original_gpt'] = original_answer # Store original 4-way
                item_copy['conversations'] = [
                    {"from": "human", "value": update_conversation_value(parsed[3], new_opts)},
                    {"from": "gpt", "value": new_gpt_value} # Updated 8-way label
                ]
                final_results.append(item_copy)
            else:
                print(f"Warning: Could not align answer for item {item['id']}")

    with open(JSON_OUTPUT_FILE, 'w') as f:
        json.dump(final_results, f, indent=2)
    print(f"Done! Saved results to {JSON_OUTPUT_FILE}")
    print(f"Summary: Enhanced {len(final_results)} items.")
    print(f"Average processing time: {avg_time:.2f}s per item.")

if __name__ == "__main__":
    main()
