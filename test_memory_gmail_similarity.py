#!/usr/bin/env python3
"""
Test Memory Agent's similarity detection for Gmail summarization prompts.
This tests whether similar prompts for Gmail summarization are correctly detected as duplicates.
"""

import sys
import os
import json
from typing import Dict, Any
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.memory_agent import MemoryAgent
from backend.utils import load_config

def test_gmail_similarity():
    """Test Memory Agent's duplicate detection for similar Gmail prompts."""
    
    print("🧠 Testing Memory Agent - Gmail Similarity Detection")
    print("=" * 60)
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    config = load_config(config_path)
    
    # Initialize memory agent
    memory_agent = MemoryAgent(config)
    
    # Clear any existing memory to start fresh
    cleanup_result = memory_agent.force_cleanup()
    print(f"✅ Cleared existing memory for clean test ({cleanup_result['cleaned_executions']} executions, {cleanup_result['cleaned_signatures']} signatures)")
    
    # Test prompts - these should be considered similar/duplicates
    test_prompts = [
        "Summarize my Gmail inbox",
        "summarize my gmail inbox",  # Same but lowercase
        "Summarize my Gmail inbox please",  # Added politeness
        "Can you summarize my Gmail inbox?",  # Question form
        "Please summarize my Gmail inbox",  # Different politeness
        "Summarize Gmail inbox",  # Shortened
        "Summarize my email inbox",  # Email instead of Gmail
        "Give me a summary of my Gmail inbox",  # Different phrasing
        "Create a summary of my Gmail messages",  # Different words
        "Summarize all emails in my Gmail",  # Reordered
    ]
    
    # Different prompts - these should NOT be considered duplicates
    different_prompts = [
        "Send an email via Gmail",  # Different action
        "Search Gmail for important emails",  # Different action
        "Delete old Gmail messages",  # Different action
        "Summarize my calendar events",  # Different service
        "Analyze GitHub repository commits",  # Completely different
    ]
    
    print(f"\n📊 Testing {len(test_prompts)} similar Gmail summarization prompts:")
    
    results = []
    for i, prompt in enumerate(test_prompts):
        print(f"\n{i+1}. Testing: '{prompt}'")
        
        # Check if it's a duplicate
        check_result = memory_agent.check_recent_execution(prompt)
        is_duplicate = check_result.get('should_skip', False)
        similarity = check_result.get('similarity', 0.0)
        match_type = check_result.get('match_type', 'unknown')
        reason = check_result.get('reason', 'No reason provided')
        
        if is_duplicate:
            print(f"   ✅ DUPLICATE detected (similarity: {similarity:.3f}, type: {match_type})")
            print(f"   📝 Reason: {reason}")
        else:
            print(f"   ❌ NOT detected as duplicate (similarity: {similarity:.3f})")
            
            # Record this execution
            execution_data = {
                "prompt": prompt,
                "task_details": {
                    "action": "gmail_summarize",
                    "params": {"prompt": prompt}
                },
                "execution_result": {
                    "status": "success",
                    "message": f"Simulated Gmail summary for: {prompt}"
                },
                "timestamp": datetime.now().isoformat()
            }
            memory_agent.record_execution(execution_data)
            print(f"   💾 Recorded execution")
        
        results.append({
            'prompt': prompt,
            'is_duplicate': is_duplicate,
            'similarity': similarity,
            'match_type': match_type,
            'reason': reason
        })
    
    print(f"\n📊 Testing {len(different_prompts)} different prompts (should NOT be duplicates):")
    
    for i, prompt in enumerate(different_prompts):
        print(f"\n{i+1}. Testing: '{prompt}'")
        
        check_result = memory_agent.check_recent_execution(prompt)
        is_duplicate = check_result.get('should_skip', False)
        similarity = check_result.get('similarity', 0.0)
        
        if is_duplicate:
            print(f"   ❌ INCORRECTLY flagged as duplicate (similarity: {similarity:.3f})")
            print(f"   📝 Reason: {check_result.get('reason', '')}")
        else:
            print(f"   ✅ Correctly NOT flagged as duplicate (similarity: {similarity:.3f})")
    
    # Analyze results
    print(f"\n📈 ANALYSIS:")
    print("=" * 60)
    
    duplicate_count = sum(1 for r in results if r['is_duplicate'])
    non_duplicate_count = len(results) - duplicate_count
    
    print(f"Similar Gmail prompts tested: {len(test_prompts)}")
    print(f"Detected as duplicates: {duplicate_count}")
    print(f"NOT detected as duplicates: {non_duplicate_count}")
    print(f"Detection rate: {(duplicate_count/len(test_prompts)*100):.1f}%")
    
    # Show similarity scores
    print(f"\n🔍 Similarity Scores:")
    for result in results:
        status = "DUPLICATE" if result['is_duplicate'] else "UNIQUE"
        print(f"  {result['similarity']:.3f} - {status} - '{result['prompt']}'")
    
    # Get current threshold
    current_threshold = memory_agent.similarity_threshold
    print(f"\n⚙️  Current similarity threshold: {current_threshold}")
    
    # Suggest threshold adjustment if needed
    max_similarity = max(r['similarity'] for r in results if not r['is_duplicate'])
    if max_similarity < current_threshold:
        suggested_threshold = max_similarity * 0.9  # 10% below the highest non-duplicate
        print(f"💡 Suggested threshold for stricter detection: {suggested_threshold:.3f}")
        print(f"   This would catch more similar prompts while avoiding false positives.")
    
    print(f"\n📁 Memory files location:")
    print(f"   Execution History: {memory_agent.execution_history_file}")
    print(f"   Prompt Signatures: {memory_agent.prompt_signatures_file}")
    
    return results

