"""Quick test of list repos fix"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import PlannerAgent
from backend.utils import load_config

config = load_config("config/config.yaml")
planner = PlannerAgent(config)

print("\n" + "="*70)
print("🧪 Testing: List GitHub repositories")
print("="*70 + "\n")

plan = planner.create_task_plan("List my GitHub repositories")

# Show the task plan
import json
print("📋 Generated Task Plan:")
print(json.dumps(plan, indent=2))

# Check GitHub task
github_task = None
for task in plan.get("tasks", []):
    if task.get("type") == "github":
        github_task = task
        break

if github_task:
    params = github_task.get("parameters", {})
    operation = params.get("operation")
    username = params.get("username")
    repository = params.get("repository")
    
    print(f"\n{'='*70}")
    print("✓ GitHub Task Found:")
    print(f"  Operation: {operation}")
    print(f"  Username: {username}")
    print(f"  Repository: {repository}")
    print(f"{'='*70}\n")
    
    if operation == "get_user_repos" and username and not repository:
        print("✅ SUCCESS! Correct parameters for listing repos!")
    else:
        print("❌ FAIL! Wrong parameters:")
        if operation != "get_user_repos":
            print(f"   - Operation should be 'get_user_repos', got '{operation}'")
        if not username:
            print(f"   - Missing 'username' parameter")
        if repository:
            print(f"   - Should NOT have 'repository' parameter for get_user_repos")
else:
    print("❌ FAIL! No GitHub task found in plan")

print()
