#!/usr/bin/env python3
"""Ingest quotes from JSON file into Neo4j."""

import json
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService


async def ingest_quotes(json_file_path: str = "/app/data/processed/quotes.json"):
    """Ingest quotes from JSON file."""
    if not os.path.exists(json_file_path):
        print(f"Error: File not found: {json_file_path}")
        sys.exit(1)

    settings = get_settings()
    neo4j_service = Neo4jService(settings)
    nlp_service = NLPService(settings)

    print(f"\nReading quotes from {json_file_path}...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)

    print(f"Found {len(quotes_data)} quotes to ingest")

    created_count = 0
    skipped_count = 0

    for idx, quote_data in enumerate(quotes_data, 1):
        try:
            author = quote_data.get("author")
            text = quote_data.get("quote")
            context = quote_data.get("context")
            original_text = quote_data.get("original_text", text)
            image_url = quote_data.get("authorImage")

            if not author or not text:
                print(f"⚠ Skipping quote {idx}: missing author or text")
                skipped_count += 1
                continue

            person = neo4j_service.get_person_by_name(author)
            if not person:
                person = neo4j_service.create_person(author, image_url=image_url)
                print(f"  Created person: {author}")
            elif image_url and person.get("image_url") != image_url:
                # Update existing person with image if it's different
                neo4j_service.update_person_image(author, image_url)
                print(f"  Updated image for: {author}")

            print(f"[{idx}/{len(quotes_data)}] Generating embedding for quote by {author}...")
            embedding = await nlp_service.generate_embedding(text)

            neo4j_service.create_quote(
                text=text,
                author_name=author,
                embedding=embedding,
                context=context,
                original_text=original_text
            )

            created_count += 1
            print(f"  ✓ Created quote {idx}")

        except Exception as e:
            print(f"✗ Error processing quote {idx}: {e}")
            skipped_count += 1
            continue

    print(f"\n{'=' * 50}")
    print(f"Ingestion complete!")
    print(f"Created: {created_count} quotes")
    print(f"Skipped: {skipped_count} quotes")
    print(f"{'=' * 50}")

    neo4j_service.close()


if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/processed/quotes.json"
    asyncio.run(ingest_quotes(json_path))
