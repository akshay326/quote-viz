from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.similarity import SimilarityService
import app.dependencies as deps

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    deps.neo4j_service = Neo4jService(settings)
    deps.nlp_service = NLPService(settings)
    deps.similarity_service = SimilarityService(deps.neo4j_service, deps.nlp_service, settings)

    yield

    deps.neo4j_service.close()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app is created to avoid circular imports
from app.api import quotes, graph, analytics

app.include_router(quotes.router, prefix="/api", tags=["quotes"])
app.include_router(graph.router, prefix="/api", tags=["graph"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Quote Visualization API",
        "version": settings.api_version,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
