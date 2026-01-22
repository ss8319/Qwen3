import re
from typing import List, Optional

def find_correct_option(new_options: List[str], original_gpt_value: str) -> Optional[str]:
    """
    STRICTLY find the new label for the original answer text.
    Must match the original diagnosis exactly (case-insensitive, ignoring label and whitespace).
    """
    clean_answer = re.sub(r'^\s*[A-Z]\)\s*', '', original_gpt_value).strip()
    if not clean_answer: return None
    
    for opt in new_options:
        opt_text = re.sub(r'^\s*[A-Z]\)\s*', '', opt).strip()
        if clean_answer.lower() == opt_text.lower():
            return opt
    return None

def run_tests():
    print("--- Red-Teaming find_correct_option() (STRICT MODE) ---")
    
    test_cases = [
        {
            "name": "Standard Label Shift",
            "original": "B) Impetigo",
            "new": ["A) Psoriasis", "F) Impetigo", "H) Scabies"],
            "expected": "F) Impetigo"
        },
        {
            "name": "Case Mismatch",
            "original": "A) MELANOMA",
            "new": ["C) melanoma", "D) Basal Cell Carcinoma"],
            "expected": "C) melanoma"
        },
        {
            "name": "Whitespace & Formatting",
            "original": "  C)   Eczema  ",
            "new": ["A) Psoriasis", "B) Eczema"],
            "expected": "B) Eczema"
        },
        {
            "name": "Strict: Reject Hallucinated Extension",
            "original": "B) Herpes Simplex",
            "new": ["A) Acne", "E) Herpes Simplex Virus Infection"],
            "expected": None # Should FAIL because model added "Virus Infection"
        },
        {
            "name": "Parentheses in Name",
            "original": "A) Papular urticaria (insect bite)",
            "new": ["G) Papular urticaria (insect bite)", "H) Other"],
            "expected": "G) Papular urticaria (insect bite)"
        },
        {
            "name": "Total Failure (Should return None)",
            "original": "B) Cancer",
            "new": ["A) Psoriasis", "C) Eczema"],
            "expected": None
        }
    ]

    passed = 0
    for case in test_cases:
        result = find_correct_option(case["new"], case["original"])
        if result == case["expected"]:
            print(f"✅ PASSED: {case['name']}")
            passed += 1
        else:
            print(f"❌ FAILED: {case['name']}")
            print(f"   Input: '{case['original']}'")
            print(f"   Expected: '{case['expected']}'")
            print(f"   Got: '{result}'")

    print(f"\nSummary: {passed}/{len(test_cases)} tests passed.")

if __name__ == "__main__":
    run_tests()
