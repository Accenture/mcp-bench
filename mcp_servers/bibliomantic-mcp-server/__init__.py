"""
Bibliomantic MCP Server Package

A Model Communication Protocol server that integrates I Ching divination 
with Anthropic's Claude AI, implementing the bibliomantic approach described 
in Philip K. Dick's "The Man in the High Castle".

This package provides:
- Complete I Ching hexagram database with interpretations
- Bibliomantic divination system using traditional three-coin method
- MCP-compliant JSON-RPC 2.0 server
- Claude AI integration for wisdom-enhanced responses
- Comprehensive testing and example client implementation
"""

__version__ = "1.0.0"
__author__ = "Dan Shields"
__description__ = "Bibliomantic MCP Server with I Ching divination and Claude AI integration"

# Core exports for package users
try:
    from .iching import IChing, divine_hexagram
    from .divination import BiblioManticDiviner, augment_query_with_divination, perform_divination
    from .claude_client import ClaudeClient, BiblioManticClaudeIntegration, ClaudeResponse
    from .server import BiblioManticMCPServer, create_mcp_server
except ImportError:
    # Fallback for when running modules directly
    from iching import IChing, divine_hexagram
    from divination import BiblioManticDiviner, augment_query_with_divination, perform_divination
    from claude_client import ClaudeClient, BiblioManticClaudeIntegration, ClaudeResponse
    from server import BiblioManticMCPServer, create_mcp_server

__all__ = [
    # I Ching system
    "IChing",
    "divine_hexagram",
    
    # Divination system
    "BiblioManticDiviner", 
    "augment_query_with_divination",
    "perform_divination",
    
    # Claude integration
    "ClaudeClient",
    "BiblioManticClaudeIntegration", 
    "ClaudeResponse",
    
    # MCP Server
    "BiblioManticMCPServer",
    "create_mcp_server",
]

# Package metadata
PACKAGE_INFO = {
    "name": "bibliomantic-mcp-server",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "bibliomantic_approach": "Philip K. Dick - The Man in the High Castle",
    "features": [
        "I Ching divination with 64 hexagram database",
        "Traditional three-coin method simulation", 
        "Claude AI integration",
        "MCP JSON-RPC 2.0 compliance",
        "Async server architecture",
        "Mock mode for testing",
        "Comprehensive health monitoring",
        "Example client implementation"
    ],
    "hexagram_count": 64,
    "randomness_method": "Cryptographically secure (Python secrets module)",
    "server_framework": "FastAPI with async support"
}


def get_package_info():
    """
    Get comprehensive package information.
    
    Returns:
        Dictionary containing package metadata and features
    """
    return PACKAGE_INFO.copy()


def get_version():
    """
    Get package version.
    
    Returns:
        Version string
    """
    return __version__


# Package-level convenience functions
def quick_divination():
    """
    Perform a quick I Ching divination.
    
    Returns:
        Tuple of (hexagram_number, name, interpretation)
    """
    return divine_hexagram()


async def quick_bibliomantic_query(query: str, api_key: str = None):
    """
    Perform a quick bibliomantic query with Claude integration.
    
    Args:
        query: The question to augment with I Ching wisdom
        api_key: Optional Anthropic API key (uses mock mode if not provided)
        
    Returns:
        Complete bibliomantic response dictionary
    """
    integration = BiblioManticClaudeIntegration(ClaudeClient(api_key=api_key))
    try:
        return await integration.process_query(query)
    finally:
        await integration.close()


# Package initialization message for debugging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Bibliomantic MCP Server package initialized (version {__version__})")
