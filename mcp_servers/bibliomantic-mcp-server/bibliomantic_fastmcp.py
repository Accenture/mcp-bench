#!/usr/bin/env python3
"""
Bibliomantic MCP Server using FastMCP

A Model Context Protocol server that integrates I Ching divination with AI responses,
following the bibliomantic approach described in Philip K. Dick's "The Man in the High Castle".

This version uses the official MCP Python SDK's FastMCP framework for maximum simplicity
and professional compliance with the MCP specification.
"""

import logging
import sys
from typing import Optional

# Import the official FastMCP framework
from mcp.server.fastmcp import FastMCP

# Import our bibliomantic components
try:
    from divination import BiblioManticDiviner
    from iching import IChing
except ImportError:
    # Fallback for direct execution
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from divination import BiblioManticDiviner
    from iching import IChing

# Configure logging to stderr (FastMCP handles stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create the FastMCP server with dependencies
mcp = FastMCP(
    name="Bibliomantic Oracle",
    dependencies=["secrets"]  # For cryptographically secure randomness
)

# Initialize our divination components
diviner = BiblioManticDiviner()
iching = IChing()

logger.info("Bibliomantic FastMCP Server initialized")


@mcp.tool()
def i_ching_divination(query: Optional[str] = None) -> str:
    """
    Perform I Ching divination using traditional three-coin method.
    
    Generates a random hexagram with interpretation for guidance.
    Uses cryptographically secure randomness to simulate coin tosses.
    
    Args:
        query: Optional question or context for the divination
        
    Returns:
        Formatted hexagram reading with interpretation
    """
    logger.info("Performing I Ching divination")
    
    result = diviner.perform_simple_divination()
    
    if result["success"]:
        response = f"""🎋 **I Ching Divination**

**Hexagram {result['hexagram_number']}: {result['hexagram_name']}**

{result['interpretation']}

*Generated using traditional three-coin method with cryptographically secure randomness.*
*This follows the authentic I Ching methodology as described in ancient Chinese divination.*"""

        if query:
            response += f"\n\n**Your Question:** {query}"
            response += f"\n\n**Guidance:** Consider how this hexagram's wisdom applies to your specific situation."
        
        logger.info(f"Generated hexagram {result['hexagram_number']} - {result['hexagram_name']}")
        return response
    else:
        error_msg = f"Divination failed: {result.get('error', 'Unknown error')}"
        logger.error(error_msg)
        return error_msg


@mcp.tool()
def bibliomantic_consultation(query: str) -> str:
    """
    Perform bibliomantic consultation following Philip K. Dick's approach.
    
    Augments your query with I Ching wisdom, creating a bridge between
    your specific question and ancient guidance, as described in 
    "The Man in the High Castle".
    
    Args:
        query: The question or situation requiring guidance
        
    Returns:
        Complete bibliomantic consultation with hexagram wisdom
    """
    logger.info(f"Performing bibliomantic consultation for query: {query[:50]}...")
    
    if not query.strip():
        return "Please provide a question for bibliomantic consultation."
    
    # Perform divination and augment query
    augmented_query, divination_info = diviner.divine_query_augmentation(query)
    
    if "error" in divination_info:
        error_msg = f"Consultation failed: {divination_info['error']}"
        logger.error(error_msg)
        return error_msg
    
    response = f"""🔮 **Bibliomantic Consultation**

**Your Question:** {query}

**Oracle's Guidance - Hexagram {divination_info['hexagram_number']}: {divination_info['hexagram_name']}**

{divination_info['interpretation']}

**Bibliomantic Integration:**
The I Ching suggests considering this wisdom in the context of your question. This ancient guidance offers perspective on the energies and patterns surrounding your situation.

**Method:** Traditional three-coin divination
**Approach:** Philip K. Dick's bibliomantic method from "The Man in the High Castle"
**Randomness:** Cryptographically secure generation

*This consultation bridges your modern question with timeless wisdom, allowing the oracle to speak to your specific circumstances.*"""
    
    logger.info(f"Completed bibliomantic consultation with hexagram {divination_info['hexagram_number']}")
    return response


