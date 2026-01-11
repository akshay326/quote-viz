#!/usr/bin/env python3
"""
Helper script for extracting quotes from unstructured notes.

This script provides a template for using Claude (via MCP filesystem access)
to extract structured quotes from unstructured text files.

Usage:
    1. Place your unstructured notes in data/raw/
    2. Use Claude with filesystem MCP enabled
    3. Ask Claude: "Read all files in data/raw/ and extract quotes"
    4. Claude will use this script's format as a guide

Alternative: Run this script directly to manually structure quotes.
"""

import json
import os
from pathlib import Path


EXTRACTION_PROMPT = """
Extract quotes from the provided text files in the following JSON format:

[
  {
    "quote": "The exact quote text",
    "author": "Author's full name",
    "context": "Context or situation where it was said (optional)",
    "source": "Source reference like book, speech, interview (optional)"
  }
]

Guidelines:
- Only extract direct quotes (things people actually said)
- Preserve the exact wording
- Include author's full name
- Add context if it helps understand the quote
- If you're unsure about attribution, skip it
- Remove duplicates
- Format as valid JSON
"""


def read_notes_from_raw_dir():
    """Read all text files from data/raw/ directory."""
    raw_dir = Path(__file__).parent.parent / "raw"
    notes = []

    if not raw_dir.exists():
        print(f"Directory not found: {raw_dir}")
        return notes

    for file_path in raw_dir.glob("*.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                notes.append({
                    "file": file_path.name,
                    "content": content
                })
                print(f"Read: {file_path.name} ({len(content)} chars)")
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    return notes


def save_quotes_to_json(quotes, output_path=None):
    """Save extracted quotes to JSON file."""
    if output_path is None:
        output_path = Path(__file__).parent.parent / "processed" / "quotes.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(quotes)} quotes to: {output_path}")


def validate_quote_format(quote):
    """Validate that a quote has the required format."""
    required = ["quote", "author"]
    for field in required:
        if field not in quote or not quote[field]:
            return False, f"Missing required field: {field}"

    if not isinstance(quote["quote"], str) or len(quote["quote"]) < 5:
        return False, "Quote text too short"

    if not isinstance(quote["author"], str) or len(quote["author"]) < 2:
        return False, "Author name too short"

    return True, "OK"


def example_manual_extraction():
    """
    Example function showing how to manually structure quotes.
    Replace this with your actual extraction logic or use Claude.
    """
    quotes = [
        {
            "quote": "Example quote here",
            "author": "Author Name",
            "context": "Context if available",
            "source": "Source if available"
        }
    ]

    return quotes


def main():
    """Main execution function."""
    print("=" * 60)
    print("Quote Extraction Helper")
    print("=" * 60)
    print()

    print("EXTRACTION PROMPT:")
    print(EXTRACTION_PROMPT)
    print()

    notes = read_notes_from_raw_dir()

    if not notes:
        print("\nNo .txt files found in data/raw/")
        print("Please add your unstructured notes there first.")
        print()
        print("Recommended: Use Claude with filesystem MCP to extract quotes")
        return

    print(f"\nFound {len(notes)} text files")
    print("\nTo extract quotes, use Claude with this prompt:")
    print("-" * 60)
    print("Read all .txt files in data/raw/ and extract quotes following")
    print("the format in data/scripts/extract_quotes.py")
    print("-" * 60)


if __name__ == "__main__":
    main()
