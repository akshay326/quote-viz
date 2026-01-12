#!/usr/bin/env python3
"""Clean quotes dataset using OpenAI API to fix extraction bugs."""

import json
import os
import sys
from pathlib import Path
from typing import Any
from openai import OpenAI

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "quotes.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "quotes_cleaned.json"
REPORT_FILE = PROJECT_ROOT / "data" / "processed" / "cleaning_report.txt"

BATCH_SIZE = 30


def load_quotes() -> list[dict[str, Any]]:
    """Load quotes from JSON file."""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_batch_with_openai(batch: list[dict], client: OpenAI) -> list[dict]:
    """Clean a batch of quotes using OpenAI API."""
    system_prompt = """You are a data cleaning expert. Fix extraction bugs in quote data.

Rules:
1. Author must be a person's name (not a quote fragment, organization, or common word)
2. Quote must be the actual quote text (not the author name)
3. If quote contains "- AuthorName" at the end, extract that as author and remove from quote text
4. Remove metadata prefixes from quotes (e.g., "& Frank (2025), Carney Institute" should be removed if it's not part of the actual quote)
5. Extract actual author from quote ONLY if:
   - Author is "Unknown" AND
   - Quote clearly starts with a person's name (not common words like "find", "for", "if", "when", etc.) AND
   - The name is followed by the actual quote
6. If quote is incomplete/cut off mid-sentence, mark needs_review as true
7. Clean author names: remove metadata like "[startup phase 2/4]", "(2013)", etc. Keep only the person's name
8. If author field is empty or just punctuation, set to "Unknown" and mark needs_review
9. For each quote, return JSON object with: {author: string, quote: string, context: string or null, source: string or null, needs_review: boolean, issue: string or null}

Examples of fixes:
- Input: {author: "In the long-run, prioritization beats efficiency", quote: "james clear"}
  Output: {author: "James Clear", quote: "In the long-run, prioritization beats efficiency", context: null, source: null, needs_review: false, issue: null}

- Input: {author: "Unknown", quote: "Everything's funny until it happens to u - dave chapelle"}
  Output: {author: "Dave Chapelle", quote: "Everything's funny until it happens to u", context: null, source: null, needs_review: false, issue: null}

- Input: {author: "Unknown", quote: "akshay if your product requires users to manipulate >4 things at a time"}
  Output: {author: "Akshay", quote: "if your product requires users to manipulate >4 things at a time", context: null, source: null, needs_review: false, issue: null}

- Input: {author: "Unknown", quote: "find your greatest love... it'll be inside the hardest thing you do - Dr Regina Dugan"}
  Output: {author: "Dr Regina Dugan", quote: "find your greatest love... it'll be inside the hardest thing you do", context: null, source: null, needs_review: false, issue: null}

- Input: {author: "Unknown", quote: "for better productivity, quality of attention (no distractions at all) is very important"}
  Output: {author: "Unknown", quote: "for better productivity, quality of attention (no distractions at all) is very important", context: null, source: null, needs_review: true, issue: "Cannot determine author"}

- Input: {author: "(2013)", quote: "Consumer's will to pay is directly correlated to..."}
  Output: {author: "Unknown", quote: "Consumer's will to pay is directly correlated to...", context: null, source: null, needs_review: true, issue: "Author field was empty/invalid metadata"}

- Input: {author: "YC [startup phase 2/4]", quote: "get smart. you learn more"}
  Output: {author: "YC", quote: "get smart. you learn more", context: null, source: null, needs_review: false, issue: null}

- Input: {author: "3 types", quote: "persistence despite difficulty"}
  Output: {author: "Unknown", quote: "persistence despite difficulty", context: null, source: null, needs_review: true, issue: "Author was '3 types', not a person name"}

Return a JSON object with a 'quotes' array containing corrected quote objects, one per input quote, in the same order."""

    user_prompt = f"""Fix these {len(batch)} quotes:

{json.dumps(batch, indent=2)}

Return a JSON object with a 'quotes' array containing the corrected quotes in the same order."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},  # Force JSON output
            temperature=0.1,
            max_tokens=8000
        )

        response_text = response.choices[0].message.content

        # Parse JSON response
        result = json.loads(response_text)

        # Extract quotes array from response
        if 'quotes' not in result:
            print(f"⚠ Warning: Response missing 'quotes' key. Keys: {list(result.keys())}")
            return [heuristic_clean(q) for q in batch]

        cleaned = result['quotes']

        if len(cleaned) != len(batch):
            print(f"⚠ Warning: Response length mismatch ({len(cleaned)} vs {len(batch)})")
            return batch  # Return original if mismatch

        return cleaned

    except Exception as e:
        print(f"✗ Error calling OpenAI API: {e}")
        print("  Falling back to heuristic cleaning...")
        return [heuristic_clean(q) for q in batch]


def heuristic_clean(quote_data: dict) -> dict:
    """Fallback heuristic cleaning if Claude API fails."""
    import re

    author = quote_data.get('author', 'Unknown')
    quote = quote_data.get('quote', '')

    needs_review = False
    issue = None

    # Fix author/quote reversal
    author_words = len(author.split())
    quote_words = len(quote.split())

    if (author_words > 6 and quote_words <= 4 and
        (author[0].islower() if author else False) and
        (quote[0].isupper() if quote else False)):
        author, quote = quote, author

    # Extract author from quote if Unknown (improved logic)
    if author == "Unknown" and quote:
        words = quote.split()
        if words and len(words[0]) > 1:
            first_word = words[0].lower()
            # Common words that are NOT names - don't extract these
            common_words = {'the', 'for', 'and', 'but', 'not', 'with', 'from',
                          'find', 'get', 'make', 'take', 'give', 'have', 'do',
                          'if', 'when', 'while', 'after', 'before', 'during',
                          'in', 'on', 'at', 'to', 'of', 'by', 'as'}

            # Only extract if lowercase AND not a common word
            if first_word[0].islower() and first_word not in common_words:
                # Likely a name mentioned at start
                author = words[0].title()
                quote = ' '.join(words[1:])

    # Clean author metadata
    author = re.sub(r'\s*\[.*?\]', '', author)  # Remove [metadata]
    author = re.sub(r'\s*\(.*?\)$', '', author)  # Remove (metadata) at end
    author = author.strip()

    # Check if author is empty or whitespace
    if not author or author.isspace():
        author = "Unknown"
        needs_review = True
        issue = "Author field was empty"

    # Check if author looks invalid
    if author.isdigit() or author in ['3 types', 'Time', 'Choose', 'If simulations are the future']:
        needs_review = True
        issue = f"Author was '{author}', may not be a person"
        author = "Unknown"

    # Check for incomplete quote
    if quote and quote.rstrip().endswith(('is', 'and', 'but', '--')):
        needs_review = True
        issue = "Quote may be incomplete"

    return {
        'author': author,
        'quote': quote,
        'context': quote_data.get('context'),
        'source': quote_data.get('source'),
        'needs_review': needs_review,
        'issue': issue
    }


def generate_report(original: list[dict], cleaned: list[dict]) -> str:
    """Generate diff report showing changes."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("QUOTE CLEANING REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    changed_count = 0
    needs_review_count = 0

    for i, (orig, clean) in enumerate(zip(original, cleaned), 1):
        orig_author = orig.get('author', '')
        orig_quote = orig.get('quote', '')
        clean_author = clean.get('author', '')
        clean_quote = clean.get('quote', '')

        if orig_author != clean_author or orig_quote != clean_quote:
            changed_count += 1
            report_lines.append(f"Quote #{i}:")
            report_lines.append(f"  BEFORE: author={orig_author!r}")
            report_lines.append(f"          quote={orig_quote[:80]!r}...")
            report_lines.append(f"  AFTER:  author={clean_author!r}")
            report_lines.append(f"          quote={clean_quote[:80]!r}...")

            if clean.get('needs_review'):
                needs_review_count += 1
                report_lines.append(f"  ⚠ NEEDS REVIEW: {clean.get('issue')}")
            report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append(f"SUMMARY")
    report_lines.append(f"Total quotes: {len(original)}")
    report_lines.append(f"Changed: {changed_count}")
    report_lines.append(f"Needs manual review: {needs_review_count}")
    report_lines.append("=" * 80)

    return '\n'.join(report_lines)


