"""
🤗 Hugging Face MCP Server 🤗

This server provides Model Context Protocol (MCP) access to the Hugging Face API,
allowing models like Claude to interact with models, datasets, spaces, and other
Hugging Face resources in a read-only manner.
"""

import asyncio
import json
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import httpx
import mcp.server.stdio
import mcp.types as types
from huggingface_hub import HfApi
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

# Initialize server
server = Server("huggingface")

# Initialize Hugging Face API client
hf_api = HfApi()

# Base URL for the Hugging Face API
HF_API_BASE = "https://huggingface.co/api"

# Initialize HTTP client for making requests
http_client = httpx.AsyncClient(timeout=30.0)


# Helper Functions
async def make_hf_request(
    endpoint: str, params: Optional[Dict[str, Any]] = None
) -> Dict:
    """Make a request to the Hugging Face API with proper error handling."""
    url = f"{HF_API_BASE}/{endpoint}"
    try:
        response = await http_client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# Tool Handlers
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools for interacting with the Hugging Face Hub.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        # Model Tools
        types.Tool(
            name="search-models",
            description="Search for models on Hugging Face Hub",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'bert', 'gpt')",
                    },
                    "author": {
                        "type": "string",
                        "description": "Filter by author/organization (e.g., 'huggingface', 'google')",
                    },
                    "tags": {
                        "type": "string",
                        "description": "Filter by tags (e.g., 'text-classification', 'translation')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                    },
                },
            },
        ),
        types.Tool(
            name="get-model-info",
            description="Get detailed information about a specific model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The ID of the model (e.g., 'google/bert-base-uncased')",
                    },
                },
                "required": ["model_id"],
            },
        ),
        # Dataset Tools
        types.Tool(
            name="search-datasets",
            description="Search for datasets on Hugging Face Hub",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"},
                    "author": {
                        "type": "string",
                        "description": "Filter by author/organization",
                    },
                    "tags": {"type": "string", "description": "Filter by tags"},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                    },
                },
            },
        ),
        types.Tool(
            name="get-dataset-info",
            description="Get detailed information about a specific dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "The ID of the dataset (e.g., 'squad')",
                    },
                },
                "required": ["dataset_id"],
            },
        ),
        # Space Tools
        types.Tool(
            name="search-spaces",
            description="Search for Spaces on Hugging Face Hub",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"},
                    "author": {
                        "type": "string",
                        "description": "Filter by author/organization",
                    },
                    "tags": {"type": "string", "description": "Filter by tags"},
                    "sdk": {
                        "type": "string",
                        "description": "Filter by SDK (e.g., 'streamlit', 'gradio', 'docker')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                    },
                },
            },
        ),
        types.Tool(
            name="get-space-info",
            description="Get detailed information about a specific Space",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_id": {
                        "type": "string",
                        "description": "The ID of the Space (e.g., 'huggingface/diffusers-demo')",
                    },
                },
                "required": ["space_id"],
            },
        ),
        # Papers Tools
        types.Tool(
            name="get-paper-info",
            description="Get information about a specific paper on Hugging Face",
            inputSchema={
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string",
                        "description": "The arXiv ID of the paper (e.g., '1810.04805')",
                    },
                },
                "required": ["arxiv_id"],
            },
        ),
        types.Tool(
            name="get-daily-papers",
            description="Get the list of daily papers curated by Hugging Face",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # Collections Tools
        types.Tool(
            name="search-collections",
            description="Search for collections on Hugging Face Hub",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Filter by owner"},
                    "item": {
                        "type": "string",
                        "description": "Filter by item (e.g., 'models/teknium/OpenHermes-2.5-Mistral-7B')",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search term for titles and descriptions",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                    },
                },
            },
        ),
        types.Tool(
            name="get-collection-info",
            description="Get detailed information about a specific collection",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "The namespace of the collection (user or organization)",
                    },
                    "collection_id": {
                        "type": "string",
                        "description": "The ID part of the collection",
                    },
                },
                "required": ["namespace", "collection_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Hugging Face API.
    """
    if not arguments:
        arguments = {}

    if name == "search-models":
        query = arguments.get("query")
        author = arguments.get("author")
        tags = arguments.get("tags")
        limit = arguments.get("limit", 10)

        params = {"limit": limit}
        if query:
            params["search"] = query
        if author:
            params["author"] = author
        if tags:
            params["filter"] = tags

        data = await make_hf_request("models", params)

        if "error" in data:
            return [
                types.TextContent(
                    type="text", text=f"Error searching models: {data['error']}"
                )
            ]

        # Format the results
        results = []
        for model in data:
            model_info = {
                "id": model.get("id", ""),
                "name": model.get("modelId", ""),
                "author": model.get("author", ""),
                "tags": model.get("tags", []),
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "lastModified": model.get("lastModified", ""),
            }
            results.append(model_info)

        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "get-model-info":
        model_id = arguments.get("model_id")
        if not model_id:
            return [types.TextContent(type="text", text="Error: model_id is required")]

        data = await make_hf_request(f"models/{quote_plus(model_id)}")

        if "error" in data:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error retrieving model information: {data['error']}",
                )
            ]

        # Format the result
        model_info = {
            "id": data.get("id", ""),
            "name": data.get("modelId", ""),
            "author": data.get("author", ""),
            "tags": data.get("tags", []),
            "pipeline_tag": data.get("pipeline_tag", ""),
            "downloads": data.get("downloads", 0),
            "likes": data.get("likes", 0),
            "lastModified": data.get("lastModified", ""),
            "description": data.get("description", "No description available"),
        }

        # Add model card if available
        if "card" in data and data["card"]:
            model_info["model_card"] = (
                data["card"].get("data", {}).get("text", "No model card available")
            )

        return [types.TextContent(type="text", text=json.dumps(model_info, indent=2))]

    elif name == "search-datasets":
        query = arguments.get("query")
        author = arguments.get("author")
        tags = arguments.get("tags")
        limit = arguments.get("limit", 10)

        params = {"limit": limit}
        if query:
            params["search"] = query
        if author:
            params["author"] = author
        if tags:
            params["filter"] = tags

        data = await make_hf_request("datasets", params)

        if "error" in data:
            return [
                types.TextContent(
                    type="text", text=f"Error searching datasets: {data['error']}"
                )
            ]

        # Format the results
        results = []
        for dataset in data:
            dataset_info = {
                "id": dataset.get("id", ""),
                "name": dataset.get("datasetId", ""),
                "author": dataset.get("author", ""),
                "tags": dataset.get("tags", []),
                "downloads": dataset.get("downloads", 0),
                "likes": dataset.get("likes", 0),
                "lastModified": dataset.get("lastModified", ""),
            }
            results.append(dataset_info)

        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "get-dataset-info":
        dataset_id = arguments.get("dataset_id")
        if not dataset_id:
            return [
                types.TextContent(type="text", text="Error: dataset_id is required")
            ]

        data = await make_hf_request(f"datasets/{quote_plus(dataset_id)}")

        if "error" in data:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error retrieving dataset information: {data['error']}",
                )
            ]

        # Format the result
        dataset_info = {
            "id": data.get("id", ""),
            "name": data.get("datasetId", ""),
            "author": data.get("author", ""),
            "tags": data.get("tags", []),
            "downloads": data.get("downloads", 0),
            "likes": data.get("likes", 0),
            "lastModified": data.get("lastModified", ""),
            "description": data.get("description", "No description available"),
        }

        # Add dataset card if available
        if "card" in data and data["card"]:
            dataset_info["dataset_card"] = (
                data["card"].get("data", {}).get("text", "No dataset card available")
            )

        return [types.TextContent(type="text", text=json.dumps(dataset_info, indent=2))]

    elif name == "search-spaces":
        query = arguments.get("query")
        author = arguments.get("author")
        tags = arguments.get("tags")
        sdk = arguments.get("sdk")
        limit = arguments.get("limit", 10)

        params = {"limit": limit}
        if query:
            params["search"] = query
        if author:
            params["author"] = author
        if tags:
            params["filter"] = tags
        if sdk:
            params["filter"] = params.get("filter", "") + f" sdk:{sdk}"

        data = await make_hf_request("spaces", params)

        if "error" in data:
            return [
                types.TextContent(
                    type="text", text=f"Error searching spaces: {data['error']}"
                )
            ]

        # Format the results
        results = []
        for space in data:
            space_info = {
                "id": space.get("id", ""),
                "name": space.get("spaceId", ""),
                "author": space.get("author", ""),
                "sdk": space.get("sdk", ""),
                "tags": space.get("tags", []),
                "likes": space.get("likes", 0),
                "lastModified": space.get("lastModified", ""),
            }
            results.append(space_info)

        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "get-space-info":
        space_id = arguments.get("space_id")
        if not space_id:
            return [types.TextContent(type="text", text="Error: space_id is required")]

        data = await make_hf_request(f"spaces/{quote_plus(space_id)}")

        if "error" in data:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error retrieving space information: {data['error']}",
                )
            ]

        # Format the result
        space_info = {
            "id": data.get("id", ""),
            "name": data.get("spaceId", ""),
            "author": data.get("author", ""),
            "sdk": data.get("sdk", ""),
            "tags": data.get("tags", []),
            "likes": data.get("likes", 0),
            "lastModified": data.get("lastModified", ""),
            "description": data.get("description", "No description available"),
            "url": f"https://huggingface.co/spaces/{space_id}",
        }

        return [types.TextContent(type="text", text=json.dumps(space_info, indent=2))]

    elif name == "get-paper-info":
        arxiv_id = arguments.get("arxiv_id")
        if not arxiv_id:
            return [types.TextContent(type="text", text="Error: arxiv_id is required")]

        data = await make_hf_request(f"papers/{arxiv_id}")

        if "error" in data:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error retrieving paper information: {data['error']}",
                )
            ]

        # Format the result
        paper_info = {
            "arxiv_id": data.get("arxivId", ""),
            "title": data.get("title", ""),
            "authors": data.get("authors", []),
            "summary": data.get("summary", "No summary available"),
            "url": f"https://huggingface.co/papers/{arxiv_id}",
        }

        # Get implementations
        implementations = await make_hf_request(f"arxiv/{arxiv_id}/repos")
        if "error" not in implementations:
            paper_info["implementations"] = implementations

        return [types.TextContent(type="text", text=json.dumps(paper_info, indent=2))]

    elif name == "get-daily-papers":
        data = await make_hf_request("daily_papers")

        if "error" in data:
            return [
                types.TextContent(
                    type="text", text=f"Error retrieving daily papers: {data['error']}"
                )
            ]

        # Format the results
        results = []
        for paper in data:
            paper_info = {
                "arxiv_id": paper.get("paper", {}).get("arxivId", ""),
                "title": paper.get("paper", {}).get("title", ""),
                "authors": paper.get("paper", {}).get("authors", []),
                "summary": paper.get("paper", {}).get("summary", "")[:200] + "..."
                if len(paper.get("paper", {}).get("summary", "")) > 200
                else paper.get("paper", {}).get("summary", ""),
            }
            results.append(paper_info)

        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "search-collections":
        owner = arguments.get("owner")
        item = arguments.get("item")
        query = arguments.get("query")
        limit = arguments.get("limit", 10)

        params = {"limit": limit}
        if owner:
            params["owner"] = owner
        if item:
            params["item"] = item
        if query:
            params["q"] = query

        data = await make_hf_request("collections", params)

        if "error" in data:
            return [
                types.TextContent(
                    type="text", text=f"Error searching collections: {data['error']}"
                )
            ]

        # Format the results
        results = []
        for collection in data:
            collection_info = {
                "id": collection.get("id", ""),
                "title": collection.get("title", ""),
                "owner": collection.get("owner", {}).get("name", ""),
                "description": collection.get(
                    "description", "No description available"
                ),
                "items_count": collection.get("itemsCount", 0),
                "upvotes": collection.get("upvotes", 0),
                "last_modified": collection.get("lastModified", ""),
            }
            results.append(collection_info)

        return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

    elif name == "get-collection-info":
        namespace = arguments.get("namespace")
        collection_id = arguments.get("collection_id")

        if not namespace or not collection_id:
            return [
                types.TextContent(
                    type="text", text="Error: namespace and collection_id are required"
                )
            ]

        # Extract the slug from the collection_id if it contains a dash
        slug = collection_id.split("-")[0] if "-" in collection_id else collection_id
        endpoint = f"collections/{namespace}/{slug}-{collection_id}"

        data = await make_hf_request(endpoint)

        if "error" in data:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error retrieving collection information: {data['error']}",
                )
            ]

        # Format the result
        collection_info = {
            "id": data.get("id", ""),
            "title": data.get("title", ""),
            "owner": data.get("owner", {}).get("name", ""),
            "description": data.get("description", "No description available"),
            "upvotes": data.get("upvotes", 0),
            "last_modified": data.get("lastModified", ""),
            "items": [],
        }

        # Add items
        for item in data.get("items", []):
            item_info = {
                "type": item.get("item", {}).get("type", ""),
                "id": item.get("item", {}).get("id", ""),
                "note": item.get("note", ""),
            }
            collection_info["items"].append(item_info)

        return [
            types.TextContent(type="text", text=json.dumps(collection_info, indent=2))
        ]

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


# Resource Handlers - Define popular models, datasets, and spaces as resources
@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available Hugging Face resources.
    This provides direct access to popular models, datasets, and spaces.
    """
    resources = []

    # Popular models
    popular_models = [
        (
            "meta-llama/Llama-3-8B-Instruct",
            "Llama 3 8B Instruct",
            "Meta's Llama 3 8B Instruct model",
        ),
        (
            "mistralai/Mistral-7B-Instruct-v0.2",
            "Mistral 7B Instruct v0.2",
            "Mistral AI's 7B instruction-following model",
        ),
        (
            "openchat/openchat-3.5-0106",
            "OpenChat 3.5",
            "Open-source chatbot based on Mistral 7B",
        ),
        (
            "stabilityai/stable-diffusion-xl-base-1.0",
            "Stable Diffusion XL 1.0",
            "SDXL text-to-image model",
        ),
    ]

    for model_id, name, description in popular_models:
        resources.append(
            types.Resource(
                uri=AnyUrl(f"hf://model/{model_id}"),
                name=name,
                description=description,
                mimeType="application/json",
            )
        )

    # Popular datasets
    popular_datasets = [
        (
            "databricks/databricks-dolly-15k",
            "Databricks Dolly 15k",
            "15k instruction-following examples",
        ),
        ("squad", "SQuAD", "Stanford Question Answering Dataset"),
        ("glue", "GLUE", "General Language Understanding Evaluation benchmark"),
        (
            "openai/summarize_from_feedback",
            "Summarize From Feedback",
            "OpenAI summarization dataset",
        ),
    ]

    for dataset_id, name, description in popular_datasets:
        resources.append(
            types.Resource(
                uri=AnyUrl(f"hf://dataset/{dataset_id}"),
                name=name,
                description=description,
                mimeType="application/json",
            )
        )

    # Popular spaces
    popular_spaces = [
        (
            "huggingface/diffusers-demo",
            "Diffusers Demo",
            "Demo of Stable Diffusion models",
        ),
        ("gradio/chatbot-demo", "Chatbot Demo", "Demo of a Gradio chatbot interface"),
        (
            "prompthero/midjourney-v4-diffusion",
            "Midjourney v4 Diffusion",
            "Replica of Midjourney v4",
        ),
        ("stabilityai/stablevicuna", "StableVicuna", "Fine-tuned Vicuna with RLHF"),
    ]

    for space_id, name, description in popular_spaces:
        resources.append(
            types.Resource(
                uri=AnyUrl(f"hf://space/{space_id}"),
                name=name,
                description=description,
                mimeType="application/json",
            )
        )

    return resources


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific Hugging Face resource by its URI.
    """
    if uri.scheme != "hf":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    if not uri.path:
        raise ValueError("Invalid Hugging Face resource URI")

    parts = uri.path.lstrip("/").split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid Hugging Face resource URI format")

    resource_type, resource_id = parts

    if resource_type == "model":
        data = await make_hf_request(f"models/{quote_plus(resource_id)}")
    elif resource_type == "dataset":
        data = await make_hf_request(f"datasets/{quote_plus(resource_id)}")
    elif resource_type == "space":
        data = await make_hf_request(f"spaces/{quote_plus(resource_id)}")
    else:
        raise ValueError(f"Unsupported resource type: {resource_type}")

    if "error" in data:
        raise ValueError(f"Error retrieving resource: {data['error']}")

    return json.dumps(data, indent=2)


# Prompt Handlers
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts for Hugging Face integration.
    """
    return [
        types.Prompt(
            name="compare-models",
            description="Compare multiple Hugging Face models",
            arguments=[
                types.PromptArgument(
                    name="model_ids",
                    description="Comma-separated list of model IDs to compare",
                    required=True,
                )
            ],
        ),
        types.Prompt(
            name="summarize-paper",
            description="Summarize an AI research paper from arXiv",
            arguments=[
                types.PromptArgument(
                    name="arxiv_id",
                    description="arXiv ID of the paper to summarize",
                    required=True,
                ),
                types.PromptArgument(
                    name="detail_level",
                    description="Level of detail in the summary (brief/detailed/eli5)",
                    required=False,
                ),
            ],
        ),
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt related to Hugging Face resources.
    """
    if not arguments:
        arguments = {}

    if name == "compare-models":
        model_ids = arguments.get("model_ids", "")
        if not model_ids:
            raise ValueError("model_ids argument is required")

        model_list = [model_id.strip() for model_id in model_ids.split(",")]
        models_data = []

        for model_id in model_list:
            data = await make_hf_request(f"models/{quote_plus(model_id)}")
            if "error" not in data:
                models_data.append(data)

        model_details = []
        for data in models_data:
            details = {
                "id": data.get("id", ""),
                "author": data.get("author", ""),
                "downloads": data.get("downloads", 0),
                "tags": data.get("tags", []),
                "description": data.get("description", "No description available"),
            }
            model_details.append(details)

        return types.GetPromptResult(
            description=f"Comparing models: {model_ids}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text="I'd like you to compare these Hugging Face models and help me understand their differences, strengths, and suitable use cases:\n\n"
                        + json.dumps(model_details, indent=2)
                        + "\n\nPlease structure your comparison with sections on architecture, performance, use cases, and limitations.",
                    ),
                )
            ],
        )

    elif name == "summarize-paper":
        arxiv_id = arguments.get("arxiv_id", "")
        if not arxiv_id:
            raise ValueError("arxiv_id argument is required")

        detail_level = arguments.get("detail_level", "detailed")

        paper_data = await make_hf_request(f"papers/{arxiv_id}")
        if "error" in paper_data:
            raise ValueError(f"Error retrieving paper: {paper_data['error']}")

        # Get implementations
        implementations = await make_hf_request(f"arxiv/{arxiv_id}/repos")

        return types.GetPromptResult(
            description=f"Summarizing paper: {paper_data.get('title', arxiv_id)}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Please provide a {'detailed' if detail_level == 'detailed' else 'brief'} summary of this AI research paper:\n\n"
                        + f"Title: {paper_data.get('title', 'Unknown')}\n"
                        + f"Authors: {', '.join(paper_data.get('authors', []))}\n"
                        + f"Abstract: {paper_data.get('summary', 'No abstract available')}\n\n"
                        + (
                            f"Implementations on Hugging Face: {json.dumps(implementations, indent=2)}\n\n"
                            if "error" not in implementations
                            else ""
                        )
                        + f"Please {'cover all key aspects including methodology, results, and implications' if detail_level == 'detailed' else 'provide a concise overview of the main contributions'}.",
                    ),
                )
            ],
        )

    else:
        raise ValueError(f"Unknown prompt: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="huggingface",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
