"""
AWS Lambda handler for AutoTasker AI
Serverless deployment wrapper for the LangGraph workflow orchestrator
"""

import json
import os
import logging
from typing import Dict, Any, Tuple
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

# Set up logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add Lambda layer path
import sys
sys.path.append('/opt/python')

# Import AutoTasker components
try:
    from backend.langgraph_runner import AutoTaskerRunner
    from backend.utils import load_config
except ImportError as e:
    logger.error(f"Failed to import AutoTasker components: {e}")
    raise

# AWS clients
secrets_client = boto3.client('secretsmanager')
eventbridge_client = boto3.client('events')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda entry point for scheduled task execution
    
    Event structure:
    {
        "prompt": "Generate DSA questions and email them",
        "task_id": "daily-dsa-questions",
        "schedule_config": {...}
    }
    """
    
    try:
        # Extract task information from event
        prompt = event.get('prompt', '')
        task_id = event.get('task_id', f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        
        if not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No prompt provided'})
            }
        
        # Load configuration from environment variables
        config = {
            'llm': {
                'provider': os.environ.get('LLM_PROVIDER', 'openrouter'),
                'api_key': os.environ.get('LLM_API_KEY'),
                'model': os.environ.get('LLM_MODEL', 'openai/gpt-3.5-turbo')
            },
            'aws': {
                'region': os.environ.get('AWS_REGION', 'us-east-1'),
                's3_bucket': os.environ.get('S3_BUCKET'),
                'dynamodb_table': os.environ.get('DYNAMODB_TABLE')
            },
            'email': {
                'provider': 'aws_ses',
                'from_email': os.environ.get('FROM_EMAIL'),
                'to_email': os.environ.get('TO_EMAIL')
            }
        }
        
        # Initialize AutoTasker with cloud config
        runner = AutoTaskerRunner(config=config)
        
        # Execute the workflow
        result = runner.run_workflow(prompt)
        
        # Store results in DynamoDB
        store_execution_result(task_id, prompt, result, config)
        
        # Store logs in S3
        store_logs_to_s3(task_id, result, config)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'task_id': task_id,
                'success': result.get('success', True),
                'execution_time': datetime.now().isoformat(),
                'result_summary': get_result_summary(result)
            })
        }
        
    except Exception as e:
        # Log error to CloudWatch
        print(f"Lambda execution failed: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'task_id': task_id if 'task_id' in locals() else 'unknown'
            })
        }


def store_execution_result(task_id: str, prompt: str, result: Dict[str, Any], config: Dict[str, Any]):
    """Store execution metadata in DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name=config['aws']['region'])
        table = dynamodb.Table(config['aws']['dynamodb_table'])
        
        item = {
            'task_id': task_id,
            'prompt': prompt,
            'execution_time': datetime.now().isoformat(),
            'success': result.get('success', True),
            'errors': result.get('errors', []),
            'agent_results': get_agent_summary(result),
            'email_sent': bool(result.get('execution_results', {}).get('email_sent')),
            'ttl': int(datetime.now().timestamp()) + (365 * 24 * 60 * 60)  # 1 year TTL
        }
        
        table.put_item(Item=item)
        print(f"Stored execution result for task {task_id}")
        
    except Exception as e:
        print(f"Failed to store in DynamoDB: {str(e)}")


def store_logs_to_s3(task_id: str, result: Dict[str, Any], config: Dict[str, Any]):
    """Store detailed logs and results in S3"""
    try:
        s3 = boto3.client('s3', region_name=config['aws']['region'])
        bucket = config['aws']['s3_bucket']
        
        # Store execution logs
        log_key = f"execution-logs/{datetime.now().strftime('%Y/%m/%d')}/{task_id}.json"
        s3.put_object(
            Bucket=bucket,
            Key=log_key,
            Body=json.dumps(result, indent=2, default=str),
            ContentType='application/json'
        )
        
        # Store email content if available
        if 'email_content' in result:
            email_key = f"email-content/{datetime.now().strftime('%Y/%m/%d')}/{task_id}.html"
            s3.put_object(
                Bucket=bucket,
                Key=email_key,
                Body=result['email_content'],
                ContentType='text/html'
            )
        
        print(f"Stored logs to S3 for task {task_id}")
        
    except Exception as e:
        print(f"Failed to store in S3: {str(e)}")


def get_agent_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract summary of agent execution results"""
    execution_results = result.get('execution_results', {})
    
    summary = {}
    for key, value in execution_results.items():
        if isinstance(value, dict):
            summary[key] = {
                'success': value.get('success', False),
                'data_size': len(str(value.get('content', '')))
            }
    
    return summary


def get_result_summary(result: Dict[str, Any]) -> str:
    """Generate human-readable summary of execution"""
    if result.get('error'):
        return f"Failed: {result['error']}"
    
    execution_results = result.get('execution_results', {})
    completed_tasks = len([r for r in execution_results.values() if isinstance(r, dict) and r.get('success')])
    total_tasks = len(execution_results)
    
    return f"Completed {completed_tasks}/{total_tasks} tasks successfully"
