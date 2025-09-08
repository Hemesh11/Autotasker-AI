#!/usr/bin/env python3
"""
Test to verify LeetCode memory agent functionality
This script will directly test the LeetCode agent to ensure memory is working
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.leetcode_agent import LeetCodeAgent
from backend.utils import load_config

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_leetcode_memory():
    """Test LeetCode agent memory functionality"""
    
    print("🧪 Testing LeetCode Memory Agent")
    print("=" * 50)
    
    # Load config
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    config = load_config(config_path)
    
    # Create LeetCode agent
    leetcode_agent = LeetCodeAgent(config)
    
    # Check initial memory state
    memory_file = leetcode_agent.memory_file
    print(f"📁 Memory file: {memory_file}")
    
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as f:
            current_memory = json.load(f)
            print(f"📚 Current memory: {current_memory}")
    else:
        print("📚 Memory file does not exist")
    
    print(f"💾 Sent questions in memory: {len(leetcode_agent.sent_questions)}")
    print(f"🔢 Sent questions set: {leetcode_agent.sent_questions}")
    
    # Test task execution
    test_task = {
        "action": "get_daily_questions",
        "description": "Get 2 easy array questions for practice",
        "context": {
            "count": 2,
            "difficulty": "easy",
            "topic": "array"
        }
    }
    
    print("\n🚀 Executing test task...")
    print(f"📋 Task: {test_task}")
    
    result = leetcode_agent.execute_task(test_task)
    
    print(f"\n✅ Result success: {result.get('success', False)}")
    print(f"📊 Question count: {result.get('count', 0)}")
    
    if result.get('questions'):
        print("\n📝 Questions retrieved:")
        for i, q in enumerate(result['questions'], 1):
            print(f"  {i}. {q.get('title', 'No title')} (#{q.get('number', 'N/A')})")
    
    # Check memory after execution
    print("\n💾 Memory state after execution:")
    print(f"🔢 Sent questions count: {len(leetcode_agent.sent_questions)}")
    print(f"📚 Sent questions: {leetcode_agent.sent_questions}")
    
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as f:
            updated_memory = json.load(f)
            print(f"📁 Updated memory file: {updated_memory}")
    
    # Test duplicate detection
    print("\n🔍 Testing duplicate detection...")
    result2 = leetcode_agent.execute_task(test_task)
    
    print(f"✅ Second result success: {result2.get('success', False)}")
    print(f"📊 Second question count: {result2.get('count', 0)}")
    
    if result2.get('questions'):
        print("\n📝 Questions from second execution:")
        for i, q in enumerate(result2['questions'], 1):
            print(f"  {i}. {q.get('title', 'No title')} (#{q.get('number', 'N/A')})")
    
    # Final memory state
    print("\n💾 Final memory state:")
    print(f"🔢 Sent questions count: {len(leetcode_agent.sent_questions)}")
    
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as f:
            final_memory = json.load(f)
            print(f"📁 Final memory file: {final_memory}")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    setup_logging()
    test_leetcode_memory()
