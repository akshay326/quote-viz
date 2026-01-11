import umap
import numpy as np
from typing import Optional


class UMAPService:
    """Service for computing 2D projections of embeddings using UMAP."""

    def __init__(self):
        self.reducer = umap.UMAP(
            n_components=2,
            n_neighbors=15,
            min_dist=0.1,
            metric='cosine',
            random_state=42
        )

    def compute_2d_projection(
        self,
        embeddings: list[tuple[str, list[float]]]
    ) -> dict[str, tuple[float, float]]:
        """
        Compute 2D UMAP projection for all embeddings.

        Args:
            embeddings: List of (quote_id, embedding) tuples

        Returns:
            dict mapping quote_id -> (x, y) coordinates normalized to [0, 1]
        """
        if len(embeddings) < 2:
            return {}

        quote_ids = [qid for qid, _ in embeddings]
        embedding_matrix = np.array([emb for _, emb in embeddings])

        # Fit and transform
        coords_2d = self.reducer.fit_transform(embedding_matrix)

        # Normalize to [0, 1] range for consistent visualization
        x_min, x_max = coords_2d[:, 0].min(), coords_2d[:, 0].max()
        y_min, y_max = coords_2d[:, 1].min(), coords_2d[:, 1].max()

        # Avoid division by zero
        x_range = x_max - x_min if x_max != x_min else 1.0
        y_range = y_max - y_min if y_max != y_min else 1.0

        coords_2d[:, 0] = (coords_2d[:, 0] - x_min) / x_range
        coords_2d[:, 1] = (coords_2d[:, 1] - y_min) / y_range

        return {
            quote_ids[i]: (float(coords_2d[i, 0]), float(coords_2d[i, 1]))
            for i in range(len(quote_ids))
        }
