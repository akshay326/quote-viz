# Quick Start Guide

Get your quote visualization system running in 5 minutes.

## Step 1: Start the System (1 min)

```bash
cd /Users/pika/Projects/quote-viz

# Start all services
docker compose up -d

# Wait for services to be ready (30 seconds)
# Watch the logs to confirm Neo4j is ready
docker compose logs -f neo4j
# Look for: "Started."
# Press Ctrl+C when ready
```

## Step 2: Initialize Database (30 seconds)

```bash
# Create indexes and constraints
docker compose exec backend python app/scripts/init_db.py
```

Expected output:
```
✓ Created unique constraint on Quote.id
✓ Created unique constraint on Person.id
...
Database initialized successfully!
```

## Step 3: Load Sample Data (1 min)

```bash
# Ingest the 15 sample quotes
docker compose exec backend python app/scripts/ingest_quotes.py
```

This will:
- Generate embeddings for each quote (~30 seconds)
- Create person nodes
- Store quotes in Neo4j

Expected: "Created: 15 quotes"

## Step 4: Compute Clusters (30 seconds)

```bash
# Run HDBSCAN clustering
docker compose exec backend python app/scripts/compute_clusters.py
```

Expected: "Clustering complete! Clusters: X"

## Step 5: Open the App (10 seconds)

Visit these URLs:

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
  - Username: `neo4j`
  - Password: `quoteviz2024` (from .env)

## What to Try

### In the Frontend (http://localhost:3000)

1. Browse the recent quotes on the home page
2. Click a quote to see similar quotes
3. Visit Analytics to see cluster distribution
4. Click "Recompute Clusters" to re-run clustering

### In Neo4j Browser (http://localhost:7474)

Run these Cypher queries:

```cypher
// Visualize the graph
MATCH (q:Quote)-[:ATTRIBUTED_TO]->(p:Person)
RETURN q, p LIMIT 25
```

```cypher
// View similarity relationships
MATCH (q1:Quote)-[s:SIMILAR_TO]->(q2:Quote)
WHERE s.similarity > 0.7
RETURN q1.text, q2.text, s.similarity
ORDER BY s.similarity DESC
LIMIT 10
```

```cypher
// Find clusters
MATCH (q:Quote)
WHERE q.cluster_id IS NOT NULL
RETURN q.cluster_id, count(q) as size
ORDER BY size DESC
```

### Via API (http://localhost:8000/docs)

1. Click "Try it out" on any endpoint
2. Create a new quote:
   ```json
   {
     "text": "Your new quote here",
     "author": "Your Name",
     "context": "Added via API"
   }
   ```
3. Search quotes: `/api/search?q=time`

## Next Steps

### Add Your Own Quotes

1. **Option A: Via API** (easiest for single quotes)
   - Use http://localhost:8000/docs
   - POST to `/api/quotes`

2. **Option B: Via JSON File** (best for bulk import)
   - Edit `data/processed/quotes.json`
   - Add your quotes following the format
   - Run: `docker compose exec backend python app/scripts/ingest_quotes.py`

3. **Option C: From Unstructured Notes** (for existing notes)
   - Place .txt files in `data/raw/`
   - Use Claude with filesystem MCP (see MCP setup below)
   - Ask Claude to extract quotes
   - Run ingestion script

### Set Up MCP Integration

For direct Claude access to your database:

1. Add to `~/.claude/settings.json`:
   ```json
   {
     "mcpServers": {
       "neo4j": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-neo4j"],
         "env": {
           "NEO4J_URI": "bolt://localhost:7687",
           "NEO4J_USER": "neo4j",
           "NEO4J_PASSWORD": "quoteviz2024"
         }
       }
     }
   }
   ```

2. Restart Claude Code

3. Test: "How many quotes are in my database?"

See `mcp-servers/README.md` for more details.

## Troubleshooting

**Services won't start**:
```bash
docker compose down
docker compose up -d
docker compose logs
```

**Frontend can't connect**:
- Check backend is running: `curl http://localhost:8000/health`
- Should return: `{"status":"healthy"}`

**No quotes appearing**:
```bash
# Check if quotes were ingested
docker compose exec backend python -c "
from app.config import get_settings
from app.services.neo4j_service import Neo4jService
neo4j = Neo4jService(get_settings())
print(f'Quotes: {len(neo4j.list_quotes(limit=100))}')
neo4j.close()
"
```

**Reset everything**:
```bash
docker compose down -v
docker compose up -d
# Then repeat steps 2-4
```

## Performance Tips

- First run downloads 80MB model (cached for future use)
- Clustering with <100 quotes might not form distinct clusters
- Add more quotes for better clustering results
- Similarity threshold (0.75) can be adjusted in backend/app/config.py

## What's Next?

Check out:
- `README.md` - Full documentation
- `mcp-servers/README.md` - MCP integration guide
- Plan file - Future features (V2 roadmap)

Enjoy your quote visualization system!
