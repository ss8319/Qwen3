import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm
import json
import os
import re
import logging
from typing import Dict, List, Tuple, Optional
import time

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
JSON_INPUT_FILE = 'data/ClinicalContext_MCQA_part1.json'
CSV_INPUT_FILE = 'data/textbook_IIYI_PubMed.csv'
JSON_OUTPUT_FILE = 'data/enhanced/ClinicalContext_MCQA_part1.json'
PROGRESS_FILE = 'progress_ClinicalContext_MCQA_part1.json'
SKIPPED_FILE = 'skipped_questions_ClinicalContext_MCQA_part1.jsonl'
ERROR_LOG_FILE = 'enhancement_errors_ClinicalContext_MCQA_part1.log'
BATCH_SIZE = 4
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

# -------------------------------------------------------------------------
# Setup Logging
# -------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ERROR_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# System Prompt (from lines 42-83 of original file)
# -------------------------------------------------------------------------
SYSTEM_PROMPT = '''You are curating and enhancing a dermatology VQA benchmark (Derm1M).
You are given the following inputs:
caption: {Origin_caption}
question: {Question}
answer (correct diagnosis): {Answer}
original_options: {Origin_option}
Task:
First, determine whether the question is a DIAGNOSIS question.
A diagnosis question explicitly asks for identification of a disease or condition, using phrases such as: "diagnosis", "most likely diagnosis", "what condition", "what disease", or "what is this lesion".
If the question is NOT a diagnosis question, output exactly: <SKIP>
If the question IS a diagnosis question, generate a revised set of multiple-choice options under the rules below.
Important rule about the caption:
Do NOT modify, rewrite, or paraphrase the caption.
The caption should be preserved exactly as given.
ONLY if the caption explicitly contains highly uncertain or speculative differential diagnoses (e.g., multiple competing diagnoses presented as possibilities rather than findings), you MAY minimally remove or neutralize those speculative diagnosis terms.
Do NOT add new information to the caption.
Do NOT rephrase confirmed diagnoses or factual findings.
Output format:
Output ONLY the options.
Exactly 8 options.
One option per line.
Use labels A) through H).
Do NOT include explanations, reasoning, or extra text.
Rules for option generation:
The correct answer diagnosis MUST appear exactly once and remain unchanged.
If the caption mentions multiple diagnoses, KEEP ONLY the correct answer diagnosis; any other diagnosis terms in the caption MUST NOT be used as options.
Do NOT include any diagnosis term that appears verbatim in the question as a distractor.
All distractors MUST be medically valid diagnostic entities. Do NOT invent terms or use vague or descriptive phrases.
Distractors SHOULD reduce superficial elimination: 
Prefer conditions sharing anatomical location, gross morphology, or clinical context with the correct answer.
Distractors MUST remain distinguishable from the correct answer: 
Do NOT include synonymous names, hierarchical variants, or the same disease under different terminology.
Do NOT include entities that would be indistinguishable without histopathology if pathology is not explicitly required by the question.
Include a mixture of distractor difficulty: 
Some common confounders.
Some less common but plausible alternatives.
Avoid making all distractors equally hard.
The final output MUST contain exactly 8 options labeled A)–H).
Final output:
Either 8 formatted options (A–H), or
<SKIP>
'''

# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------

