from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.models.quote import (
    QuoteCreate,
    QuoteUpdate,
    Quote,
    QuoteWithSimilar,
    PersonCreate,
    Person
)
from app.dependencies import get_neo4j_service, get_nlp_service, get_similarity_service
from app.services.neo4j_service import Neo4jService
from app.services.nlp_service import NLPService
from app.services.similarity import SimilarityService

router = APIRouter()


@router.post("/quotes", response_model=Quote, status_code=201)
def create_quote(
    quote: QuoteCreate,
    neo4j: Neo4jService = Depends(get_neo4j_service),
    nlp: NLPService = Depends(get_nlp_service)
):
    """Create a new quote with automatic embedding generation."""
    person = neo4j.get_person_by_name(quote.author)
    if not person:
        person = neo4j.create_person(quote.author)

    embedding = nlp.generate_embedding(quote.text)

    created_quote = neo4j.create_quote(
        text=quote.text,
        author_name=quote.author,
        embedding=embedding,
        context=quote.context,
        original_text=quote.text
    )

    return created_quote


@router.get("/quotes", response_model=list[Quote])
def list_quotes(
    person: Optional[str] = Query(None, description="Filter by person name"),
    cluster_id: Optional[int] = Query(None, description="Filter by cluster ID"),
    limit: int = Query(100, ge=1, le=500),
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """List quotes with optional filters."""
    quotes = neo4j.list_quotes(person_name=person, cluster_id=cluster_id, limit=limit)
    return quotes


@router.get("/quotes/{quote_id}", response_model=QuoteWithSimilar)
def get_quote(
    quote_id: str,
    neo4j: Neo4jService = Depends(get_neo4j_service),
    similarity: SimilarityService = Depends(get_similarity_service)
):
    """Get a single quote with similar quotes."""
    quote = neo4j.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    similar_quotes = similarity.find_similar_quotes(quote_id, top_k=5)

    return {**quote, "similar_quotes": similar_quotes}


@router.put("/quotes/{quote_id}", response_model=Quote)
def update_quote(
    quote_id: str,
    quote_update: QuoteUpdate,
    neo4j: Neo4jService = Depends(get_neo4j_service),
    nlp: NLPService = Depends(get_nlp_service)
):
    """Update a quote."""
    existing_quote = neo4j.get_quote(quote_id)
    if not existing_quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    embedding = None
    if quote_update.text is not None:
        embedding = nlp.generate_embedding(quote_update.text)

    if quote_update.author:
        person = neo4j.get_person_by_name(quote_update.author)
        if not person:
            person = neo4j.create_person(quote_update.author)

    updated_quote = neo4j.update_quote(
        quote_id=quote_id,
        text=quote_update.text,
        context=quote_update.context,
        author_name=quote_update.author,
        embedding=embedding
    )

    return updated_quote


@router.delete("/quotes/{quote_id}", status_code=204)
def delete_quote(
    quote_id: str,
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """Delete a quote."""
    deleted = neo4j.delete_quote(quote_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Quote not found")


@router.get("/search", response_model=list[Quote])
def search_quotes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """Full-text search for quotes."""
    quotes = neo4j.search_quotes(q, limit=limit)
    return quotes


@router.get("/similar/{quote_id}", response_model=list[Quote])
def get_similar_quotes(
    quote_id: str,
    top_k: int = Query(5, ge=1, le=20),
    similarity: SimilarityService = Depends(get_similarity_service)
):
    """Get similar quotes to a given quote."""
    similar_quotes = similarity.find_similar_quotes(quote_id, top_k=top_k)
    if not similar_quotes and not similarity.neo4j_service.get_quote(quote_id):
        raise HTTPException(status_code=404, detail="Quote not found")

    return similar_quotes


@router.post("/people", response_model=Person, status_code=201)
def create_person(
    person: PersonCreate,
    neo4j: Neo4jService = Depends(get_neo4j_service)
):
    """Create a new person."""
    existing_person = neo4j.get_person_by_name(person.name)
    if existing_person:
        raise HTTPException(status_code=409, detail="Person already exists")

    created_person = neo4j.create_person(person.name, person.bio)
    return created_person
