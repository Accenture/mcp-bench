#!/usr/bin/env python3
"""
Bibliomantic MCP Server with Ethical Safeguards

This version includes ethical disclaimers in the actual MCP responses
to ensure end users understand the nature and limitations of the divination.
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

logger.info("Bibliomantic FastMCP Server initialized with ethical safeguards")

# Ethical disclaimer that appears in user-facing responses
ETHICAL_DISCLAIMER = """
⚠️ **Important Notice**: This divination uses cryptographically secure randomness, not supernatural guidance. It's designed for philosophical reflection and entertainment, following Philip K. Dick's literary exploration of meaning-making. Do not use for important financial, medical, legal, or safety decisions. Consult qualified professionals for serious life matters. The wisdom comes from your own reflection, not mystical prediction.
"""

BRIEF_DISCLAIMER = """
⚠️ *For reflection and entertainment only. Not for important life decisions.*
"""


@mcp.tool()
def i_ching_divination(query: Optional[str] = None) -> str:
    """
    Perform I Ching divination using traditional three-coin method.
    
    Generates a random hexagram with interpretation for philosophical guidance.
    Uses cryptographically secure randomness to simulate coin tosses.
    
    Args:
        query: Optional question or context for the divination
        
    Returns:
        Formatted hexagram reading with interpretation and ethical disclaimer
    """
    logger.info("Performing I Ching divination with ethical safeguards")
    
    result = diviner.perform_simple_divination()
    
    if result["success"]:
        response = f"""🎋 **I Ching Divination**

**Hexagram {result['hexagram_number']}: {result['hexagram_name']}**

{result['interpretation']}

**Method:** Traditional three-coin method using cryptographically secure randomness
**Purpose:** Philosophical reflection and contemplation

{ETHICAL_DISCLAIMER}"""

        if query:
            response += f"\n\n**Your Question:** {query}"
            response += f"\n\n**Guidance:** Consider how this hexagram's wisdom might offer perspective on your situation, while remembering this is a tool for reflection, not prediction."
        
        logger.info(f"Generated hexagram {result['hexagram_number']} - {result['hexagram_name']} with ethical disclaimer")
        return response
    else:
        error_msg = f"Divination failed: {result.get('error', 'Unknown error')}"
        logger.error(error_msg)
        return f"{error_msg}\n\n{BRIEF_DISCLAIMER}"


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
        Complete bibliomantic consultation with hexagram wisdom and ethical context
    """
    logger.info(f"Performing bibliomantic consultation with ethical safeguards")
    
    if not query.strip():
        return f"Please provide a question for bibliomantic consultation.\n\n{BRIEF_DISCLAIMER}"
    
    # Perform divination and augment query
    augmented_query, divination_info = diviner.divine_query_augmentation(query)
    
    if "error" in divination_info:
        error_msg = f"Consultation failed: {divination_info['error']}"
        logger.error(error_msg)
        return f"{error_msg}\n\n{BRIEF_DISCLAIMER}"
    
    response = f"""🔮 **Bibliomantic Consultation**

**Your Question:** {query}

**Oracle's Guidance - Hexagram {divination_info['hexagram_number']}: {divination_info['hexagram_name']}**

{divination_info['interpretation']}

**Bibliomantic Context:**
This consultation follows the approach described in Philip K. Dick's "The Man in the High Castle," where characters use the I Ching for reflection on complex decisions. The randomness is generated cryptographically, and any wisdom emerges from your own contemplation of the patterns and meanings.

**How to Use This Guidance:**
Consider how this ancient perspective might offer new ways of thinking about your situation. The value lies not in prediction, but in the fresh viewpoints that can emerge from engaging with different frameworks of understanding.

{ETHICAL_DISCLAIMER}"""
    
    logger.info(f"Completed bibliomantic consultation with hexagram {divination_info['hexagram_number']} and ethical context")
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
        Detailed hexagram information with educational context
    """
    logger.info(f"Retrieving details for hexagram {hexagram_number}")
    
    if not isinstance(hexagram_number, int) or not (1 <= hexagram_number <= 64):
        return f"Please provide a valid hexagram number between 1 and 64.\n\n{BRIEF_DISCLAIMER}"
    
    name, interpretation = iching.get_hexagram_by_number(hexagram_number)
    
    response = f"""📖 **Hexagram {hexagram_number}: {name}**

