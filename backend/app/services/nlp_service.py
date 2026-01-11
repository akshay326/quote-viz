from openai import AsyncOpenAI
from typing import Optional
import numpy as np
from app.config import Settings


class NLPService:
    """Service for NLP operations: embeddings and similarity."""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.model_name
        self.batch_size = settings.embedding_batch_size

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text using OpenAI."""
        response = await self.client.embeddings.create(
            model=self.model_name,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches."""
        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            chunk = texts[i:i + self.batch_size]
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=chunk,
                encoding_format="float"
            )
            all_embeddings.extend([d.embedding for d in response.data])

        return all_embeddings

    def compute_cosine_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_top_similar(
        self,
        target_embedding: list[float],
        all_embeddings: list[tuple[str, list[float]]],
        top_k: int = 5,
        exclude_id: Optional[str] = None
    ) -> list[tuple[str, float]]:
        """
        Find top K most similar embeddings to target.

        Args:
            target_embedding: The embedding to compare against
            all_embeddings: List of (id, embedding) tuples
            top_k: Number of top results to return
            exclude_id: ID to exclude from results (e.g., the target quote itself)

        Returns:
            List of (id, similarity_score) tuples, sorted by similarity descending
        """
        similarities = []

        for quote_id, embedding in all_embeddings:
            if exclude_id and quote_id == exclude_id:
                continue

            similarity = self.compute_cosine_similarity(target_embedding, embedding)
            similarities.append((quote_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
