#!/usr/bin/env python3
"""Generate author image mappings with fallbacks."""

import json
import base64
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
QUOTES_FILE = PROJECT_ROOT / "data" / "processed" / "quotes_cleaned.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "author_images.json"


def generate_fallback_image(author_name: str) -> str:
    """Generate data URL for colored sphere with initials."""
    # Get initials (up to 2 letters)
    words = author_name.strip().split()
    initials = ''.join(word[0].upper() for word in words if word)[:2]

    if not initials:
        initials = "?"

    # Generate deterministic color from name hash
    color_hash = abs(hash(author_name)) % 0xFFFFFF
    color = f"#{color_hash:06x}"

    # Create SVG
    svg = f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="90" fill="{color}"/>
  <text x="100" y="125" font-size="60" text-anchor="middle"
        fill="white" font-weight="bold" font-family="Arial, sans-serif">{initials}</text>
</svg>'''

    # Convert to base64 data URL
    svg_bytes = svg.encode('utf-8')
    b64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"


def main():
    """Main execution."""
    print("Generating Author Images")
    print("=" * 50)

    # Load cleaned quotes
    print(f"\nLoading quotes from: {QUOTES_FILE}")
    with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
        quotes = json.load(f)
    print(f"✓ Loaded {len(quotes)} quotes")

    # Get unique authors
    authors = set()
    for quote in quotes:
        author = quote.get('author', '').strip()
        if author and author not in ['Unknown', '']:
            authors.add(author)

    authors = sorted(list(authors))
    print(f"✓ Found {len(authors)} unique authors")

    # Generate fallback images for all
    print(f"\nGenerating fallback images...")
    image_map = {}

    for i, author in enumerate(authors, 1):
        image_map[author] = generate_fallback_image(author)
        if i % 20 == 0:
            print(f"  Processed {i}/{len(authors)}...")

    print(f"✓ Generated {len(image_map)} fallback images")

    # Save results
    print(f"\nSaving to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(image_map, f, indent=2, ensure_ascii=False)
    print("✓ Saved")

    # Print sample authors for verification
    print(f"\nSample authors:")
    for author in sorted(authors)[:10]:
        print(f"  - {author}")

    print(f"\n{'=' * 50}")
    print(f"SUMMARY")
    print(f"Total authors: {len(authors)}")
    print(f"Images generated: {len(image_map)}")
    print(f"{'=' * 50}")

    print("\n✓ Complete!")


if __name__ == "__main__":
    main()
