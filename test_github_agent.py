#!/usr/bin/env python3
"""
Manual test script for GitHub Agent
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.github_agent import GitHubAgent


def test_github_agent():
    """Test GitHub Agent with various operations"""
    
    print("=== GITHUB AGENT MANUAL TEST ===\n")
    
    # Configuration (will use mock data if no token)
    config = {
        "github": {
            "token": os.getenv("GITHUB_TOKEN")  # Optional - will use mock data if not set
        }
    }
    
    # Initialize agent
    agent = GitHubAgent(config)
    
    print(f"GitHub Token Configured: {'Yes' if agent.github_token else 'No (using mock data)'}\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Get Repository Commits",
            "task": {
                "parameters": {
                    "operation": "get_commits",
                    "repository": "microsoft/vscode",
                    "limit": 5
                }
            }
        },
        {
            "name": "Get Repository Issues",
            "task": {
                "parameters": {
                    "operation": "get_issues",
                    "repository": "microsoft/vscode",
                    "state": "open",
                    "limit": 3
                }
            }
        },
        {
            "name": "Get Repository Info",
            "task": {
                "parameters": {
                    "operation": "get_repo_info",
                    "repository": "microsoft/vscode"
                }
            }
        },
        {
            "name": "Get User Repositories",
            "task": {
                "parameters": {
                    "operation": "get_user_repos",
                    "username": "microsoft",
                    "limit": 3
                }
            }
        },
        {
            "name": "Search Repositories",
            "task": {
                "parameters": {
                    "operation": "search_repositories",
                    "query": "python machine learning",
                    "limit": 3
                }
            }
        }
    ]
    
    # Execute tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * 50)
        
        try:
            result = agent.execute_task(test_case["task"])
            
            print(f"Success: {result['success']}")
            print(f"Content: {result['content']}")
            
            if result.get("data"):
                data = result["data"]
                if "commits" in data:
                    print(f"Commits found: {len(data['commits'])}")
                    for commit in data["commits"][:2]:  # Show first 2
                        print(f"  - {commit['sha']}: {commit['message'][:50]}...")
                
                elif "issues" in data:
                    print(f"Issues found: {len(data['issues'])}")
                    for issue in data["issues"][:2]:  # Show first 2
                        print(f"  - #{issue['number']}: {issue['title'][:50]}...")
                
                elif "repositories" in data:
                    print(f"Repositories found: {len(data['repositories'])}")
                    for repo in data["repositories"][:2]:  # Show first 2
                        print(f"  - {repo['full_name']}: {repo['stars']} stars")
                
                elif "name" in data:  # Repository info
                    print(f"Repository: {data['full_name']}")
                    print(f"Language: {data['language']}, Stars: {data['stars']}, Forks: {data['forks']}")
            
            if result.get("mock_data"):
                print("📝 Using mock data (no GitHub token configured)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*60 + "\n")


def test_specific_operation():
    """Test a specific GitHub operation with custom parameters"""
    
    print("=== CUSTOM GITHUB TEST ===\n")
    
    # Get user input
    print("Available operations:")
    print("1. get_commits")
    print("2. get_issues") 
    print("3. get_repo_info")
    print("4. get_user_repos")
    print("5. search_repositories")
    
    choice = input("\nSelect operation (1-5): ").strip()
    
    operations = {
        "1": "get_commits",
        "2": "get_issues",
        "3": "get_repo_info", 
        "4": "get_user_repos",
        "5": "search_repositories"
    }
    
    operation = operations.get(choice)
    if not operation:
        print("Invalid choice!")
        return
    
    # Get parameters based on operation
    parameters = {"operation": operation}
    
    if operation in ["get_commits", "get_issues", "get_repo_info"]:
        repo = input("Enter repository (owner/repo): ").strip()
        parameters["repository"] = repo
        
        if operation == "get_commits":
            limit = input("Enter limit (default 5): ").strip()
            parameters["limit"] = int(limit) if limit else 5
        
        elif operation == "get_issues":
            state = input("Enter state (open/closed, default open): ").strip()
            parameters["state"] = state if state else "open"
            limit = input("Enter limit (default 5): ").strip()
            parameters["limit"] = int(limit) if limit else 5
    
    elif operation == "get_user_repos":
        username = input("Enter username: ").strip()
        parameters["username"] = username
        limit = input("Enter limit (default 5): ").strip()
        parameters["limit"] = int(limit) if limit else 5
    
    elif operation == "search_repositories":
        query = input("Enter search query: ").strip()
        parameters["query"] = query
        limit = input("Enter limit (default 5): ").strip()
        parameters["limit"] = int(limit) if limit else 5
    
    # Execute test
    config = {"github": {"token": os.getenv("GITHUB_TOKEN")}}
    agent = GitHubAgent(config)
    
    task = {"parameters": parameters}
    result = agent.execute_task(task)
    
    print(f"\n=== RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Content: {result['content']}")
    
    if result.get("data"):
        print(f"\nData: {json.dumps(result['data'], indent=2)}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")


def test_with_environment_setup():
    """Test GitHub agent with environment variable setup"""
    
    print("=== ENVIRONMENT SETUP TEST ===\n")
    
    # Check environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_token:
        print("⚠️  GITHUB_TOKEN environment variable not set")
        print("\nTo test with real GitHub data:")
        print("1. Create a GitHub Personal Access Token:")
        print("   - Go to GitHub Settings > Developer settings > Personal access tokens")
        print("   - Generate a classic token with 'repo' scope")
        print("2. Set environment variable:")
        print("   - Windows: set GITHUB_TOKEN=your_token_here")
        print("   - Linux/Mac: export GITHUB_TOKEN=your_token_here")
        print("3. Re-run this test")
        print("\n📝 Will use mock data for now...\n")
    else:
        print(f"✅ GITHUB_TOKEN configured (length: {len(github_token)})")
        print("🌐 Will use real GitHub API data\n")
    
    # Test with environment config
    config = {}  # Empty config to test environment variable pickup
    agent = GitHubAgent(config)
    
    # Simple test
    task = {
        "parameters": {
            "operation": "get_repo_info",
            "repository": "octocat/Hello-World"
        }
    }
    
    result = agent.execute_task(task)
    print("Test Result:")
    print(f"Success: {result['success']}")
    print(f"Content: {result['content']}")
    
    if result.get("mock_data"):
        print("📝 Used mock data")
    else:
        print("🌐 Used real GitHub API")


if __name__ == "__main__":
    print("GitHub Agent Test Options:")
    print("1. Run all tests")
    print("2. Test specific operation")
    print("3. Test environment setup")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        test_github_agent()
    elif choice == "2":
        test_specific_operation()
    elif choice == "3":
        test_with_environment_setup()
    else:
        print("Invalid choice!")
