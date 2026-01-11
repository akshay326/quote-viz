from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PersonBase(BaseModel):
    """Base Person model."""
    name: str = Field(..., min_length=1, max_length=200)
    bio: Optional[str] = None


class PersonCreate(PersonBase):
    """Model for creating a person."""
    pass


class Person(PersonBase):
    """Person model with ID."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    """Base Quote model."""
    text: str = Field(..., min_length=1)
    context: Optional[str] = None
    source: Optional[str] = None


class QuoteCreate(QuoteBase):
    """Model for creating a quote."""
    author: str = Field(..., description="Name of the person who said the quote")


class QuoteUpdate(BaseModel):
    """Model for updating a quote."""
    text: Optional[str] = Field(None, min_length=1)
    context: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None


class Quote(QuoteBase):
    """Quote model with full details."""
    id: str
    author: Person
    cluster_id: Optional[int] = None
    umap_x: Optional[float] = None
    umap_y: Optional[float] = None
    created_at: datetime
    similarity_score: Optional[float] = Field(None, description="Used when fetching similar quotes")

    class Config:
        from_attributes = True


class QuoteWithSimilar(Quote):
    """Quote model with similar quotes."""
    similar_quotes: list[Quote] = []
