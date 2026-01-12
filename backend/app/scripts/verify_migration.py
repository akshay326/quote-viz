#!/usr/bin/env python3
"""
Verify the migration was successful.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from neo4j import GraphDatabase
from app.config import get_settings


def verify():
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    print("Running verification checks...\n")
    all_passed = True

    with driver.session() as session:
        # Check 1: No quotes should have source property
        print("1. Checking for quotes with source property...")
        result = session.run("""
            MATCH (q:Quote)
            WHERE q.source IS NOT NULL
            RETURN count(q) as count
        """)
        count = result.single()["count"]
        if count == 0:
            print(f"   ✓ PASS: No quotes have source property")
        else:
            print(f"   ✗ FAIL: {count} quotes still have source property")
            all_passed = False

        # Check 2: All quotes should have original_text
        print("\n2. Checking for quotes without original_text...")
        result = session.run("""
            MATCH (q:Quote)
            WHERE q.original_text IS NULL
            RETURN count(q) as count
        """)
        count = result.single()["count"]
        if count == 0:
            print(f"   ✓ PASS: All quotes have original_text")
        else:
            print(f"   ✗ FAIL: {count} quotes missing original_text")
            all_passed = False

        # Check 3: Check Person node count
        print("\n3. Checking Person node count...")
        result = session.run("""
            MATCH (p:Person)
            RETURN count(p) as count
        """)
        person_count = result.single()["count"]
        print(f"   ℹ INFO: {person_count} Person nodes exist")

        # Check 4: Verify source values became authors
        print("\n4. Checking for institutional authors...")
        result = session.run("""
            MATCH (p:Person)
            WHERE p.name =~ ".*Institute.*|.*Sutra.*|.*doi\\.org.*"
            RETURN p.name as name
            LIMIT 5
        """)
        institutional_authors = [r["name"] for r in result]
        if institutional_authors:
            print(f"   ✓ PASS: Found institutional authors:")
            for name in institutional_authors:
                print(f"     - {name}")
        else:
            print(f"   ℹ INFO: No institutional authors found")

        # Check 5: Check for orphaned Unknown person
        print("\n5. Checking for Unknown person with quotes...")
        result = session.run("""
            MATCH (p:Person {name: "Unknown"})<-[:ATTRIBUTED_TO]-(q:Quote)
            RETURN count(q) as count
        """)
        unknown_count = result.single()["count"]
        print(f"   ℹ INFO: {unknown_count} quotes attributed to 'Unknown'")
        if unknown_count <= 14:
            print(f"   ✓ PASS: Unknown quote count is reasonable")
        else:
            print(f"   ⚠ WARNING: More Unknown quotes than expected")

    driver.close()

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All verification checks PASSED!")
    else:
        print("✗ Some verification checks FAILED!")
    print("=" * 50)

    return all_passed


if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)
