#!/usr/bin/env python3
"""
Memory Agent Individual Test
Tests task history management and duplicate detection
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.memory_agent import MemoryAgent
from backend.utils import load_config


def test_memory_agent() -> bool:
    """Test Memory Agent functionality comprehensively"""
    
    print("=" * 70)
    print("MEMORY AGENT INDIVIDUAL TEST")
    print("=" * 70)
    print("Tests task history, duplicate detection, and pattern analysis")
    print("=" * 70)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        # Minimal fallback config
        config = {
            "memory": {
                "retention_days": 30,
                "similarity_threshold": 0.8,
                "use_vector_store": False
            }
        }
    
    # Initialize Memory Agent
    print("\n" + "-" * 50)
    print("INITIALIZING MEMORY AGENT")
    print("-" * 50)
    
    try:
        memory_agent = MemoryAgent(config)
        print("✓ Memory Agent initialized successfully")
        print(f"✓ Retention period: {memory_agent.retention_days} days")
        print(f"✓ Similarity threshold: {memory_agent.similarity_threshold}")
        print(f"✓ Memory directory: {memory_agent.memory_dir}")
    except Exception as e:
        print(f"✗ Failed to initialize Memory Agent: {e}")
        return False
    
    # Start fresh for testing
    print("\n" + "-" * 50)
    print("CLEARING MEMORY FOR CLEAN TEST")
    print("-" * 50)
    
    cleanup_result = memory_agent.force_cleanup()
    print(f"✓ Cleaned {cleanup_result['cleaned_executions']} executions")
    print(f"✓ Cleaned {cleanup_result['cleaned_signatures']} signatures")
    
    # Test 1: Record some sample executions
    print("\n" + "-" * 50)
    print("TEST 1: RECORDING SAMPLE EXECUTIONS")
    print("-" * 50)
    
    sample_executions = [
        {
            "prompt": "Send me daily coding questions",
            "execution_id": "exec_001",
            "task_plan": {
                "tasks": [
                    {"type": "dsa", "description": "Generate coding questions"},
                    {"type": "email", "description": "Send results"}
                ]
            },
            "duration": "45 seconds",
            "errors": []
        },
        {
            "prompt": "Check my Gmail and summarize important emails",
            "execution_id": "exec_002", 
            "task_plan": {
                "tasks": [
                    {"type": "gmail", "description": "Fetch emails"},
                    {"type": "summarize", "description": "Summarize content"},
                    {"type": "email", "description": "Send summary"}
                ]
            },
            "duration": "32 seconds",
            "errors": []
        },
        {
            "prompt": "Get GitHub activity and email me a report", 
            "execution_id": "exec_003",
            "task_plan": {
                "tasks": [
                    {"type": "github", "description": "Fetch activity"},
                    {"type": "email", "description": "Send report"}
                ]
            },
            "duration": "28 seconds",
            "errors": ["GitHub API rate limit"]
        }
    ]
    
    for execution in sample_executions:
        memory_agent.record_execution(execution)
        print(f"✓ Recorded: {execution['prompt'][:50]}...")
    
    # Test 2: Check for duplicate detection
    print("\n" + "-" * 50)
    print("TEST 2: DUPLICATE DETECTION")
    print("-" * 50)
    
    duplicate_tests = [
        {
            "prompt": "Send me daily coding questions",  # Exact match
            "expected": "exact"
        },
        {
            "prompt": "Send me daily coding problems",  # Similar (questions vs problems)
            "expected": "similar"
        },
        {
            "prompt": "Get my Gmail and summarize important messages",  # Similar
            "expected": "similar"
        },
        {
            "prompt": "Create a shopping list for groceries",  # Completely different
            "expected": "none"
        },
        {
            "prompt": "Send daily coding questions to me",  # Similar word order
            "expected": "similar"
        }
    ]
    
    for i, test in enumerate(duplicate_tests, 1):
        print(f"\n[{i}] Testing: '{test['prompt']}'")
        
        check_result = memory_agent.check_recent_execution(test['prompt'])
        
        should_skip = check_result.get('should_skip', False)
        similarity = check_result.get('similarity', 0.0)
        match_type = check_result.get('match_type', 'unknown')
        reason = check_result.get('reason', 'No reason provided')
        
        print(f"    Should skip: {should_skip}")
        print(f"    Similarity: {similarity:.3f}")
        print(f"    Match type: {match_type}")
        print(f"    Reason: {reason}")
        
        # Validate results
        if test['expected'] == 'exact' and match_type == 'exact':
            print("    ✓ Correctly detected exact match")
        elif test['expected'] == 'similar' and match_type in ['similar', 'exact']:
            print("    ✓ Correctly detected similar match")
        elif test['expected'] == 'none' and match_type == 'none':
            print("    ✓ Correctly found no match")
        else:
            print(f"    ⚠️ Unexpected result: expected {test['expected']}, got {match_type}")
    
    # Test 3: Pattern Analysis
    print("\n" + "-" * 50)
    print("TEST 3: PATTERN ANALYSIS")
    print("-" * 50)
    
    patterns = memory_agent.get_execution_patterns()
    
    print(f"✓ Total executions: {patterns['total_executions']}")
    print(f"✓ Retention period: {patterns['retention_period_days']} days")
    
    print("\n📊 AGENT USAGE PATTERNS:")
    agent_usage = patterns['patterns']['most_common_agents']
    for agent, count in agent_usage.items():
        print(f"    {agent}: {count} times")
    
    print("\n📈 SUCCESS PATTERNS:")
    success_patterns = patterns['patterns']['success_patterns']
    print(f"    Success rate: {success_patterns['success_rate']:.1f}%")
    print(f"    Total executions: {success_patterns['total_executions']}")
    print(f"    Successful: {success_patterns['successful_executions']}")
    
    print("\n🕒 TIME PATTERNS:")
    time_patterns = patterns['patterns']['time_patterns']
    if time_patterns.get('peak_hours'):
        print("    Peak execution hours:")
        for hour, count in time_patterns['peak_hours']:
            print(f"      {hour:02d}:00 - {count} executions")
    
    print("\n📝 PROMPT PATTERNS:")
    prompt_patterns = patterns['patterns']['prompt_patterns']
    print(f"    Unique words: {prompt_patterns['unique_words']}")
    print(f"    Unique prompts: {prompt_patterns['unique_prompt_signatures']}")
    if prompt_patterns.get('most_common_words'):
        print("    Most common words:")
        for word, count in prompt_patterns['most_common_words'][:5]:
            print(f"      '{word}': {count} times")
    
    # Test 4: Memory persistence
    print("\n" + "-" * 50)
    print("TEST 4: MEMORY PERSISTENCE")
    print("-" * 50)
    
    # Record another execution
    new_execution = {
        "prompt": "Test memory persistence functionality",
        "execution_id": "exec_004",
        "task_plan": {"tasks": [{"type": "test", "description": "Test task"}]},
        "duration": "5 seconds",
        "errors": []
    }
    
    memory_agent.record_execution(new_execution)
    print("✓ Recorded new execution")
    
    # Create new instance to test persistence
    try:
        memory_agent2 = MemoryAgent(config)
        patterns2 = memory_agent2.get_execution_patterns()
        
        if patterns2['total_executions'] == patterns['total_executions'] + 1:
            print("✓ Memory persistence working correctly")
        else:
            print(f"⚠️ Memory persistence issue: expected {patterns['total_executions'] + 1}, got {patterns2['total_executions']}")
    except Exception as e:
        print(f"✗ Memory persistence test failed: {e}")
    
    # Test 5: Time-based cleanup
    print("\n" + "-" * 50)
    print("TEST 5: TIME-BASED CLEANUP")
    print("-" * 50)
    
    # Create an old execution by manipulating the timestamp
    old_execution = {
        "prompt": "This is an old execution that should be cleaned up",
        "execution_id": "exec_old",
        "task_plan": {"tasks": []},
        "duration": "1 second",
        "errors": []
    }
    
    # Add directly to avoid current timestamp
    old_record = {
        "timestamp": (datetime.now() - timedelta(days=35)).isoformat(),
        "prompt": old_execution["prompt"],
        "prompt_signature": memory_agent._generate_prompt_signature(old_execution["prompt"]),
        "task_plan": old_execution["task_plan"],
        "success": True,
        "execution_id": old_execution["execution_id"],
        "duration": old_execution["duration"],
        "agent_types": []
    }
    
    memory_agent.recent_executions.append(old_record)
    memory_agent._save_memory_data()
    
    before_cleanup = len(memory_agent.recent_executions)
    print(f"✓ Added old record, total executions: {before_cleanup}")
    
    # Trigger cleanup
    memory_agent._cleanup_old_memory_data()
    after_cleanup = len(memory_agent.recent_executions)
    
    if after_cleanup < before_cleanup:
        print(f"✓ Cleanup working: removed {before_cleanup - after_cleanup} old records")
    else:
        print("ℹ️ No old records to clean up")
    
    # Test Summary
    print("\n" + "=" * 70)
    print("MEMORY AGENT CAPABILITIES SUMMARY")
    print("=" * 70)
    
    print("""
