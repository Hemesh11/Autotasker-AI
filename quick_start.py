#!/usr/bin/env python3
"""
Quick Start Script for AutoTasker AI

This script helps you get started quickly by checking your configuration
and testing the setup with OpenRouter.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from backend.utils import load_config
from backend.llm_factory import create_llm_client, get_chat_completion


def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    # Check .env file exists
    env_file = project_root / "config" / ".env"
    if not env_file.exists():
        print("❌ .env file not found. Please copy .env.example to .env and configure it.")
        return False
    
    # Check LLM API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openai_key and not openrouter_key:
        print("❌ No LLM API key found. Please set either OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file.")
        print("   We recommend OpenRouter: https://openrouter.ai")
        return False
    
    if openrouter_key:
        print("✅ OpenRouter API key found")
    elif openai_key:
        print("✅ OpenAI API key found")
    
    # Check AWS credentials (optional for basic testing)
    aws_access = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access and aws_secret:
        print("✅ AWS credentials found")
    else:
        print("⚠️  AWS credentials not found (optional for basic testing)")
    
    return True


def test_llm_connection():
    """Test LLM connection with a simple query"""
    print("\n🧪 Testing LLM connection...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Create LLM client
        client = create_llm_client(config)
        
        # Test with simple query
        response = get_chat_completion(
            client=client,
            messages=[
                {"role": "user", "content": "Hello! Please respond with 'Connection successful' if you can see this message."}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ LLM Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        return False


def run_sample_task():
    """Run a sample AutoTasker AI task"""
    print("\n🚀 Running sample task...")
    
    try:
        from agents.planner_agent import PlannerAgent
        
        # Load configuration
        config = load_config()
        
        # Create planner agent
        planner = PlannerAgent(config)
        
        # Test planning
        sample_prompt = "Generate 1 easy coding question about arrays"
        
        print(f"Prompt: {sample_prompt}")
        print("Planning task...")
        
        plan = planner.execute_task({"prompt": sample_prompt})
        
        if plan.get("success"):
            print("✅ Sample task completed successfully!")
            print(f"Generated plan with {len(plan.get('tasks', []))} steps")
            return True
        else:
            print(f"❌ Sample task failed: {plan.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Sample task failed: {e}")
        return False


def show_next_steps():
    """Show next steps for the user"""
    print("\n🎯 Next Steps:")
    print("1. Start the Streamlit UI:")
    print("   streamlit run frontend/streamlit_app.py")
    print()
    print("2. Try these sample prompts:")
    print("   - 'Generate 2 coding questions about trees'")
    print("   - 'Create a daily task plan'")
    print()
    print("3. Set up additional services:")
    print("   - AWS credentials: See docs/AWS_SETUP.md")
    print("   - Google OAuth: See google_auth/README.md")
    print()
    print("4. Explore the configuration:")
    print("   - Edit config/config.yaml for model preferences")
    print("   - Update agents/ folder for custom agents")


def main():
    """Main quick start function"""
    print("🤖 AutoTasker AI - Quick Start\n")
    
    # Check environment
    if not check_environment():
        return False
    
    # Test LLM connection
    if not test_llm_connection():
        return False
    
    # Run sample task
    if not run_sample_task():
        return False
    
    # Show next steps
    show_next_steps()
    
    print("\n🎉 Setup complete! AutoTasker AI is ready to use.")
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(project_root / "config" / ".env")
    
    success = main()
    sys.exit(0 if success else 1)
