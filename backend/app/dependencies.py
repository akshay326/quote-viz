"""Dependency injection for FastAPI."""

from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.similarity import SimilarityService

# Global service instances (initialized in main.py lifespan)
neo4j_service: Neo4jService = None
nlp_service: NLPService = None
similarity_service: SimilarityService = None


def get_neo4j_service() -> Neo4jService:
    """Dependency to get Neo4j service."""
    return neo4j_service


def get_nlp_service() -> NLPService:
    """Dependency to get NLP service."""
    return nlp_service


def get_similarity_service() -> SimilarityService:
    """Dependency to get Similarity service."""
    return similarity_service
