#!/usr/bin/env python3
"""
Comprehensive Manual Test Script for GitHub Agent
Tests all major operations with both real API calls and mock data fallbacks
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.github_agent import GitHubAgent
from backend.utils import load_config


def test_github_agent():
    """Comprehensive test suite for GitHub Agent"""
    
    print("=" * 60)
    print("GITHUB AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        # Use minimal config for testing
        config = {
            "github": {
                "token": os.getenv("GITHUB_TOKEN")
            }
        }
    
    # Initialize agent
    agent = GitHubAgent(config)
    
    # Test cases with various scenarios
    test_cases = [
        {
            "name": "Repository Commits - Popular Repo",
            "task": {
                "parameters": {
                    "operation": "get_commits",
                    "repository": "microsoft/vscode",
                    "limit": 5
                }
            }
        },
        {
            "name": "Repository Commits - With Date Filter",
            "task": {
                "parameters": {
                    "operation": "get_commits",
                    "repository": "facebook/react",
                    "limit": 3,
                    "since": (datetime.now() - timedelta(days=7)).isoformat()
                }
            }
        },
        {
            "name": "Repository Issues - Open Issues",
            "task": {
                "parameters": {
                    "operation": "get_issues",
                    "repository": "microsoft/vscode",
                    "state": "open",
                    "limit": 5
                }
            }
        },
        {
            "name": "Repository Issues - Closed Issues",
            "task": {
                "parameters": {
                    "operation": "get_issues",
                    "repository": "facebook/react",
                    "state": "closed",
                    "limit": 3
                }
            }
        },
        {
            "name": "Repository Information",
            "task": {
                "parameters": {
                    "operation": "get_repo_info",
                    "repository": "torvalds/linux"
                }
            }
        },
        {
            "name": "User Repositories",
            "task": {
                "parameters": {
                    "operation": "get_user_repos",
                    "username": "octocat",
                    "limit": 5,
                    "sort": "updated"
                }
            }
        },
        {
            "name": "Search Repositories - Python Projects",
            "task": {
                "parameters": {
                    "operation": "search_repositories",
                    "query": "python machine learning",
                    "limit": 5,
                    "sort": "stars"
                }
            }
        },
        {
            "name": "Search Repositories - JavaScript Frameworks",
            "task": {
                "parameters": {
                    "operation": "search_repositories",
                    "query": "javascript framework",
                    "limit": 3
                }
            }
        },
        {
            "name": "Invalid Repository Test",
            "task": {
                "parameters": {
                    "operation": "get_commits",
                    "repository": "nonexistent/repository123456"
                }
            }
        },
        {
            "name": "Missing Parameters Test",
            "task": {
                "parameters": {
                    "operation": "get_commits"
                    # Missing repository parameter
                }
            }
        },
        {
            "name": "Mock Data Fallback Test",
            "task": {
                "parameters": {
                    "operation": "unknown_operation",
                    "repository": "test/repo",
                    "max_results": 3
                }
            }
        }
    ]
    
    # Execute test cases
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] Testing: {test_case['name']}")
        print("-" * 50)
        
        try:
            result = agent.execute_task(test_case["task"])
            
            # Display results
            print(f"Success: {result.get('success', False)}")
            print(f"Content: {result.get('content', 'No content')}")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
            
            if result.get('data'):
                data = result['data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key in ['commits', 'issues', 'repositories']:
                            print(f"{key.title()}: {len(value) if isinstance(value, list) else value}")
                        elif key not in ['commits', 'issues', 'repositories']:  # Avoid printing large arrays
                            print(f"{key}: {value}")
            
            if result.get('mock_data'):
                print("⚠️  Using mock data (GitHub token not available or API failed)")
            
            results.append({
                "test": test_case['name'],
                "success": result.get('success', False),
                "mock_data": result.get('mock_data', False)
            })
            
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Test Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['success'])
    mock_data_tests = sum(1 for r in results if r.get('mock_data'))
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {len(results) - successful_tests}")
    print(f"Using Mock Data: {mock_data_tests}")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✓" if result['success'] else "✗"
        mock_indicator = " (MOCK)" if result.get('mock_data') else ""
        error_info = f" - {result.get('error', '')}" if result.get('error') else ""
        print(f"{status} {result['test']}{mock_indicator}{error_info}")
    
    # Configuration Check
    print("\n" + "=" * 60)
    print("CONFIGURATION STATUS")
    print("=" * 60)
    
    github_token = config.get("github", {}).get("token") or config.get("github_token")
    if github_token:
        print("✓ GitHub token configured")
        print("  - Real API calls will be attempted")
        print("  - Mock data used as fallback for errors")
    else:
        print("⚠️  GitHub token not configured")
        print("  - All operations will use mock data")
        print("  - To enable real API calls, set GITHUB_TOKEN environment variable")
        print("  - Or add 'github_token' to your config.yaml")
    
    print("\n" + "=" * 60)
    print("MANUAL TESTING GUIDE")
    print("=" * 60)
    print("""
