#!/usr/bin/env python3
"""Re-ingest cleaned quotes into Neo4j database."""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CLEANED_FILE = PROJECT_ROOT / "data" / "processed" / "quotes_cleaned.json"

# Neo4j connection from environment or defaults
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "quoteviz2024")

def load_cleaned_quotes():
    """Load cleaned quotes from JSON file."""
    with open(CLEANED_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """Re-ingest cleaned quotes into Neo4j."""
    print("Quote Re-Ingestion to Neo4j")
    print("=" * 60)

    # Load cleaned quotes
    print(f"\nLoading cleaned quotes from: {CLEANED_FILE}")
    cleaned_quotes = load_cleaned_quotes()
    print(f"✓ Loaded {len(cleaned_quotes)} quotes")

    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        stats = {
            'total': len(cleaned_quotes),
            'updated': 0,
            'author_changed': 0,
            'text_changed': 0,
            'not_found': 0,
            'errors': 0
        }

        # Get all quotes from Neo4j first (in order)
        with driver.session() as session:
            result = session.run(
                """
                MATCH (q:Quote)-[r:ATTRIBUTED_TO]->(p:Person)
                RETURN q.id as quote_id, q.text as old_text, p.name as old_author_name, q.source as source
                ORDER BY q.created_at ASC
                """
            )
            neo4j_quotes = list(result)

        print(f"  Found {len(neo4j_quotes)} quotes in Neo4j")

        if len(neo4j_quotes) != len(cleaned_quotes):
            print(f"  ⚠ Warning: Count mismatch - Neo4j: {len(neo4j_quotes)}, Cleaned: {len(cleaned_quotes)}")
            print(f"  Will match by index position for first {min(len(neo4j_quotes), len(cleaned_quotes))} quotes")

        print(f"\nProcessing quotes...")
        for i in range(min(len(neo4j_quotes), len(cleaned_quotes))):
            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(cleaned_quotes)}] Processed...")

            try:
                cleaned = cleaned_quotes[i]
                neo4j_quote = neo4j_quotes[i]

                new_author = cleaned['author']
                new_text = cleaned['quote']

                old_text = neo4j_quote['old_text']
                old_author_name = neo4j_quote['old_author_name']
                quote_id = neo4j_quote['quote_id']

                # Track changes
                text_changed = old_text != new_text
                author_changed = old_author_name != new_author

                if text_changed:
                    stats['text_changed'] += 1
                if author_changed:
                    stats['author_changed'] += 1

                # Update if anything changed
                if text_changed or author_changed:
                    # Update quote text and author relationship
                    with driver.session() as session:
                        session.run(
                            """
                            MATCH (q:Quote {id: $quote_id})
                            SET q.text = $new_text,
                                q.updated_at = datetime()
                            WITH q
                            MATCH (q)-[r:ATTRIBUTED_TO]->(old_author:Person)
                            DELETE r
                            WITH q
                            MERGE (new_author:Person {name: $new_author})
                            ON CREATE SET new_author.id = randomUUID(),
                                         new_author.created_at = datetime()
                            CREATE (q)-[:ATTRIBUTED_TO]->(new_author)
                            RETURN q
                            """,
                            quote_id=quote_id,
                            new_text=new_text,
                            new_author=new_author
                        )
                    stats['updated'] += 1

            except Exception as e:
                print(f"  ✗ Error processing quote #{i+1}: {e}")
                stats['errors'] += 1

        print(f"\n{'=' * 60}")
        print("RE-INGESTION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total quotes processed: {stats['total']}")
        print(f"Quotes updated: {stats['updated']}")
        print(f"  - Author changed: {stats['author_changed']}")
        print(f"  - Text changed: {stats['text_changed']}")
        print(f"Quotes not found in DB: {stats['not_found']}")
        print(f"Errors: {stats['errors']}")
        print(f"\n✓ Re-ingestion complete!")

        if stats['updated'] > 0:
            print(f"\n⚠ IMPORTANT: You should now re-run:")
            print(f"  1. Embedding generation (if text changed)")
            print(f"  2. Clustering: python3 backend/app/scripts/compute_clusters.py")
            print(f"  3. UMAP projection update")

    finally:
        driver.close()

if __name__ == "__main__":
    main()
