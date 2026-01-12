#!/usr/bin/env python3
"""
Migrate Neo4j database to remove source field and add original_text field.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from neo4j import GraphDatabase
from app.config import get_settings


def migrate():
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    print("Starting migration...")

    with driver.session() as session:
        # Step 1: Add original_text to all quotes
        print("\n1. Adding original_text field to all quotes...")
        result = session.run("""
            MATCH (q:Quote)
            WHERE q.original_text IS NULL
            SET q.original_text = q.text
            RETURN count(q) as updated
        """)
        count = result.single()["updated"]
        print(f"   ✓ Added original_text to {count} quotes")

        # Step 2: Migrate Unknown authors with source
        print("\n2. Migrating quotes with Unknown author and source...")
        result = session.run("""
            MATCH (q:Quote)-[r:ATTRIBUTED_TO]->(p:Person {name: "Unknown"})
            WHERE q.source IS NOT NULL
            WITH q, r, p, q.source as source_value
            DELETE r
            WITH q, source_value
            MERGE (new_author:Person {name: source_value})
            ON CREATE SET
                new_author.id = randomUUID(),
                new_author.created_at = datetime()
            CREATE (q)-[:ATTRIBUTED_TO]->(new_author)
            RETURN count(q) as migrated
        """)
        count = result.single()["migrated"]
        print(f"   ✓ Migrated {count} quotes from Unknown to source author")

        # Step 3: Remove source field from all quotes
        print("\n3. Removing source field from all quotes...")
        result = session.run("""
            MATCH (q:Quote)
            WHERE q.source IS NOT NULL
            REMOVE q.source
            RETURN count(q) as updated
        """)
        count = result.single()["updated"]
        print(f"   ✓ Removed source field from {count} quotes")

        # Step 4: Cleanup orphaned Unknown Person nodes
        print("\n4. Cleaning up orphaned Person nodes...")
        result = session.run("""
            MATCH (p:Person)
            WHERE NOT (p)<-[:ATTRIBUTED_TO]-()
            DELETE p
            RETURN count(p) as deleted
        """)
        count = result.single()["deleted"]
        print(f"   ✓ Deleted {count} orphaned Person nodes")

    driver.close()
    print("\n✓ Migration completed successfully!")


if __name__ == "__main__":
    migrate()
