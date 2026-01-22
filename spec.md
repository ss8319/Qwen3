Overview Idea: we will make our benchmark more challenging by adding more disctctor options for each VQA in our benchmark. 4 options -> 8 options using Qwen2.5 72B.

## Implementation Status: ✅ COMPLETE

The MCQA enhancement pipeline has been implemented. See:
- **Main Script**: `mcqa_enhancement.py`
- **Documentation**: `MCQA_ENHANCEMENT_README.md`
- **Test Suite**: `test_mcqa_enhancement.py`

To run: `python mcqa_enhancement.py`

---

Below is the key workflow.

/data/ClinicalContext_MCQA.json
This is file we want to enhance.

This is the prompt we use for Qwen. Undestand the workflow.
'''
You are curating and enhancing a dermatology VQA benchmark (Derm1M).
You are given the following inputs:
caption: {Origin_caption}
question: {Question}
answer (correct diagnosis): {Answer}
original_options: {Origin_option}
Task:
First, determine whether the question is a DIAGNOSIS question.
A diagnosis question explicitly asks for identification of a disease or condition, using phrases such as: “diagnosis”, “most likely diagnosis”, “what condition”, “what disease”, or “what is this lesion”.
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

You need to parse different files to provide the following context for each LLM call.
caption: {Origin_caption}
Origin_caption is the original caption available in '/mnt/hdd/sda/samus/Qwen3/data/textbook_IIYI_PubMed.csv
question: {Question}
Question comes from the JSON: data/ClinicalContext_MCQA.json
answer (correct diagnosis): {Answer}
Answer comes from the JSON: data/ClinicalContext_MCQA.json
original_options: {Origin_option}
Answer comes from the JSON: data/ClinicalContext_MCQA.json 
It should be parsed carefully 

Example of MCQA, please refer to json for more examples.
  {
    "id": "21898_5",
    "image": "Images/education/21898_5.png",
    "source": "IIYI_chinese",
    "disease": "pyoderma",
    "conversations": [
      {
        "from": "human",
        "value": "<image>\nA 2-year-old male child presents with a 4-day history of a painful rash and intermittent fevers for one week. Examination reveals scattered crusted papules and pustules. Laboratory testing shows a white blood cell count of 11,000/µL with 72% neutrophils. Which of the following is the most likely diagnosis?\nOptions:\nA) Impetigo (pyoderma)\nB) Kaposi varicelliform eruption\nC) Varicella (chickenpox)\nD) Eczema herpeticum"
      },
      {
        "from": "gpt",
        "value": "A) Impetigo (pyoderma)"
      }
    ]
  },