@mcp.tool()
def get_hexagram_details(hexagram_number: int) -> str:
    """
    Get detailed information about a specific I Ching hexagram.
    
    Provides the traditional name and interpretation for any of the
    64 hexagrams in the I Ching (Book of Changes).
    
    Args:
        hexagram_number: The hexagram number (1-64)
        
    Returns:
        Detailed hexagram information and interpretation
    """
    logger.info(f"Retrieving details for hexagram {hexagram_number}")
    
    if not isinstance(hexagram_number, int) or not (1 <= hexagram_number <= 64):
        return "Please provide a valid hexagram number between 1 and 64."
    
    name, interpretation = iching.get_hexagram_by_number(hexagram_number)
    
    response = f"""📖 **Hexagram {hexagram_number}: {name}**

**Traditional Interpretation:**
{interpretation}

**About This Hexagram:**
This is one of the 64 hexagrams in the I Ching (Book of Changes), the ancient Chinese divination text. Each hexagram represents a unique combination of yin and yang energies and offers guidance for understanding life's patterns and changes.

**Historical Context:**
The I Ching dates back over 3,000 years and has been used for divination, philosophy, and understanding the natural order. Each hexagram consists of six lines (yin or yang) that form a unique pattern of meaning.

**Usage in Bibliomancy:**
As described in Philip K. Dick's work, hexagrams can be consulted for guidance on complex decisions and situations, providing a bridge between ancient wisdom and modern challenges."""
    
    logger.info(f"Retrieved details for hexagram {hexagram_number} - {name}")
    return response


@mcp.resource("hexagram://{number}")
def get_hexagram_resource(number: str) -> str:
    """
    Access hexagram information as a resource for context loading.
    
    This resource allows AI models to load hexagram data directly
    into their context for reference during conversations.
    
    Args:
        number: Hexagram number as string (1-64)
        
    Returns:
        Hexagram data formatted for context use
    """
    try:
        hexagram_num = int(number)
        if not (1 <= hexagram_num <= 64):
            return "Invalid hexagram number. Must be between 1 and 64."
        
        name, interpretation = iching.get_hexagram_by_number(hexagram_num)
        
        return f"""I Ching Hexagram {hexagram_num}: {name}

{interpretation}

Traditional Classification: One of 64 hexagrams in the Book of Changes
Historical Period: Ancient China (3000+ years old)
Divination Method: Three-coin traditional method
Philosophical Framework: Yin-Yang dynamics and change patterns"""
        
    except ValueError:
        return "Invalid hexagram number format. Please provide a number between 1 and 64."


@mcp.resource("iching://database")
def get_iching_database() -> str:
    """
    Access the complete I Ching database as a resource.
    
    Provides a summary of all 64 hexagrams for context loading,
    useful when AI models need to reference the complete system.
    
    Returns:
        Complete hexagram database summary
    """
    hexagram_list = []
    for i in range(1, 65):
        name, _ = iching.get_hexagram_by_number(i)
        hexagram_list.append(f"{i:2d}. {name}")
    
    return f"""I Ching Complete Database - 64 Hexagrams

The Book of Changes (I Ching) contains 64 hexagrams, each representing unique patterns of change and guidance:

{chr(10).join(hexagram_list)}

System Information:
- Total Hexagrams: 64
- Randomness Method: Cryptographically secure three-coin simulation
- Historical Origin: Ancient China (Zhou Dynasty, ~1000 BCE)
- Philosophical Basis: Yin-Yang cosmology and patterns of change
- Bibliomantic Usage: As described in Philip K. Dick's "The Man in the High Castle"

Each hexagram consists of six lines (yin or yang) forming 2^6 = 64 possible combinations,
representing the complete spectrum of situations and changes in the universe."""


