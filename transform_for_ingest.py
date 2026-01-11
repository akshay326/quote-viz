import json

# Read extracted quotes
with open('data/processed/quotes.json', 'r', encoding='utf-8') as f:
    quotes = json.load(f)

# Transform to match ingestion format
transformed = []
for q in quotes:
    if q.get('quote'):  # Only include if there's a quote
        transformed.append({
            'author': q.get('person') or 'Unknown',  # Use 'Unknown' if person is null
            'quote': q['quote'],
            'context': q.get('context'),
            'source': q.get('original')
        })

# Save
with open('data/processed/quotes.json', 'w', encoding='utf-8') as f:
    json.dump(transformed, f, indent=2, ensure_ascii=False)

print(f"Transformed {len(transformed)} quotes")
print(f"- With author: {sum(1 for q in transformed if q['author'] != 'Unknown')}")
print(f"- With context: {sum(1 for q in transformed if q['context'])}")
