# Testing the Wikipedia MCP Server

This guide explains how to test the Wikipedia MCP server with Claude Desktop or through a simple test client.

## Testing with Claude Desktop

The Wikipedia MCP server is designed to be used with Claude Desktop or other clients that support the Model Context Protocol (MCP). Here's how to test it with Claude Desktop:

### Prerequisites

- Claude Desktop installed on your computer
- Wikipedia MCP server installed (see main README.md for installation instructions)

### Setup

1. Configure Claude Desktop to use the Wikipedia MCP server:

   Edit your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

   Add the following configuration:

   ```json
   {
     "mcpServers": {
       "wikipedia": {
         "command": "wikipedia-mcp"
       }
     }
   }
   ```

2. Start Claude Desktop
   
   Claude Desktop will automatically start the Wikipedia MCP server when needed.

3. Test with prompts

   In Claude Desktop, try using these prompts to test the Wikipedia integration:
   
   - "Tell me about quantum computing using the Wikipedia information."
   - "Summarize the history of artificial intelligence based on Wikipedia."
   - "What does Wikipedia say about climate change?"
   - "Find Wikipedia articles related to machine learning."
   - "Get me the introduction section of the article on neural networks from Wikipedia."

### Troubleshooting Claude Desktop Integration

- Check Claude Desktop logs for any errors related to the MCP server
- Make sure the path to the `wikipedia-mcp` command is in your system PATH
- If using a virtual environment, ensure Claude Desktop can access it
- On Windows, you might need to specify the full path to the executable

## Testing with the Test Client

If you don't have Claude Desktop, you can use the included test client to verify the Wikipedia MCP server is working correctly.

### Running the Test Client

1. Ensure you have the Wikipedia MCP package installed
2. Run the test client:

   ```bash
   python3 test_mcp_client.py
   ```

3. The test client will:
   - Start the Wikipedia MCP server
   - Send a tool discovery request
   - Display the available tools
   - Verify the server is functioning correctly

### Expected Output

When the test client runs successfully, you should see output similar to:

```
Starting Wikipedia MCP server...
Sending discovery message to server...

Server Response:
{
  "type": "discover_tools_response",
  "version": "1.0.0",
  "tools": [
    {
      "name": "search_wikipedia",
      "description": "Search Wikipedia for articles matching a query.",
      "parameters": {
        "query": {
          "type": "string",
          "description": "The search term"
        },
        "limit": {
          "type": "integer",
          "description": "Maximum number of results to return",
          "default": 10
        }
      }
    },
    // Other tools will be listed here
  ]
}

Available MCP Tools:
- search_wikipedia: Search Wikipedia for articles matching a query.
- get_article: Get the full content of a Wikipedia article.
- get_summary: Get a summary of a Wikipedia article.
- get_related_topics: Get topics related to a Wikipedia article based on links and categories.

Test successful! The Wikipedia MCP server is working correctly.
```

### Manual Testing

You can also manually test the server by sending MCP commands:

1. Start the server in one terminal:

   ```bash
   python3 -m wikipedia_mcp
   ```

2. In another terminal, send a JSON message:

   ```bash
   echo '{"type": "discover_tools", "version": "1.0.0"}' | python3 -m wikipedia_mcp
   ```

   This should return a JSON response with the available tools.

## Advanced Testing

For more advanced testing, you can use the Python MCP client library:

```python
from mcp.client import Client

# Create an MCP client connected to the Wikipedia server
client = Client(["python3", "-m", "wikipedia_mcp"])

# Discover available tools
tools = client.discover_tools()
print(f"Available tools: {tools}")

# Call a tool
result = client.call_tool("search_wikipedia", {"query": "quantum computing", "limit": 5})
print(f"Search results: {result}")

# Close the client
client.close()
```

This allows you to programmatically interact with the Wikipedia MCP server from your Python code.

## Reporting Issues

If you encounter any issues while testing the Wikipedia MCP server, please report them on the GitHub repository:

[https://github.com/rudra-ravi/wikipedia-mcp/issues](https://github.com/rudra-ravi/wikipedia-mcp/issues) 