@mcp.prompt()
def career_guidance_prompt(situation: str) -> str:
    """
    Generate a prompt for career guidance consultation.
    
    Creates a structured prompt for seeking I Ching guidance
    on career-related decisions and situations.
    
    Args:
        situation: Description of the career situation or decision
        
    Returns:
        Formatted prompt for career guidance
    """
    return f"""I'm facing this career situation: {situation}

Please consult the I Ching oracle using the bibliomantic method from Philip K. Dick's "The Man in the High Castle" and provide guidance based on ancient wisdom.

Specifically, I would like:
1. An I Ching divination relevant to my career situation
2. Interpretation of how the hexagram applies to my specific circumstances  
3. Practical guidance based on the oracle's wisdom
4. Perspective on timing and approach for my career decisions

Please use the traditional three-coin method for authentic divination."""


@mcp.prompt()
def creative_guidance_prompt(project: str) -> str:
    """
    Generate a prompt for creative project guidance.
    
    Creates a structured prompt for seeking I Ching wisdom
    on creative endeavors and artistic decisions.
    
    Args:
        project: Description of the creative project or challenge
        
    Returns:
        Formatted prompt for creative guidance
    """
    return f"""I'm working on this creative project: {project}

Please perform a bibliomantic I Ching consultation to provide guidance on my creative work, following the approach described in Philip K. Dick's "The Man in the High Castle."

I seek wisdom on:
1. The creative direction and approach for this project
2. Potential obstacles or opportunities I should be aware of
3. The timing and energy surrounding this creative endeavor
4. How to align my creative process with natural patterns and flow

Please generate a hexagram using the traditional three-coin method and interpret its relevance to my creative journey."""


@mcp.prompt()
def general_guidance_prompt(question: str) -> str:
    """
    Generate a prompt for general life guidance.
    
    Creates a structured prompt for seeking I Ching wisdom
    on any life situation or decision.
    
    Args:
        question: The life question or situation requiring guidance
        
    Returns:
        Formatted prompt for general guidance
    """
    return f"""I have this question about my life path: {question}

Please consult the I Ching oracle using the bibliomantic divination method, as described in Philip K. Dick's "The Man in the High Castle", to provide ancient wisdom for my modern situation.

I'm looking for:
1. A relevant I Ching hexagram generated through traditional three-coin method
2. Understanding of how this ancient wisdom applies to my current situation
3. Guidance on the energies and patterns surrounding my question
4. Insight into the timing and approach for moving forward

Please bridge the ancient oracle's wisdom with my contemporary circumstances, helping me understand how timeless patterns apply to my specific situation."""


# Server statistics and health monitoring
@mcp.tool()
def server_statistics() -> str:
    """
    Get bibliomantic server statistics and system information.
    
    Provides information about the server's capabilities, the I Ching
    database, and divination system status.
    
    Returns:
        Complete server statistics and system information
    """
    stats = diviner.get_divination_statistics()
    
    return f"""📊 **Bibliomantic Server Statistics**

**System Status:** {stats['system_status'].title()}
**Total Hexagrams:** {stats['total_hexagrams']}
**Divination Method:** {stats['divination_method']}
**Randomness Source:** {stats['randomness_source']}
**Bibliomantic Approach:** {stats['bibliomantic_approach']}

**Server Capabilities:**
- I Ching Divination (traditional three-coin method)
- Bibliomantic Consultation (Philip K. Dick approach)
- Hexagram Details Lookup (all 64 hexagrams)
- Resource Access (hexagram database and individual entries)
- Prompt Templates (career, creative, and general guidance)

**Framework:** FastMCP (Official MCP Python SDK)
**Protocol Version:** MCP 2024-11-05
**Transport:** Standard I/O (stdio)

**Historical Context:**
This server implements the bibliomantic divination approach described in
Philip K. Dick's "The Man in the High Castle", combining ancient I Ching
wisdom with modern AI capabilities for guided decision-making."""


if __name__ == "__main__":
    # FastMCP handles all the complex server setup automatically
    logger.info("Starting Bibliomantic FastMCP Server")
    mcp.run()