**Traditional Interpretation:**
{interpretation}

**Historical Context:**
The I Ching (Book of Changes) is an ancient Chinese divination text dating back over 3,000 years. Each hexagram represents patterns of change and philosophical insights rather than supernatural predictions.

**Educational Purpose:**
This information is provided for learning about ancient Chinese philosophy and wisdom traditions. The hexagrams offer frameworks for contemplating life's patterns and changes.

**Literary Connection:**
Philip K. Dick's "The Man in the High Castle" explores how people create meaning through engagement with such traditional systems, highlighting the human tendency to find significance in patterns.

{BRIEF_DISCLAIMER}"""
    
    logger.info(f"Retrieved details for hexagram {hexagram_number} - {name} with educational context")
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
        Hexagram data formatted for context use with educational framing
    """
    try:
        hexagram_num = int(number)
        if not (1 <= hexagram_num <= 64):
            return "Invalid hexagram number. Must be between 1 and 64."
        
        name, interpretation = iching.get_hexagram_by_number(hexagram_num)
        
        return f"""I Ching Hexagram {hexagram_num}: {name}

{interpretation}

Educational Context: This is from the ancient Chinese Book of Changes, a philosophical text used for contemplating patterns of change and decision-making. This information is provided for educational and reflective purposes.

Traditional Classification: One of 64 hexagrams in the I Ching
Historical Period: Ancient China (3000+ years old)
Purpose: Philosophical reflection and pattern recognition
Literary Context: Featured in Philip K. Dick's "The Man in the High Castle"

Note: This represents traditional wisdom for contemplation, not supernatural prediction."""
        
    except ValueError:
        return "Invalid hexagram number format. Please provide a number between 1 and 64."


@mcp.resource("iching://database")
def get_iching_database() -> str:
    """
    Access the complete I Ching database as a resource.
    
    Provides a summary of all 64 hexagrams for context loading,
    useful when AI models need to reference the complete system.
    
    Returns:
        Complete hexagram database summary with educational context
    """
    hexagram_list = []
    for i in range(1, 65):
        name, _ = iching.get_hexagram_by_number(i)
        hexagram_list.append(f"{i:2d}. {name}")
    
    return f"""I Ching Complete Database - 64 Hexagrams

Educational Overview: The Book of Changes (I Ching) contains 64 hexagrams representing philosophical insights into patterns of change and decision-making:

{chr(10).join(hexagram_list)}

System Information:
- Total Hexagrams: 64
- Historical Origin: Ancient China (Zhou Dynasty, ~1000 BCE)
- Philosophical Basis: Yin-Yang cosmology and patterns of change
- Modern Implementation: Cryptographically secure randomness simulation
- Literary Context: Philip K. Dick's "The Man in the High Castle"

Educational Purpose: This database provides traditional Chinese philosophical frameworks for contemplating life's changes and decisions. The wisdom lies in reflection and pattern recognition, not supernatural prediction.

Each hexagram consists of six lines (yin or yang) forming 2^6 = 64 possible combinations, representing different situations and approaches to change."""