def load_caption_lookup(csv_path: str) -> Dict[str, str]:
    """Load CSV and create case-insensitive filename -> caption mapping."""
    if not os.path.exists(csv_path):
        logger.error(f"FATAL: CSV file not found at {csv_path}")
        raise FileNotFoundError(f"Missing input: {csv_path}")
        
    logger.info(f"Loading captions from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
        if 'filename' not in df.columns or 'caption' not in df.columns:
            logger.error(f"FATAL: CSV must contain 'filename' and 'caption' columns. Found: {df.columns.tolist()}")
            raise ValueError("Malformed CSV headers")
            
        caption_dict = {}
        for _, row in df.iterrows():
            filename = str(row['filename'])
            caption = str(row['caption'])
            caption_dict[filename.lower()] = caption
        logger.info(f"Loaded {len(caption_dict)} captions")
        return caption_dict
    except Exception as e:
        logger.error(f"FATAL: Failed to read CSV: {e}")
        raise

def parse_mcqa_item(item: dict) -> Optional[Tuple[str, str, List[str], str]]:
    """
    Parse MCQA item to extract question, options, and answer.
    """
    item_id = item.get('id', 'unknown')
    try:
        if 'conversations' not in item or len(item['conversations']) < 2:
            logger.warning(f"Item {item_id}: Missing conversations")
            return None
            
        conversation_value = item['conversations'][0]['value']
        
        if 'Options:' not in conversation_value:
            logger.warning(f"Item {item_id}: No 'Options:' delimiter found in human message")
            return None
        
        parts = conversation_value.split('Options:')
        question_text = parts[0].replace('<image>\n', '').replace('<image>', '').strip()
        options_text = parts[1].strip()
        
        options = re.findall(r'([A-Z]\).*?)(?=[A-Z]\)|$)', options_text, re.DOTALL)
        options = [opt.strip() for opt in options]
        
        if len(options) < 1:
            logger.warning(f"Item {item_id}: No options found. Content: {options_text[:100]}...")
            return None
        
        answer_text = item['conversations'][1]['value'].strip()
        return question_text, answer_text, options, conversation_value
        
    except Exception as e:
        logger.error(f"Item {item_id}: Unexpected parsing error: {e}")
        return None


def build_user_prompt(caption: str, question: str, answer: str, options: List[str]) -> str:
    """Build the user prompt for LLM."""
    formatted_options = '\n'.join(options)
    
    user_input = f"""caption: {caption}
question: {question}
answer (correct diagnosis): {answer}
original_options:
{formatted_options}"""
    
    return user_input


def parse_llm_response(response: str) -> Optional[List[str]]:
    """
    Parse LLM response to extract 8 options or detect SKIP.
    
    Returns:
        List of 8 options, or None if SKIP or invalid
    """
    response = response.strip()
    
    # Check for SKIP
    if response == '<SKIP>':
        return None
    
    # Extract options A) through H)
    options = re.findall(r'([A-H]\).*?)(?=[A-H]\)|$)', response, re.DOTALL)
    options = [opt.strip() for opt in options]
    
    if len(options) != 8:
        logger.warning(f"Expected 8 options, found {len(options)}")
        return None
    
    return options


def update_conversation_value(original_value: str, new_options: List[str]) -> str:
    """Update the conversation value with new 8 options.
    The text before the string "Options:" is kept; everything after "Options:" is replaced by the 8 LLM-generated options."""
    # Split by "Options:"
    parts = original_value.split('Options:')
    question_part = parts[0]
    
    # Build new options text
    new_options_text = '\n'.join(new_options)
    
    # Reconstruct
    new_value = f"{question_part}Options:\n{new_options_text}"
    
    return new_value


def load_progress() -> set:
    """Load processed IDs from progress file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            return set(progress.get('processed_ids', []))
    return set()


def save_progress(processed_ids: set):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'processed_ids': list(processed_ids)}, f)


def append_to_output(item: dict):
    """Append enhanced item to output JSON file while keeping valid array structure."""
    if not os.path.exists(JSON_OUTPUT_FILE):
        # Create new file
        try:
            with open(JSON_OUTPUT_FILE, 'w') as f:
                f.write('[\n')
                json.dump(item, f, indent=2)
                f.write('\n]')
        except Exception as e:
            logger.error(f"IO ERROR: Failed to write to {JSON_OUTPUT_FILE}: {e}")
            raise
    else:
        # Append to existing file - use 'r+' mode to allow seeking and reading
        try:
            with open(JSON_OUTPUT_FILE, 'r+') as f:
                # Robustly find the last closing bracket to append correctly
                f.seek(0, os.SEEK_END)
                pos = f.tell()
                # Search backwards for the last ']'
                search_back = min(pos, 100)  # Search up to 100 chars back
                if search_back > 0:
                    f.seek(pos - search_back)
                    content = f.read(search_back)
                    bracket_pos = content.rfind(']')
                    if bracket_pos != -1:
                        # Move pointer to the ']' character position
                        f.seek(pos - search_back + bracket_pos)
                        f.truncate()  # Remove the ']' and everything after
                        f.write(',\n')
                    else:
                        # Fallback for unexpected file structure
                        logger.warning(f"Unexpected JSON structure in {JSON_OUTPUT_FILE}, appending with newline")
                        f.seek(0, os.SEEK_END)
                        f.write(',\n')
                else:
                    # File is very small or empty
                    f.seek(0, os.SEEK_END)
                    f.write(',\n')
                
                json.dump(item, f, indent=2)
                f.write('\n]')
        except Exception as e:
            logger.error(f"IO ERROR: Failed to append to {JSON_OUTPUT_FILE}: {e}")
            raise


def log_skipped(item: dict):
    """Log skipped question to JSONL file."""
    with open(SKIPPED_FILE, 'a') as f:
        json.dump(item, f)
        f.write('\n')


def find_correct_option(new_options: List[str], original_gpt_value: str) -> Optional[str]:
    """
    STRICTLY find the new label for the original answer text.
    Must match the original diagnosis exactly (case-insensitive, ignoring label and whitespace).
    """
    # 1. Extract clean diagnosis (e.g., "B) Impetigo" -> "Impetigo")
    clean_answer = re.sub(r'^\s*[A-Z]\)\s*', '', original_gpt_value).strip()
    
    if not clean_answer:
        return None
    
    # 2. Search for EXACT match in new options (ignoring labels/spacing)
    for opt in new_options:
        opt_text = re.sub(r'^\s*[A-Z]\)\s*', '', opt).strip()
        if clean_answer.lower() == opt_text.lower():
            return opt
            
    # NO FALLBACK allowed. If the LLM changed "Herpes Simplex" to 
    # "Herpes Simplex Virus", this will return None and trigger an error log.
    return None


# -------------------------------------------------------------------------
# Main Processing
# -------------------------------------------------------------------------

def main():
    logger.info("=" * 80)
    logger.info("MCQA Enhancement Pipeline Starting")
    logger.info("=" * 80)
    
    # 1. Load data
    logger.info("Step 1: Loading data...")
    caption_dict = load_caption_lookup(CSV_INPUT_FILE)
    
    with open(JSON_INPUT_FILE, 'r') as f:
        mcqa_data = json.load(f)
    logger.info(f"Loaded {len(mcqa_data)} MCQA items")
    
    # 2. Load progress
    processed_ids = load_progress()
    logger.info(f"Found {len(processed_ids)} previously processed items")
    
    # Filter out already processed items
    items_to_process = [item for item in mcqa_data if item['id'] not in processed_ids]
    
    # # Testing limit: only process first 20 items
    # N_TEST = 8
    # if len(items_to_process) > N_TEST:
    #     logger.info(f"Test Mode: Limiting to first {N_TEST} items")
    #     items_to_process = items_to_process[:N_TEST]
        
    logger.info(f"Items to process: {len(items_to_process)}")
    
    if len(items_to_process) == 0:
        logger.info("All items already processed!")
        return
    
    # 3. Load model
    logger.info("Step 2: Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto"
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        pad_token='<|extra_0|>',
        eos_token='<|endoftext|>',
        padding_side='left',
        trust_remote_code=True
    )
    logger.info("Model loaded successfully")
    
    # 4. Process in batches
    logger.info("Step 3: Processing items...")
    
    skipped_count = 0
    enhanced_count = 0
    error_count = 0
    total_processing_time = 0
    total_processed_items = 0
    
    for start_idx in tqdm(range(0, len(items_to_process), BATCH_SIZE), desc="Processing batches"):
        batch_start_time = time.time()
        batch = items_to_process[start_idx:start_idx + BATCH_SIZE]
        
        batch_prompts = []
        batch_items = []
        batch_parsed = []
        
        # Prepare batch
        for item in batch:
            # Get caption
            image_path = item['image']
            caption = caption_dict.get(image_path.lower(), "")
            
            if not caption:
                logger.warning(f"No caption found for {image_path}, skipping item {item['id']}")
                error_count += 1
                processed_ids.add(item['id'])
                continue
            
            # Parse MCQA item
            parsed = parse_mcqa_item(item)
            if parsed is None:
                logger.error(f"Failed to parse item {item['id']}, skipping")
                error_count += 1
                processed_ids.add(item['id'])
                continue
            
            question_text, answer_text, options, _ = parsed
            
            # Build prompt
            user_prompt = build_user_prompt(caption, question_text, answer_text, options)
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            batch_prompts.append(text)
            batch_items.append(item)
            batch_parsed.append(parsed)
        
        if len(batch_prompts) == 0:
            continue
        
        # Tokenize batch
        model_inputs = tokenizer(
            batch_prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(model.device)
        
        # Generate
        try:
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=512,
                pad_token_id=tokenizer.pad_token_id
            )
            
            # Extract new tokens
            generated_tokens = [
                output_ids[len(input_ids):] 
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            responses = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            
            # --- Sanity Check Prints for the first batch ---
            if start_idx == 0:
                for i in range(min(2, len(responses))):
                    print(f"\n{'#'*100}")
                    print(f"SANITY CHECK: ITEM {i+1} (ID: {batch_items[i]['id']})")
                    print(f"{'#'*100}")
                    print("\n[FULL INPUT PROMPT (including system instructions)]:")
                    print(batch_prompts[i])
                    print("\n[FULL RAW MODEL OUTPUT]:")
                    print(responses[i])
                    print(f"\n{'#'*100}\n")
                
                print("Sanity check complete. Continuing with batch processing...\n")
                
        except RuntimeError as e:
            # Fatal GPU/Hardware errors: STOP the script so we don't mark 9k items as "done" incorrectly
            if "CUDA out of memory" in str(e) or "device" in str(e):
                logger.error(f"FATAL GPU ERROR: {e}")
                logger.error("Stopping script to prevent data corruption/loss.")
                raise e
            raise e
        except Exception as e:
            # Transient/Other errors: Log and skip this batch
            logger.error(f"Generation error in batch: {e}")
            error_count += len(batch_items)
            # We DON'T add to processed_ids here so we can retry them later
            continue
        
        # Process responses
        for item, response, parsed in zip(batch_items, responses, batch_parsed):
            question_text, answer_text, options, original_value = parsed
            
            # Parse response
            new_options = parse_llm_response(response)
            
            if new_options is None:
                # Either SKIP or invalid response
                if response.strip() == '<SKIP>':
                    log_skipped(item)
                    skipped_count += 1
                    logger.info(f"Item {item['id']} marked as SKIP (non-diagnosis question)")
                else:
                    logger.error(f"Invalid response for item {item['id']}: {response[:100]}")
                    error_count += 1
                
                processed_ids.add(item['id'])
                continue
            
            # Realignment Logic: Find the new label for the correct answer
            new_gpt_value = find_correct_option(new_options, answer_text)
            
            if not new_gpt_value:
                # Log detailed debug info for inspection
                clean_target = re.sub(r'^\s*[A-Z]\)\s*', '', answer_text).strip()
                available_opts = [re.sub(r'^\s*[A-Z]\)\s*', '', o).strip() for o in new_options]
                logger.error(f"GT ALIGNMENT FAILURE for item {item['id']}")
                logger.error(f"  Target Diagnosis: '{clean_target}'")
                logger.error(f"  Model provided:   {available_opts}")
                logger.error(f"  Likely cause: Model modified the ground truth text.")
                error_count += 1
                processed_ids.add(item['id'])
                continue

            # Update conversation value (Human message)
            new_human_value = update_conversation_value(original_value, new_options)
            
            # Create enhanced item
            enhanced_item = item.copy()
            enhanced_item['original_gpt_answer'] = answer_text # Store original 4-way answer
            enhanced_item['original_options'] = options # Store original 4-way options
            enhanced_item['conversations'] = [
                {"from": "human", "value": new_human_value},
                {"from": "gpt", "value": new_gpt_value} # Updated 8-way label
            ]
            
            # Append to output
            append_to_output(enhanced_item)
            enhanced_count += 1
            processed_ids.add(item['id'])
            
            logger.info(f"Enhanced item {item['id']} (4 -> 8 options, aligned label)")

        batch_end_time = time.time()
        batch_duration = batch_end_time - batch_start_time
        total_processing_time += batch_duration
        total_processed_items += len(batch_prompts)
        
        avg_time = total_processing_time / total_processed_items
        logger.info(f"Batch completed in {batch_duration:.2f}s | Avg time per QA: {avg_time:.2f}s")
        
        # Save progress after each batch
        save_progress(processed_ids)
    
    # Final summary
    logger.info("=" * 80)
    logger.info("Processing Complete!")
    logger.info(f"Enhanced: {enhanced_count}")
    logger.info(f"Skipped (non-diagnosis): {skipped_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Total processed: {len(processed_ids)}")
    if total_processed_items > 0:
        logger.info(f"Average time per QA: {total_processing_time / total_processed_items:.2f}s")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
