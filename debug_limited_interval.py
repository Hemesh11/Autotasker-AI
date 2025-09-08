#!/usr/bin/env python3
"""
Debug limited interval execution
"""

import sys
import os
import time
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.scheduler import TaskScheduler
from backend.utils import load_config

def test_limited_interval_execution():
    """Test limited interval execution step by step"""
    print("🔍 DEBUGGING LIMITED INTERVAL EXECUTION")
    print("=" * 60)
    
    try:
        # Load config and create scheduler
        config = load_config("config/config.yaml")
        scheduler = TaskScheduler(config)
        
        if not scheduler.is_running:
            scheduler.start()
            print("✅ Scheduler started")
        
        # Create a short test job (every 30 seconds, 3 times)
        print("\n📅 Creating limited interval job...")
        job_id = scheduler.schedule_task(
            prompt="Generate 1 coding question and email it to me",
            schedule_type="limited_interval",
            schedule_value="30:3",  # Every 30 seconds, 3 times
            task_name="Debug Limited Job"
        )
        
        print(f"✅ Created job: {job_id}")
        
        # Monitor for 2 minutes
        print(f"\n⏰ Monitoring for 2 minutes...")
        start_time = time.time()
        
        for i in range(24):  # Check every 5 seconds for 2 minutes
            elapsed = time.time() - start_time
            
            # Check job status
            jobs = scheduler.list_jobs()
            job_exists = any(job['id'] == job_id for job in jobs)
            
            # Check limited job tracking
            tracking_data = scheduler._limited_job_data.get(job_id, {})
            current_runs = tracking_data.get('current_runs', 0)
            max_runs = tracking_data.get('max_runs', 0)
            
            print(f"   {elapsed:4.0f}s - Job exists: {job_exists}, Runs: {current_runs}/{max_runs}")
            
            # Check for execution logs
            log_file = "data/logs/scheduled_tasks.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_log = json.loads(lines[-1])
                        if last_log.get('job_id') == job_id:
                            print(f"   📝 Last execution: {last_log.get('executed_at')} - Success: {last_log.get('success')}")
            
            # If job is done, break
            if not job_exists and current_runs >= max_runs:
                print(f"   ✅ Job completed all {max_runs} runs and was removed")
                break
            
            time.sleep(5)
        
        # Final status
        print(f"\n📊 Final Status:")
        remaining_jobs = scheduler.list_jobs()
        print(f"   Remaining jobs: {len(remaining_jobs)}")
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                job_logs = [json.loads(line) for line in lines if json.loads(line).get('job_id') == job_id]
                print(f"   Total executions logged: {len(job_logs)}")
                for i, log in enumerate(job_logs, 1):
                    print(f"     Execution {i}: {log.get('executed_at')} - Success: {log.get('success')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_limited_interval_execution()
