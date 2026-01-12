#!/usr/bin/env python3
"""Fetch author images using web search and generate fallbacks."""

import json
import os
import sys
import base64
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings
from app.services.neo4j_service import Neo4jService

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
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


def search_author_image(author_name: str) -> Optional[str]:
    """Search for author image using web search.

    Note: This function uses the WebSearch MCP which is available through
    Claude Code. Since this script runs outside the Claude Code context,
    we'll generate fallback images for all authors.

    In the actual implementation, you would call the WebSearch MCP here.
    """
    # TODO: Implement web search when running in Claude Code context
    # For now, return None to use fallback images
    return None


def get_unique_authors() -> list[str]:
    """Get unique author names from Neo4j database."""
    try:
        settings = get_settings()
        neo4j_service = Neo4jService(settings)

        with neo4j_service.driver.session() as session:
            result = session.run("MATCH (p:Person) RETURN DISTINCT p.name as name ORDER BY name")
            authors = [record["name"] for record in result]

        neo4j_service.close()
        return authors

    except Exception as e:
        print(f"✗ Error getting authors from database: {e}")
        print("  Falling back to extracting from cleaned quotes file...")
        return get_authors_from_file()


def get_authors_from_file() -> list[str]:
    """Get unique authors from cleaned quotes file as fallback."""
    quotes_file = PROJECT_ROOT / "data" / "processed" / "quotes_cleaned.json"

    if not quotes_file.exists():
        print(f"✗ Error: Cleaned quotes file not found: {quotes_file}")
        return []

    with open(quotes_file, 'r', encoding='utf-8') as f:
        quotes = json.load(f)

    # Get unique authors, filter out empty/Unknown
    authors = set()
    for quote in quotes:
        author = quote.get('author', '').strip()
        if author and author not in ['Unknown', '']:
            authors.add(author)

    return sorted(list(authors))


def main():
    """Main execution."""
    print("Author Image Fetching")
    print("=" * 50)

    # Load existing cache if available
    if OUTPUT_FILE.exists():
        print(f"\nFound existing cache: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            image_map = json.load(f)
        print(f"✓ Loaded {len(image_map)} cached images")
    else:
        image_map = {}

    # Get unique authors
    print("\nFetching unique authors...")
    authors = get_unique_authors()
    print(f"✓ Found {len(authors)} unique authors")

    # Process each author
    print(f"\nProcessing authors (skipping already cached)...")
    new_count = 0
    skipped_count = 0

    for i, author in enumerate(authors, 1):
        if author in image_map:
            skipped_count += 1
            continue

        print(f"  [{i}/{len(authors)}] {author}...", end=' ')

        # Try to search for image
        image_url = search_author_image(author)

        if image_url:
            print(f"✓ Found image")
            image_map[author] = image_url
        else:
            # Generate fallback
            fallback = generate_fallback_image(author)
            print(f"✓ Generated fallback")
            image_map[author] = fallback

        new_count += 1

        # Rate limiting (if we were actually doing web searches)
        # time.sleep(1)

    # Save results
    print(f"\nSaving results to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(image_map, f, indent=2, ensure_ascii=False)
    print("✓ Saved")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"SUMMARY")
    print(f"Total authors: {len(authors)}")
    print(f"Newly processed: {new_count}")
    print(f"Already cached: {skipped_count}")
    print(f"Total in cache: {len(image_map)}")
    print(f"{'=' * 50}")

    print("\n✓ Image fetching complete!")
    print(f"\nNote: Since WebSearch MCP is not available in this script context,")
    print(f"all images are generated as colored sphere fallbacks with initials.")
    print(f"\nTo fetch real images, run this via Claude Code with WebSearch MCP enabled.")


if __name__ == "__main__":
    main()