To manually test different scenarios:

1. **With GitHub Token:**
   - Set environment variable: GITHUB_TOKEN=your_token_here
   - Or add to config.yaml: github_token: your_token_here
   - Real API calls will be made

2. **Without GitHub Token:**
   - All operations return mock data
   - Useful for testing error handling

3. **Test Different Repositories:**
   - Popular repos: microsoft/vscode, facebook/react, google/tensorflow
   - Your own repos: yourusername/yourrepo
   - Non-existent repos: test error handling

4. **Test Different Parameters:**
   - Date ranges for commits
   - Different issue states (open/closed)
   - Various search queries
   - Different user accounts

5. **Integration Testing:**
   - Test through main workflow: python quick_start.py
   - Test through Streamlit UI: streamlit run frontend/streamlit_app.py
   - Use natural language: "Show me recent commits from microsoft/vscode"
    """)


def test_specific_operation():
    """Test a specific GitHub operation interactively"""
    
    print("\n" + "=" * 60)
    print("INTERACTIVE GITHUB AGENT TEST")
    print("=" * 60)
    
    config = load_config("config/config.yaml")
    agent = GitHubAgent(config)
    
    print("Available operations:")
    print("1. get_commits - Get repository commits")
    print("2. get_issues - Get repository issues")
    print("3. get_repo_info - Get repository information")
    print("4. get_user_repos - Get user repositories")
    print("5. search_repositories - Search repositories")
    
    try:
        choice = input("\nEnter operation number (1-5): ").strip()
        
        operations = {
            "1": "get_commits",
            "2": "get_issues", 
            "3": "get_repo_info",
            "4": "get_user_repos",
            "5": "search_repositories"
        }
        
        if choice not in operations:
            print("Invalid choice")
            return
            
        operation = operations[choice]
        
        # Get parameters based on operation
        if operation in ["get_commits", "get_issues", "get_repo_info"]:
            repository = input("Enter repository (owner/repo): ").strip()
            if not repository:
                print("Repository is required")
                return
                
            task = {
                "parameters": {
                    "operation": operation,
                    "repository": repository,
                    "limit": 5
                }
            }
            
            if operation == "get_issues":
                state = input("Enter state (open/closed/all) [open]: ").strip() or "open"
                task["parameters"]["state"] = state
                
        elif operation == "get_user_repos":
            username = input("Enter username: ").strip()
            if not username:
                print("Username is required")
                return
                
            task = {
                "parameters": {
                    "operation": operation,
                    "username": username,
                    "limit": 5
                }
            }
            
        elif operation == "search_repositories":
            query = input("Enter search query: ").strip()
            if not query:
                print("Query is required")
                return
                
            task = {
                "parameters": {
                    "operation": operation,
                    "query": query,
                    "limit": 5
                }
            }
        
        # Execute the task
        print(f"\nExecuting {operation}...")
        result = agent.execute_task(task)
        
        print("\nResult:")
        print(f"Success: {result.get('success')}")
        print(f"Content: {result.get('content')}")
        
        if result.get('data'):
            print("\nData:")
            import json
            print(json.dumps(result['data'], indent=2, default=str))
            
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"Error during interactive test: {e}")


if __name__ == "__main__":
    try:
        # Run comprehensive test suite
        test_github_agent()
        
        # Optional: Run interactive test
        while True:
            choice = input("\nRun interactive test? (y/n): ").strip().lower()
            if choice == 'y':
                test_specific_operation()
                break
            elif choice == 'n':
                break
            else:
                print("Please enter 'y' or 'n'")
                
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
    except Exception as e:
        print(f"Testing failed: {e}")
        import traceback
        traceback.print_exc()
