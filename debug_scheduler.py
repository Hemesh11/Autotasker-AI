#!/usr/bin/env python3
"""
Debug scheduled task execution
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.scheduler import TaskScheduler
from backend.utils import load_config

def debug_scheduler():
    """Debug the scheduler to see what's happening"""
    print("🔍 DEBUGGING SCHEDULER")
    print("=" * 60)
    
    try:
        # Load config and create scheduler
        config = load_config("config/config.yaml")
        scheduler = TaskScheduler(config)
        
        if not scheduler.is_running:
            scheduler.start()
            print("✅ Scheduler started")
        
        # List current jobs
        jobs = scheduler.list_jobs()
        print(f"\n📋 Current scheduled jobs: {len(jobs)}")
        
        for job in jobs:
            print(f"   Job ID: {job['id']}")
            print(f"   Name: {job['name']}")
            print(f"   Next Run: {job['next_run']}")
            print(f"   Trigger: {job['trigger']}")
            print()
        
        if len(jobs) == 0:
            print("⚠️ No scheduled jobs found!")
            print("\nLet's create a test job:")
            
            # Create a test limited interval job
            job_id = scheduler.schedule_task(
                prompt="Generate 2 coding questions and email them to me",
                schedule_type="limited_interval",
                schedule_value="60:2",  # Every 1 minute, 2 times
                task_name="Test Limited Job"
            )
            
            print(f"✅ Created test job: {job_id}")
            
            # List jobs again
            jobs = scheduler.list_jobs()
            print(f"\n📋 Jobs after creation: {len(jobs)}")
            for job in jobs:
                print(f"   Job ID: {job['id']}")
                print(f"   Next Run: {job['next_run']}")
        
        # Check limited job tracking
        if hasattr(scheduler, '_limited_job_data'):
            print(f"\n🎯 Limited job tracking: {len(scheduler._limited_job_data)} jobs")
            for job_id, data in scheduler._limited_job_data.items():
                print(f"   {job_id}: {data['current_runs']}/{data['max_runs']} runs")
        
        print("\n⏰ Waiting 65 seconds to see if job executes...")
        time.sleep(65)
        
        # Check logs
        log_file = "data/logs/scheduled_tasks.log"
        if os.path.exists(log_file):
            print(f"\n📝 Execution log found:")
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:  # Show last 5 lines
                    print(f"   {line.strip()}")
        else:
            print(f"\n❌ No execution log found at: {log_file}")
            print("This means scheduled tasks are not executing!")
        
        # List jobs again to see if any were removed
        jobs = scheduler.list_jobs()
        print(f"\n📋 Jobs after waiting: {len(jobs)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_scheduler()
