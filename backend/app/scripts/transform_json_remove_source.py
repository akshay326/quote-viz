#!/usr/bin/env python3
import json

def transform_quotes():
    input_file = "data/processed/quotes_cleaned.json"
    output_file = "data/processed/quotes_cleaned.json"

    with open(input_file, 'r') as f:
        quotes = json.load(f)

    updates_count = 0
    for quote in quotes:
        # Rule 1: If author == "Unknown" AND source exists → author = source
        if quote.get("author") == "Unknown" and quote.get("source"):
            quote["author"] = quote["source"]
            updates_count += 1

        # Rule 2: Add original_text = quote (preserve initial text)
        quote["original_text"] = quote["quote"]

        # Rule 3: Remove source field
        if "source" in quote:
            del quote["source"]

    with open(output_file, 'w') as f:
        json.dump(quotes, f, indent=2)

    print(f"✓ Transformed {len(quotes)} quotes")
    print(f"✓ Updated {updates_count} quotes with Unknown → source author")
    print(f"✓ Added original_text to all quotes")
    print(f"✓ Removed source field from all quotes")

if __name__ == "__main__":
    transform_quotes()
