import json
import random
import os
from collections import Counter
import argparse

def sample_data(input_file, output_file, n_samples):
    # 1. Load data
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)

    total_items = len(data)
    print(f"Total items in source: {total_items}")

    # 2. Randomly sample
    sample_size = min(n_samples, total_items)
    print(f"Sampling {sample_size} items...")
    sampled_data = random.sample(data, sample_size)

    # 3. Save to new JSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(sampled_data, f, indent=2)
    print(f"Sampled data saved to {output_file}")

    # 4. Count proportions
    print("\n📊 SAMPLE SOURCE ANALYSIS")
    print("-" * 40)
    sources = [item.get('source', 'unknown') for item in sampled_data]
    source_counts = Counter(sources)

    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / sample_size) * 100
        print(f"  {source:<20} {count:>3} items ({percentage:>5.2f}%)")

    print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample items from MCQA JSON file")
    parser.add_argument("--input", default="data/ClinicalContext_MCQA.json", help="Input JSON file")
    parser.add_argument("--output", default="data/sampled_ClinicalContext_MCQA.json", help="Output JSON file")
    parser.add_argument("--n", type=int, default=100, help="Number of samples")
    
    args = parser.parse_args()
    sample_data(args.input, args.output, args.n)

