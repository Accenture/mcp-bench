#!/usr/bin/env python3
"""
Example script for interacting with the Wikipedia MCP server.

This script demonstrates how to use the MCP client to interact with
the Wikipedia MCP server programmatically.
"""

import json
import sys
import argparse
try:
    from mcp.client import Client
except ImportError:
    print("Error: mcp package not found. Install it with: pip install mcp")
    sys.exit(1)

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def discover_tools(client):
    """Discover and print available tools on the MCP server."""
    print("Discovering tools...")
    tools = client.discover_tools()
    print("\nAvailable tools:")
    for tool in tools:
        print(f"- {tool.get('name')}: {tool.get('description')}")
    return tools

def search_wikipedia(client, query, limit=5):
    """Search Wikipedia using the MCP server."""
    print(f"\nSearching Wikipedia for: {query} (limit: {limit})")
    result = client.call_tool("search_wikipedia", {"query": query, "limit": limit})
    print("\nSearch results:")
    print_json(result)
    return result

def get_article(client, title):
    """Get a full Wikipedia article."""
    print(f"\nGetting article: {title}")
    result = client.call_tool("get_article", {"title": title})
    
    if not result.get("exists", False):
        print(f"Article not found: {title}")
        return None
    
    print(f"\nArticle: {title}")
    print(f"Summary: {result.get('summary', '')[:200]}...")
    print(f"Total content length: {len(result.get('text', ''))}")
    print(f"Sections: {len(result.get('sections', []))}")
    print(f"Links: {len(result.get('links', []))}")
    return result

def get_summary(client, title):
    """Get a summary of a Wikipedia article."""
    print(f"\nGetting summary for: {title}")
    result = client.call_tool("get_summary", {"title": title})
    print(f"\nSummary for {title}:")
    print(result)
    return result

def get_related_topics(client, title, limit=5):
    """Get topics related to a Wikipedia article."""
    print(f"\nGetting related topics for: {title} (limit: {limit})")
    result = client.call_tool("get_related_topics", {"title": title, "limit": limit})
    print(f"\nRelated topics for {title}:")
    print_json(result)
    return result

def main():
    parser = argparse.ArgumentParser(description="Wikipedia MCP Client Example")
    parser.add_argument("--command", choices=["discover", "search", "article", "summary", "related", "demo"], 
                      default="demo", help="Command to execute")
    parser.add_argument("--query", help="Search query or article title")
    parser.add_argument("--limit", type=int, default=5, help="Limit for search results or related topics")
    args = parser.parse_args()

    print("Connecting to Wikipedia MCP server...")
    with Client(["python3", "-m", "wikipedia_mcp"]) as client:
        print("Connected!")
        
        # Always discover tools first to verify connection
        tools = discover_tools(client)
        
        if args.command == "discover":
            # Already done above
            pass
        elif args.command == "search":
            if not args.query:
                print("Error: --query is required for search")
                return
            search_wikipedia(client, args.query, args.limit)
        elif args.command == "article":
            if not args.query:
                print("Error: --query is required for article (as title)")
                return
            get_article(client, args.query)
        elif args.command == "summary":
            if not args.query:
                print("Error: --query is required for summary (as title)")
                return
            get_summary(client, args.query)
        elif args.command == "related":
            if not args.query:
                print("Error: --query is required for related topics (as title)")
                return
            get_related_topics(client, args.query, args.limit)
        elif args.command == "demo":
            # Run a full demo of all features
            print("\n=== Running full demo ===\n")
            
            # Search for a topic
            search_results = search_wikipedia(client, "quantum computing", 3)
            
            # Get the first article title from the search results
            if search_results and search_results.get("results"):
                first_title = search_results["results"][0]["title"]
                
                # Get the summary of the article
                get_summary(client, first_title)
                
                # Get related topics
                get_related_topics(client, first_title, 3)
                
                # Get the full article
                get_article(client, first_title)
            else:
                print("No search results found to continue demo")

if __name__ == "__main__":
    main() 