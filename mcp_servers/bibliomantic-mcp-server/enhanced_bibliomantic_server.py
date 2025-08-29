#!/usr/bin/env python3
"""
Enhanced Bibliomantic MCP Server
Drop-in replacement with dramatically improved content quality
Maintains 100% backward compatibility with existing MCP interface
"""

import logging
import sys
import os
from typing import Optional

# Import the official FastMCP framework
from mcp.server.fastmcp import FastMCP

# Import enhanced components (with fallback)
try:
    from enhanced_divination import EnhancedBiblioManticDiviner
    from enhanced_iching_core import IChingAdapter
    ENHANCED_MODE = True
except ImportError:
    # Fallback to original implementation
    from divination import BiblioManticDiviner as EnhancedBiblioManticDiviner
    from iching import IChing as IChingAdapter
    ENHANCED_MODE = False
    print("Running in compatibility mode", file=sys.stderr)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP(
    name="Enhanced Bibliomantic Oracle",
    dependencies=["secrets"]
)

# Initialize components
if ENHANCED_MODE:
    diviner = EnhancedBiblioManticDiviner(use_enhanced=True)
    iching = IChingAdapter(use_enhanced=True)
    logger.info("Enhanced Bibliomantic FastMCP Server initialized with full traditional content")
else:
    diviner = EnhancedBiblioManticDiviner()
    iching = IChingAdapter()
    logger.info("Bibliomantic FastMCP Server initialized in compatibility mode")

# Ethical disclaimers (unchanged)
ETHICAL_DISCLAIMER = """
⚠️ **Important Notice**: This divination uses cryptographically secure randomness, not supernatural guidance. It's designed for philosophical reflection and entertainment, following Philip K. Dick's literary exploration of meaning-making. Do not use for important financial, medical, legal, or safety decisions. Consult qualified professionals for serious life matters. The wisdom comes from your own reflection, not mystical prediction.
"""

BRIEF_DISCLAIMER = """
⚠️ *For reflection and entertainment only. Not for important life decisions.*
"""

@mcp.tool()
def i_ching_divination(query: Optional[str] = None) -> str:
    """
    Enhanced I Ching divination with traditional three-coin method and changing lines.
    MAINTAINS EXACT BACKWARD COMPATIBILITY while providing richer content.
    """
    logger.info("Performing enhanced I Ching divination")
    
    result = diviner.perform_simple_divination()
    
    if result["success"]:
        # Enhanced formatting while maintaining compatibility
        response = f"""🎋 **I Ching Divination**

**Hexagram {result['hexagram_number']}: {result['hexagram_name']}**

{result['interpretation']}

**Method:** Traditional three-coin method using cryptographically secure randomness"""

        # Add enhanced features if available
        if result.get("enhanced") and result.get("changing_lines"):
            response += f"\n**Changing Lines:** {', '.join(map(str, result['changing_lines']))}"
        
        response += f"\n**Purpose:** Philosophical reflection and contemplation\n\n{ETHICAL_DISCLAIMER}"

        if query:
            response += f"\n\n**Your Question:** {query}"
            if ENHANCED_MODE and hasattr(diviner, 'enhanced_engine') and diviner.enhanced_engine:
                # Add contextual guidance
                context = diviner.enhanced_engine.infer_context_from_query(query)
                contextual_guidance = diviner.enhanced_engine.get_contextual_interpretation(
                    result['hexagram_number'], context
                )
                response += f"\n\n**Contextual Guidance:** {contextual_guidance}"
            else:
                response += f"\n\n**Guidance:** Consider how this hexagram's wisdom might offer perspective on your situation."
        
        logger.info(f"Generated enhanced hexagram {result['hexagram_number']} - {result['hexagram_name']}")
        return response
    else:
        error_msg = f"Divination failed: {result.get('error', 'Unknown error')}"
        logger.error(error_msg)
        return f"{error_msg}\n\n{BRIEF_DISCLAIMER}"