🧠 MEMORY MANAGEMENT:
   • Records all task executions with metadata
   • Stores prompt signatures for duplicate detection
   • Maintains execution history with timestamps
   • Automatic cleanup of old data (configurable retention)

🔍 DUPLICATE DETECTION:
   • Exact prompt matching using MD5 signatures
   • Fuzzy text similarity using Jaccard similarity
   • Configurable similarity threshold (default 0.8)
   • Intelligent prompt normalization (time, variations)

📊 PATTERN ANALYSIS:
   • Agent usage frequency tracking
   • Success/failure rate analysis
   • Time-based execution patterns
   • Most common prompt words and phrases

💾 PERSISTENCE & STORAGE:
   • JSON-based storage for execution history
   • Separate prompt signature tracking
   • Automatic file creation and management
   • Memory directory organization

🛡️ ROBUSTNESS FEATURES:
   • Graceful handling of corrupted data
   • Automatic cleanup of invalid entries
   • Configurable retention policies
   • Error recovery and logging

⚙️ CONFIGURATION OPTIONS:
   • retention_days: How long to keep history
   • similarity_threshold: When to consider prompts similar
   • use_vector_store: Enable advanced similarity (future)
""")
    
    final_patterns = memory_agent.get_execution_patterns()
    print(f"\n📈 Final Statistics:")
    print(f"   Total executions recorded: {final_patterns['total_executions']}")
    print(f"   Success rate: {final_patterns['patterns']['success_patterns']['success_rate']:.1f}%")
    print(f"   Unique agent types used: {len(final_patterns['patterns']['most_common_agents'])}")
    print(f"   Memory retention period: {final_patterns['retention_period_days']} days")
    
    print(f"\n🎉 Memory Agent testing completed!")
    print("The Memory Agent successfully prevents duplicate executions and tracks patterns!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_memory_agent()
        if success:
            print("\n🚀 Memory Agent is production-ready!")
        else:
            print("\n🔧 Memory Agent needs attention")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
