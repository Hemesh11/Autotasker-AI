"""Check if the runner code is correct"""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Force reload modules
import importlib
if 'backend.langgraph_runner' in sys.modules:
    del sys.modules['backend.langgraph_runner']
if 'agents.planner_agent' in sys.modules:
    del sys.modules['agents.planner_agent']

from backend.langgraph_runner import AutoTaskerRunner
from agents.planner_agent import PlannerAgent
from backend.utils import load_config
import inspect

print("\n" + "="*70)
print("🔍 Checking Current Code in Memory")
print("="*70 + "\n")

config = load_config("config/config.yaml")

# Check planner code
print("📋 Checking Planner Agent...")
planner = PlannerAgent(config)
source = inspect.getsource(planner._enhance_github_task)

if 'operation == "get_user_repos"' in source and 'return' in source:
    print("✅ Planner has the fix (checks operation and returns early)")
else:
    print("❌ Planner is missing the fix!")
    print("\nFirst 500 chars of _enhance_github_task:")
    print(source[:500])

# Check runner code
print("\n🏃 Checking Runner...")
runner = AutoTaskerRunner(config)
source = inspect.getsource(runner.github_task_node)

if 'operation = params.get("operation"' in source and 'get_user_repos' in source:
    print("✅ Runner has the fix (checks operation before normalization)")
else:
    print("❌ Runner is missing the fix!")
    print("\nFirst 800 chars of github_task_node:")
    print(source[:800])

# Test the actual flow
print("\n" + "="*70)
print("🧪 Testing Actual Execution")
print("="*70 + "\n")

plan = planner.create_task_plan("List my GitHub repositories")

github_task = None
for task in plan.get("tasks", []):
    if task.get("type") == "github":
        github_task = task
        break

if github_task:
    params = github_task["parameters"]
    print(f"📋 Planner Output:")
    print(f"   Operation: {params.get('operation')}")
    print(f"   Username: {params.get('username')}")
    print(f"   Repository: {params.get('repository')}")
    
    if params.get('operation') == 'get_user_repos' and params.get('username') and not params.get('repository'):
        print("\n✅ Planner output is CORRECT!")
    else:
        print("\n❌ Planner output is WRONG!")
else:
    print("❌ No GitHub task found!")

print("\n" + "="*70)
print("\n💡 If tests show fixes are present but Streamlit still fails:")
print("   1. Stop Streamlit completely (Ctrl+C)")
print("   2. Close all browser tabs")
print("   3. Run: streamlit cache clear")
print("   4. Restart Streamlit")
print()
