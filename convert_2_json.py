import json

with open('skipped_questions.jsonl', 'r') as f_in:
    # Read each line and parse it as a JSON object, creating a list
    data = [json.loads(line) for line in f_in]

with open('skipped_questions.json', 'w') as f_out:
    # Dump the list as a single JSON array
    json.dump(data, f_out, indent=2) 