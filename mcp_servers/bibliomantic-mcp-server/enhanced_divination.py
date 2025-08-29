"""
Enhanced Bibliomantic Divination System
Maintains backward compatibility while adding rich traditional content
"""

import logging
from typing import Optional, Tuple, Dict, Any
try:
    from .enhanced_iching_core import IChingAdapter, EnhancedIChing
except ImportError:
    from enhanced_iching_core import IChingAdapter, EnhancedIChing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBiblioManticDiviner:
    """Enhanced divination system with rich traditional content"""
    
    def __init__(self, use_enhanced: bool = True):
        self.iching = IChingAdapter(use_enhanced=use_enhanced)
        self.enhanced_engine = EnhancedIChing() if use_enhanced else None
        self.use_enhanced = use_enhanced
        logger.info("Enhanced BiblioMantic Divination System initialized")
    
    def divine_query_augmentation(self, original_query: str) -> Tuple[str, dict]:
        """Enhanced query augmentation with richer content"""
        try:
            if self.use_enhanced and self.enhanced_engine:
                # Use enhanced divination
                result = self.enhanced_engine.generate_enhanced_divination(original_query)
                hexagram = result['primary_hexagram']
                
                divination_info = {
                    "hexagram_number": hexagram.number,
                    "hexagram_name": hexagram.english_name,
                    "interpretation": hexagram.general_meaning,
                    "method": "enhanced_three_coin_traditional",
                    "bibliomantic_approach": "dick_high_castle_enhanced",
                    "changing_lines": result.get('changing_lines', []),
                    "contextual": True
                }
                
                # Create enhanced wisdom text with context awareness
                context = self.enhanced_engine.infer_context_from_query(original_query)
                contextual_interpretation = self.enhanced_engine.get_contextual_interpretation(
                    hexagram.number, context
                )
                
                wisdom_text = f"I Ching Hexagram {hexagram.number} - {hexagram.english_name} ({hexagram.chinese_name} {hexagram.unicode_symbol}): {contextual_interpretation}"
                
                # Add changing line guidance if present
                if result.get('changing_lines'):
                    line_guidance = self.enhanced_engine.get_changing_line_guidance(
                        hexagram.number, result['changing_lines']
                    )
                    wisdom_text += f" Changing lines: {'; '.join(line_guidance)}"
                
            else:
                # Fallback to basic divination
                hexagram_number, hexagram_name, interpretation = self.iching.generate_hexagram_by_coins()
                
                divination_info = {
                    "hexagram_number": hexagram_number,
                    "hexagram_name": hexagram_name,
                    "interpretation": interpretation,
                    "method": "three_coin_traditional",
                    "bibliomantic_approach": "dick_high_castle"
                }
                
                wisdom_text = self.iching.format_divination_text(
                    hexagram_number, hexagram_name, interpretation
                )
            
            # Augment the original query with enhanced wisdom
            augmented_query = self._integrate_wisdom_with_query(wisdom_text, original_query)
            
            logger.info(f"Enhanced divination performed: Hexagram {divination_info['hexagram_number']} - {divination_info['hexagram_name']}")
            
            return augmented_query, divination_info
            
        except Exception as e:
            logger.error(f"Enhanced divination failed: {str(e)}")
            return original_query, {"error": str(e), "fallback": True}
    
    def _integrate_wisdom_with_query(self, wisdom_text: str, original_query: str) -> str:
        """Enhanced wisdom integration"""
        integration_template = (
            "Consider this ancient wisdom as context for your response: {wisdom}\n\n"
            "Now, regarding the following question or request: {query}"
        )
        
        return integration_template.format(
            wisdom=wisdom_text,
            query=original_query
        )
    
    def perform_simple_divination(self) -> dict:
        """Enhanced simple divination with backward compatibility"""
        try:
            if self.use_enhanced and self.enhanced_engine:
                result = self.enhanced_engine.generate_enhanced_divination()
                hexagram = result['primary_hexagram']
                
                return {
                    "success": True,
                    "hexagram_number": hexagram.number,
                    "hexagram_name": hexagram.english_name,
                    "interpretation": hexagram.general_meaning,
                    "formatted_text": f"I Ching Hexagram {hexagram.number} - {hexagram.english_name}: {hexagram.general_meaning}",
                    "enhanced": True,
                    "changing_lines": result.get('changing_lines', [])
                }
            else:
                # Fallback to basic
                hexagram_number, hexagram_name, interpretation = self.iching.generate_hexagram_by_coins()
                
                return {
                    "success": True,
                    "hexagram_number": hexagram_number,
                    "hexagram_name": hexagram_name,
                    "interpretation": interpretation,
                    "formatted_text": self.iching.format_divination_text(
                        hexagram_number, hexagram_name, interpretation
                    ),
                    "enhanced": False
                }
                
        except Exception as e:
            logger.error(f"Enhanced simple divination failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_wisdom": "The path forward requires inner contemplation and patient observation."
            }
    
    def perform_enhanced_consultation(self, query: str) -> str:
        """New enhanced consultation method with full traditional content"""
        if not self.use_enhanced or not self.enhanced_engine:
            return "Enhanced mode not available"
        
        try:
            result = self.enhanced_engine.generate_enhanced_divination(query)
            return self._format_enhanced_consultation(result, query)
        except Exception as e:
            logger.error(f"Enhanced consultation failed: {str(e)}")
            return f"Enhanced consultation failed: {str(e)}"
    
    def _format_enhanced_consultation(self, divination_result: Dict[str, Any], query: str) -> str:
        """Format enhanced consultation with full traditional elements"""
        hexagram = divination_result['primary_hexagram']
        changing_lines = divination_result.get('changing_lines', [])
        resulting_hexagram = divination_result.get('resulting_hexagram')
        
        # Infer context for targeted guidance
        context = self.enhanced_engine.infer_context_from_query(query)
        
        result = f"🔮 **Enhanced Bibliomantic Consultation**\n\n"
        result += f"**Your Question:** {query}\n\n"
        
        # Enhanced hexagram presentation
        result += f"**Oracle's Guidance - Hexagram {hexagram.number}: {hexagram.english_name}**\n"
        result += f"*{hexagram.chinese_name} {hexagram.unicode_symbol}*\n\n"
        
        # Judgment and Image (core I Ching elements)
        result += f"**Judgment:** {hexagram.judgment}\n\n"
        result += f"**Image:** {hexagram.image}\n\n"
        
        # Context-specific guidance
        if context != "general" and context in hexagram.interpretations:
            result += f"**{context.title()} Guidance:** {hexagram.interpretations[context]}\n\n"
        else:
            result += f"**General Meaning:** {hexagram.general_meaning}\n\n"
        
        # Changing lines guidance if present
        if changing_lines:
            result += f"**Changing Lines:** {', '.join(map(str, changing_lines))}\n\n"
            line_guidance = self.enhanced_engine.get_changing_line_guidance(hexagram.number, changing_lines)
            for guidance in line_guidance:
                result += f"• {guidance}\n"
            result += "\n"
            
            if resulting_hexagram:
                result += f"**Resulting Situation - Hexagram {resulting_hexagram.number}: {resulting_hexagram.english_name}**\n"
                result += f"*{resulting_hexagram.chinese_name} {resulting_hexagram.unicode_symbol}*\n\n"
                result += f"{resulting_hexagram.general_meaning}\n\n"
        
        # Trigram analysis
        upper_trigram = self.enhanced_engine.trigrams.get(hexagram.upper_trigram)
        lower_trigram = self.enhanced_engine.trigrams.get(hexagram.lower_trigram)
        
        if upper_trigram and lower_trigram:
            result += f"**Trigram Analysis:**\n"
            result += f"• Upper: {upper_trigram.name} ({upper_trigram.chinese_name}) - {upper_trigram.attribute}\n"
            result += f"• Lower: {lower_trigram.name} ({lower_trigram.chinese_name}) - {lower_trigram.attribute}\n\n"
        
        # Commentary
        if hexagram.commentary.get('wilhelm'):
            result += f"**Traditional Commentary:** {hexagram.commentary['wilhelm']}\n\n"
        
        # Bibliomantic context (maintains existing format)
        result += "**Bibliomantic Context:**\n"
        result += "This enhanced consultation follows Philip K. Dick's approach in \"The Man in the High Castle,\" "
        result += "now enriched with traditional I Ching elements including changing lines, trigram analysis, "
        result += "and contextual interpretations for deeper philosophical reflection.\n\n"
        
        return result
    
    def validate_query(self, query: str) -> bool:
        """Validate that a query is suitable for bibliomantic augmentation"""
        if not query or not isinstance(query, str):
            return False
        
        cleaned_query = query.strip()
        
        if len(cleaned_query) < 3:
            return False
        
        return True
    
    def get_divination_statistics(self) -> dict:
        """Enhanced statistics"""
        base_stats = {
            "total_hexagrams": 64,
            "divination_method": "Enhanced Traditional I Ching three-coin method with changing lines",
            "randomness_source": "Python secrets module (cryptographically secure)",
            "bibliomantic_approach": "Philip K. Dick - The Man in the High Castle style (Enhanced)",
            "system_status": "operational"
        }
        
        if self.use_enhanced:
            base_stats.update({
                "enhanced_features": True,
                "changing_lines": True,
                "trigram_analysis": True,
                "contextual_interpretations": True,
                "traditional_commentaries": True,
                "unicode_symbols": True
            })
        
        return base_stats

# Backward compatibility functions
def augment_query_with_divination(query: str) -> Tuple[str, dict]:
    """Enhanced compatibility function"""
    diviner = EnhancedBiblioManticDiviner()
    return diviner.divine_query_augmentation(query)

def perform_divination() -> dict:
    """Enhanced compatibility function"""
    diviner = EnhancedBiblioManticDiviner()
    return diviner.perform_simple_divination()