@mcp.prompt()
def career_guidance_prompt(situation: str) -> str:
    """
    Generate a prompt for career guidance consultation.
    
    Creates a structured prompt for seeking I Ching guidance
    on career-related decisions and situations.
    
    Args:
        situation: Description of the career situation or decision
        
    Returns:
        Formatted prompt for career guidance with ethical context
    """
    return f"""I'm facing this career situation: {situation}

Please consult the I Ching oracle using the bibliomantic method from Philip K. Dick's "The Man in the High Castle" and provide guidance based on ancient wisdom patterns.

I understand this is for philosophical reflection and creative thinking, not prediction or professional advice. I'm looking for:

1. An I Ching divination relevant to my career situation
2. Interpretation of how the hexagram's patterns might apply to my circumstances  
3. New perspectives based on ancient wisdom frameworks
4. Understanding of timing and approach patterns for career decisions

Please generate a hexagram using the traditional three-coin method and help me explore how these ancient patterns might offer fresh perspectives on my modern career situation.

Important: I understand this is for reflection and contemplation only, and I will consult qualified career professionals for important decisions."""


@mcp.prompt()
def creative_guidance_prompt(project: str) -> str:
    """
    Generate a prompt for creative project guidance.
    
    Creates a structured prompt for seeking I Ching wisdom
    on creative endeavors and artistic decisions.
    
    Args:
        project: Description of the creative project or challenge
        
    Returns:
        Formatted prompt for creative guidance with educational context
    """
    return f"""I'm working on this creative project: {project}

Please perform a bibliomantic I Ching consultation to provide perspective on my creative work, following the literary approach described in Philip K. Dick's "The Man in the High Castle."

I seek ancient wisdom patterns for contemplating:
1. Creative direction and approach for this project
2. Potential patterns or opportunities I might consider
3. Timing and energy surrounding this creative endeavor
4. How to align my creative process with natural change patterns

Please generate a hexagram using the traditional three-coin method and interpret its relevance to my creative journey as a framework for reflection.

I understand this is for philosophical exploration and creative inspiration, not supernatural guidance or professional advice."""


@mcp.prompt()
def general_guidance_prompt(question: str) -> str:
    """
    Generate a prompt for general life guidance.
    
    Creates a structured prompt for seeking I Ching wisdom
    on any life situation or decision.
    
    Args:
        question: The life question or situation requiring guidance
        
    Returns:
        Formatted prompt for general guidance with clear ethical context
    """
    return f"""I have this question about my life path: {question}

Please consult the I Ching oracle using the bibliomantic divination method, as described in Philip K. Dick's "The Man in the High Castle", to provide ancient wisdom patterns for my modern situation.

I'm seeking philosophical perspectives through:
1. A relevant I Ching hexagram generated through traditional three-coin method
2. Understanding of how these ancient patterns might apply to my current situation
3. Insight into timing and approach patterns for moving forward
4. New frameworks for contemplating my circumstances

Please bridge the ancient oracle's wisdom patterns with my contemporary circumstances, helping me understand how timeless change patterns might offer fresh perspectives.

Important: I understand this is for philosophical reflection and pattern exploration only. For important life decisions, I will consult qualified professionals in relevant fields."""


# Server statistics and health monitoring
@mcp.tool()
def server_statistics() -> str:
    """
    Get bibliomantic server statistics and system information.
    
    Provides information about the server's capabilities, the I Ching
    database, and divination system status.
    
    Returns:
        Complete server statistics and system information with ethical context
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

**Ethical Framework:**
- All responses include appropriate disclaimers
- Educational and philosophical focus maintained
- No supernatural or predictive claims made
- Users guided toward professional consultation for important decisions

**Framework:** FastMCP (Official MCP Python SDK)
**Protocol Version:** MCP 2024-11-05
**Transport:** Standard I/O (stdio)

**Historical Context:**
This server implements the bibliomantic divination approach described in
Philip K. Dick's "The Man in the High Castle", combining ancient I Ching
wisdom patterns with modern AI capabilities for philosophical exploration
and creative reflection."""


if __name__ == "__main__":
    # FastMCP handles all the complex server setup automatically
    logger.info("Starting Bibliomantic FastMCP Server with ethical safeguards")
    mcp.run()
