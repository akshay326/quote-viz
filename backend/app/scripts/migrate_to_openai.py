#!/usr/bin/env python3
"""Migrate existing quotes to OpenAI embeddings and compute UMAP."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.umap_service import UMAPService


async def migrate_embeddings():
    """Main migration function."""
    settings = get_settings()
    neo4j = Neo4jService(settings)
    nlp = NLPService(settings)
    umap_service = UMAPService()

    print("=" * 60)
    print("MIGRATION: OpenAI Embeddings + UMAP Projection")
    print("=" * 60)

    # 1. Fetch all quotes
    print("\n[1/6] Fetching all quotes from Neo4j...")
    quotes = neo4j.list_quotes(limit=10000)
    print(f"✓ Found {len(quotes)} quotes")

    if len(quotes) == 0:
        print("No quotes to migrate. Exiting.")
        neo4j.close()
        return

    # 2. Generate new OpenAI embeddings in batches
    print(f"\n[2/6] Generating OpenAI embeddings (model: {settings.model_name})...")
    print(f"       Batch size: {settings.embedding_batch_size}")
    texts = [q["text"] for q in quotes]
    quote_ids = [q["id"] for q in quotes]

    try:
        embeddings = await nlp.generate_embeddings_batch(texts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"  Embedding dimension: {len(embeddings[0])}")
    except Exception as e:
        print(f"✗ Error generating embeddings: {e}")
        print("  Make sure OPENAI_API_KEY is set in .env file")
        neo4j.close()
        return

    # 3. Update embeddings in Neo4j
    print("\n[3/6] Updating embeddings in Neo4j...")
    for i, (quote_id, embedding) in enumerate(zip(quote_ids, embeddings)):
        neo4j.update_quote(quote_id, embedding=embedding)
        if (i + 1) % 50 == 0:
            print(f"  Updated {i+1}/{len(quote_ids)} quotes...")
    print(f"✓ All {len(quote_ids)} embeddings updated")

    # 4. Compute UMAP 2D projection
    print("\n[4/6] Computing UMAP 2D projection...")
    embeddings_with_ids = list(zip(quote_ids, embeddings))

    try:
        umap_coords = umap_service.compute_2d_projection(embeddings_with_ids)
        print(f"✓ Computed UMAP for {len(umap_coords)} quotes")
    except Exception as e:
        print(f"✗ Error computing UMAP: {e}")
        neo4j.close()
        return

    # 5. Store UMAP coordinates in Neo4j
    print("\n[5/6] Storing UMAP coordinates...")
    neo4j.update_umap_coordinates(umap_coords)
    print(f"✓ UMAP coordinates stored")

    # 6. Compute top-5 similarity edges for each quote
    print("\n[6/6] Computing top-5 similarity edges...")
    top_k_map = {}
    for i, (quote_id, embedding) in enumerate(embeddings_with_ids):
        similar = nlp.find_top_similar(
            embedding,
            embeddings_with_ids,
            top_k=5,
            exclude_id=quote_id
        )
        top_k_map[quote_id] = similar

        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(embeddings_with_ids)} quotes...")

    print(f"✓ Computed similarities for {len(top_k_map)} quotes")

    # 7. Create similarity edges in Neo4j
    print("\nCreating similarity edges in Neo4j...")
    neo4j.create_similarity_edges_top_k(top_k_map)
    total_edges = sum(len(similar) for similar in top_k_map.values())
    print(f"✓ Created {total_edges} similarity edges")

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)
    print(f"Quotes migrated:       {len(quotes)}")
    print(f"Embedding model:       {settings.model_name}")
    print(f"Embedding dimensions:  {len(embeddings[0])}")
    print(f"UMAP coordinates:      {len(umap_coords)} (2D)")
    print(f"Similarity edges:      {total_edges} (top-5 per quote)")
    print("=" * 60)

    neo4j.close()


if __name__ == "__main__":
    asyncio.run(migrate_embeddings())