@mcp.tool()
def bibliomantic_consultation(query: str) -> str:
    """
    Enhanced bibliomantic consultation with full traditional I Ching elements.
    DRAMATICALLY IMPROVED CONTENT while maintaining exact interface compatibility.
    """
    logger.info("Performing enhanced bibliomantic consultation")
    
    if not query.strip():
        return f"Please provide a question for bibliomantic consultation.\n\n{BRIEF_DISCLAIMER}"
    
    # Use enhanced consultation if available
    if ENHANCED_MODE and hasattr(diviner, 'perform_enhanced_consultation'):
        try:
            enhanced_result = diviner.perform_enhanced_consultation(query)
            
            # Add bibliomantic context and disclaimer
            enhanced_result += f"\n\n**How to Use This Guidance:**\n"
            enhanced_result += "Consider how this ancient perspective might offer new ways of thinking about your situation. "
            enhanced_result += "The value lies not in prediction, but in the fresh viewpoints that can emerge from engaging "
            enhanced_result += "with different frameworks of understanding.\n\n"
            enhanced_result += ETHICAL_DISCLAIMER
            
            logger.info("Completed enhanced bibliomantic consultation")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced consultation failed, falling back: {str(e)}")
    
    # Fallback to original method (backward compatibility)
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
    
    logger.info(f"Completed bibliomantic consultation with hexagram {divination_info['hexagram_number']}")
    return response

@mcp.tool()
def get_hexagram_details(hexagram_number: int) -> str:
    """
    Enhanced hexagram details with traditional Chinese names, Unicode symbols, and rich commentary.
    MAINTAINS BACKWARD COMPATIBILITY while dramatically improving content quality.
    """
    logger.info(f"Retrieving enhanced details for hexagram {hexagram_number}")
    
    if not isinstance(hexagram_number, int) or not (1 <= hexagram_number <= 64):
        return f"Please provide a valid hexagram number between 1 and 64.\n\n{BRIEF_DISCLAIMER}"
    
    # Use enhanced details if available
    if ENHANCED_MODE and hasattr(iching, 'enhanced_engine') and iching.enhanced_engine:
        hexagram = iching.enhanced_engine.hexagrams.get(hexagram_number)
        if hexagram:
            response = f"""📖 **Hexagram {hexagram.number}: {hexagram.english_name}**

*{hexagram.chinese_name} {hexagram.unicode_symbol}*

**Judgment:** {hexagram.judgment}

**Image:** {hexagram.image}

**Traditional Interpretation:**
{hexagram.general_meaning}"""

            # Add trigram information
            upper_trigram = iching.enhanced_engine.trigrams.get(hexagram.upper_trigram)
            lower_trigram = iching.enhanced_engine.trigrams.get(hexagram.lower_trigram)
            
            if upper_trigram and lower_trigram:
                response += f"""

**Trigram Composition:**
• Upper: {upper_trigram.name} ({upper_trigram.chinese_name} {upper_trigram.unicode_symbol}) - {upper_trigram.attribute}
• Lower: {lower_trigram.name} ({lower_trigram.chinese_name} {lower_trigram.unicode_symbol}) - {lower_trigram.attribute}"""

            # Add commentary if available
            if hexagram.commentary.get('wilhelm'):
                response += f"""

**Traditional Commentary:**
{hexagram.commentary['wilhelm']}"""

            response += f"""

**Historical Context:**
The I Ching (Book of Changes) is an ancient Chinese divination text dating back over 3,000 years. Each hexagram represents patterns of change and philosophical insights rather than supernatural predictions.

**Educational Purpose:**
This information is provided for learning about ancient Chinese philosophy and wisdom traditions. The hexagrams offer frameworks for contemplating life's patterns and changes.

**Literary Connection:**
Philip K. Dick's "The Man in the High Castle" explores how people create meaning through engagement with such traditional systems, highlighting the human tendency to find significance in patterns.

{BRIEF_DISCLAIMER}"""
            
            logger.info(f"Retrieved enhanced details for hexagram {hexagram_number} - {hexagram.english_name}")
            return response
    
    # Fallback to basic method
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
    
    logger.info(f"Retrieved basic details for hexagram {hexagram_number} - {name}")
    return response

