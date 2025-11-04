"""
Test planner's handling of "list repositories" prompts
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import PlannerAgent
from backend.utils import load_config

def test_list_repos_planning():
    """Test that planner creates correct task for listing repos"""
    
    print("\n" + "="*70)
    print("🧪 Testing Planner: List Repositories Prompt")
    print("="*70 + "\n")
    
    config = load_config("config/config.yaml")
    planner = PlannerAgent(config)
    
    test_prompts = [
        "List my GitHub repositories",
        "Show all my repos",
        "Get my GitHub repos",
        "Show me all my repositories"
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*70}")
        print(f"📝 Prompt: '{prompt}'")
        print("="*70)
        
        try:
            plan = planner.create_task_plan(prompt)
            
            # Check if task plan was created
            tasks = plan.get("tasks", [])
            if not tasks:
                print("❌ FAIL: No tasks created")
                continue
            
            # Find GitHub task
            github_task = None
            for task in tasks:
                if task.get("type") == "github":
                    github_task = task
                    break
            
            if not github_task:
                print("❌ FAIL: No GitHub task found")
                continue
            
            # Check parameters
            params = github_task.get("parameters", {})
            operation = params.get("operation", "")
            
            print(f"\n✓ Task created:")
            print(f"  Type: {github_task.get('type')}")
            print(f"  Description: {github_task.get('description')}")
            print(f"  Operation: {operation}")
            print(f"  Parameters: {params}")
            
            # Validate
            if operation == "get_user_repos":
                if "username" in params:
                    print(f"\n✅ PASS: Correct operation and parameters!")
                    print(f"   Username: {params['username']}")
                else:
                    print(f"\n⚠️  WARNING: Missing 'username' parameter")
            else:
                print(f"\n❌ FAIL: Wrong operation '{operation}' (should be 'get_user_repos')")
                print(f"   This will NOT list all repos!")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("🎉 Test Complete!")
    print("="*70)
    print("\nIf tests passed, restart Streamlit and try:")
    print("  'List my GitHub repositories'")
    print()

if __name__ == "__main__":
    test_list_repos_planning()
