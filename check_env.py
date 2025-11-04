"""
Quick test to verify environment variables are loaded correctly
Run this BEFORE restarting Streamlit to verify .env is accessible
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("🔍 Environment Variable Check")
print("=" * 70)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Check if .env file exists
env_path = project_root / "config" / ".env"
print(f"\n📁 Checking .env file: {env_path}")
print(f"   Exists: {env_path.exists()}")

if env_path.exists():
    print(f"   Size: {env_path.stat().st_size} bytes")
    
    # Load dotenv
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    print("\n✅ Environment variables loaded successfully!")
    
    # Check critical GitHub variables
    print("\n🐙 GitHub Configuration:")
    github_token = os.getenv("GITHUB_TOKEN")
    github_owner = os.getenv("GITHUB_DEFAULT_OWNER")
    github_repo = os.getenv("GITHUB_DEFAULT_REPO")
    
    if github_token:
        print(f"   GITHUB_TOKEN: {github_token[:10]}...{github_token[-4:]} ✅")
    else:
        print(f"   GITHUB_TOKEN: ❌ NOT SET")
    
    if github_owner:
        print(f"   GITHUB_DEFAULT_OWNER: {github_owner} ✅")
    else:
        print(f"   GITHUB_DEFAULT_OWNER: ❌ NOT SET")
    
    if github_repo:
        print(f"   GITHUB_DEFAULT_REPO: {github_repo} ✅")
    else:
        print(f"   GITHUB_DEFAULT_REPO: ❌ NOT SET")
    
    # Check other important variables
    print("\n📧 Other Configuration:")
    print(f"   GMAIL_ADDRESS: {os.getenv('GMAIL_ADDRESS', '❌ NOT SET')}")
    print(f"   AWS_REGION: {os.getenv('AWS_REGION', '❌ NOT SET')}")
    print(f"   OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY', '❌ NOT SET')[:10]}..." if os.getenv('OPENROUTER_API_KEY') else '   OPENROUTER_API_KEY: ❌ NOT SET')
    
    print("\n" + "=" * 70)
    
    if github_token and github_owner and github_repo:
        print("🎉 ALL GITHUB VARIABLES ARE SET - Ready to go!")
    else:
        print("⚠️  MISSING GITHUB VARIABLES - GitHub features will fail")
    
    print("=" * 70)
    print("\n💡 Next step: Restart Streamlit using:")
    print("   .\\restart_streamlit_with_env.ps1")
    print("   OR")
    print("   restart_streamlit_with_env.bat")
    
else:
    print("\n❌ ERROR: .env file not found!")
    print(f"   Expected location: {env_path}")
    print("\n💡 Please ensure config/.env exists with GitHub credentials")
