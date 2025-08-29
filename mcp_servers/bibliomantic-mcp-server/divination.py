"""
Bibliomantic Divination System

This module implements the core divination logic that integrates I Ching wisdom
with user queries, following the bibliomantic approach described in Philip K. Dick's
"The Man in the High Castle".
"""

import logging
from typing import Optional, Tuple
try:
    from .iching import IChing, divine_hexagram
except ImportError:
    from iching import IChing, divine_hexagram

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BiblioManticDiviner:
    """
    Bibliomantic divination system that augments queries with I Ching wisdom.
    
    This class provides the core functionality for integrating random I Ching
    hexagrams with user queries, creating the bibliomantic effect described
    in Philip K. Dick's work.
    """
    
    def __init__(self):
        """Initialize the divination system with I Ching database."""
        self.iching = IChing()
        logger.info("BiblioMantic Divination System initialized")
    
    def divine_query_augmentation(self, original_query: str) -> Tuple[str, dict]:
        """
        Augment a user query with bibliomantic I Ching wisdom.
        
        This method performs the core bibliomantic operation:
        1. Generate random hexagram through coin divination
        2. Extract wisdom text from the hexagram
        3. Integrate this wisdom with the original query
        4. Return augmented query with divination metadata
        
        Args:
            original_query: The user's original question or request
            
        Returns:
            Tuple containing:
            - augmented_query: Original query prefaced with I Ching wisdom
            - divination_info: Metadata about the divination performed
        """
        try:
            # Perform I Ching divination
            hexagram_number, hexagram_name, interpretation = self.iching.generate_hexagram_by_coins()
            
            # Create divination metadata for transparency
            divination_info = {
                "hexagram_number": hexagram_number,
                "hexagram_name": hexagram_name,
                "interpretation": interpretation,
                "method": "three_coin_traditional",
                "bibliomantic_approach": "dick_high_castle"
            }
            
            # Format the I Ching wisdom for integration
            wisdom_text = self.iching.format_divination_text(
                hexagram_number, hexagram_name, interpretation
            )
            
            # Augment the original query with bibliomantic wisdom
            augmented_query = self._integrate_wisdom_with_query(wisdom_text, original_query)
            
            logger.info(f"Divination performed: Hexagram {hexagram_number} - {hexagram_name}")
            
            return augmented_query, divination_info
            
        except Exception as e:
            logger.error(f"Divination failed: {str(e)}")
            # Graceful degradation: return original query if divination fails
            return original_query, {"error": str(e), "fallback": True}
    
    def _integrate_wisdom_with_query(self, wisdom_text: str, original_query: str) -> str:
        """
        Integrate I Ching wisdom with the user's original query.
        
        This method creates the bibliomantic integration by prefacing the user's
        query with relevant I Ching wisdom, allowing Claude to naturally incorporate
        the divinatory guidance into its response.
        
        Args:
            wisdom_text: Formatted I Ching hexagram wisdom
            original_query: The user's original question
            
        Returns:
            Augmented query string combining wisdom and original question
        """
        integration_template = (
            "Consider this ancient wisdom as context for your response: {wisdom}\n\n"
            "Now, regarding the following question or request: {query}"
        )
        
        return integration_template.format(
            wisdom=wisdom_text,
            query=original_query
        )
    
    def perform_simple_divination(self) -> dict:
        """
        Perform a standalone divination without query integration.
        
        Useful for testing the divination system or providing pure I Ching
        consultations without Claude integration.
        
        Returns:
            Dictionary containing complete divination information
        """
        try:
            hexagram_number, hexagram_name, interpretation = self.iching.generate_hexagram_by_coins()
            
            return {
                "success": True,
                "hexagram_number": hexagram_number,
                "hexagram_name": hexagram_name,
                "interpretation": interpretation,
                "formatted_text": self.iching.format_divination_text(
                    hexagram_number, hexagram_name, interpretation
                )
            }
            
        except Exception as e:
            logger.error(f"Simple divination failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_wisdom": "The path forward requires inner contemplation and patient observation."
            }
    
    def validate_query(self, query: str) -> bool:
        """
        Validate that a query is suitable for bibliomantic augmentation.
        
        Args:
            query: The user query to validate
            
        Returns:
            True if query is valid, False otherwise
        """
        if not query or not isinstance(query, str):
            return False
        
        # Remove excessive whitespace
        cleaned_query = query.strip()
        
        # Check for minimum meaningful content
        if len(cleaned_query) < 3:
            return False
        
        # Additional validation rules can be added here
        # For example, filtering out inappropriate content
        
        return True
    
    def get_divination_statistics(self) -> dict:
        """
        Provide statistics about the divination system.
        
        Returns:
            Dictionary containing system information and statistics
        """
        return {
            "total_hexagrams": len(self.iching.hexagrams),
            "divination_method": "Traditional I Ching three-coin method",
            "randomness_source": "Python secrets module (cryptographically secure)",
            "bibliomantic_approach": "Philip K. Dick - The Man in the High Castle style",
            "system_status": "operational"
        }


# Module-level convenience functions
def augment_query_with_divination(query: str) -> Tuple[str, dict]:
    """
    Convenience function to augment a query with I Ching divination.
    
    Args:
        query: Original user query
        
    Returns:
        Tuple of (augmented_query, divination_info)
    """
    diviner = BiblioManticDiviner()
    return diviner.divine_query_augmentation(query)


def perform_divination() -> dict:
    """
    Convenience function to perform a standalone divination.
    
    Returns:
        Dictionary containing divination results
    """
    diviner = BiblioManticDiviner()
    return diviner.perform_simple_divination()


if __name__ == "__main__":
    # Demonstration of the bibliomantic divination system
    print("Bibliomantic Divination System Demo")
    print("=" * 45)
    
    diviner = BiblioManticDiviner()
    
    # Test query augmentation
    test_query = "How should I approach my new project?"
    augmented, info = diviner.divine_query_augmentation(test_query)
    
    print(f"\nOriginal Query: {test_query}")
    print(f"\nAugmented Query:\n{augmented}")
    print(f"\nDivination Info: {info}")
    
    # Test standalone divination
    print("\n" + "=" * 45)
    print("Standalone Divination:")
    divination_result = diviner.perform_simple_divination()
    print(divination_result)
    
    # System statistics
    print("\n" + "=" * 45)
    print("System Statistics:")
    stats = diviner.get_divination_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
