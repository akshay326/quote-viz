from pydantic import BaseModel
from typing import Any


class GraphNode(BaseModel):
    """Node in the graph visualization."""
    id: str
    label: str
    type: str  # 'quote', 'person', 'cluster'
    data: dict[str, Any] = {}


class GraphEdge(BaseModel):
    """Edge in the graph visualization."""
    source: str
    target: str
    type: str  # 'attributed_to', 'similar_to', 'belongs_to'
    weight: float = 1.0


class GraphData(BaseModel):
    """Complete graph data for visualization."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class AnalyticsStats(BaseModel):
    """Analytics statistics."""
    total_quotes: int
    total_people: int
    avg_quotes_per_person: float
    top_people: list[dict[str, Any]]
