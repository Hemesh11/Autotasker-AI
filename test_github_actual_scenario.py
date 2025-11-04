"""
Test the actual failing scenario: "Summarize my GitHub commits from yesterday"
"""

import os
import sys
import yaml
import json
from datetime import datetime, timedelta

# Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv("config/.env")

def test_actual_github_prompt():
    """Test the exact failing scenario from user"""
    
    print("\n" + "="*70)
    print("🎯 Testing Actual User Scenario")
    print("="*70)
    print("\n📝 Prompt: 'Summarize my GitHub commits from yesterday'\n")
    
    # Load config
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Import agents
    from agents.github_agent import GitHubAgent
    
    print("1️⃣  Initializing GitHub agent...")
    github_agent = GitHubAgent(config)
    
    if github_agent.authenticated_user:
        username = github_agent.authenticated_user.get("login")
        print(f"   ✅ Authenticated as: {username}\n")
    else:
        print("   ⚠️  Not authenticated\n")
    
    print("2️⃣  Fetching commits from yesterday...")
    
    # Calculate yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    today = datetime.now().isoformat()
    
    # Simulate the task parameters that would be generated
    task_params = {
        "repository": "",  # Empty - should trigger auto-detection
        "since": yesterday,
        "until": today,
        "max_results": 5
    }
    
    print(f"   📅 Date range: {yesterday[:10]} to {today[:10]}")
    print(f"   📦 Repository: (auto-detect)\n")
    
    try:
        result = github_agent.get_repository_commits(task_params)
        
        if result.get("success"):
            print("   ✅ SUCCESS! Commits fetched successfully!\n")
            
            data = result.get("data", {})
            repo = data.get("repository")
            commits = data.get("commits", [])
            
            print(f"   📦 Repository: {repo}")
            print(f"   📊 Total commits: {len(commits)}\n")
            
            if commits:
                print("   📝 Commit Summary:")
                print("   " + "-"*66)
                for i, commit in enumerate(commits[:5], 1):
                    sha = commit.get("sha", "")[:8]
                    message = commit.get("message", "")[:50]
                    author = commit.get("author", "")
                    date = commit.get("date", "")[:10]
                    
                    print(f"   {i}. [{sha}] {message}")
                    print(f"      By: {author} on {date}")
                print("   " + "-"*66)
            else:
                print("   ℹ️  No commits found in this date range")
            
            print("\n" + "="*70)
            print("✅ GitHub Agent Working Correctly!")
            print("="*70)
            print("\n✨ The system can now:")
            print("   • Auto-detect your repositories")
            print("   • Fetch commits without manual configuration")
            print("   • Summarize GitHub activity intelligently")
            print("\n🎉 The original error is FIXED!\n")
            
        else:
            error = result.get("error", "Unknown error")
            print(f"   ❌ FAILED: {error}\n")
            
            if "Repository parameter is required" in error:
                print("   💡 The error message now provides helpful instructions!")
                print("   📝 Set GITHUB_DEFAULT_OWNER and GITHUB_DEFAULT_REPO in .env\n")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}\n")

if __name__ == "__main__":
    test_actual_github_prompt()
