#!/usr/bin/env python3
"""
Clear All Logs Script
Cleans up all test logs for a fresh start
"""

import os
import shutil
import json
from pathlib import Path

def clear_all_logs():
    """Clear all logs and reset for production"""
    
    print("🧹 CLEARING ALL LOGS FOR FRESH START")
    print("=" * 60)
    
    logs_cleared = 0
    
    # 1. Clear Logger Agent logs
    print("\n📝 Clearing Logger Agent logs...")
    
    logs_dir = "data/logs"
    if os.path.exists(logs_dir):
        # Clear CSV log file
        csv_file = os.path.join(logs_dir, "execution_log.csv")
        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"   ✓ Removed: {csv_file}")
            logs_cleared += 1
        
        # Clear detailed logs directory
        detailed_dir = os.path.join(logs_dir, "detailed")
        if os.path.exists(detailed_dir):
            files = os.listdir(detailed_dir)
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(detailed_dir, file)
                    os.remove(file_path)
                    print(f"   ✓ Removed: {file}")
                    logs_cleared += 1
        
        # Clear export files
        export_files = [f for f in os.listdir(logs_dir) if f.startswith('autotasker_export_')]
        for file in export_files:
            file_path = os.path.join(logs_dir, file)
            os.remove(file_path)
            print(f"   ✓ Removed: {file}")
            logs_cleared += 1
    
    # 2. Clear Memory Agent data
    print("\n🧠 Clearing Memory Agent data...")
    
    memory_dir = "memory"
    if os.path.exists(memory_dir):
        # Clear execution history
        exec_history_file = os.path.join(memory_dir, "execution_history.json")
        if os.path.exists(exec_history_file):
            # Reset to empty array
            with open(exec_history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"   ✓ Cleared: {exec_history_file}")
            logs_cleared += 1
        
        # Clear prompt signatures
        signatures_file = os.path.join(memory_dir, "prompt_signatures.json")
        if os.path.exists(signatures_file):
            # Reset to empty object
            with open(signatures_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print(f"   ✓ Cleared: {signatures_file}")
            logs_cleared += 1
        
        # Clear LeetCode history if exists
        leetcode_file = os.path.join(memory_dir, "leetcode_history.json")
        if os.path.exists(leetcode_file):
            with open(leetcode_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print(f"   ✓ Cleared: {leetcode_file}")
            logs_cleared += 1
    
    # 3. Clear any debug files
    print("\n🔧 Clearing debug and test files...")
    
    debug_files = [
        "debug_logger.py"
    ]
    
    for file in debug_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"   ✓ Removed: {file}")
            logs_cleared += 1
    
    # 4. Check for any remaining log files
    print("\n🔍 Checking for other log files...")
    
    # Look for any remaining .log files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith('.log') or 'test_' in file and file.endswith('.py'):
                if 'test_' in file and any(x in file for x in ['memory', 'gmail', 'logger', 'planner']):
                    continue  # Keep agent test files
                file_path = os.path.join(root, file)
                if 'test_' not in file:  # Only remove .log files, not test scripts
                    try:
                        os.remove(file_path)
                        print(f"   ✓ Removed: {file_path}")
                        logs_cleared += 1
                    except:
                        pass
    
    # 5. Verify cleanup
    print("\n✅ CLEANUP SUMMARY")
    print("=" * 60)
    print(f"   Total files/entries cleared: {logs_cleared}")
    
    # Check final state
    print("\n📊 Final State:")
    
    # Logger Agent state
    if os.path.exists("data/logs/execution_log.csv"):
        print("   ❌ CSV log still exists")
    else:
        print("   ✅ CSV log cleared")
    
    if os.path.exists("data/logs/detailed"):
        detailed_files = len([f for f in os.listdir("data/logs/detailed") if f.endswith('.json')])
        if detailed_files == 0:
            print("   ✅ Detailed logs cleared")
        else:
            print(f"   ❌ {detailed_files} detailed logs remain")
    
    # Memory Agent state
    if os.path.exists("memory/execution_history.json"):
        with open("memory/execution_history.json", 'r') as f:
            history = json.load(f)
        if len(history) == 0:
            print("   ✅ Execution history cleared")
        else:
            print(f"   ❌ {len(history)} execution records remain")
    
    if os.path.exists("memory/prompt_signatures.json"):
        with open("memory/prompt_signatures.json", 'r') as f:
            signatures = json.load(f)
        if len(signatures) == 0:
            print("   ✅ Prompt signatures cleared")
        else:
            print(f"   ❌ {len(signatures)} signatures remain")
    
    print(f"\n🎉 System reset complete! Ready for production use.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        clear_all_logs()
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
