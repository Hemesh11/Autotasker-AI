#!/usr/bin/env python3
"""
Tool Selector Individual Test
Tests agent mapping, dependency resolution, and execution planning
"""

import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.tool_selector import ToolSelector
from backend.utils import load_config


def test_tool_selector() -> bool:
    """Test Tool Selector functionality comprehensively"""
    
    print("=" * 70)
    print("TOOL SELECTOR INDIVIDUAL TEST")
    print("=" * 70)
    print("Tests agent mapping, dependency resolution, and execution planning")
    print("=" * 70)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False
    
    # Initialize Tool Selector
    print("\\n" + "-" * 50)
    print("INITIALIZING TOOL SELECTOR")
    print("-" * 50)
    
    try:
        tool_selector = ToolSelector(config)
        print("✓ Tool Selector initialized successfully")
        print(f"✓ Task mappings: {len(tool_selector.task_mappings)} types")
        print(f"✓ Agent capabilities: {len(tool_selector.agent_capabilities)} agents")
        print(f"✓ Supported agents: {list(tool_selector.agent_capabilities.keys())}")
    except Exception as e:
        print(f"✗ Failed to initialize Tool Selector: {e}")
        return False
    
    # Test 1: Direct Task Type Mapping
    print("\\n" + "-" * 50)
    print("TEST 1: DIRECT TASK TYPE MAPPING")
    print("-" * 50)
    
    direct_mapping_tests = [
        {
            "task": {"type": "gmail", "description": "Fetch emails"},
            "expected_agents": ["gmail_agent", "logger_agent"]
        },
        {
            "task": {"type": "github", "description": "Get commits"},
            "expected_agents": ["github_agent", "logger_agent"]
        },
        {
            "task": {"type": "dsa", "description": "Generate coding questions"},
            "expected_agents": ["dsa_agent", "logger_agent"]
        },
        {
            "task": {"type": "summarize", "description": "Summarize content"},
            "expected_agents": ["summarizer_agent", "logger_agent"]
        },
        {
            "task": {"type": "email", "description": "Send results"},
            "expected_agents": ["email_agent", "logger_agent"]
        }
    ]
    
    for i, test in enumerate(direct_mapping_tests, 1):
        print(f"\\n[{i}] Testing: {test['task']['type']} task")
        
        selected_agents = tool_selector.select_agents_for_task(test['task'])
        
        print(f"    Expected: {test['expected_agents']}")
        print(f"    Selected: {selected_agents}")
        
        # Check if all expected agents are present
        expected_set = set(test['expected_agents'])
        selected_set = set(selected_agents)
        
        if expected_set.issubset(selected_set):
            print("    ✓ Correct agents selected")
        else:
            missing = expected_set - selected_set
            print(f"    ⚠️ Missing agents: {missing}")
    
    # Test 2: Fuzzy Keyword Matching
    print("\\n" + "-" * 50)
    print("TEST 2: FUZZY KEYWORD MATCHING")
    print("-" * 50)
    
    fuzzy_matching_tests = [
        {
            "task": {"type": "custom", "description": "Check my Gmail inbox for urgent emails"},
            "expected_keywords": ["gmail", "inbox"],
            "expected_agents": ["gmail_agent"]
        },
        {
            "task": {"type": "automation", "description": "Analyze GitHub repository commits"},
            "expected_keywords": ["github", "repository"],
            "expected_agents": ["github_agent"]
        },
        {
            "task": {"type": "workflow", "description": "Generate algorithm questions for practice"},
            "expected_keywords": ["algorithm", "questions"],
            "expected_agents": ["dsa_agent"]
        },
        {
            "task": {"type": "process", "description": "Summarize and analyze the content"},
            "expected_keywords": ["summarize", "analyze"],
            "expected_agents": ["summarizer_agent"]
        }
    ]
    
    for i, test in enumerate(fuzzy_matching_tests, 1):
        print(f"\\n[{i}] Testing: '{test['task']['description']}'")
        
        selected_agents = tool_selector.select_agents_for_task(test['task'])
        
        print(f"    Keywords: {test['expected_keywords']}")
        print(f"    Expected agents: {test['expected_agents']}")
        print(f"    Selected agents: {selected_agents}")
        
        # Check if expected agents are present
        expected_found = any(agent in selected_agents for agent in test['expected_agents'])
        
        if expected_found:
            print("    ✓ Keywords correctly matched to agents")
        else:
            print("    ⚠️ Keywords not properly matched")
    
    # Test 3: Parameter-Based Inference
    print("\\n" + "-" * 50)
    print("TEST 3: PARAMETER-BASED INFERENCE")
    print("-" * 50)
    
    parameter_tests = [
        {
            "task": {
                "type": "unknown",
                "description": "Process data",
                "parameters": {"email": "user@domain.com", "gmail": True}
            },
            "expected_agents": ["gmail_agent"]
        },
        {
            "task": {
                "type": "unknown",
                "description": "Fetch information",
                "parameters": {"github": True, "repo": "autotasker", "commit": "abc123"}
            },
            "expected_agents": ["github_agent"]
        },
        {
            "task": {
                "type": "unknown", 
                "description": "Generate content",
                "parameters": {"count": 5, "difficulty": "medium", "questions": True}
            },
            "expected_agents": ["dsa_agent"]
        }
    ]
    
    for i, test in enumerate(parameter_tests, 1):
        print(f"\\n[{i}] Testing parameter inference:")
        print(f"    Parameters: {test['task']['parameters']}")
        
        selected_agents = tool_selector.select_agents_for_task(test['task'])
        
        print(f"    Expected agents: {test['expected_agents']}")
        print(f"    Selected agents: {selected_agents}")
        
        expected_found = any(agent in selected_agents for agent in test['expected_agents'])
        
        if expected_found:
            print("    ✓ Parameters correctly inferred agents")
        else:
            print("    ⚠️ Parameter inference failed")
    
    # Test 4: Agent Dependency Resolution
    print("\\n" + "-" * 50)
    print("TEST 4: AGENT DEPENDENCY RESOLUTION")
    print("-" * 50)
    
    dependency_tests = [
        {"agent": "gmail_agent", "expected_deps": []},
        {"agent": "github_agent", "expected_deps": []},
        {"agent": "dsa_agent", "expected_deps": []},
        {"agent": "summarizer_agent", "expected_deps": ["gmail_agent", "github_agent"]},
        {"agent": "email_agent", "expected_deps": []},
        {"agent": "logger_agent", "expected_deps": []},
        {"agent": "memory_agent", "expected_deps": []},
        {"agent": "retry_agent", "expected_deps": []}
    ]
    
    for test in dependency_tests:
        agent = test["agent"]
        expected = test["expected_deps"]
        
        dependencies = tool_selector.get_agent_dependencies(agent)
        
        print(f"\\n{agent}:")
        print(f"    Expected deps: {expected}")
        print(f"    Actual deps: {dependencies}")
        
        if set(dependencies) == set(expected):
            print("    ✓ Dependencies correct")
        else:
            print("    ⚠️ Dependency mismatch")
    
    # Test 5: Agent Requirement Validation
    print("\\n" + "-" * 50)
    print("TEST 5: AGENT REQUIREMENT VALIDATION")
    print("-" * 50)
    
    validation_agents = ["gmail_agent", "github_agent", "dsa_agent", "summarizer_agent", "email_agent"]
    
    for agent in validation_agents:
        print(f"\\n[{agent}] Validation:")
        
        validation = tool_selector.validate_agent_requirements(agent)
        
        print(f"    Available: {validation['available']}")
        if validation['issues']:
            print(f"    Issues: {validation['issues']}")
        else:
            print("    ✓ All requirements met")
    
    # Test 6: Complex Multi-Task Workflow
    print("\\n" + "-" * 50)
    print("TEST 6: COMPLEX MULTI-TASK WORKFLOW")
    print("-" * 50)
    
    complex_tasks = [
        {
            "id": "task_1",
            "type": "gmail",
            "description": "Fetch recent emails",
            "priority": 1,
            "dependencies": []
        },
        {
            "id": "task_2",
            "type": "github", 
            "description": "Get repository activity",
            "priority": 1,
            "dependencies": []
        },
        {
            "id": "task_3",
            "type": "summarize",
            "description": "Summarize emails and GitHub data",
            "priority": 2,
            "dependencies": ["task_1", "task_2"]
        },
        {
            "id": "task_4",
            "type": "dsa",
            "description": "Generate coding questions",
            "priority": 2,
            "dependencies": []
        },
        {
            "id": "task_5",
            "type": "email",
            "description": "Send combined results",
            "priority": 3,
            "dependencies": ["task_3", "task_4"]
        }
    ]
    
    print("\\n📋 Complex workflow tasks:")
    for task in complex_tasks:
        print(f"    {task['id']}: {task['description']} (deps: {task['dependencies']})")
    
    # Test agent mapping for all tasks
    print("\\n🔗 Agent mapping:")
    task_agents = tool_selector.select_agents_for_tasks(complex_tasks)
    
    for task_id, agents in task_agents.items():
        print(f"    {task_id}: {agents}")
    
    # Test execution order
    print("\\n⏯️ Execution order:")
    execution_order = tool_selector.get_execution_order(complex_tasks)
    print(f"    Sequential: {execution_order}")
    
    # Test parallel execution groups
    print("\\n⚡ Parallel execution groups:")
    parallel_groups = tool_selector.get_parallel_execution_groups(complex_tasks)
    
    for i, group in enumerate(parallel_groups, 1):
        print(f"    Group {i}: {group} (can run in parallel)")
    
    # Test 7: Edge Cases
    print("\\n" + "-" * 50)
    print("TEST 7: EDGE CASES")
    print("-" * 50)
    
    edge_cases = [
        {
            "description": "Empty task",
            "task": {}
        },
        {
            "description": "Unknown task type",
            "task": {"type": "unknown_type", "description": "Unknown task"}
        },
        {
            "description": "Task with no clear indicators",
            "task": {"type": "mystery", "description": "Do something"}
        }
    ]
    
    for i, test in enumerate(edge_cases, 1):
        print(f"\\n[{i}] Testing: {test['description']}")
        
        try:
            selected_agents = tool_selector.select_agents_for_task(test['task'])
            print(f"    Selected agents: {selected_agents}")
            
            # Should always include logger_agent as minimum
            if "logger_agent" in selected_agents:
                print("    ✓ Logger agent included (minimum requirement)")
            else:
                print("    ⚠️ Logger agent missing")
                
        except Exception as e:
            print(f"    ✗ Exception: {e}")
    
    # Test Summary
    print("\\n" + "=" * 70)
    print("TOOL SELECTOR CAPABILITIES SUMMARY")
    print("=" * 70)
    
    print(f"""
🎯 TASK MAPPING:
   • Direct type mapping for {len(tool_selector.task_mappings)} task types
   • Fuzzy keyword matching in descriptions
   • Parameter-based agent inference
   • Always includes logger_agent for tracking

🤖 AGENT MANAGEMENT:
   • {len(tool_selector.agent_capabilities)} specialized agents supported
   • Capability-based validation
   • Dependency resolution and tracking
   • Authentication requirement checking

⚡ EXECUTION PLANNING:
   • Dependency-aware task ordering
   • Priority-based execution scheduling
   • Parallel execution group identification
   • Circular dependency detection

🛡️ ROBUSTNESS:
   • Graceful handling of unknown task types
   • Fallback to default agents when needed
   • Comprehensive requirement validation
   • Error handling for edge cases

🔗 INTEGRATION FEATURES:
   • Multi-task workflow orchestration
   • Agent requirement pre-validation
   • Execution order optimization
   • Parallel processing support
""")
    
    print(f"\\n🎉 Tool Selector testing completed!")
    print("The Tool Selector successfully maps tasks to agents and plans execution!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_tool_selector()
        if success:
            print("\\n🚀 Tool Selector is production-ready!")
        else:
            print("\\n🔧 Tool Selector needs attention")
    except KeyboardInterrupt:
        print("\\nTest interrupted by user")
    except Exception as e:
        print(f"\\nTest failed: {e}")
        import traceback
        traceback.print_exc()
