from fastapi import APIRouter, Depends
from app.models.graph import AnalyticsStats
from app.dependencies import (
    get_neo4j_service,
    get_nlp_service,
    get_similarity_service
)
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.similarity import SimilarityService

router = APIRouter()


@router.get("/analytics/stats", response_model=AnalyticsStats)
def get_analytics_stats(neo4j: Neo4jService = Depends(get_neo4j_service)):
    """Get analytics statistics."""
    stats = neo4j.get_analytics_stats()
    return stats


@router.post("/analytics/recompute-similarities")
def recompute_similarities(
    similarity: SimilarityService = Depends(get_similarity_service)
):
    """Recompute top-K similarity edges for all quotes."""
    result = similarity.recompute_similarity_edges_top_k(top_k=5)

    return {
        "message": "Similarities recomputed successfully",
        "quotes_processed": result["total_quotes"],
        "similarity_edges_created": result["similarity_edges_created"],
        "top_k": result["top_k"]
    }
