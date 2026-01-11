from fastapi import APIRouter, Depends
from app.models.graph import GraphData
from app.dependencies import get_neo4j_service
from app.services.neo4j_service import Neo4jService

router = APIRouter()


@router.get("/graph", response_model=GraphData)
def get_graph(neo4j: Neo4jService = Depends(get_neo4j_service)):
    """Get full graph data for visualization."""
    graph_data = neo4j.get_graph_data()
    return graph_data
