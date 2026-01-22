import re
from typing import List, Tuple, Optional

# --- Copy of the logic from mcqa_enhancement.py to keep the test self-contained ---

def parse_mcqa_item(item: dict) -> Optional[Tuple[str, str, List[str], str]]:
    try:
        if 'conversations' not in item or len(item['conversations']) < 2:
            return None
            
        conversation_value = item['conversations'][0]['value']
        
        if 'Options:' not in conversation_value:
            return None
        
        parts = conversation_value.split('Options:')
        question_text = parts[0].replace('<image>\n', '').replace('<image>', '').strip()
        options_text = parts[1].strip()
        
        # Updated regex: [A-Z] instead of [A-D], and relaxed length check
        options = re.findall(r'([A-Z]\).*?)(?=[A-Z]\)|$)', options_text, re.DOTALL)
        options = [opt.strip() for opt in options]
        
        if len(options) < 1:
            return None
        
        answer_text = item['conversations'][1]['value'].strip()
        return question_text, answer_text, options, conversation_value
        
    except Exception:
        return None

# --- Test Suite ---

def run_tests():
    test_cases = [
        {
            "name": "Standard 4 options",
            "item": {
                "id": "test_1",
                "conversations": [
                    {"from": "human", "value": "<image>\nWhat is this?\nOptions:\nA) Opt1\nB) Opt2\nC) Opt3\nD) Opt4"},
                    {"from": "gpt", "value": "A) Opt1"}
                ]
            },
            "expected_count": 4
        },
        {
            "name": "3 options (previously failing case)",
            "item": {
                "id": "test_2",
                "conversations": [
                    {"from": "human", "value": "A question.\nOptions:\nA) Choice 1\nB) Choice 2\nC) Choice 3"},
                    {"from": "gpt", "value": "B) Choice 2"}
                ]
            },
            "expected_count": 3
        },
        {
            "name": "1 option (minimum case)",
            "item": {
                "id": "test_3",
                "conversations": [
                    {"from": "human", "value": "Single choice.\nOptions:\nA) Only choice"},
                    {"from": "gpt", "value": "A) Only choice"}
                ]
            },
            "expected_count": 1
        },
        {
            "name": "6 options (extended case)",
            "item": {
                "id": "test_4",
                "conversations": [
                    {"from": "human", "value": "Many choices.\nOptions:\nA) O1\nB) O2\nC) O3\nD) O4\nE) O5\nF) O6"},
                    {"from": "gpt", "value": "F) O6"}
                ]
            },
            "expected_count": 6
        },
        {
            "name": "Options with labels not starting at A",
            "item": {
                "id": "test_5",
                "conversations": [
                    {"from": "human", "value": "Shifted labels.\nOptions:\nC) Start at C\nD) Then D\nE) Then E"},
                    {"from": "gpt", "value": "C) Start at C"}
                ]
            },
            "expected_count": 3
        },
        {
            "name": "Multline options",
            "item": {
                "id": "test_6",
                "conversations": [
                    {"from": "human", "value": "Long options.\nOptions:\nA) This is a\nvery long\nmultiline option\nB) Simple one\nC) Another\nmultiline\none"},
                    {"from": "gpt", "value": "A) This is a\nvery long\nmultiline option"}
                ]
            },
            "expected_count": 3
        },
        {
            "name": "Edge case: No 'Options:' delimiter (should fail)",
            "item": {
                "id": "test_7",
                "conversations": [
                    {"from": "human", "value": "Where are the options? A) Nope B) Nope"},
                    {"from": "gpt", "value": "A) Nope"}
                ]
            },
            "expected_count": None
        }
    ]

    print(f"{'Test Name':<40} | {'Status':<10} | {'Result'}")
    print("-" * 70)
    
    passed = 0
    for case in test_cases:
        result = parse_mcqa_item(case["item"])
        
        status = "FAIL"
        actual = "None"
        if result is None:
            if case["expected_count"] is None:
                status = "PASS"
                passed += 1
            actual = "None"
        else:
            _, _, opts, _ = result
            actual = f"{len(opts)} options"
            if len(opts) == case["expected_count"]:
                status = "PASS"
                passed += 1
        
        print(f"{case['name']:<40} | {status:<10} | {actual}")

    print("-" * 70)
    print(f"Passed: {passed}/{len(test_cases)}")

if __name__ == "__main__":
    run_tests()