def test_with_different_threshold():
    """Test with a lower threshold to see the difference."""
    print(f"\n🔧 Testing with LOWER threshold (0.6 instead of 0.8)")
    print("=" * 60)
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    config = load_config(config_path)
    
    # Create a new memory agent with lower threshold
    memory_agent = MemoryAgent(config)
    memory_agent.similarity_threshold = 0.6  # Lower threshold = stricter detection
    memory_agent.force_cleanup()
    
    test_prompts = [
        "Summarize my Gmail inbox",
        "Please summarize my Gmail inbox",
        "Can you summarize my Gmail inbox?",
        "Give me a summary of my Gmail inbox",
        "Summarize all emails in my Gmail",
    ]
    
    results = []
    for i, prompt in enumerate(test_prompts):
        print(f"\n{i+1}. Testing: '{prompt}'")
        
        check_result = memory_agent.check_recent_execution(prompt)
        is_duplicate = check_result.get('should_skip', False)
        similarity = check_result.get('similarity', 0.0)
        
        if is_duplicate:
            print(f"   ✅ DUPLICATE detected (similarity: {similarity:.3f})")
            print(f"   📝 Reason: {check_result.get('reason', '')}")
        else:
            print(f"   ❌ NOT detected as duplicate (similarity: {similarity:.3f})")
            
            # Record execution
            execution_data = {
                "prompt": prompt,
                "task_details": {"action": "gmail_summarize", "params": {"prompt": prompt}},
                "execution_result": {"status": "success", "message": f"Simulated summary"},
                "timestamp": datetime.now().isoformat()
            }
            memory_agent.record_execution(execution_data)
        
        results.append({
            'prompt': prompt,
            'is_duplicate': is_duplicate,
            'similarity': similarity
        })
    
    duplicate_count = sum(1 for r in results if r['is_duplicate'])
    print(f"\n📈 With threshold 0.6:")
    print(f"   Detected as duplicates: {duplicate_count}/{len(test_prompts)}")
    print(f"   Detection rate: {(duplicate_count/len(test_prompts)*100):.1f}%")

if __name__ == "__main__":
    try:
        # Test with current threshold
        results = test_gmail_similarity()
        
        # Test with lower threshold
        test_with_different_threshold()
        
        print(f"\n✅ Memory Agent Gmail similarity testing completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
