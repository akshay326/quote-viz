#!/usr/bin/env python3
"""Ingest quotes from JSON file into Neo4j."""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService


def ingest_quotes(json_file_path: str = "/app/data/processed/quotes.json"):
    """Ingest quotes from JSON file."""
    if not os.path.exists(json_file_path):
        print(f"Error: File not found: {json_file_path}")
        sys.exit(1)

    settings = get_settings()
    neo4j_service = Neo4jService(settings)
    nlp_service = NLPService(settings)

    print("Loading NLP model...")
    nlp_service.load_model()
    print("✓ Model loaded")

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
            source = quote_data.get("source")

            if not author or not text:
                print(f"⚠ Skipping quote {idx}: missing author or text")
                skipped_count += 1
                continue

            person = neo4j_service.get_person_by_name(author)
            if not person:
                person = neo4j_service.create_person(author)
                print(f"  Created person: {author}")

            print(f"[{idx}/{len(quotes_data)}] Generating embedding for quote by {author}...")
            embedding = nlp_service.generate_embedding(text)

            neo4j_service.create_quote(
                text=text,
                author_name=author,
                embedding=embedding,
                context=context,
                source=source
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
    ingest_quotes(json_path)
