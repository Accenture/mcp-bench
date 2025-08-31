#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced I Ching System
Validates backward compatibility and enhanced features
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from enhanced_iching_core import IChingAdapter, EnhancedIChing
    from enhanced_divination import EnhancedBiblioManticDiviner
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

# Always test original implementation
from iching import IChing
from divination import BiblioManticDiviner

class TestBackwardCompatibility:
    """Ensure zero breaking changes to existing functionality"""
    
    def test_original_iching_interface(self):
        """Test original IChing interface unchanged"""
        iching = IChing()
        
        # Test coin generation
        number, name, interpretation = iching.generate_hexagram_by_coins()
        assert isinstance(number, int)
        assert 1 <= number <= 64
        assert isinstance(name, str)
        assert len(name) > 0
        assert isinstance(interpretation, str)
        assert len(interpretation) > 10
        
        # Test hexagram lookup
        lookup_name, lookup_interp = iching.get_hexagram_by_number(1)
        assert lookup_name == "The Creative"
        assert "creative force" in lookup_interp.lower()
        
        # Test formatting
        formatted = iching.format_divination_text(1, "The Creative", "Test interpretation")
        assert "I Ching Hexagram 1 - The Creative: Test interpretation" == formatted
    
    def test_original_diviner_interface(self):
        """Test original BiblioManticDiviner interface unchanged"""
        diviner = BiblioManticDiviner()
        
        # Test simple divination
        result = diviner.perform_simple_divination()
        assert result["success"] is True
        assert "hexagram_number" in result
        assert "hexagram_name" in result
        assert "interpretation" in result
        assert "formatted_text" in result
        
        # Test query augmentation
        query = "Test query"
        augmented, info = diviner.divine_query_augmentation(query)
        assert query in augmented
        assert "hexagram_number" in info
        assert "hexagram_name" in info
        assert "interpretation" in info
        
        # Test statistics
        stats = diviner.get_divination_statistics()
        assert stats["total_hexagrams"] == 64
        assert stats["system_status"] == "operational"

@pytest.mark.skipif(not ENHANCED_AVAILABLE, reason="Enhanced features not available")
class TestEnhancedFeatures:
    """Test enhanced functionality"""
    
    def test_enhanced_iching_creation(self):
        """Test enhanced IChing engine creation"""
        enhanced = EnhancedIChing()
        assert len(enhanced.hexagrams) == 64
        assert len(enhanced.trigrams) == 8
        assert len(enhanced.king_wen_sequence) == 64
    
    def test_enhanced_hexagram_quality(self):
        """Test enhanced hexagram content quality"""
        enhanced = EnhancedIChing()
        
        # Test hexagram 1 (fully enhanced)
        hex1 = enhanced.hexagrams[1]
        assert hex1.chinese_name == "乾"
        assert hex1.english_name == "The Creative"
        assert hex1.unicode_symbol == "☰☰"
        assert "perseverance" in hex1.judgment.lower()
        assert "heaven" in hex1.image.lower()
        assert len(hex1.interpretations) >= 5
        assert len(hex1.changing_lines) == 6
        assert len(hex1.commentary) >= 2
    
    def test_adapter_backward_compatibility(self):
        """Test adapter maintains exact interface"""
        adapter = IChingAdapter(use_enhanced=True)
        
        # Test original methods work
        number, name, interpretation = adapter.generate_hexagram_by_coins()
        assert isinstance(number, int)
        assert 1 <= number <= 64
        assert isinstance(name, str)
        assert isinstance(interpretation, str)
        
        # Test lookup
        lookup_name, lookup_interp = adapter.get_hexagram_by_number(1)
        assert isinstance(lookup_name, str)
        assert isinstance(lookup_interp, str)
        
        # Test formatting
        formatted = adapter.format_divination_text(1, "Test", "Test interp")
        assert "I Ching Hexagram 1 - Test: Test interp" == formatted
    
    def test_enhanced_diviner_compatibility(self):
        """Test enhanced diviner maintains compatibility"""
        diviner = EnhancedBiblioManticDiviner(use_enhanced=True)
        
        # Test original interface
        result = diviner.perform_simple_divination()
        assert result["success"] is True
        assert "hexagram_number" in result
        assert "hexagram_name" in result
        assert "interpretation" in result
        
        # Test enhanced features
        if result.get("enhanced"):
            assert "changing_lines" in result

class TestPerformance:
    """Test performance requirements"""
    
    def test_divination_speed(self):
        """Test divination performance"""
        import time
        
        # Test original performance
        diviner = BiblioManticDiviner()
        start = time.time()
        for _ in range(10):
            diviner.perform_simple_divination()
        original_time = time.time() - start
        
        # Test enhanced performance (if available)
        if ENHANCED_AVAILABLE:
            enhanced_diviner = EnhancedBiblioManticDiviner(use_enhanced=True)
            start = time.time()
            for _ in range(10):
                enhanced_diviner.perform_simple_divination()
            enhanced_time = time.time() - start
            
            # Enhanced should not be more than 2x slower
            assert enhanced_time < original_time * 2
        
        # Both should complete quickly
        assert original_time < 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
