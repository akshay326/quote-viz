import csv
import re
import json

def parse_quote(text):
    """Parse a quote entry into person, context, and quote components."""
    result = {
        'person': None,
        'context': None,
        'quote': None,
        'original': text.strip('"')
    }

    # Remove outer quotes
    text = text.strip('"')

    # Extract context marked with [ctx: ...] or (context: ...)
    ctx_match = re.search(r'\[ctx:\s*([^\]]+)\]', text)
    if not ctx_match:
        ctx_match = re.search(r'\(context:\s*([^\)]+)\)', text, re.IGNORECASE)

    if ctx_match:
        result['context'] = ctx_match.group(1).strip()
        text = text.replace(ctx_match.group(0), '').strip()

    # Try different patterns

    # Pattern 1: "Person - quote" or "Person -- quote"
    match = re.match(r'^(.+?)\s*--\s+(.+)$', text)
    if match:
        result['person'] = match.group(1).strip()
        result['quote'] = match.group(2).strip()
        return result

    match = re.match(r'^(.+?)\s+-\s+(.+)$', text)
    if match:
        person_part = match.group(1).strip()
        quote_part = match.group(2).strip()
        # Check if person part looks like a name (short and no lowercase starting)
        if len(person_part.split()) <= 5 and person_part[0].isupper():
            result['person'] = person_part
            result['quote'] = quote_part
            return result

    # Pattern 2: "Person [info] - quote"
    match = re.match(r'^([^-\[]+(?:\[[^\]]+\])?)\s+-\s+(.+)$', text)
    if match:
        result['person'] = match.group(1).strip()
        result['quote'] = match.group(2).strip()
        return result

    # Pattern 3: Just person and quote with colon
    match = re.match(r'^([A-Z][^:]+):\s+(.+)$', text)
    if match and len(match.group(1).split()) <= 5:
        result['person'] = match.group(1).strip()
        result['quote'] = match.group(2).strip()
        return result

    # If no clear pattern, entire text is the quote
    result['quote'] = text.strip()

    return result

# Read and parse
quotes = []
with open('/Users/pika/Projects/quote-viz/data/raw/quotes.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader, 1):
        if row:
            parsed = parse_quote(row[0])
            parsed['id'] = i
            quotes.append(parsed)

# Save as JSON
with open('/Users/pika/Projects/quote-viz/data/processed/quotes.json', 'w', encoding='utf-8') as f:
    json.dump(quotes, f, indent=2, ensure_ascii=False)

# Save as structured CSV
with open('/Users/pika/Projects/quote-viz/data/processed/quotes_structured.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'person', 'context', 'quote', 'original'])
    writer.writeheader()
    writer.writerows(quotes)

print(f"Extracted {len(quotes)} quotes")
print(f"\nSample:")
for q in quotes[:3]:
    print(f"\nID: {q['id']}")
    print(f"Person: {q['person']}")
    print(f"Context: {q['context']}")
    print(f"Quote: {q['quote']}")
