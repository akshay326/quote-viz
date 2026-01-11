#!/usr/bin/env python3
"""Compute clusters for quotes using embeddings."""

import sys
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import get_settings
from app.services.neo4j_service import Neo4jService


def compute_clusters(n_clusters: int = 10):
    """Compute clusters using K-Means on quote embeddings."""
    settings = get_settings()
    neo4j = Neo4jService(settings)

    print("=" * 60)
    print(f"CLUSTERING: K-Means with {n_clusters} clusters")
    print("=" * 60)

    # 1. Fetch all quotes with embeddings
    print("\n[1/4] Fetching quotes with embeddings...")
    embeddings_data = neo4j.get_all_embeddings()
    print(f"✓ Found {len(embeddings_data)} quotes with embeddings")

    if len(embeddings_data) < n_clusters:
        print(f"✗ Not enough quotes ({len(embeddings_data)}) for {n_clusters} clusters")
        print(f"  Adjusting to {max(2, len(embeddings_data) // 10)} clusters")
        n_clusters = max(2, len(embeddings_data) // 10)

    # 2. Prepare embedding matrix
    print("\n[2/4] Preparing embedding matrix...")
    quote_ids = [qid for qid, _ in embeddings_data]
    embeddings = np.array([emb for _, emb in embeddings_data])

    # Normalize embeddings (cosine distance = euclidean on normalized vectors)
    embeddings_normalized = normalize(embeddings)
    print(f"✓ Matrix shape: {embeddings.shape}")

    # 3. Run K-Means clustering
    print(f"\n[3/4] Running K-Means clustering (n_clusters={n_clusters})...")
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=20,  # More initializations for better results
        max_iter=500,
        algorithm='lloyd'
    )

    cluster_labels = kmeans.fit_predict(embeddings_normalized)
    print(f"✓ Clustering complete")
    print(f"  Inertia: {kmeans.inertia_:.2f}")

    # Show cluster distribution
    unique, counts = np.unique(cluster_labels, return_counts=True)
    print(f"\n  Cluster distribution:")
    for cluster_id, count in zip(unique, counts):
        percentage = (count / len(cluster_labels)) * 100
        print(f"    Cluster {cluster_id}: {count} quotes ({percentage:.1f}%)")

    # 4. Update Neo4j with cluster assignments
    print(f"\n[4/4] Updating Neo4j with cluster assignments...")
    updates = {}
    for quote_id, cluster_id in zip(quote_ids, cluster_labels):
        updates[quote_id] = int(cluster_id)

    neo4j.update_cluster_ids(updates)
    print(f"✓ Updated {len(updates)} quotes with cluster IDs")

    print("\n" + "=" * 60)
    print("CLUSTERING COMPLETE!")
    print("=" * 60)
    print(f"Total quotes clustered: {len(embeddings_data)}")
    print(f"Number of clusters:     {n_clusters}")
    print(f"Avg cluster size:       {len(embeddings_data) / n_clusters:.1f}")
    print("=" * 60)

    neo4j.close()


if __name__ == "__main__":
    n_clusters = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    compute_clusters(n_clusters)
