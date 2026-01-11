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
    original_text = text

    # Extract context first
    ctx_match = re.search(r'\[ctx:\s*([^\]]+)\]', text)
    if ctx_match:
        result['context'] = ctx_match.group(1).strip()
        text = text[:ctx_match.start()].strip() + ' ' + text[ctx_match.end():].strip()
        text = text.strip()

    if not ctx_match:
        ctx_match = re.search(r'\(context:\s*([^\)]+)\)', text, re.IGNORECASE)
        if ctx_match:
            result['context'] = ctx_match.group(1).strip()
            text = text[:ctx_match.start()].strip() + ' ' + text[ctx_match.end():].strip()
            text = text.strip()

    # Now parse person and quote
    # Pattern 1: Person -- quote (double dash)
    if ' -- ' in text or ' — ' in text:
        parts = re.split(r'\s+(?:--|—)\s+', text, 1)
        if len(parts) == 2:
            result['person'] = parts[0].strip()
            result['quote'] = parts[1].strip()
            return result

    # Pattern 2: Person - quote (single dash, but be careful)
    dash_match = re.match(r'^(.+?)\s+-\s+(.+)$', text)
    if dash_match:
        person = dash_match.group(1).strip()
        quote = dash_match.group(2).strip()
        # Only accept if person part is reasonably short (likely a name)
        if len(person.split()) <= 6:
            result['person'] = person
            result['quote'] = quote
            return result

    # Pattern 3: Person: quote
    colon_match = re.match(r'^([^:]+?):\s+(.+)$', text)
    if colon_match:
        person = colon_match.group(1).strip()
        quote = colon_match.group(2).strip()
        # Check if person part looks like a name
        if len(person.split()) <= 6 and person[0].isupper():
            result['person'] = person
            result['quote'] = quote
            return result

    # If still no match, try to split on first sentence-like boundary
    # Look for patterns like "Name (info) rest of text"
    name_pattern = re.match(r'^([A-Z][^\.!?]*?)(?:\([^\)]+\))?\s+(.+)$', text)
    if name_pattern and ' - ' not in text[:50]:
        potential_person = name_pattern.group(1).strip()
        rest = name_pattern.group(2).strip()
        # If first part is short, it might be a person
        if len(potential_person.split()) <= 4 and not potential_person.endswith(','):
            result['person'] = potential_person
            result['quote'] = rest
            return result

    # Default: entire text is quote
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
print(f"\nStats:")
print(f"- With person: {sum(1 for q in quotes if q['person'])}")
print(f"- With context: {sum(1 for q in quotes if q['context'])}")
print(f"- Quote only: {sum(1 for q in quotes if not q['person'])}")
print(f"\nSample entries:")
for q in quotes[3:8]:
    print(f"\n#{q['id']}")
    if q['person']:
        print(f"  Person: {q['person']}")
    if q['context']:
        print(f"  Context: {q['context']}")
    print(f"  Quote: {q['quote'][:80]}...")