# Resource handlers (enhanced but backward compatible)
@mcp.resource("hexagram://{number}")
def get_hexagram_resource(number: str) -> str:
    """Enhanced hexagram resource with traditional content"""
    try:
        hexagram_num = int(number)
        if not (1 <= hexagram_num <= 64):
            return "Invalid hexagram number. Must be between 1 and 64."
        
        if ENHANCED_MODE and hasattr(iching, 'enhanced_engine') and iching.enhanced_engine:
            hexagram = iching.enhanced_engine.hexagrams.get(hexagram_num)
            if hexagram:
                return f"""I Ching Hexagram {hexagram.number}: {hexagram.english_name}

Chinese Name: {hexagram.chinese_name} {hexagram.unicode_symbol}

Judgment: {hexagram.judgment}

Image: {hexagram.image}

General Meaning: {hexagram.general_meaning}

Educational Context: This is from the ancient Chinese Book of Changes, a philosophical text used for contemplating patterns of change and decision-making. This information is provided for educational and reflective purposes.

Traditional Classification: One of 64 hexagrams in the I Ching
Historical Period: Ancient China (3000+ years old)
Purpose: Philosophical reflection and pattern recognition
Literary Context: Featured in Philip K. Dick's "The Man in the High Castle"

Note: This represents traditional wisdom for contemplation, not supernatural prediction."""
        
        # Fallback
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
    """Enhanced I Ching database resource"""
    hexagram_list = []
    
    if ENHANCED_MODE and hasattr(iching, 'enhanced_engine') and iching.enhanced_engine:
        for i in range(1, 65):
            hexagram = iching.enhanced_engine.hexagrams.get(i)
            if hexagram:
                hexagram_list.append(f"{i:2d}. {hexagram.english_name} ({hexagram.chinese_name} {hexagram.unicode_symbol})")
            else:
                hexagram_list.append(f"{i:2d}. Hexagram {i}")
    else:
        for i in range(1, 65):
            name, _ = iching.get_hexagram_by_number(i)
            hexagram_list.append(f"{i:2d}. {name}")
    
    return f"""I Ching Complete Enhanced Database - 64 Hexagrams

Educational Overview: The Book of Changes (I Ching) contains 64 hexagrams representing philosophical insights into patterns of change and decision-making:

{chr(10).join(hexagram_list)}

Enhanced System Information:
- Total Hexagrams: 64 (with traditional Chinese names and Unicode symbols)
- Changing Lines: Full traditional interpretations included
- Trigram Analysis: Complete eight trigram system with attributes
- Contextual Interpretations: Career, relationships, creative, business, personal
- Commentary: Traditional and modern perspectives
- Historical Origin: Ancient China (Zhou Dynasty, ~1000 BCE)
- Philosophical Basis: Yin-Yang cosmology and patterns of change
- Modern Implementation: Cryptographically secure randomness simulation
- Literary Context: Philip K. Dick's "The Man in the High Castle"

Educational Purpose: This enhanced database provides authentic traditional Chinese philosophical frameworks for contemplating life's changes and decisions. The wisdom lies in reflection and pattern recognition, not supernatural prediction.

Each hexagram consists of six lines (yin or yang) forming 2^6 = 64 possible combinations, representing different situations and approaches to change."""

# Prompt templates (enhanced but backward compatible)
@mcp.prompt()
def career_guidance_prompt(situation: str) -> str:
    """Enhanced career guidance prompt"""
    return f"""I'm facing this career situation: {situation}

Please consult the enhanced I Ching oracle using the bibliomantic method from Philip K. Dick's "The Man in the High Castle" and provide guidance based on ancient wisdom patterns.

I understand this is for philosophical reflection and creative thinking, not prediction or professional advice. I'm looking for:

1. An I Ching divination with traditional Chinese names and symbols
2. Interpretation of how the hexagram's patterns might apply to my career circumstances  
3. Changing line guidance if applicable
4. Contextual career-specific interpretation
5. Trigram analysis for deeper symbolic understanding
6. New perspectives based on authentic traditional wisdom frameworks

Please generate a hexagram using the traditional three-coin method and help me explore how these ancient patterns might offer fresh perspectives on my modern career situation.

Important: I understand this is for reflection and contemplation only, and I will consult qualified career professionals for important decisions."""

