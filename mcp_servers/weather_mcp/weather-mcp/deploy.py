#!/usr/bin/env python3
"""
Smithery Deployment Script for WeatherAPI MCP
"""

import os
import requests
import json
import zipfile
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
SMITHERY_BASE_URL = "https://api.smithery.ai"

def create_deployment_package():
    """Create a deployment package for Smithery"""
    print("📦 Creating deployment package...")
    
    # Files to include in the package
    files_to_include = [
        "server.py",
        "requirements.txt",
        "smithery.yaml",
        "README.md",
        ".env.example"
    ]
    
    # Create temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_name in files_to_include:
                file_path = Path(file_name)
                if file_path.exists():
                    zipf.write(file_path, file_name)
                    print(f"  ✅ Added: {file_name}")
                else:
                    print(f"  ⚠️  Missing: {file_name}")
        
        print(f"📦 Package created: {tmp_file.name}")
        return tmp_file.name

def deploy_to_smithery(package_path):
    """Deploy the MCP package to Smithery"""
    if not SMITHERY_API_KEY:
        print("❌ SMITHERY_API_KEY not found in environment variables")
        return False
    
    print("🚀 Deploying to Smithery...")
    
    headers = {
        "Authorization": f"Bearer {SMITHERY_API_KEY}",
    }
    
    # Upload the package
    with open(package_path, 'rb') as package_file:
        files = {
            'package': ('weather-mcp.zip', package_file, 'application/zip')
        }
        
        data = {
            'name': 'weather-api-mcp',
            'version': '1.0.0',
            'description': 'WeatherAPI MCP Server for current weather and forecasts'
        }
        
        try:
            response = requests.post(
                f"{SMITHERY_BASE_URL}/v1/mcps",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✅ Successfully deployed to Smithery!")
                print(f"   📍 MCP ID: {result.get('id', 'N/A')}")
                print(f"   🔗 URL: {result.get('url', 'N/A')}")
                return True
            else:
                print(f"❌ Deployment failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error during deployment: {e}")
            return False

def validate_environment():
    """Validate that all required environment variables are set"""
    print("🔧 Validating environment...")
    
    required_vars = {
        "WEATHER_API_KEY": "WeatherAPI key",
        "SMITHERY_API_KEY": "Smithery API key"
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:10]}...")
        else:
            print(f"  ❌ {var}: Missing")
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    return True

def main():
    """Main deployment function"""
    print("🌤️  WeatherAPI MCP Smithery Deployment")
    print("=" * 50)
    
    # Validate environment
    if not validate_environment():
        print("\n💡 Please set the missing environment variables in your .env file")
        return
    
    # Create deployment package
    package_path = create_deployment_package()
    
    try:
        # Deploy to Smithery
        if deploy_to_smithery(package_path):
            print("\n🎉 Deployment completed successfully!")
            print("\n📋 Next steps:")
            print("1. Check your Smithery dashboard")
            print("2. Configure the MCP with your WeatherAPI key")
            print("3. Test the weather tools")
        else:
            print("\n❌ Deployment failed. Please check the error messages above.")
    
    finally:
        # Clean up temporary file
        if os.path.exists(package_path):
            os.unlink(package_path)
            print(f"🧹 Cleaned up temporary file: {package_path}")

if __name__ == "__main__":
    main()
