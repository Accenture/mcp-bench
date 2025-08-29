# Wikipedia MCP API Documentation

This document describes the API endpoints and tools available in the Wikipedia MCP server.

## HTTP Endpoints

### Search Articles
```
GET /search/{query}
```
Search Wikipedia for articles matching a query.

**Parameters:**
- `query` (string, required): The search query

**Response:**
```json
{
    "query": "search query",
    "results": [
        {
            "title": "Article title",
            "snippet": "Article snippet",
            "pageid": 12345,
            "wordcount": 1000,
            "timestamp": "2024-03-08T12:00:00Z"
        }
    ]
}
```

### Get Article
```
GET /article/{title}
```
Get the full content of a Wikipedia article.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article

**Response:**
```json
{
    "title": "Article title",
    "pageid": 12345,
    "summary": "Article summary",
    "text": "Full article text",
    "url": "https://en.wikipedia.org/wiki/Article_title",
    "sections": [
        {
            "title": "Section title",
            "text": "Section content",
            "level": 1
        }
    ],
    "categories": ["Category1", "Category2"],
    "links": ["Link1", "Link2"],
    "exists": true
}
```

### Get Summary
```
GET /summary/{title}
```
Get a summary of a Wikipedia article.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article

**Response:**
```json
{
    "title": "Article title",
    "summary": "Article summary"
}
```

### Get Sections
```
GET /sections/{title}
```
Get the sections of a Wikipedia article.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article

**Response:**
```json
{
    "title": "Article title",
    "sections": [
        {
            "title": "Section title",
            "text": "Section content",
            "level": 1
        }
    ]
}
```

### Get Links
```
GET /links/{title}
```
Get the links in a Wikipedia article.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article

**Response:**
```json
{
    "title": "Article title",
    "links": ["Link1", "Link2", "Link3"]
}
```

## MCP Tools

### search_wikipedia
Search Wikipedia for articles matching a query.

**Parameters:**
- `query` (string, required): The search query
- `limit` (integer, optional, default=10): Maximum number of results to return

### get_article
Get the full content of a Wikipedia article.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article

### get_summary
Get a summary of a Wikipedia article.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article

### get_related_topics
Get topics related to a Wikipedia article based on links and categories.

**Parameters:**
- `title` (string, required): The title of the Wikipedia article
- `limit` (integer, optional, default=10): Maximum number of related topics to return