def main():
    """Main execution."""
    print("Quote Dataset Cleaning")
    print("=" * 50)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("✗ Error: OPENAI_API_KEY environment variable not set")
        print("  Please set it to use OpenAI API for cleaning")
        print("  Falling back to heuristic cleaning only...")
        use_openai = False
    else:
        use_openai = True
        client = OpenAI(api_key=api_key)

    # Load quotes
    print(f"\nLoading quotes from: {INPUT_FILE}")
    quotes = load_quotes()
    print(f"✓ Loaded {len(quotes)} quotes")

    # Process in batches
    cleaned_quotes = []
    total_batches = (len(quotes) + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\nProcessing in batches of {BATCH_SIZE}...")
    for i in range(0, len(quotes), BATCH_SIZE):
        batch = quotes[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        print(f"  [{batch_num}/{total_batches}] Processing quotes {i+1}-{i+len(batch)}...", end='')

        if use_openai:
            cleaned_batch = clean_batch_with_openai(batch, client)
        else:
            cleaned_batch = [heuristic_clean(q) for q in batch]

        cleaned_quotes.extend(cleaned_batch)
        print(" ✓")

    # Generate report
    print(f"\nGenerating diff report...")
    report = generate_report(quotes, cleaned_quotes)

    # Save cleaned data
    print(f"Saving cleaned data to: {OUTPUT_FILE}")
    # Remove needs_review and issue fields from final output
    final_quotes = [
        {
            'author': q['author'],
            'quote': q['quote'],
            'context': q.get('context'),
            'source': q.get('source')
        }
        for q in cleaned_quotes
    ]

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_quotes, f, indent=2, ensure_ascii=False)
    print("✓ Saved")

    # Save report
    print(f"Saving report to: {REPORT_FILE}")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    print("✓ Saved")

    # Print summary
    needs_review = [q for q in cleaned_quotes if q.get('needs_review')]
    print(f"\n{report}")

    if needs_review:
        print(f"\n⚠ {len(needs_review)} quotes flagged for manual review")
        print("  See cleaning_report.txt for details")

    print("\n✓ Cleaning complete!")


if __name__ == "__main__":
    main()
