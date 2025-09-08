"""
Task Scheduler for AutoTasker AI

Supports both local scheduling with APScheduler and cloud scheduling with AWS EventBridge.
Provides recurring task execution based on natural language prompts.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from backend.langgraph_runner import AutoTaskerRunner
from backend.utils import load_config, create_task_id

# Try to import EventBridge scheduler
try:
    from aws.eventbridge_scheduler import EventBridgeScheduler, ScheduleExpressionBuilder
    EVENTBRIDGE_AVAILABLE = True
except ImportError:
    EVENTBRIDGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages scheduled execution of AutoTasker AI workflows"""
    
    def __init__(self, config: Dict[str, Any], use_cloud: bool = False):
        """Initialize the task scheduler"""
        self.config = config
        self.use_cloud = use_cloud and EVENTBRIDGE_AVAILABLE
        
        # Track limited interval jobs
        self._limited_job_data = {}
        
        if self.use_cloud:
            self._init_cloud_scheduler()
        else:
            self._init_local_scheduler()
        
        self.logger = logger
        
    def _init_local_scheduler(self):
        """Initialize local APScheduler"""
        self.runner = AutoTaskerRunner(config=self.config)
        
        # Configure job store (Memory store to avoid pickle issues)
        from apscheduler.jobstores.memory import MemoryJobStore
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(20)
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        self.is_running = False
        
    def _init_cloud_scheduler(self):
        """Initialize AWS EventBridge scheduler"""
        self.eventbridge_scheduler = EventBridgeScheduler(self.config)
        self.is_running = True  # EventBridge is always "running"
        
    def start(self):
        """Start the scheduler"""
        if not self.use_cloud:
            if not self.is_running:
                try:
                    self.scheduler.start()
                    self.is_running = True
                    logger.info("Local task scheduler started successfully")
                except Exception as e:
                    logger.error(f"Failed to start scheduler: {e}")
                    raise
        else:
            logger.info("Cloud scheduler is always active")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.use_cloud:
            if self.is_running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("Local task scheduler stopped")
        else:
            logger.info("Cloud scheduler cannot be stopped (always active)")
    
    def schedule_task(
        self,
        prompt: str,
        schedule_type: str,
        schedule_value: str,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a task for execution
        
        Args:
            prompt: Natural language task description
            schedule_type: Type of schedule (daily, weekly, monthly, interval, cron)
            schedule_value: Schedule specification
            task_name: Optional task name
            metadata: Additional metadata
            
        Returns:
            Job ID or rule name
        """
        if self.use_cloud:
            return self._schedule_cloud_task(prompt, schedule_type, schedule_value, task_name, metadata)
        else:
            return self._schedule_local_task(prompt, schedule_type, schedule_value, task_name, metadata)
    
    def _schedule_local_task(
        self,
        prompt: str,
        schedule_type: str,
        schedule_value: str,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Schedule task using local APScheduler"""
        try:
            job_id = create_task_id(prompt)
            task_metadata = {
                'job_id': job_id,
                'task_name': task_name or f"Task {job_id}",
                'schedule_type': schedule_type,
                'schedule_value': schedule_value,
                **(metadata or {})
            }
            
            # Handle limited intervals specially
            if schedule_type == 'limited_interval':
                seconds, max_runs = schedule_value.split(':')
                max_runs = int(max_runs)
                
                # Store tracking data
                self._limited_job_data[job_id] = {
                    'max_runs': max_runs,
                    'current_runs': 0,
                    'original_prompt': prompt,
                    'task_name': task_metadata['task_name']
                }
            
            # Create trigger based on schedule type
            trigger = self._create_trigger(schedule_type, schedule_value)
            
            # Schedule the job
            self.scheduler.add_job(
                func=self._execute_scheduled_task,
                trigger=trigger,
                args=[prompt, task_metadata],
                id=job_id,
                name=task_metadata['task_name'],
                replace_existing=True
            )
            
            logger.info(f"Scheduled local task '{task_metadata['task_name']}' with ID: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to schedule local task: {e}")
            raise
    
    def _schedule_cloud_task(
        self,
        prompt: str,
        schedule_type: str,
        schedule_value: str,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Schedule task using AWS EventBridge"""
        try:
            # Convert schedule to EventBridge expression
            schedule_expression = self._convert_to_eventbridge_expression(schedule_type, schedule_value)
            
            # Schedule using EventBridge
            rule_name = self.eventbridge_scheduler.schedule_task(
                prompt=prompt,
                schedule_expression=schedule_expression,
                task_name=task_name,
                metadata=metadata
            )
            
            logger.info(f"Scheduled cloud task '{task_name}' with rule: {rule_name}")
            return rule_name
            
        except Exception as e:
            logger.error(f"Failed to schedule cloud task: {e}")
            raise
    
    def _convert_to_eventbridge_expression(self, schedule_type: str, schedule_value: str) -> str:
        """Convert local schedule format to EventBridge expression"""
        if schedule_type == 'daily':
            # schedule_value: "09:00"
            hour, minute = map(int, schedule_value.split(':'))
            return ScheduleExpressionBuilder.daily_at_time(hour, minute)
            
        elif schedule_type == 'weekly':
            # schedule_value: "MON:09:00"
            day, time = schedule_value.split(':')
            hour, minute = map(int, time.split(':'))
            return ScheduleExpressionBuilder.weekly_on_day(day, hour, minute)
            
        elif schedule_type == 'monthly':
            # schedule_value: "1:09:00"
            day, time = schedule_value.split(':')
            hour, minute = map(int, time.split(':'))
            return ScheduleExpressionBuilder.monthly_on_day(int(day), hour, minute)
            
        elif schedule_type == 'interval':
            # schedule_value: seconds as string
            seconds = int(schedule_value)
            minutes = seconds // 60
            return ScheduleExpressionBuilder.rate_expression(minutes, 'minutes')
            
        elif schedule_type == 'cron':
            # schedule_value: cron expression
            return ScheduleExpressionBuilder.custom_cron(schedule_value)
            
        else:
            raise ValueError(f"Unsupported schedule type for cloud: {schedule_type}")
    
    def _create_trigger(self, schedule_type: str, schedule_value: str):
        """Create appropriate trigger based on schedule type"""
        if schedule_type == 'daily':
            # schedule_value should be time like "09:00"
            hour, minute = map(int, schedule_value.split(':'))
            return CronTrigger(hour=hour, minute=minute)
            
        elif schedule_type == 'weekly':
            # schedule_value should be "MON:09:00" format
            day, time = schedule_value.split(':')
            hour, minute = map(int, time.split(':'))
            day_map = {
                'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3,
                'FRI': 4, 'SAT': 5, 'SUN': 6
            }
            return CronTrigger(day_of_week=day_map[day], hour=hour, minute=minute)
            
        elif schedule_type == 'monthly':
            # schedule_value should be "1:09:00" (day:hour:minute)
            day, hour, minute = map(int, schedule_value.split(':'))
            return CronTrigger(day=day, hour=hour, minute=minute)
            
        elif schedule_type == 'cron':
            # schedule_value should be cron expression
            return CronTrigger.from_crontab(schedule_value)
            
        elif schedule_type == 'interval':
            # schedule_value should be seconds
            seconds = int(schedule_value)
            return IntervalTrigger(seconds=seconds)
            
        elif schedule_type == 'limited_interval':
            # schedule_value should be "seconds:repetitions" like "300:3"
            seconds, max_runs = schedule_value.split(':')
            seconds = int(seconds)
            max_runs = int(max_runs)
            
            # Use regular IntervalTrigger without max_instances (not supported)
            # We'll track the execution count manually
            return IntervalTrigger(seconds=seconds)
            
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
    
    def _execute_scheduled_task(self, prompt: str, metadata: Dict[str, Any]):
        """Execute a scheduled task"""
        try:
            job_id = metadata.get('job_id')
            logger.info(f"Executing scheduled task: {metadata['task_name']}")
            
            # Check if this is a limited interval job
            if job_id in self._limited_job_data:
                job_data = self._limited_job_data[job_id]
                job_data['current_runs'] += 1
                
                logger.info(f"Limited interval job {job_id}: execution {job_data['current_runs']}/{job_data['max_runs']}")
            
            # Execute the workflow
            result = self.runner.run_workflow(prompt)
            
            # Determine success based on workflow state
            # If result has an 'error' key, it means workflow failed before completion
            # Otherwise, check if the state has errors
            if isinstance(result, dict) and 'error' in result:
                # Workflow failed during execution
                success = False
                error_msg = result.get('error')
            else:
                # Workflow completed, check for errors in state
                errors = result.get('errors', []) if isinstance(result, dict) else []
                success = len(errors) == 0
                error_msg = '; '.join(errors) if errors else None
            
            # Check if we need to remove the job after successful execution
            if job_id in self._limited_job_data:
                job_data = self._limited_job_data[job_id]
                if job_data['current_runs'] >= job_data['max_runs']:
                    logger.info(f"Limited interval job {job_id} completed all {job_data['max_runs']} runs")
                    # Remove the job after this execution
                    try:
                        self.scheduler.remove_job(job_id)
                        del self._limited_job_data[job_id]
                    except Exception as e:
                        logger.warning(f"Could not remove completed job {job_id}: {e}")
            
            # Log the execution
            execution_log = {
                'job_id': metadata.get('job_id'),
                'task_name': metadata['task_name'],
                'prompt': prompt,
                'executed_at': datetime.now().isoformat(),
                'success': success,
                'error': error_msg,
                'result_summary': self._create_result_summary(result)
            }
            
            self._log_execution(execution_log)
            
            if success:
                logger.info(f"Scheduled task completed successfully: {metadata['task_name']}")
            else:
                logger.error(f"Scheduled task failed: {metadata['task_name']}, Error: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error executing scheduled task: {e}")
            
            # Log the error
            error_log = {
                'job_id': metadata.get('job_id'),
                'task_name': metadata['task_name'],
                'executed_at': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
            self._log_execution(error_log)
    
    def _create_result_summary(self, result: Any) -> str:
        """Create a summary of the execution result"""
        # Handle error case (dict with 'error' key)
        if isinstance(result, dict) and 'error' in result:
            return f"Failed: {result.get('error', 'Unknown error')}"
        
        # Handle WorkflowState (should be a dict-like object)
        if not isinstance(result, dict):
            return "Execution completed"
        
        # Check for errors in state
        errors = result.get('errors', [])
        if errors:
            return f"Failed: {'; '.join(errors)}"
        
        # Extract key information from the result
        execution_results = result.get('execution_results', {})
        if execution_results:
            steps_completed = len([r for r in execution_results.values() if isinstance(r, dict) and r.get('success')])
            total_steps = len(execution_results)
            return f"Completed {steps_completed}/{total_steps} steps successfully"
        
        return "Execution completed successfully"
    
    def _log_execution(self, log_data: Dict[str, Any]):
        """Log task execution to file"""
        try:
            log_file = "data/logs/scheduled_tasks.log"
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'args': job.args,
                    'kwargs': job.kwargs
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get job info for {job_id}: {e}")
            return None
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False


class ScheduleParser:
    """Parse natural language schedule descriptions"""
    
    @staticmethod
    def parse_schedule(schedule_text: str) -> Dict[str, str]:
        """
        Parse natural language schedule into schedule_type and schedule_value
        
        Examples:
        - "daily at 9AM" -> {'type': 'daily', 'value': '09:00'}
        - "every Monday at 2PM" -> {'type': 'weekly', 'value': 'MON:14:00'}
        - "every 30 minutes" -> {'type': 'interval', 'value': '1800'}
        - "every 5 minutes, 3 times" -> {'type': 'limited_interval', 'value': '300:3'}
        """
        schedule_text = schedule_text.lower().strip()
        
        # Limited repetition patterns (enhanced!)
        import re
        
        # Pattern 1: "every X minutes, Y times"
        limited_pattern1 = re.search(r'every\s+(\d+)\s+(minute|hour)s?,?\s*(\d+)\s*times?', schedule_text)
        
        # Pattern 2: "every X minutes once, for Y times" 
        limited_pattern2 = re.search(r'every\s+(\d+)\s+(minute|hour)s?\s+once,?\s*for\s+(\d+)\s*times?', schedule_text)
        
        # Pattern 3: "for Y times" at the end
        limited_pattern3 = re.search(r'every\s+(\d+)\s+(minute|hour)s?.*?for\s+(\d+)\s*times?', schedule_text)
        
        # Pattern 4: "repeat Y times"
        limited_pattern4 = re.search(r'every\s+(\d+)\s+(minute|hour)s?.*?repeat\s+(\d+)\s*times?', schedule_text)
        
        # Check all patterns
        for pattern in [limited_pattern1, limited_pattern2, limited_pattern3, limited_pattern4]:
            if pattern:
                number = int(pattern.group(1))
                unit = pattern.group(2)
                repetitions = int(pattern.group(3))
                
                if unit == 'minute':
                    interval_seconds = number * 60
                else:  # hour
                    interval_seconds = number * 3600
                    
                return {'type': 'limited_interval', 'value': f"{interval_seconds}:{repetitions}"}
        
        # Daily patterns
        if 'daily' in schedule_text or 'every day' in schedule_text:
            time_match = ScheduleParser._extract_time(schedule_text)
            if time_match:
                return {'type': 'daily', 'value': time_match}
        
        # Weekly patterns
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_abbrev = {'monday': 'MON', 'tuesday': 'TUE', 'wednesday': 'WED', 
                      'thursday': 'THU', 'friday': 'FRI', 'saturday': 'SAT', 'sunday': 'SUN'}
        
        for day in days:
            if day in schedule_text:
                time_match = ScheduleParser._extract_time(schedule_text)
                if time_match:
                    return {'type': 'weekly', 'value': f"{day_abbrev[day]}:{time_match}"}
        
        # Interval patterns
        if 'every' in schedule_text and ('minute' in schedule_text or 'hour' in schedule_text):
            number_match = re.search(r'(\d+)', schedule_text)
            if number_match:
                number = int(number_match.group(1))
                if 'minute' in schedule_text:
                    return {'type': 'interval', 'value': str(number * 60)}
                elif 'hour' in schedule_text:
                    return {'type': 'interval', 'value': str(number * 3600)}
        
        # Default to daily at 9AM if can't parse
        return {'type': 'daily', 'value': '09:00'}
    
    @staticmethod
    def _extract_time(text: str) -> Optional[str]:
        """Extract time from text (e.g., '9AM' -> '09:00')"""
        import re
        
        # Match patterns like "9AM", "2:30PM", "14:00"
        time_patterns = [
            r'(\d{1,2}):?(\d{2})?\s*(am|pm)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*(am|pm)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                
                # Handle AM/PM
                if len(match.groups()) >= 3 and match.group(3):
                    ampm = match.group(3)
                    if ampm == 'pm' and hour != 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                
                return f"{hour:02d}:{minute:02d}"
        
        return None


def create_scheduler(config_path: str = "config/config.yaml") -> TaskScheduler:
    """Factory function to create a task scheduler"""
    config = load_config(config_path)
    return TaskScheduler(config)


# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the scheduler
    
    # Create scheduler
    scheduler = create_scheduler()
    scheduler.start()
    
    try:
        # Schedule a daily task
        job_id = scheduler.schedule_task(
            prompt="Generate 2 coding questions and email them to me",
            schedule_type="daily", 
            schedule_value="09:00",
            task_name="Daily Coding Questions"
        )
        
        print(f"Scheduled job with ID: {job_id}")
        
        # List all jobs
        jobs = scheduler.list_jobs()
        print(f"Active jobs: {len(jobs)}")
        
        # Keep running (in real usage, this would be managed by your application)
        import time
        time.sleep(10)
        
    finally:
        scheduler.stop()
