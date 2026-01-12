#!/usr/bin/env python3
"""Initialize Neo4j database with constraints and indexes."""

from neo4j import GraphDatabase
import os
import sys


def init_database():
    """Create constraints and indexes in Neo4j."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not password:
        print("Error: NEO4J_PASSWORD environment variable not set")
        sys.exit(1)

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        print("Creating constraints...")

        session.run(
            "CREATE CONSTRAINT quote_id IF NOT EXISTS "
            "FOR (q:Quote) REQUIRE q.id IS UNIQUE"
        )
        print("✓ Created unique constraint on Quote.id")

        session.run(
            "CREATE CONSTRAINT person_id IF NOT EXISTS "
            "FOR (p:Person) REQUIRE p.id IS UNIQUE"
        )
        print("✓ Created unique constraint on Person.id")

        session.run(
            "CREATE CONSTRAINT person_name IF NOT EXISTS "
            "FOR (p:Person) REQUIRE p.name IS UNIQUE"
        )
        print("✓ Created unique constraint on Person.name")

        session.run(
            "CREATE CONSTRAINT quote_text_unique IF NOT EXISTS "
            "FOR (q:Quote) REQUIRE q.text IS UNIQUE"
        )
        print("✓ Created unique constraint on Quote.text")

        print("\nCreating indexes...")

        session.run(
            "CREATE INDEX quote_text IF NOT EXISTS "
            "FOR (q:Quote) ON (q.text)"
        )
        print("✓ Created index on Quote.text")

        session.run(
            "CREATE INDEX quote_cluster IF NOT EXISTS "
            "FOR (q:Quote) ON (q.cluster_id)"
        )
        print("✓ Created index on Quote.cluster_id")

        session.run(
            "CREATE INDEX person_name_idx IF NOT EXISTS "
            "FOR (p:Person) ON (p.name)"
        )
        print("✓ Created index on Person.name")

        print("\nVerifying database setup...")
        result = session.run(
            "MATCH (q:Quote) RETURN count(q) as quote_count"
        )
        quote_count = result.single()["quote_count"]

        result = session.run(
            "MATCH (p:Person) RETURN count(p) as person_count"
        )
        person_count = result.single()["person_count"]

        print(f"\nDatabase initialized successfully!")
        print(f"Current quotes: {quote_count}")
        print(f"Current people: {person_count}")

    driver.close()


if __name__ == "__main__":
    init_database()
