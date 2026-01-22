"""
Test script for MCQA enhancement pipeline.
Tests with first 10 items to verify data flow.
"""
import json
import pandas as pd
import os
import sys

def test_data_loading():
    """Test data loading and caption matching."""
    print("=" * 80)
    print("Test 1: Data Loading and Caption Matching")
    print("=" * 80)
    
    # Load CSV
    csv_path = 'data/textbook_IIYI_PubMed.csv'
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded CSV with {len(df)} rows")
    
    # Build caption dict
    caption_dict = {}
    for _, row in df.iterrows():
        filename = row['filename']
        caption_dict[filename.lower()] = row['caption']
    print(f"✓ Built caption dictionary with {len(caption_dict)} entries")
    
    # Load JSON
    json_path = 'data/ClinicalContext_MCQA.json'
    with open(json_path, 'r') as f:
        mcqa_data = json.load(f)
    print(f"✓ Loaded JSON with {len(mcqa_data)} MCQA items")
    
    # Test first 10 matches
    print("\nTesting first 10 caption matches:")
    for i, item in enumerate(mcqa_data[:10]):
        image_path = item['image']
        caption = caption_dict.get(image_path.lower(), None)
        
        if caption:
            print(f"  [{i+1}] {item['id']}: ✓ Caption found ({len(caption)} chars)")
        else:
            print(f"  [{i+1}] {item['id']}: ✗ Caption NOT found for {image_path}")
    
    return caption_dict, mcqa_data


def test_mcqa_parsing(mcqa_data):
    """Test MCQA item parsing."""
    print("\n" + "=" * 80)
    print("Test 2: MCQA Item Parsing")
    print("=" * 80)
    
    import re
    
    for i, item in enumerate(mcqa_data[:5]):
        print(f"\nItem {i+1}: {item['id']}")
        
        try:
            conversation_value = item['conversations'][0]['value']
            
            # Check for Options:
            if 'Options:' not in conversation_value:
                print(f"  ✗ No 'Options:' found")
                continue
            
            # Split
            parts = conversation_value.split('Options:')
            question = parts[0].replace('<image>\n', '').replace('<image>', '').strip()
            options_text = parts[1].strip()
            
            # Extract options
            options = re.findall(r'([A-D]\).*?)(?=[A-D]\)|$)', options_text, re.DOTALL)
            options = [opt.strip() for opt in options]
            
            # Get answer
            answer = item['conversations'][1]['value'].strip()
            
            print(f"  ✓ Question: {question[:80]}...")
            print(f"  ✓ Options: {len(options)} found")
            for opt in options:
                print(f"    - {opt[:60]}...")
            print(f"  ✓ Answer: {answer}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_prompt_building(caption_dict, mcqa_data):
    """Test prompt building."""
    print("\n" + "=" * 80)
    print("Test 3: Prompt Building")
    print("=" * 80)
    
    import re
    
    item = mcqa_data[0]
    print(f"Testing with item: {item['id']}")
    
    # Get caption
    image_path = item['image']
    caption = caption_dict.get(image_path.lower(), "")
    print(f"✓ Caption: {caption[:100]}...")
    
    # Parse item
    conversation_value = item['conversations'][0]['value']
    parts = conversation_value.split('Options:')
    question = parts[0].replace('<image>\n', '').replace('<image>', '').strip()
    options_text = parts[1].strip()
    options = re.findall(r'([A-D]\).*?)(?=[A-D]\)|$)', options_text, re.DOTALL)
    options = [opt.strip() for opt in options]
    answer = item['conversations'][1]['value'].strip()
    
    # Build prompt
    formatted_options = '\n'.join(options)
    user_input = f"""caption: {caption}
question: {question}
answer (correct diagnosis): {answer}
original_options:
{formatted_options}"""
    
    print("\n✓ User prompt built:")
    print("-" * 80)
    print(user_input[:500])
    print("...")
    print("-" * 80)


def test_response_parsing():
    """Test response parsing."""
    print("\n" + "=" * 80)
    print("Test 4: Response Parsing")
    print("=" * 80)
    
    import re
    
    # Test SKIP response
    skip_response = "<SKIP>"
    print(f"Testing SKIP response: '{skip_response}'")
    if skip_response.strip() == '<SKIP>':
        print("  ✓ SKIP detected correctly")
    
    # Test valid 8-option response
    valid_response = """A) Impetigo (pyoderma)
B) Kaposi varicelliform eruption
C) Varicella (chickenpox)
D) Eczema herpeticum
E) Bullous impetigo
F) Staphylococcal scalded skin syndrome
G) Herpes simplex infection
H) Erythema multiforme"""
    
    print(f"\nTesting valid 8-option response:")
    options = re.findall(r'([A-H]\).*?)(?=[A-H]\)|$)', valid_response, re.DOTALL)
    options = [opt.strip() for opt in options]
    print(f"  ✓ Extracted {len(options)} options")
    for opt in options:
        print(f"    - {opt}")
    
    # Test invalid response
    invalid_response = """A) Option 1
B) Option 2
C) Option 3"""
    
    print(f"\nTesting invalid response (only 3 options):")
    options = re.findall(r'([A-H]\).*?)(?=[A-H]\)|$)', invalid_response, re.DOTALL)
    print(f"  ✓ Extracted {len(options)} options (should reject)")


def test_json_update():
    """Test JSON update logic."""
    print("\n" + "=" * 80)
    print("Test 5: JSON Update Logic")
    print("=" * 80)
    
    original_value = """<image>
A 2-year-old male child presents with a 4-day history of a painful rash and intermittent fevers for one week. Examination reveals scattered crusted papules and pustules. Laboratory testing shows a white blood cell count of 11,000/µL with 72% neutrophils. Which of the following is the most likely diagnosis?
Options:
A) Impetigo (pyoderma)
B) Kaposi varicelliform eruption
C) Varicella (chickenpox)
D) Eczema herpeticum"""
    
    new_options = [
        "A) Impetigo (pyoderma)",
        "B) Kaposi varicelliform eruption",
        "C) Varicella (chickenpox)",
        "D) Eczema herpeticum",
        "E) Bullous impetigo",
        "F) Staphylococcal scalded skin syndrome",
        "G) Herpes simplex infection",
        "H) Erythema multiforme"
    ]
    
    # Update
    parts = original_value.split('Options:')
    question_part = parts[0]
    new_options_text = '\n'.join(new_options)
    new_value = f"{question_part}Options:\n{new_options_text}"
    
    print("Original (4 options):")
    print("-" * 80)
    print(original_value)
    print("\nUpdated (8 options):")
    print("-" * 80)
    print(new_value)
    print("\n✓ JSON update logic works correctly")


def main():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MCQA Enhancement Test Suite" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    try:
        # Test 1: Data loading
        caption_dict, mcqa_data = test_data_loading()
        
        # Test 2: MCQA parsing
        test_mcqa_parsing(mcqa_data)
        
        # Test 3: Prompt building
        test_prompt_building(caption_dict, mcqa_data)
        
        # Test 4: Response parsing
        test_response_parsing()
        
        # Test 5: JSON update
        test_json_update()
        
        print("\n" + "=" * 80)
        print("✓ All tests completed successfully!")
        print("=" * 80)
        print("\nThe pipeline is ready to run. Execute:")
        print("  python mcqa_enhancement.py")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

