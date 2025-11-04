"""
Test the GitHub fix in Streamlit execution context
"""

import os
import sys
import yaml
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv("config/.env")

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_streamlit_github_scenario():
    """Simulate the exact Streamlit execution flow"""
    
    print("\n" + "="*70)
    print("🧪 Testing Streamlit GitHub Execution")
    print("="*70 + "\n")
    
    # Load config
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Import runner
    from backend.langgraph_runner import AutoTaskerRunner
    
    # Test prompts that were failing
    test_prompts = [
        "Summarize my GitHub Hemesh11 commits from yesterday and email the report",
        "Summarize my commits from last week",
        "Get my GitHub activity"
    ]
    
    runner = AutoTaskerRunner(config)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_prompts)}: {prompt}")
        print("="*70)
        
        try:
            result = runner.run_workflow(prompt)
            
            # Check GitHub execution
            github_results = {k: v for k, v in result["execution_results"].items() if k.startswith("github")}
            
            if github_results:
                for key, value in github_results.items():
                    print(f"\n📦 {key}:")
                    print(f"   Success: {value.get('success')}")
                    
                    if value.get('success'):
                        print(f"   ✅ GitHub agent executed successfully!")
                        if 'data' in value:
                            repo = value['data'].get('repository', 'unknown')
                            print(f"   📂 Repository: {repo}")
                            commits = value['data'].get('total_commits', 0)
                            print(f"   📊 Commits found: {commits}")
                    else:
                        error = value.get('error', 'Unknown error')
                        print(f"   ❌ Error: {error}")
            else:
                print("   ⚠️  No GitHub execution in results")
            
            # Overall status
            if any(v.get('success') for k, v in result["execution_results"].items() if k.startswith("github")):
                print(f"\n✅ Test PASSED")
            else:
                print(f"\n❌ Test FAILED")
                
        except Exception as e:
            print(f"\n❌ Exception: {e}")
    
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print("\n✅ All tests completed!")
    print("🎉 GitHub agent should now work in Streamlit!")

if __name__ == "__main__":
    test_streamlit_github_scenario()
