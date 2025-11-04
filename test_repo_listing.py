"""
Quick test to show repository listing feature
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.github_agent import GitHubAgent
from backend.utils import load_config

def test_list_repos():
    """Test listing all repositories"""
    print("\n" + "="*70)
    print("🐙 Testing GitHub Repository Listing")
    print("="*70 + "\n")
    
    # Load config
    config = load_config("config/config.yaml")
    github_agent = GitHubAgent(config)
    
    # Test parameters for listing repos
    test_cases = [
        {
            "name": "List repos for authenticated user",
            "params": {
                "operation": "get_user_repos",
                "username": "Hemesh11",
                "max_results": 10
            }
        },
        {
            "name": "Get info about specific repo",
            "params": {
                "operation": "get_repo_info",
                "repository": "Hemesh11/Autotasker-AI"
            }
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*70}")
        print(f"Parameters: {test['params']}\n")
        
        # Execute the task
        task = {
            "type": "github",
            "parameters": test['params']
        }
        
        result = github_agent.execute_task(task)
        
        print(f"Status: {'✅ Success' if result.get('success') else '❌ Failed'}")
        print(f"Content: {result.get('content', 'N/A')}")
        
        if result.get('success'):
            data = result.get('data', {})
            
            # Show repository list
            if 'repositories' in data:
                repos = data['repositories']
                print(f"\n📊 Found {len(repos)} repositories:\n")
                for repo in repos[:5]:  # Show first 5
                    print(f"  📁 {repo['full_name']}")
                    print(f"     Language: {repo.get('language', 'None')}")
                    print(f"     ⭐ {repo['stars']} stars | 🍴 {repo['forks']} forks")
                    print(f"     Updated: {repo['updated_at']}")
                    print(f"     {repo['url']}")
                    print()
                
                if len(repos) > 5:
                    print(f"  ... and {len(repos) - 5} more repositories\n")
            
            # Show repo info
            elif 'name' in data:
                print(f"\n📊 Repository Details:\n")
                print(f"  Name: {data['full_name']}")
                print(f"  Description: {data.get('description', 'N/A')}")
                print(f"  Language: {data.get('language', 'N/A')}")
                print(f"  ⭐ Stars: {data['stars']}")
                print(f"  🍴 Forks: {data['forks']}")
                print(f"  🐛 Open Issues: {data['open_issues']}")
                print(f"  Created: {data['created_at']}")
                print(f"  Updated: {data['updated_at']}")
                print(f"  URL: {data['url']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*70}")
    print("🎉 Test Complete!")
    print("="*70)
    print("\n💡 Try these prompts in Streamlit:")
    print("   • List my GitHub repositories")
    print("   • Show all my repos")
    print("   • Get info about Hemesh11/Autotasker-AI")
    print("   • Summarize commits from Hemesh11/[YourRepo] from last week")
    print()

if __name__ == "__main__":
    test_list_repos()