@mcp.prompt()
def creative_guidance_prompt(project: str) -> str:
    """Enhanced creative guidance prompt"""
    return f"""I'm working on this creative project: {project}

Please perform an enhanced bibliomantic I Ching consultation to provide perspective on my creative work, following the literary approach described in Philip K. Dick's "The Man in the High Castle" but with full traditional elements.

I seek ancient wisdom patterns for contemplating:
1. Creative direction and approach for this project with traditional I Ching judgment and image
2. Changing line guidance for creative process timing
3. Trigram interactions and their creative symbolism
4. Context-specific creative interpretation
5. How to align my creative process with natural change patterns

Please generate a hexagram using the traditional three-coin method with Chinese names, Unicode symbols, and complete traditional commentary.

I understand this is for philosophical exploration and creative inspiration, not supernatural guidance or professional advice."""

@mcp.prompt()
def general_guidance_prompt(question: str) -> str:
    """Enhanced general guidance prompt"""
    return f"""I have this question about my life path: {question}

Please consult the enhanced I Ching oracle using the bibliomantic divination method, as described in Philip K. Dick's "The Man in the High Castle", to provide ancient wisdom patterns with full traditional elements for my modern situation.

I'm seeking philosophical perspectives through:
1. A relevant I Ching hexagram with traditional Chinese name and Unicode symbol
2. Complete traditional judgment and image interpretations
3. Changing line analysis and guidance
4. Trigram composition and symbolic meaning
5. Contextual interpretation based on my question's domain
6. Traditional commentary perspectives
7. Understanding of timing and approach patterns for moving forward

Please bridge the authentic oracle's wisdom patterns with my contemporary circumstances, using the complete traditional I Ching system to offer fresh perspectives.

Important: I understand this is for philosophical reflection and pattern exploration only. For important life decisions, I will consult qualified professionals in relevant fields."""

@mcp.tool()
def server_statistics() -> str:
    """Enhanced server statistics"""
    stats = diviner.get_divination_statistics()
    
    enhanced_features = ""
    if ENHANCED_MODE:
        enhanced_features = """
**Enhanced Features:**
- Traditional Chinese names and Unicode symbols
- Complete judgment and image texts  
- Changing line interpretations
- Trigram analysis and interactions
- Contextual interpretations (career, relationships, creative, business, personal)
- Traditional and modern commentary
- King Wen sequence binary mapping
- Context-aware query analysis"""
    
    return f"""📊 **Enhanced Bibliomantic Server Statistics**

**System Status:** {stats['system_status'].title()}
**Enhanced Mode:** {"Active" if ENHANCED_MODE else "Compatibility Mode"}
**Total Hexagrams:** {stats['total_hexagrams']}
**Divination Method:** {stats['divination_method']}
**Randomness Source:** {stats['randomness_source']}
**Bibliomantic Approach:** {stats['bibliomantic_approach']}{enhanced_features}

**Server Capabilities:**
- Enhanced I Ching Divination (traditional three-coin method with changing lines)
- Rich Bibliomantic Consultation (Philip K. Dick approach with full traditional elements)
- Complete Hexagram Details (all 64 with Chinese names and Unicode symbols)
- Enhanced Resource Access (hexagram database with traditional content)
- Contextual Prompt Templates (career, creative, and general guidance)

**Ethical Framework:**
- All responses include appropriate disclaimers
- Educational and philosophical focus maintained
- No supernatural or predictive claims made
- Users guided toward professional consultation for important decisions

**Framework:** FastMCP (Official MCP Python SDK)
**Protocol Version:** MCP 2024-11-05
**Transport:** Standard I/O (stdio)

**Historical Context:**
This enhanced server implements the bibliomantic divination approach described in
Philip K. Dick's "The Man in the High Castle", combining authentic traditional I Ching
wisdom with modern AI capabilities for deep philosophical exploration and creative reflection.

**Quality Enhancement:**
Traditional interpretations now include judgment, image, changing lines, trigram analysis,
contextual guidance, and multiple commentary perspectives for authentic I Ching experience."""

if __name__ == "__main__":
    logger.info("Starting Enhanced Bibliomantic FastMCP Server")
    mcp.run()
