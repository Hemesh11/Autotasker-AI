"""
Quick test to verify GitHub agent repository parameter fix
"""

import os
import sys
import yaml
import logging
from dotenv import load_dotenv

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv("config/.env")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_github_agent_with_auto_repo():
    """Test GitHub agent with automatic repository detection"""
    
    print("\n" + "="*60)
    print("🧪 Testing GitHub Agent - Auto Repository Detection")
    print("="*60 + "\n")
    
    # Load config
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Import agents
    from agents.github_agent import GitHubAgent
    
    # Test 1: Check if GitHub token is configured
    print("1️⃣  Checking GitHub configuration...")
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token and github_token != "your_github_token_here":
        print(f"   ✅ GitHub token found: {github_token[:10]}...")
    else:
        print("   ⚠️  GitHub token not configured or using placeholder")
    
    # Test 2: Initialize GitHub agent
    print("\n2️⃣  Initializing GitHub agent...")
    github_agent = GitHubAgent(config)
    
    if github_agent.authenticated_user:
        username = github_agent.authenticated_user.get("login")
        print(f"   ✅ Authenticated as: {username}")
    else:
        print("   ⚠️  Not authenticated - will use config defaults")
    
    # Test 3: Get recent repository
    print("\n3️⃣  Finding default repository...")
    recent_repo = github_agent._get_user_recent_repo()
    
    if recent_repo:
        print(f"   ✅ Most recent repo: {recent_repo}")
    else:
        print("   ⚠️  Could not find recent repo")
        
        # Check config defaults
        github_config = config.get("github", {})
        default_owner = github_config.get("default_owner")
        default_repo = github_config.get("default_repo")
        
        if default_owner and default_repo and default_owner != "your-username":
            print(f"   📝 Config default: {default_owner}/{default_repo}")
        else:
            print("   ❌ No valid repository configured!")
    
    # Test 4: Test GitHub task with missing repository
    print("\n4️⃣  Testing GitHub agent with empty repository...")
    
    test_params = {
        "repository": "",
        "time_range": "1d",
        "max_results": 5
    }
    
    try:
        result = github_agent.get_repository_commits(test_params)
        
        if result.get("success"):
            print(f"   ✅ Successfully fetched commits!")
            print(f"   📦 Repository used: {result.get('data', {}).get('repository')}")
        else:
            error = result.get("error", "Unknown error")
            print(f"   ⚠️  Error: {error[:100]}")
            
            if "Repository parameter is required" in error:
                print("   💡 This is expected - the fix provides helpful error messages")
                
    except Exception as e:
        print(f"   ⚠️  Exception: {str(e)[:100]}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    if github_agent.authenticated_user and recent_repo:
        print("✅ GitHub is fully configured - auto-detection working!")
        print(f"   Using repository: {recent_repo}")
    elif github_token and github_token != "your_github_token_here":
        env_owner = os.getenv("GITHUB_DEFAULT_OWNER")
        env_repo = os.getenv("GITHUB_DEFAULT_REPO")
        
        if env_owner and env_repo and env_owner != "your-username":
            print("✅ GitHub configured via environment files")
            print(f"   Using repository: {env_owner}/{env_repo}")
        else:
            print("⚠️  GitHub token configured but repository defaults need setup")
    else:
        print("⚠️  GitHub needs configuration!")
    
    print("\n📝 To fix, edit config/.env and set:")
    print("   GITHUB_DEFAULT_OWNER=Hemesh11")
    print("   GITHUB_DEFAULT_REPO=Autotasker-AI")
    print("\n✨ After setting, the system will auto-detect your repository!")
    
    print("\n")

if __name__ == "__main__":
    test_github_agent_with_auto_repo()
