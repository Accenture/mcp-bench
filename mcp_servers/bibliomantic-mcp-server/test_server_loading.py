#!/usr/bin/env python3
"""
Quick test to verify the enhanced I Ching server loads correctly
"""

import sys
import traceback
from pathlib import Path

def test_server_loading():
    """Test that the enhanced server can be imported and runs"""
    print("🔍 Testing Enhanced I Ching Server Loading")
    print("=" * 50)
    
    try:
        print("1. Testing bibliomantic_server import...")
        import bibliomantic_server
        
        if hasattr(bibliomantic_server, 'mcp'):
            print("✅ bibliomantic_server imported successfully")
            print(f"   Server name: {bibliomantic_server.mcp.name}")
            print("✅ MCP server object found and ready")
        else:
            print("❌ No mcp object found in bibliomantic_server")
            return False
            
    except Exception as e:
        print(f"❌ Failed to import bibliomantic_server: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("\n2. Testing enhanced core components...")
        from enhanced_iching_core import EnhancedIChing, IChingAdapter
        
        # Test engine creation
        engine = EnhancedIChing()
        print(f"✅ EnhancedIChing engine created with {len(engine.hexagrams)} hexagrams")
        
        # Test adapter
        adapter = IChingAdapter(use_enhanced=True)
        print("✅ IChingAdapter created successfully")
        
        # Test a simple divination
        result = adapter.generate_hexagram_by_coins()
        print(f"✅ Test divination: Hexagram {result[0]} - {result[1]}")
        
    except Exception as e:
        print(f"❌ Enhanced components failed: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Enhanced server is ready!")
    print("\nYour enhanced I Ching server should now work with Claude Desktop.")
    print("Just restart Claude Desktop to pick up the changes!")
    return True

if __name__ == "__main__":
    success = test_server_loading()
    sys.exit(0 if success else 1)
