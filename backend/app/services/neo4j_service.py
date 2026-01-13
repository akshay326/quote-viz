from neo4j import GraphDatabase, Driver
from neo4j.time import DateTime as Neo4jDateTime
from typing import Optional
from datetime import datetime
import uuid
from app.config import Settings


def convert_neo4j_datetime(dt) -> datetime:
    """Convert Neo4j DateTime to Python datetime."""
    if isinstance(dt, Neo4jDateTime):
        # Convert nanoseconds to microseconds (divide by 1000)
        microseconds = dt.nanosecond // 1000
        return datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, microseconds, tzinfo=dt.tzinfo)
    if isinstance(dt, datetime):
        return dt
    return dt


class Neo4jService:
    """Service for Neo4j database operations."""

    def __init__(self, settings: Settings):
        self.driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self):
        """Close the database connection."""
        self.driver.close()

    def create_person(self, name: str, bio: Optional[str] = None, image_url: Optional[str] = None) -> dict:
        """Create a person node."""
        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (p:Person {name: $name})
                ON CREATE SET
                    p.id = $id,
                    p.created_at = datetime(),
                    p.bio = $bio,
                    p.image_url = $image_url
                ON MATCH SET
                    p.bio = COALESCE($bio, p.bio),
                    p.image_url = COALESCE($image_url, p.image_url)
                RETURN p
                """,
                name=name,
                id=str(uuid.uuid4()),
                bio=bio,
                image_url=image_url
            )
            record = result.single()
            if record:
                person = record["p"]
                return {
                    "id": person["id"],
                    "name": person["name"],
                    "bio": person.get("bio"),
                    "image_url": person.get("image_url"),
                    "created_at": convert_neo4j_datetime(person["created_at"])
                }

    def get_person_by_name(self, name: str) -> Optional[dict]:
        """Get a person by name."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (p:Person {name: $name}) RETURN p",
                name=name
            )
            record = result.single()
            if record:
                person = record["p"]
                return {
                    "id": person["id"],
                    "name": person["name"],
                    "bio": person.get("bio"),
                    "image_url": person.get("image_url"),
                    "created_at": convert_neo4j_datetime(person["created_at"])
                }
            return None

    def update_person_image(self, name: str, image_url: str) -> bool:
        """Update person's image URL."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Person {name: $name})
                SET p.image_url = $image_url
                RETURN p
                """,
                name=name,
                image_url=image_url
            )
            return result.single() is not None

    def create_quote(
        self,
        text: str,
        author_name: str,
        embedding: list[float],
        context: Optional[str] = None,
        original_text: Optional[str] = None,
        umap_x: Optional[float] = None,
        umap_y: Optional[float] = None
    ) -> dict:
        """Create or update a quote node and link to person."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Person {name: $author_name})
                MERGE (q:Quote {text: $text})
                ON CREATE SET
                    q.id = $id,
                    q.context = $context,
                    q.original_text = $original_text,
                    q.embedding = $embedding,
                    q.umap_x = $umap_x,
                    q.umap_y = $umap_y,
                    q.created_at = datetime()
                ON MATCH SET
                    q.embedding = $embedding,
                    q.context = COALESCE($context, q.context),
                    q.original_text = COALESCE($original_text, q.original_text),
                    q.umap_x = COALESCE($umap_x, q.umap_x),
                    q.umap_y = COALESCE($umap_y, q.umap_y)
                MERGE (q)-[:ATTRIBUTED_TO]->(p)
                RETURN q, p
                """,
                id=str(uuid.uuid4()),
                text=text,
                context=context,
                original_text=original_text,
                embedding=embedding,
                umap_x=umap_x,
                umap_y=umap_y,
                author_name=author_name
            )
            record = result.single()
            if record:
                quote = record["q"]
                person = record["p"]
                return {
                    "id": quote["id"],
                    "text": quote["text"],
                    "context": quote.get("context"),
                    "original_text": quote.get("original_text"),
                    "umap_x": quote.get("umap_x"),
                    "umap_y": quote.get("umap_y"),
                    "created_at": convert_neo4j_datetime(quote["created_at"]),
                    "author": {
                        "id": person["id"],
                        "name": person["name"],
                        "bio": person.get("bio"),
                        "image_url": person.get("image_url"),
                        "created_at": convert_neo4j_datetime(person["created_at"])
                    }
                }

    def get_quote(self, quote_id: str) -> Optional[dict]:
        """Get a quote by ID."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (q:Quote {id: $quote_id})-[:ATTRIBUTED_TO]->(p:Person)
                RETURN q, p
                """,
                quote_id=quote_id
            )
            record = result.single()
            if record:
                quote = record["q"]
                person = record["p"]
                return {
                    "id": quote["id"],
                    "text": quote["text"],
                    "context": quote.get("context"),
                    "original_text": quote.get("original_text"),
                    "umap_x": quote.get("umap_x"),
                    "umap_y": quote.get("umap_y"),
                    "created_at": convert_neo4j_datetime(quote["created_at"]),
                    "author": {
                        "id": person["id"],
                        "name": person["name"],
                        "bio": person.get("bio"),
                        "image_url": person.get("image_url"),
                        "created_at": convert_neo4j_datetime(person["created_at"])
                    }
                }
            return None

    def list_quotes(
        self,
        person_name: Optional[str] = None,
        cluster_id: Optional[int] = None,
        limit: int = 100
    ) -> list[dict]:
        """List quotes with optional filters."""
        with self.driver.session() as session:
            query = "MATCH (q:Quote)-[:ATTRIBUTED_TO]->(p:Person)"
            params = {"limit": limit}

            where_clauses = []
            if person_name:
                where_clauses.append("p.name = $person_name")
                params["person_name"] = person_name
            if cluster_id is not None:
                where_clauses.append("q.cluster_id = $cluster_id")
                params["cluster_id"] = cluster_id

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " RETURN q, p ORDER BY q.created_at DESC LIMIT $limit"

            result = session.run(query, **params)
            quotes = []
            for record in result:
                quote = record["q"]
                person = record["p"]
                quotes.append({
                    "id": quote["id"],
                    "text": quote["text"],
                    "context": quote.get("context"),
                    "original_text": quote.get("original_text"),
                    "cluster_id": quote.get("cluster_id"),
                    "umap_x": quote.get("umap_x"),
                    "umap_y": quote.get("umap_y"),
                    "created_at": convert_neo4j_datetime(quote["created_at"]),
                    "author": {
                        "id": person["id"],
                        "name": person["name"],
                        "bio": person.get("bio"),
                        "image_url": person.get("image_url"),
                        "created_at": convert_neo4j_datetime(person["created_at"])
                    }
                })
            return quotes

    def update_quote(
        self,
        quote_id: str,
        text: Optional[str] = None,
        context: Optional[str] = None,
        author_name: Optional[str] = None,
        embedding: Optional[list[float]] = None
    ) -> Optional[dict]:
        """Update a quote."""
        with self.driver.session() as session:
            updates = []
            params = {"quote_id": quote_id}

            if text is not None:
                updates.append("q.text = $text")
                params["text"] = text
            if context is not None:
                updates.append("q.context = $context")
                params["context"] = context
            if embedding is not None:
                updates.append("q.embedding = $embedding")
                params["embedding"] = embedding

            if not updates and not author_name:
                return self.get_quote(quote_id)

            set_clause = ", ".join(updates) if updates else ""
            query = f"MATCH (q:Quote {{id: $quote_id}})"

            if author_name:
                query += "-[r:ATTRIBUTED_TO]->(:Person) DELETE r WITH q "
                query += "MATCH (p:Person {name: $author_name}) "
                if set_clause:
                    query += f"SET {set_clause} "
                query += "CREATE (q)-[:ATTRIBUTED_TO]->(p) RETURN q, p"
                params["author_name"] = author_name
            else:
                query += "-[:ATTRIBUTED_TO]->(p:Person) "
                if set_clause:
                    query += f"SET {set_clause} "
                query += "RETURN q, p"

            result = session.run(query, **params)
            record = result.single()
            if record:
                quote = record["q"]
                person = record["p"]
                return {
                    "id": quote["id"],
                    "text": quote["text"],
                    "context": quote.get("context"),
                    "original_text": quote.get("original_text"),
                    "umap_x": quote.get("umap_x"),
                    "umap_y": quote.get("umap_y"),
                    "created_at": convert_neo4j_datetime(quote["created_at"]),
                    "author": {
                        "id": person["id"],
                        "name": person["name"],
                        "bio": person.get("bio"),
                        "image_url": person.get("image_url"),
                        "created_at": convert_neo4j_datetime(person["created_at"])
                    }
                }
            return None

    def delete_quote(self, quote_id: str) -> bool:
        """Delete a quote."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (q:Quote {id: $quote_id}) DETACH DELETE q RETURN count(q) as deleted",
                quote_id=quote_id
            )
            record = result.single()
            return record["deleted"] > 0 if record else False

    def get_all_embeddings(self) -> list[tuple[str, list[float]]]:
        """Get all quote embeddings for clustering."""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (q:Quote) RETURN q.id as id, q.embedding as embedding"
            )
            return [(record["id"], record["embedding"]) for record in result if record["embedding"]]

    def update_umap_coordinates(self, coordinates: dict[str, tuple[float, float]]):
        """Update UMAP x,y coordinates for quotes."""
        with self.driver.session() as session:
            for quote_id, (x, y) in coordinates.items():
                session.run(
                    """
                    MATCH (q:Quote {id: $quote_id})
                    SET q.umap_x = $x, q.umap_y = $y
                    """,
                    quote_id=quote_id,
                    x=x,
                    y=y
                )

    def update_cluster_ids(self, cluster_map: dict[str, int]):
        """Update cluster_id for quotes."""
        with self.driver.session() as session:
            for quote_id, cluster_id in cluster_map.items():
                session.run(
                    """
                    MATCH (q:Quote {id: $quote_id})
                    SET q.cluster_id = $cluster_id
                    """,
                    quote_id=quote_id,
                    cluster_id=cluster_id
                )

    def create_similarity_edges_top_k(self, top_k_map: dict[str, list[tuple[str, float]]]):
        """Create directed top-K similarity edges."""
        with self.driver.session() as session:
            # Clear existing edges
            session.run("MATCH ()-[r:SIMILAR_TO]->() DELETE r")

            # Create directed edges
            for source_id, similar_quotes in top_k_map.items():
                for target_id, similarity in similar_quotes:
                    session.run(
                        """
                        MATCH (q1:Quote {id: $source_id}), (q2:Quote {id: $target_id})
                        CREATE (q1)-[:SIMILAR_TO {similarity: $similarity}]->(q2)
                        """,
                        source_id=source_id,
                        target_id=target_id,
                        similarity=similarity
                    )

    def get_graph_data(self) -> dict:
        """Get full graph data for visualization."""
        with self.driver.session() as session:
            nodes = []
            edges = []

            # Get quotes and people
            result = session.run(
                """
                MATCH (q:Quote)-[:ATTRIBUTED_TO]->(p:Person)
                RETURN q, p
                """
            )
            people_seen = set()
            for record in result:
                quote = record["q"]
                person = record["p"]

                nodes.append({
                    "id": quote["id"],
                    "label": quote["text"][:50] + "..." if len(quote["text"]) > 50 else quote["text"],
                    "type": "quote",
                    "data": {
                        "text": quote["text"],
                        "author": person["name"],
                        "umap_x": quote.get("umap_x"),
                        "umap_y": quote.get("umap_y"),
                        "cluster_id": quote.get("cluster_id")
                    }
                })

                if person["id"] not in people_seen:
                    nodes.append({
                        "id": person["id"],
                        "label": person["name"],
                        "type": "person",
                        "data": {
                            "name": person["name"],
                            "image_url": person.get("image_url")
                        }
                    })
                    people_seen.add(person["id"])

                edges.append({
                    "source": quote["id"],
                    "target": person["id"],
                    "type": "attributed_to",
                    "weight": 1.0
                })

            # Get similarity relationships
            result = session.run(
                """
                MATCH (q1:Quote)-[s:SIMILAR_TO]->(q2:Quote)
                RETURN q1.id as source, q2.id as target, s.similarity as similarity
                """
            )
            for record in result:
                edges.append({
                    "source": record["source"],
                    "target": record["target"],
                    "type": "similar_to",
                    "weight": record["similarity"]
                })

            return {"nodes": nodes, "edges": edges}

    def get_analytics_stats(self) -> dict:
        """Get analytics statistics."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (q:Quote)
                OPTIONAL MATCH (p:Person)
                WITH count(DISTINCT q) as quote_count, count(DISTINCT p) as person_count
                RETURN quote_count, person_count
                """
            )
            record = result.single()
            total_quotes = record["quote_count"]
            total_people = record["person_count"]

            # Get top people
            result = session.run(
                """
                MATCH (q:Quote)-[:ATTRIBUTED_TO]->(p:Person)
                RETURN p.name as name, count(q) as quote_count
                ORDER BY quote_count DESC
                LIMIT 10
                """
            )
            top_people = [{"name": r["name"], "quote_count": r["quote_count"]} for r in result]

            # Get cluster statistics
            result = session.run(
                """
                MATCH (q:Quote)
                WHERE q.cluster_id IS NOT NULL
                WITH q.cluster_id as cluster_id, count(q) as quote_count
                OPTIONAL MATCH (q1:Quote)-[s:SIMILAR_TO]->(q2:Quote)
                WHERE q1.cluster_id = cluster_id AND q2.cluster_id = cluster_id
                WITH cluster_id, quote_count, avg(s.similarity) as avg_similarity
                RETURN cluster_id, quote_count, COALESCE(avg_similarity, 0.0) as avg_similarity
                ORDER BY cluster_id
                """
            )
            cluster_distribution = [
                {
                    "cluster_id": r["cluster_id"],
                    "quote_count": r["quote_count"],
                    "avg_similarity": r["avg_similarity"]
                }
                for r in result
            ]

            total_clusters = len(cluster_distribution)
            avg_cluster_size = (
                sum(c["quote_count"] for c in cluster_distribution) / total_clusters
                if total_clusters > 0 else 0
            )

            return {
                "total_quotes": total_quotes,
                "total_people": total_people,
                "avg_quotes_per_person": total_quotes / total_people if total_people > 0 else 0,
                "top_people": top_people,
                "total_clusters": total_clusters,
                "cluster_distribution": cluster_distribution,
                "avg_cluster_size": avg_cluster_size
            }

    def search_quotes(self, query: str, limit: int = 20) -> list[dict]:
        """Full-text search for quotes."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (q:Quote)-[:ATTRIBUTED_TO]->(p:Person)
                WHERE toLower(q.text) CONTAINS toLower($query_text)
                   OR toLower(p.name) CONTAINS toLower($query_text)
                   OR toLower(q.context) CONTAINS toLower($query_text)
                RETURN q, p
                ORDER BY q.created_at DESC
                LIMIT $limit
                """,
                query_text=query,
                limit=limit
            )
            quotes = []
            for record in result:
                quote = record["q"]
                person = record["p"]
                quotes.append({
                    "id": quote["id"],
                    "text": quote["text"],
                    "context": quote.get("context"),
                    "original_text": quote.get("original_text"),
                    "cluster_id": quote.get("cluster_id"),
                    "umap_x": quote.get("umap_x"),
                    "umap_y": quote.get("umap_y"),
                    "created_at": convert_neo4j_datetime(quote["created_at"]),
                    "author": {
                        "id": person["id"],
                        "name": person["name"],
                        "bio": person.get("bio"),
                        "image_url": person.get("image_url"),
                        "created_at": convert_neo4j_datetime(person["created_at"])
                    }
                })
            return quotes
