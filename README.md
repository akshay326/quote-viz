# Quote Visualization System

A local web-based quote visualization system with graph relationships, semantic similarity clustering, and search capabilities.

## Features

- **Quote Management**: Create, read, update, and delete quotes with automatic embedding generation
- **Graph Visualization**: View relationships between quotes and people
- **Semantic Similarity**: Find similar quotes using NLP embeddings
- **Clustering**: Automatic grouping of related quotes using HDBSCAN
- **Full-text Search**: Search quotes by text, author, or context
- **Analytics Dashboard**: View statistics and cluster distributions

## Tech Stack

- **Database**: Neo4j Community Edition (graph database)
- **Backend**: FastAPI + Python 3.11
- **NLP**: sentence-transformers (all-MiniLM-L6-v2), HDBSCAN, scikit-learn
- **Frontend**: React + TypeScript + Vite
- **Deployment**: Docker Compose

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

1. **Clone and navigate to the project**
   ```bash
   cd /Users/pika/Projects/quote-viz
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set a secure password:
   ```
   NEO4J_PASSWORD=your-secure-password-here
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

   This will start:
   - Neo4j at http://localhost:7474 (browser) and bolt://localhost:7687
   - Backend API at http://localhost:8000
   - Frontend at http://localhost:3000

4. **Initialize the database**
   ```bash
   docker compose exec backend python app/scripts/init_db.py
   ```

5. **Load sample quotes**
   ```bash
   docker compose exec backend python app/scripts/ingest_quotes.py
   ```

6. **Compute clusters**
   ```bash
   docker compose exec backend python app/scripts/compute_clusters.py
   ```

7. **Access the application**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474

## Data Ingestion

### Format Your Quotes

Create a JSON file in `data/processed/quotes.json` with this format:

```json
[
  {
    "quote": "The quote text here",
    "author": "Author Name",
    "context": "Optional context or situation",
    "source": "Optional source reference"
  }
]
```

### Extract from Unstructured Notes

1. Place your unstructured notes in `data/raw/`
2. Use Claude with filesystem MCP to extract quotes:
   ```
   Read all files in data/raw/ and extract quotes in the format:
   {quote, author, context, source}
   ```
3. Review and save to `data/processed/quotes.json`
4. Run ingestion script

### Ingest Quotes

```bash
docker compose exec backend python app/scripts/ingest_quotes.py
```

This will:
- Generate embeddings for each quote
- Create person nodes if they don't exist
- Store quotes in Neo4j

## MCP Integration

### Neo4j MCP Server

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "neo4j": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-neo4j"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password-here"
      }
    }
  }
}
```

Then you can ask Claude:
- "How many quotes are in the database?"
- "Show me all quotes by Einstein"
- "What are the largest clusters?"

## API Endpoints

### Quotes
- `POST /api/quotes` - Create a quote
- `GET /api/quotes` - List quotes (with filters)
- `GET /api/quotes/{id}` - Get quote with similar quotes
- `PUT /api/quotes/{id}` - Update a quote
- `DELETE /api/quotes/{id}` - Delete a quote
- `GET /api/search?q=query` - Full-text search
- `GET /api/similar/{id}` - Get similar quotes

### Graph
- `GET /api/graph` - Get full graph data

### Analytics
- `GET /api/analytics/stats` - Get statistics
- `POST /api/analytics/recompute-clusters` - Recompute clusters

## Development

### Backend Development

```bash
# Install dependencies locally (optional, for IDE)
cd backend
pip install -r requirements.txt

# Run tests (when implemented)
docker compose exec backend pytest

# View logs
docker compose logs -f backend
```

### Frontend Development

For faster frontend development with hot reload:

```bash
cd frontend
npm install
npm run dev
```

Update `frontend/src/api/client.ts` to use `http://localhost:8000` for the API.

### Database Management

**View data in Neo4j Browser** (http://localhost:7474):
```cypher
// View all quotes and people
MATCH (q:Quote)-[:ATTRIBUTED_TO]->(p:Person)
RETURN q, p LIMIT 25

// View cluster distribution
MATCH (q:Quote)
WHERE q.cluster_id IS NOT NULL
RETURN q.cluster_id, count(q) as quote_count
ORDER BY quote_count DESC

// Find similar quotes
MATCH (q1:Quote)-[s:SIMILAR_TO]->(q2:Quote)
RETURN q1.text, q2.text, s.similarity
ORDER BY s.similarity DESC
LIMIT 10
```

## Project Structure

```
quote-viz/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   │   ├── neo4j_service.py
│   │   │   ├── nlp_service.py
│   │   │   └── similarity.py
│   │   ├── api/              # API endpoints
│   │   └── scripts/          # CLI scripts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
├── data/
│   ├── raw/                  # Unstructured notes
│   └── processed/            # Extracted quotes JSON
├── docker-compose.yml
└── README.md
```

## Troubleshooting

### Neo4j won't start
- Ensure port 7474 and 7687 are not in use
- Check Docker logs: `docker compose logs neo4j`
- Verify NEO4J_PASSWORD is set in .env

### Backend can't connect to Neo4j
- Wait for Neo4j health check to pass (30s)
- Check connection: `docker compose exec backend python -c "from app.config import get_settings; print(get_settings().neo4j_uri)"`

### Frontend can't reach API
- Verify VITE_API_URL in .env
- Check CORS settings in backend/app/config.py
- Ensure backend is running: `curl http://localhost:8000/health`

### Model download fails
- The first run downloads ~80MB model
- Check internet connection
- Model cache is persisted in Docker volume

## Performance

With 500-1000 quotes:
- Embedding generation: <2s for 100 quotes
- Similarity search: <100ms
- Clustering: <5s
- Graph query: <50ms

## Future Enhancements (V2)

- [ ] Voice note transcription (Whisper)
- [ ] Email/WhatsApp integration
- [ ] Browser extension for web quotes
- [ ] Topic extraction (BERTopic)
- [ ] Timeline view
- [ ] Person relationship inference
- [ ] Export to Markdown/PDF
- [ ] 3D graph visualization with Reagraph

## License

MIT
