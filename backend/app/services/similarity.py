from typing import Optional
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.config import Settings


class SimilarityService:
    """Service for finding similar quotes."""

    def __init__(
        self,
        neo4j_service: Neo4jService,
        nlp_service: NLPService,
        settings: Settings
    ):
        self.neo4j_service = neo4j_service
        self.nlp_service = nlp_service
        self.similarity_threshold = settings.similarity_threshold

    def find_similar_quotes(
        self,
        quote_id: str,
        top_k: int = 5
    ) -> list[dict]:
        """Find top K similar quotes to a given quote."""
        quote = self.neo4j_service.get_quote(quote_id)
        if not quote:
            return []

        # Get the quote's embedding from Neo4j
        with self.neo4j_service.driver.session() as session:
            result = session.run(
                "MATCH (q:Quote {id: $quote_id}) RETURN q.embedding as embedding",
                quote_id=quote_id
            )
            record = result.single()
            if not record or not record["embedding"]:
                return []

            target_embedding = record["embedding"]

        # Get all embeddings
        all_embeddings = self.neo4j_service.get_all_embeddings()

        # Find top similar
        similar_ids_scores = self.nlp_service.find_top_similar(
            target_embedding,
            all_embeddings,
            top_k=top_k,
            exclude_id=quote_id
        )

        # Fetch full quote data
        similar_quotes = []
        for similar_id, similarity_score in similar_ids_scores:
            similar_quote = self.neo4j_service.get_quote(similar_id)
            if similar_quote:
                similar_quote["similarity_score"] = similarity_score
                similar_quotes.append(similar_quote)

        return similar_quotes

    def recompute_similarity_edges_top_k(self, top_k: int = 5):
        """Recompute top-K similarity edges for all quotes."""
        all_embeddings = self.neo4j_service.get_all_embeddings()

        top_k_map = {}
        for quote_id, embedding in all_embeddings:
            similar = self.nlp_service.find_top_similar(
                embedding,
                all_embeddings,
                top_k=top_k,
                exclude_id=quote_id
            )
            top_k_map[quote_id] = similar

        self.neo4j_service.create_similarity_edges_top_k(top_k_map)

        total_edges = sum(len(similar) for similar in top_k_map.values())
        return {
            "total_quotes": len(all_embeddings),
            "similarity_edges_created": total_edges,
            "top_k": top_k
        }
