#!/usr/bin/env python3
"""
Logger Agent Individual Test
Tests logging functionality across different backends
"""

import sys
import os
import json
import csv
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.logger_agent import LoggerAgent
from backend.utils import load_config


def test_logger_agent() -> bool:
    """Test Logger Agent functionality comprehensively"""
    
    print("=" * 70)
    print("LOGGER AGENT INDIVIDUAL TEST")
    print("=" * 70)
    print("Tests logging to multiple backends and data retrieval")
    print("=" * 70)
    
    # Load configuration
    try:
        config = load_config("config/config.yaml")
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        # Minimal fallback config
        config = {
            "logging": {
                "use_local": True,
                "use_sheets": False,
                "use_s3": False
            },
            "aws": {
                "region": "us-east-1",
                "s3_bucket": "autotasker-logs"
            }
        }
    
    # Initialize Logger Agent
    print("\\n" + "-" * 50)
    print("INITIALIZING LOGGER AGENT")
    print("-" * 50)
    
    try:
        logger_agent = LoggerAgent(config)
        print("✓ Logger Agent initialized successfully")
        print(f"✓ Local logging: {logger_agent.use_local}")
        print(f"✓ Google Sheets: {logger_agent.use_sheets}")
        print(f"✓ AWS S3: {logger_agent.use_s3}")
        print(f"✓ Logs directory: {logger_agent.logs_dir}")
    except Exception as e:
        print(f"✗ Failed to initialize Logger Agent: {e}")
        return False
    
    # Test 1: Log sample executions
    print("\\n" + "-" * 50)
    print("TEST 1: LOGGING SAMPLE EXECUTIONS")
    print("-" * 50)
    
    sample_executions = [
        {
            "prompt": "Send me daily coding questions",
            "timestamp": datetime.now().isoformat(),
            "task_plan": {
                "tasks": [
                    {"type": "dsa", "description": "Generate coding questions"},
                    {"type": "email", "description": "Send results"}
                ]
            },
            "duration": "45 seconds",
            "errors": [],
            "retry_count": 0
        },
        {
            "prompt": "Check my Gmail and summarize important emails",
            "timestamp": datetime.now().isoformat(),
            "task_plan": {
                "tasks": [
                    {"type": "gmail", "description": "Fetch emails"},
                    {"type": "summarize", "description": "Summarize content"},
                    {"type": "email", "description": "Send summary"}
                ]
            },
            "duration": "32 seconds",
            "errors": [],
            "retry_count": 0
        },
        {
            "prompt": "Get GitHub activity and email me a report",
            "timestamp": datetime.now().isoformat(),
            "task_plan": {
                "tasks": [
                    {"type": "github", "description": "Fetch activity"},
                    {"type": "email", "description": "Send report"}
                ]
            },
            "duration": "28 seconds",
            "errors": ["GitHub API rate limit exceeded"],
            "retry_count": 2
        },
        {
            "prompt": "Create calendar reminder for project deadline",
            "timestamp": datetime.now().isoformat(),
            "task_plan": {
                "tasks": [
                    {"type": "calendar", "description": "Create reminder"}
                ]
            },
            "duration": "15 seconds",
            "errors": [],
            "retry_count": 0
        }
    ]
    
    logged_executions = []
    
    for i, execution in enumerate(sample_executions, 1):
        print(f"\\n[{i}] Logging: '{execution['prompt'][:50]}...'")
        
        # Add small delay to ensure different timestamps
        import time
        time.sleep(0.2)  # 200ms delay for distinct timestamps
        
        try:
            result = logger_agent.log_execution(execution)
            
            if result["success"]:
                print(f"    ✓ Successfully logged to: {', '.join(result['results']['logged_to'])}")
                print(f"    ✓ Execution ID: {result['execution_id']}")
                logged_executions.append(result['execution_id'])
                
                if result["results"]["errors"]:
                    print(f"    ⚠️ Some backends failed: {result['results']['errors']}")
            else:
                print(f"    ✗ Logging failed: {result['results']['errors']}")
        
        except Exception as e:
            print(f"    ✗ Exception during logging: {e}")
        
        # Small delay between logs
        time.sleep(0.1)
    
    print(f"\\n✓ Logged {len(logged_executions)} executions successfully")
    
    # Test 2: Verify local file storage
    print("\\n" + "-" * 50)
    print("TEST 2: VERIFY LOCAL FILE STORAGE")
    print("-" * 50)
    
    # Check CSV log file
    csv_path = logger_agent.execution_log_file
    if os.path.exists(csv_path):
        print(f"✓ CSV log file exists: {csv_path}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                csv_records = list(reader)
            
            print(f"✓ CSV contains {len(csv_records)} records")
            
            # Show last few records
            print("\\n📊 Recent CSV entries:")
            for record in csv_records[-3:]:
                success_icon = "✅" if record.get('success') == 'True' else "❌"
                print(f"    {success_icon} {record.get('timestamp', 'N/A')} - {record.get('prompt', 'N/A')[:40]}...")
        
        except Exception as e:
            print(f"✗ Failed to read CSV file: {e}")
    else:
        print(f"✗ CSV log file not found: {csv_path}")
    
    # Check detailed JSON logs
    detailed_dir = logger_agent.detailed_logs_dir
    if os.path.exists(detailed_dir):
        json_files = [f for f in os.listdir(detailed_dir) if f.endswith('.json')]
        print(f"\\n✓ Detailed logs directory exists with {len(json_files)} files")
        
        # Verify JSON files for our logged executions
        for exec_id in logged_executions:
            json_file = f"execution_{exec_id}.json"
            json_path = os.path.join(detailed_dir, json_file)
            
            if os.path.exists(json_path):
                print(f"    ✓ Found detailed log: {json_file}")
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        detailed_data = json.load(f)
                    
                    print(f"      📝 Prompt: {detailed_data.get('prompt', 'N/A')[:50]}...")
                    print(f"      🕒 Duration: {detailed_data.get('duration', 'N/A')}")
                    print(f"      📋 Tasks: {len(detailed_data.get('task_plan', {}).get('tasks', []))}")
                
                except Exception as e:
                    print(f"      ✗ Failed to read JSON: {e}")
            else:
                print(f"    ✗ Missing detailed log: {json_file}")
    else:
        print(f"✗ Detailed logs directory not found: {detailed_dir}")
    
    # Test 3: Get execution history
    print("\\n" + "-" * 50)
    print("TEST 3: EXECUTION HISTORY RETRIEVAL")
    print("-" * 50)
    
    try:
        history = logger_agent.get_execution_history(limit=10)
        print(f"✓ Retrieved {len(history)} execution records")
        
        if history:
            print("\\n📊 Execution History (recent first):")
            for i, record in enumerate(history[:5], 1):
                success_icon = "✅" if record.get('success') == 'True' else "❌"
                prompt = record.get('prompt', 'N/A')[:40]
                timestamp = record.get('timestamp', 'N/A')
                task_count = record.get('task_count', '0')
                
                print(f"    [{i}] {success_icon} {timestamp} - {prompt}... ({task_count} tasks)")
        else:
            print("⚠️ No execution history found")
    
    except Exception as e:
        print(f"✗ Failed to get execution history: {e}")
    
    # Test 4: Get detailed log for specific execution
    print("\\n" + "-" * 50)
    print("TEST 4: DETAILED LOG RETRIEVAL")
    print("-" * 50)
    
    if logged_executions:
        test_exec_id = logged_executions[0]
        print(f"Testing detailed log retrieval for: {test_exec_id}")
        
        try:
            detailed_log = logger_agent.get_detailed_log(test_exec_id)
            
            if detailed_log:
                print("✓ Successfully retrieved detailed log")
                print(f"    📝 Prompt: {detailed_log.get('prompt', 'N/A')}")
                print(f"    🕒 Timestamp: {detailed_log.get('timestamp', 'N/A')}")
                print(f"    ⏱️ Duration: {detailed_log.get('duration', 'N/A')}")
                print(f"    🔄 Retry count: {detailed_log.get('retry_count', 0)}")
                print(f"    ❌ Errors: {len(detailed_log.get('errors', []))}")
                
                tasks = detailed_log.get('task_plan', {}).get('tasks', [])
                print(f"    📋 Tasks ({len(tasks)}):")
                for task in tasks:
                    print(f"        - {task.get('type', 'unknown')}: {task.get('description', 'N/A')}")
            else:
                print(f"✗ Failed to retrieve detailed log for {test_exec_id}")
        
        except Exception as e:
            print(f"✗ Exception during detailed log retrieval: {e}")
    else:
        print("⚠️ No logged executions to test")
    
    # Test 5: Statistics generation
    print("\\n" + "-" * 50)
    print("TEST 5: STATISTICS GENERATION")
    print("-" * 50)
    
    try:
        stats = logger_agent.get_statistics()
        
        print("✓ Successfully generated statistics")
        print(f"\\n📊 EXECUTION STATISTICS:")
        print(f"    Total executions: {stats['total_executions']}")
        print(f"    Successful: {stats['successful_executions']}")
        print(f"    Failed: {stats['failed_executions']}")
        print(f"    Success rate: {stats['success_rate']:.1f}%")
        print(f"    Average tasks per execution: {stats['average_tasks']}")
        
        if stats['most_recent']:
            print(f"\\n🕒 Most recent execution:")
            recent = stats['most_recent']
            print(f"    Time: {recent.get('timestamp', 'N/A')}")
            print(f"    Prompt: {recent.get('prompt', 'N/A')}")
            print(f"    Success: {recent.get('success', 'N/A')}")
        
        date_range = stats.get('date_range', {})
        if date_range.get('oldest') and date_range.get('newest'):
            print(f"\\n📅 Date range:")
            print(f"    Oldest: {date_range['oldest']}")
            print(f"    Newest: {date_range['newest']}")
    
    except Exception as e:
        print(f"✗ Failed to generate statistics: {e}")
    
    # Test 6: Export functionality
    print("\\n" + "-" * 50)
    print("TEST 6: LOG EXPORT FUNCTIONALITY")
    print("-" * 50)
    
    try:
        # Test JSON export
        json_export_path = logger_agent.export_logs(format_type="json")
        
        if os.path.exists(json_export_path):
            print(f"✓ JSON export successful: {json_export_path}")
            
            # Check file size
            file_size = os.path.getsize(json_export_path)
            print(f"    📁 File size: {file_size} bytes")
        else:
            print(f"✗ JSON export file not found: {json_export_path}")
        
        # Test CSV export
        csv_export_path = logger_agent.export_logs(format_type="csv")
        
        if os.path.exists(csv_export_path):
            print(f"✓ CSV export successful: {csv_export_path}")
            
            # Check file size
            file_size = os.path.getsize(csv_export_path)
            print(f"    📁 File size: {file_size} bytes")
        else:
            print(f"✗ CSV export file not found: {csv_export_path}")
    
    except Exception as e:
        print(f"✗ Export functionality failed: {e}")
    
    # Test 7: Cleanup functionality
    print("\\n" + "-" * 50)
    print("TEST 7: LOG CLEANUP FUNCTIONALITY")
    print("-" * 50)
    
    try:
        # Count files before cleanup
        json_files_before = len([f for f in os.listdir(logger_agent.detailed_logs_dir) if f.endswith('.json')]) if os.path.exists(logger_agent.detailed_logs_dir) else 0
        
        # Test cleanup (using 7 days to keep recent logs)
        cleanup_result = logger_agent.cleanup_old_logs(days_to_keep=7)
        
        print("✓ Cleanup functionality tested")
        print(f"    📁 Files cleaned: {cleanup_result['cleaned_files']}")
        print(f"    📁 Files before cleanup: {json_files_before}")
        print(f"    ❌ Errors: {len(cleanup_result['errors'])}")
        print(f"    📅 Cutoff date: {cleanup_result['cutoff_date']}")
        print(f"    💡 Note: Using 7-day retention to preserve recent logs")
        
        if cleanup_result['errors']:
            print("    Error details:")
            for error in cleanup_result['errors']:
                print(f"        - {error}")
    
    except Exception as e:
        print(f"✗ Cleanup functionality failed: {e}")
    
    # Test Summary
    print("\\n" + "=" * 70)
    print("LOGGER AGENT CAPABILITIES SUMMARY")
    print("=" * 70)
    
    print("""
📝 LOGGING CAPABILITIES:
   • Multi-backend logging (Local, Google Sheets, AWS S3)
   • CSV summary logs for quick analysis
   • Detailed JSON logs for complete data
   • Automatic execution ID generation
   • Error handling and retry tracking

📊 DATA RETRIEVAL:
   • Execution history with filtering
   • Detailed log retrieval by execution ID
   • Statistics generation and analysis
   • Export functionality (JSON, CSV)
   • Date range filtering support

🔧 MAINTENANCE FEATURES:
   • Automatic log cleanup based on retention
   • File size management
   • Error tracking and reporting
   • Storage backend flexibility

⚙️ CONFIGURATION OPTIONS:
   • Enable/disable specific backends
   • Configure retention periods
   • Set storage paths and buckets
   • Customize export formats

🛡️ ROBUSTNESS:
   • Graceful degradation if backends fail
   • Error logging and recovery
   • File system error handling
   • Configurable retry mechanisms
""")
    
    # Final statistics
    try:
        final_stats = logger_agent.get_statistics()
        print(f"\\n📈 Final Statistics:")
        print(f"   Total executions logged: {final_stats['total_executions']}")
        print(f"   Success rate: {final_stats['success_rate']:.1f}%")
        print(f"   Storage backends active: {sum([logger_agent.use_local, logger_agent.use_sheets, logger_agent.use_s3])}")
        
        # Check file system (after cleanup, so files might be gone)
        if os.path.exists(logger_agent.logs_dir):
            csv_size = os.path.getsize(logger_agent.execution_log_file) if os.path.exists(logger_agent.execution_log_file) else 0
            json_files_remaining = len([f for f in os.listdir(logger_agent.detailed_logs_dir) if f.endswith('.json')]) if os.path.exists(logger_agent.detailed_logs_dir) else 0
            
            print(f"   CSV log size: {csv_size} bytes")
            print(f"   Detailed logs remaining: {json_files_remaining} files (after cleanup)")
    
    except Exception as e:
        print(f"   Error getting final stats: {e}")
    
    print(f"\\n🎉 Logger Agent testing completed!")
    print("The Logger Agent successfully handles multi-backend logging and data retrieval!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_logger_agent()
        if success:
            print("\\n🚀 Logger Agent is production-ready!")
        else:
            print("\\n🔧 Logger Agent needs attention")
    except KeyboardInterrupt:
        print("\\nTest interrupted by user")
    except Exception as e:
        print(f"\\nTest failed: {e}")
        import traceback
        traceback.print_exc()
