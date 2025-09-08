#!/usr/bin/env python3
"""
Quick Planner Agent Examples
Shows real output from natural language prompts
"""

import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner_agent import PlannerAgent
from backend.utils import load_config


def run_planner_examples():
    """Run the exact examples you requested"""
    
    print("=" * 70)
    print("PLANNER AGENT - LIVE EXAMPLES")
    print("=" * 70)
    
    # Load config
    config = load_config("config/config.yaml")
    planner = PlannerAgent(config)
    
    examples = [
        "Send me daily coding questions and check my Gmail",
        "Analyze my GitHub activity and email me a summary", 
        "Generate 5 hard DSA questions on trees and graphs"
    ]
    
    for i, prompt in enumerate(examples, 1):
        print(f"\n[{i}] PROMPT: '{prompt}'")
        print("-" * 60)
        
        plan = planner.create_task_plan(prompt)
        
        print(f"✓ Intent: {plan.get('intent', 'N/A')}")
        print(f"✓ Schedule: {plan.get('schedule', 'once')}")
        print(f"✓ Total Tasks: {len(plan.get('tasks', []))}")
        
        print("\n📋 TASK PLAN:")
        for task in plan.get('tasks', []):
            deps = f" → depends on: {', '.join(task.get('dependencies', []))}" if task.get('dependencies') else ""
            print(f"  • {task.get('id')}: {task.get('type').upper()} - {task.get('description')}{deps}")
        
        print(f"\n📄 FULL JSON PLAN:")
        print(json.dumps(plan, indent=2))
        print("\n" + "="*70)


if __name__ == "__main__":
    run_planner_examples()
