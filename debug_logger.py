#!/usr/bin/env python3
"""
Quick Logger Agent Debug Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.logger_agent import LoggerAgent
from backend.utils import load_config

def debug_logger():
    """Debug why detailed logs aren't being saved"""
    
    print("🔍 DEBUGGING LOGGER AGENT - DETAILED LOGS ISSUE")
    print("=" * 60)
    
    # Load config
    config = load_config("config/config.yaml")
    
    # Initialize Logger Agent
    logger_agent = LoggerAgent(config)
    
    print(f"✓ Logger Agent initialized")
    print(f"✓ Logs directory: {logger_agent.logs_dir}")
    print(f"✓ Detailed logs directory: {logger_agent.detailed_logs_dir}")
    print(f"✓ Use local: {logger_agent.use_local}")
    
    # Check if directories exist
    print(f"\n📁 Directory Status:")
    print(f"   Logs dir exists: {os.path.exists(logger_agent.logs_dir)}")
    print(f"   Detailed dir exists: {os.path.exists(logger_agent.detailed_logs_dir)}")
    
    # Test a simple execution log
    from datetime import datetime
    test_execution = {
        "prompt": "DEBUG TEST - Simple prompt",
        "timestamp": datetime.now().isoformat(),
        "task_plan": {
            "tasks": [
                {"type": "test", "description": "Debug task"}
            ]
        },
        "duration": "5 seconds",
        "errors": [],
        "success": True
    }
    
    print(f"\n🧪 Testing log_execution...")
    result = logger_agent.log_execution(test_execution)
    
    print(f"✓ Log result: {result}")
    
    if result["success"]:
        execution_id = result["execution_id"]
        print(f"✓ Execution ID: {execution_id}")
        
        # Check if detailed file was created
        json_filename = f"execution_{execution_id}.json"
        json_filepath = os.path.join(logger_agent.detailed_logs_dir, json_filename)
        
        print(f"\n📄 Expected JSON file: {json_filepath}")
        print(f"   File exists: {os.path.exists(json_filepath)}")
        
        if os.path.exists(json_filepath):
            file_size = os.path.getsize(json_filepath)
            print(f"   File size: {file_size} bytes")
        
        # List all files in detailed directory
        if os.path.exists(logger_agent.detailed_logs_dir):
            files = os.listdir(logger_agent.detailed_logs_dir)
            print(f"\n📂 Files in detailed directory:")
            for file in files:
                print(f"   - {file}")
        else:
            print(f"\n❌ Detailed directory doesn't exist!")
    
    else:
        print(f"❌ Logging failed: {result}")

if __name__ == "__main__":
    debug_logger()
