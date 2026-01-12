#!/usr/bin/env python3
"""Migrate Neo4j database to add image_url field to Person nodes."""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings
from app.services.neo4j_service import Neo4jService

# Paths
# Use /app/data when running in Docker, otherwise use project root
if Path("/app/data").exists():
    IMAGE_MAP_FILE = Path("/app/data/processed/author_images.json")
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    IMAGE_MAP_FILE = PROJECT_ROOT / "data" / "processed" / "author_images.json"


def main():
    """Main execution."""
    print("Neo4j Database Migration: Add image_url to Person")
    print("=" * 50)

    # Load image mappings
    if not IMAGE_MAP_FILE.exists():
        print(f"✗ Error: Image map file not found: {IMAGE_MAP_FILE}")
        print("  Run generate_author_images.py first")
        sys.exit(1)

    print(f"\nLoading image mappings from: {IMAGE_MAP_FILE}")
    with open(IMAGE_MAP_FILE, 'r', encoding='utf-8') as f:
        image_map = json.load(f)
    print(f"✓ Loaded {len(image_map)} image mappings")

    # Connect to Neo4j
    print("\nConnecting to Neo4j...")
    settings = get_settings()
    neo4j_service = Neo4jService(settings)

    try:
        # Step 1: Add image_url property to all Person nodes (initialize to null)
        print("\nStep 1: Initializing image_url field on all Person nodes...")
        with neo4j_service.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Person)
                WHERE p.image_url IS NULL
                SET p.image_url = null
                RETURN count(p) as updated_count
                """
            )
            record = result.single()
            count = record["updated_count"] if record else 0
            print(f"✓ Initialized image_url field on {count} Person nodes")

        # Step 2: Update Person nodes with image URLs
        print(f"\nStep 2: Updating Person nodes with image URLs...")
        updated_count = 0
        not_found_count = 0

        for i, (author_name, image_url) in enumerate(image_map.items(), 1):
            success = neo4j_service.update_person_image(author_name, image_url)

            if success:
                updated_count += 1
                if i % 20 == 0:
                    print(f"  Updated {i}/{len(image_map)}...")
            else:
                not_found_count += 1
                # Person might not exist in DB if they were filtered out during ingestion
                # This is expected for authors marked as "Unknown" etc.

        print(f"✓ Updated {updated_count} Person nodes")
        if not_found_count > 0:
            print(f"⚠ {not_found_count} authors not found in database (likely filtered during ingestion)")

        # Step 3: Verify migration
        print("\nStep 3: Verifying migration...")
        with neo4j_service.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Person)
                RETURN
                    count(p) as total_people,
                    count(p.image_url) as with_image_url,
                    sum(CASE WHEN p.image_url IS NOT NULL THEN 1 ELSE 0 END) as non_null_image_url
                """
            )
            record = result.single()
            if record:
                total = record["total_people"]
                with_field = record["with_image_url"]
                non_null = record["non_null_image_url"]
                print(f"  Total Person nodes: {total}")
                print(f"  With image_url field: {with_field}")
                print(f"  With non-null image_url: {non_null}")
                print(f"  Coverage: {non_null}/{total} ({100*non_null//total if total > 0 else 0}%)")

        # Sample verification
        print("\nSample Person nodes with images:")
        with neo4j_service.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Person)
                WHERE p.image_url IS NOT NULL
                RETURN p.name as name, p.image_url as image_url
                ORDER BY p.name
                LIMIT 5
                """
            )
            for record in result:
                name = record["name"]
                image_url = record["image_url"]
                preview = image_url[:60] + "..." if len(image_url) > 60 else image_url
                print(f"  - {name}: {preview}")

        print(f"\n{'=' * 50}")
        print("Migration complete!")
        print(f"{'=' * 50}")

    finally:
        neo4j_service.close()


if __name__ == "__main__":
    main()
