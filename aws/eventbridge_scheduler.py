"""
AWS EventBridge Scheduler for AutoTasker AI
Manages cloud-native scheduling using AWS EventBridge and Lambda
"""

import boto3
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EventBridgeScheduler:
    """Manages scheduled tasks using AWS EventBridge and Lambda"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize EventBridge scheduler"""
        self.config = config
        self.aws_config = config.get('aws', {})
        self.region = self.aws_config.get('region', 'us-east-1')
        self.lambda_function_name = self.aws_config.get('lambda_function_name', 'autotasker-runner')
        
        # Initialize AWS clients
        self.eventbridge = boto3.client('events', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
        self.logger = logger
        
    def schedule_task(
        self,
        prompt: str,
        schedule_expression: str,
        task_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a task using EventBridge
        
        Args:
            prompt: Natural language task description
            schedule_expression: Cron expression (e.g., "cron(0 9 * * ? *)" for daily at 9 AM)
            task_name: Optional task name
            metadata: Additional metadata
            
        Returns:
            Rule name/ID for the scheduled task
        """
        try:
            # Generate unique rule name
            rule_name = f"autotasker-{uuid.uuid4().hex[:8]}"
            task_name = task_name or f"Task-{rule_name}"
            
            # Create EventBridge rule
            rule_response = self.eventbridge.put_rule(
                Name=rule_name,
                ScheduleExpression=schedule_expression,
                Description=f"AutoTasker AI scheduled task: {task_name}",
                State='ENABLED'
            )
            
            # Prepare Lambda input
            lambda_input = {
                'prompt': prompt,
                'task_id': rule_name,
                'task_name': task_name,
                'schedule_config': {
                    'schedule_expression': schedule_expression,
                    'created_at': datetime.now().isoformat(),
                    'metadata': metadata or {}
                }
            }
            
            # Add Lambda as target
            target_response = self.eventbridge.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': self._get_lambda_arn(),
                        'Input': json.dumps(lambda_input)
                    }
                ]
            )
            
            # Grant EventBridge permission to invoke Lambda
            self._add_lambda_permission(rule_name)
            
            self.logger.info(f"Scheduled task '{task_name}' with rule: {rule_name}")
            return rule_name
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task: {e}")
            raise
    
    def delete_scheduled_task(self, rule_name: str) -> bool:
        """Delete a scheduled task"""
        try:
            # Remove targets first
            self.eventbridge.remove_targets(
                Rule=rule_name,
                Ids=['1']
            )
            
            # Delete the rule
            self.eventbridge.delete_rule(Name=rule_name)
            
            # Remove Lambda permission
            self._remove_lambda_permission(rule_name)
            
            self.logger.info(f"Deleted scheduled task: {rule_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete scheduled task {rule_name}: {e}")
            return False
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        try:
            response = self.eventbridge.list_rules(NamePrefix='autotasker-')
            
            tasks = []
            for rule in response.get('Rules', []):
                # Get targets for this rule
                targets_response = self.eventbridge.list_targets_by_rule(Rule=rule['Name'])
                
                task_info = {
                    'rule_name': rule['Name'],
                    'description': rule.get('Description', ''),
                    'schedule': rule.get('ScheduleExpression', ''),
                    'state': rule.get('State', ''),
                    'created_at': rule.get('CreatedAt', ''),
                    'targets': len(targets_response.get('Targets', []))
                }
                
                # Extract task details from target input if available
                targets = targets_response.get('Targets', [])
                if targets:
                    try:
                        target_input = json.loads(targets[0].get('Input', '{}'))
                        task_info.update({
                            'prompt': target_input.get('prompt', ''),
                            'task_name': target_input.get('task_name', ''),
                            'task_id': target_input.get('task_id', '')
                        })
                    except json.JSONDecodeError:
                        pass
                
                tasks.append(task_info)
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Failed to list scheduled tasks: {e}")
            return []
    
    def pause_task(self, rule_name: str) -> bool:
        """Pause a scheduled task"""
        try:
            self.eventbridge.disable_rule(Name=rule_name)
            self.logger.info(f"Paused task: {rule_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pause task {rule_name}: {e}")
            return False
    
    def resume_task(self, rule_name: str) -> bool:
        """Resume a paused task"""
        try:
            self.eventbridge.enable_rule(Name=rule_name)
            self.logger.info(f"Resumed task: {rule_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to resume task {rule_name}: {e}")
            return False
    
    def _get_lambda_arn(self) -> str:
        """Get the ARN of the Lambda function"""
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"arn:aws:lambda:{self.region}:{account_id}:function:{self.lambda_function_name}"
    
    def _add_lambda_permission(self, rule_name: str) -> None:
        """Add permission for EventBridge to invoke Lambda"""
        try:
            statement_id = f"autotasker-{rule_name}"
            source_arn = f"arn:aws:events:{self.region}:*:rule/{rule_name}"
            
            self.lambda_client.add_permission(
                FunctionName=self.lambda_function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=source_arn
            )
        except self.lambda_client.exceptions.ResourceConflictException:
            # Permission already exists
            pass
        except Exception as e:
            self.logger.warning(f"Failed to add Lambda permission: {e}")
    
    def _remove_lambda_permission(self, rule_name: str) -> None:
        """Remove EventBridge permission from Lambda"""
        try:
            statement_id = f"autotasker-{rule_name}"
            self.lambda_client.remove_permission(
                FunctionName=self.lambda_function_name,
                StatementId=statement_id
            )
        except Exception as e:
            self.logger.warning(f"Failed to remove Lambda permission: {e}")


class ScheduleExpressionBuilder:
    """Helper to build EventBridge schedule expressions from natural language"""
    
    @staticmethod
    def daily_at_time(hour: int, minute: int = 0) -> str:
        """Create daily schedule expression"""
        return f"cron({minute} {hour} * * ? *)"
    
    @staticmethod
    def weekly_on_day(day_of_week: str, hour: int, minute: int = 0) -> str:
        """Create weekly schedule expression"""
        day_map = {
            'MON': '2', 'TUE': '3', 'WED': '4', 'THU': '5',
            'FRI': '6', 'SAT': '7', 'SUN': '1'
        }
        day_num = day_map.get(day_of_week.upper(), '1')
        return f"cron({minute} {hour} ? * {day_num} *)"
    
    @staticmethod
    def monthly_on_day(day: int, hour: int, minute: int = 0) -> str:
        """Create monthly schedule expression"""
        return f"cron({minute} {hour} {day} * ? *)"
    
    @staticmethod
    def custom_cron(expression: str) -> str:
        """Use custom cron expression"""
        if not expression.startswith('cron('):
            expression = f"cron({expression})"
        return expression
    
    @staticmethod
    def rate_expression(value: int, unit: str) -> str:
        """Create rate expression (e.g., 'rate(1 hour)')"""
        return f"rate({value} {unit})"


def create_eventbridge_scheduler(config_path: str = "config/config.yaml") -> EventBridgeScheduler:
    """Factory function to create EventBridge scheduler"""
    from backend.utils import load_config
    config = load_config(config_path)
    return EventBridgeScheduler(config)


# Example usage
if __name__ == "__main__":
    import os
    from backend.utils import load_config
    
    # Load config
    config = load_config("../config/config.yaml")
    
    # Create scheduler
    scheduler = EventBridgeScheduler(config)
    
    # Schedule a daily task
    rule_name = scheduler.schedule_task(
        prompt="Generate 2 coding questions and email them to me",
        schedule_expression=ScheduleExpressionBuilder.daily_at_time(9, 0),
        task_name="Daily Coding Questions"
    )
    
    print(f"Scheduled task with rule: {rule_name}")
    
    # List all tasks
    tasks = scheduler.list_scheduled_tasks()
    print(f"Active tasks: {len(tasks)}")
    for task in tasks:
        print(f"- {task['task_name']}: {task['schedule']}")
