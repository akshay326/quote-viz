# MCP Server Configuration

This directory contains example MCP (Model Context Protocol) server configurations for integrating Claude with your quote visualization system.

## Neo4j MCP Server

The Neo4j MCP server allows Claude to directly query your graph database.

### Installation

Add the configuration from `neo4j-config.json` to your Claude Code settings file (`~/.claude/settings.json`):

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

**Important**: Replace `NEO4J_PASSWORD` with your actual password from `.env` file.

### Usage Examples

Once configured, you can ask Claude:

```
How many quotes are currently in the database?
```

```
Show me all quotes by Steve Jobs
```

```
What are the top 5 largest clusters?
```

```
Find all quotes that mention 'time' or 'future'
```

```
Generate a Cypher query to find the most connected people
```

## Filesystem MCP Server

The filesystem MCP server helps with data extraction from unstructured notes.

### Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_DIRECTORIES": "/Users/pika/Projects/quote-viz/data/raw"
      }
    }
  }
}
```

### Usage Examples

```
Read all markdown files in data/raw/ and extract quotes in JSON format
```

```
Help me structure the quotes from my notes into the required format
```

## Combining MCPs

You can have both MCP servers running simultaneously. This allows you to:

1. Extract quotes from notes using filesystem MCP
2. Validate the data format
3. Check what's already in the database using Neo4j MCP
4. Avoid duplicates before ingestion

## Troubleshooting

**MCP server not connecting**:
- Ensure Docker containers are running: `docker compose ps`
- Verify Neo4j is accessible: `curl http://localhost:7474`
- Check password matches in both .env and MCP config

**Permission errors**:
- For filesystem MCP, ensure the allowed directory path is correct
- Check file permissions in data/raw/

**Commands not working**:
- Restart Claude Code after adding MCP configuration
- Check Claude Code logs for MCP connection errors
