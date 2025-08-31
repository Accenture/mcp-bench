#!/usr/bin/env python3
"""
Test script to verify the Wikipedia MCP package build process.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Success: {description}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Wikipedia MCP Package Build Process")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("setup.py").exists() or not Path("pyproject.toml").exists():
        print("❌ Error: setup.py or pyproject.toml not found. Run this from the project root.")
        sys.exit(1)
    
    # Use system python3 instead of sys.executable
    python_cmd = "/usr/bin/python3"
    
    tests = [
        # Test package import
        ([python_cmd, "-c", "import wikipedia_mcp; print('Package import successful')"], 
         "Testing package import"),
        
        # Test setup.py check
        ([python_cmd, "setup.py", "check"], 
         "Validating setup.py configuration"),
        
        # Test if main module is accessible
        ([python_cmd, "-c", "from wikipedia_mcp.__main__ import main; print('Main module accessible')"], 
         "Testing main module access"),
    ]
    
    # Run tests
    passed = 0
    total = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your package is ready for publishing.")
        print("\nNext steps:")
        print("1. Follow the PUBLISHING_GUIDE.md for PyPI setup")
        print("2. Set up GitHub secrets for automated publishing")
        print("3. Use GitHub Actions to publish your package")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues before publishing.")
        sys.exit(1)

if __name__ == "__main__":
    main() 