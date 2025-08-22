"""
Demo: GitHub Agent JSON to User-Friendly Summary Transformation
Shows how raw GitHub API data gets converted to readable summaries
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.github_agent import GitHubAgent
from agents.summarizer_agent import SummarizerAgent
from backend.utils import load_config


def demo_github_summarization():
    """Demonstrate the complete flow from GitHub API to user summary"""
    
    print("🚀 GitHub Agent to Summary Demo")
    print("=" * 50)
    
    # Load configuration
    config = load_config("config/config.yaml")
    
    # Initialize agents
    github_agent = GitHubAgent(config)
    summarizer_agent = SummarizerAgent(config)
    
    # Example 1: Recent commits for a repository
    print("\n📝 DEMO 1: Repository Commits Summary")
    print("-" * 40)
    
    commit_task = {
        "type": "github",
        "operation": "get_commits",
        "parameters": {
            "owner": "microsoft",
            "repo": "vscode",
            "limit": 5
        }
    }
    
    print(f"🔍 Fetching commits for {commit_task['parameters']['owner']}/{commit_task['parameters']['repo']}...")
    
    # Step 1: Get raw JSON data from GitHub agent
    raw_result = github_agent.execute_task(commit_task)
    
    print("\n📊 Raw GitHub Agent Output (JSON):")
    print(json.dumps(raw_result, indent=2)[:500] + "..." if len(json.dumps(raw_result, indent=2)) > 500 else json.dumps(raw_result, indent=2))
    
    # Step 2: Transform to user-friendly summary
    if raw_result.get("success") and raw_result.get("data"):
        summary_task = {
            "type": "summarize",
            "content_type": "github",
            "content": raw_result["data"]
        }
        
        print("\n🤖 Generating Human-Readable Summary...")
        summary_result = summarizer_agent.execute_task(summary_task)
        
        print("\n📝 User-Friendly Summary:")
        print("=" * 30)
        print(summary_result.get("content", "No summary generated"))
        print("=" * 30)
    
    # Example 2: User repositories
    print("\n\n📁 DEMO 2: User Repositories Summary")
    print("-" * 40)
    
    repos_task = {
        "type": "github",
        "operation": "get_user_repos",
        "parameters": {
            "username": "torvalds",
            "limit": 3
        }
    }
    
    print(f"🔍 Fetching repositories for user: {repos_task['parameters']['username']}...")
    
    # Step 1: Get raw JSON data
    raw_result = github_agent.execute_task(repos_task)
    
    print("\n📊 Raw GitHub Agent Output (JSON):")
    print(json.dumps(raw_result, indent=2)[:500] + "..." if len(json.dumps(raw_result, indent=2)) > 500 else json.dumps(raw_result, indent=2))
    
    # Step 2: Transform to user-friendly summary
    if raw_result.get("success") and raw_result.get("data"):
        summary_task = {
            "type": "summarize",
            "content_type": "github",
            "content": raw_result["data"]
        }
        
        print("\n🤖 Generating Human-Readable Summary...")
        summary_result = summarizer_agent.execute_task(summary_task)
        
        print("\n📝 User-Friendly Summary:")
        print("=" * 30)
        print(summary_result.get("content", "No summary generated"))
        print("=" * 30)
    
    # Example 3: Repository search
    print("\n\n🔎 DEMO 3: Repository Search Summary")
    print("-" * 40)
    
    search_task = {
        "type": "github",
        "operation": "search_repositories",
        "parameters": {
            "query": "python machine learning",
            "limit": 3
        }
    }
    
    print(f"🔍 Searching repositories with query: '{search_task['parameters']['query']}'...")
    
    # Step 1: Get raw JSON data
    raw_result = github_agent.execute_task(search_task)
    
    print("\n📊 Raw GitHub Agent Output (JSON):")
    print(json.dumps(raw_result, indent=2)[:500] + "..." if len(json.dumps(raw_result, indent=2)) > 500 else json.dumps(raw_result, indent=2))
    
    # Step 2: Transform to user-friendly summary
    if raw_result.get("success") and raw_result.get("data"):
        summary_task = {
            "type": "summarize",
            "content_type": "github",
            "content": raw_result["data"]
        }
        
        print("\n🤖 Generating Human-Readable Summary...")
        summary_result = summarizer_agent.execute_task(summary_task)
        
        print("\n📝 User-Friendly Summary:")
        print("=" * 30)
        print(summary_result.get("content", "No summary generated"))
        print("=" * 30)


def demo_workflow_integration():
    """Show how this works in the complete AutoTasker workflow"""
    
    print("\n\n🔄 WORKFLOW INTEGRATION DEMO")
    print("=" * 50)
    
    print("In the full AutoTasker AI workflow:")
    print()
    print("1. 📝 User Input: 'Show me recent commits for microsoft/vscode'")
    print("2. 🧠 Planner Agent: Converts to structured task plan")
    print("3. 🐙 GitHub Agent: Fetches raw JSON data from GitHub API")
    print("4. 🤖 Summarizer Agent: Converts JSON to human-readable summary")
    print("5. 📧 Email Agent: Sends summary to user")
    print("6. 🖥️  Frontend: Displays summary in Streamlit UI")
    print()
    print("The user never sees the raw JSON - only the final summary!")


def demo_frontend_display():
    """Show how summaries appear in the Streamlit frontend"""
    
    print("\n\n🖥️  FRONTEND DISPLAY DEMO")
    print("=" * 50)
    
    print("In the Streamlit frontend, users see:")
    print()
    print("✅ Task executed successfully!")
    print()
    print("📋 Generated Task Plan")
    print("Intent: github_analysis")
    print("Total Tasks: 1")
    print("Schedule: once")
    print()
    print("📊 Execution Results")
    print("GitHub Analysis:")
    print("┌─────────────────────────────────────────────┐")
    print("│ Recent development activity shows:          │")
    print("│                                             │")
    print("│ • 5 commits from 3 different contributors  │")
    print("│ • Main focus on bug fixes and performance  │")
    print("│ • Most active contributor: John Doe        │")
    print("│ • Latest changes include UI improvements    │")
    print("│                                             │")
    print("│ Notable commits:                            │")
    print("│ - Fix memory leak in extension host         │")
    print("│ - Improve syntax highlighting performance   │")
    print("│ - Add support for new language features     │")
    print("└─────────────────────────────────────────────┘")
    print()
    print("Instead of seeing raw JSON like:")
    print('{"commit": {"sha": "abc123", "message": "Fix bug"...}}')


if __name__ == "__main__":
    try:
        demo_github_summarization()
        demo_workflow_integration()
        demo_frontend_display()
        
        print("\n\n🎉 Demo completed!")
        print("This shows how GitHub API JSON gets transformed into user-friendly summaries.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nNote: This demo requires:")
        print("- GITHUB_TOKEN in .env file")
        print("- OpenAI or OpenRouter API key for summarization")
        print("- Internet connection for GitHub API calls")
