"""
AWS Deployment Scripts for AutoTasker AI
Automates deployment of Lambda function, EventBridge rules, and required AWS resources
"""

import json
import zipfile
import os
import time
from typing import Dict, Any, List
import subprocess


class AutoTaskerDeployer:
    """Handles deployment of AutoTasker AI to AWS"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize deployer with configuration"""
        self.config = config
        self.aws_config = config.get('aws', {})
        self.region = self.aws_config.get('region', 'us-east-1')
        self.function_name = self.aws_config.get('lambda_function_name', 'autotasker-runner')
        
        # Check if AWS CLI is available
        try:
            subprocess.run(['aws', '--version'], check=True, capture_output=True)
            self.aws_cli_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.aws_cli_available = False
            print("Warning: AWS CLI not found. Some features may not work.")
    
    def create_deployment_package(self) -> str:
        """Create Lambda deployment package"""
        print("📦 Creating deployment package...")
        
        # Create temporary deployment directory
        deploy_dir = "aws/deploy"
        os.makedirs(deploy_dir, exist_ok=True)
        
        # Files to include in deployment
        files_to_include = [
            'backend/',
            'agents/',
            'aws/lambda_handler.py',
            'config/config.yaml',
            'requirements.txt'
        ]
        
        # Create zip file
        zip_path = f"{deploy_dir}/autotasker-lambda.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_pattern in files_to_include:
                if file_pattern.endswith('/'):
                    # Add directory
                    for root, dirs, files in os.walk(file_pattern):
                        for file in files:
                            if file.endswith('.py'):
                                file_path = os.path.join(root, file)
                                arcname = file_path.replace('\\', '/')
                                zipf.write(file_path, arcname)
                else:
                    # Add single file
                    if os.path.exists(file_pattern):
                        zipf.write(file_pattern, file_pattern.replace('\\', '/'))
        
        print(f"✅ Deployment package created: {zip_path}")
        return os.path.abspath(zip_path)
    
    def create_lambda_function(self) -> Dict[str, Any]:
        """Create Lambda function using AWS CLI"""
        if not self.aws_cli_available:
            raise Exception("AWS CLI is required for Lambda deployment")
        
        print(f"🚀 Creating Lambda function: {self.function_name}")
        
        # Get deployment package
        zip_path = self.create_deployment_package()
        
        # Prepare Lambda configuration
        lambda_config = {
            "FunctionName": self.function_name,
            "Runtime": "python3.9",
            "Role": self._get_lambda_role_arn(),
            "Handler": "aws.lambda_handler.lambda_handler",
            "Code": {"ZipFile": "fileb://" + zip_path},
            "Description": "AutoTasker AI - Serverless task executor",
            "Timeout": self.aws_config.get('lambda_timeout', 300),
            "MemorySize": 512,
            "Environment": {
                "Variables": self._get_lambda_environment_variables()
            }
        }
        
        # Create function using AWS CLI
        cmd = [
            'aws', 'lambda', 'create-function',
            '--region', self.region,
            '--function-name', self.function_name,
            '--runtime', 'python3.9',
            '--role', self._get_lambda_role_arn(),
            '--handler', 'aws.lambda_handler.lambda_handler',
            '--zip-file', f'fileb://{zip_path}',
            '--description', 'AutoTasker AI - Serverless task executor',
            '--timeout', str(self.aws_config.get('lambda_timeout', 300)),
            '--memory-size', '512'
        ]
        
        # Add environment variables
        env_vars = self._get_lambda_environment_variables()
        if env_vars:
            env_json = json.dumps({"Variables": env_vars})
            cmd.extend(['--environment', env_json])
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            response = json.loads(result.stdout)
            print(f"✅ Lambda function created: {response['FunctionArn']}")
            return response
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create Lambda function: {e.stderr}")
            raise
    
    def update_lambda_function(self) -> Dict[str, Any]:
        """Update existing Lambda function"""
        if not self.aws_cli_available:
            raise Exception("AWS CLI is required for Lambda deployment")
        
        print(f"🔄 Updating Lambda function: {self.function_name}")
        
        # Get deployment package
        zip_path = self.create_deployment_package()
        
        # Update function code
        cmd = [
            'aws', 'lambda', 'update-function-code',
            '--region', self.region,
            '--function-name', self.function_name,
            '--zip-file', f'fileb://{zip_path}'
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            response = json.loads(result.stdout)
            print(f"✅ Lambda function updated: {response['FunctionArn']}")
            
            # Update environment variables
            self._update_lambda_environment()
            
            return response
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to update Lambda function: {e.stderr}")
            raise
    
    def deploy_infrastructure(self) -> Dict[str, Any]:
        """Deploy complete infrastructure (S3, DynamoDB, IAM roles, etc.)"""
        print("🏗️ Deploying AWS infrastructure...")
        
        results = {}
        
        # Create S3 bucket
        try:
            s3_result = self._create_s3_bucket()
            results['s3_bucket'] = s3_result
        except Exception as e:
            print(f"⚠️ S3 bucket creation failed: {e}")
        
        # Create DynamoDB table
        try:
            dynamodb_result = self._create_dynamodb_table()
            results['dynamodb_table'] = dynamodb_result
        except Exception as e:
            print(f"⚠️ DynamoDB table creation failed: {e}")
        
        # Create IAM role for Lambda
        try:
            role_result = self._create_lambda_role()
            results['lambda_role'] = role_result
        except Exception as e:
            print(f"⚠️ Lambda role creation failed: {e}")
        
        print("✅ Infrastructure deployment completed")
        return results
    
    def deploy_complete_stack(self) -> Dict[str, Any]:
        """Deploy complete AutoTasker AI stack"""
        print("🚀 Starting complete AutoTasker AI deployment...")
        
        # Step 1: Deploy infrastructure
        infra_results = self.deploy_infrastructure()
        
        # Wait for resources to be ready
        print("⏳ Waiting for AWS resources to be ready...")
        time.sleep(30)
        
        # Step 2: Create or update Lambda function
        try:
            lambda_result = self.create_lambda_function()
        except Exception:
            # If creation fails, try update
            print("🔄 Function exists, updating instead...")
            lambda_result = self.update_lambda_function()
        
        # Step 3: Set up EventBridge permissions
        self._setup_eventbridge_permissions()
        
        results = {
            'infrastructure': infra_results,
            'lambda_function': lambda_result,
            'deployment_status': 'success'
        }
        
        print("🎉 AutoTasker AI deployment completed successfully!")
        print(f"Lambda Function ARN: {lambda_result.get('FunctionArn')}")
        print("\nNext steps:")
        print("1. Test the Lambda function with a test event")
        print("2. Create EventBridge rules for scheduled tasks")
        print("3. Configure your .env file with the deployed resources")
        
        return results
    
    def _get_lambda_role_arn(self) -> str:
        """Get Lambda execution role ARN"""
        # This should be created by the infrastructure deployment
        account_id = self._get_aws_account_id()
        role_name = self.aws_config.get('lambda_role_name', 'AutoTaskerLambdaRole')
        return f"arn:aws:iam::{account_id}:role/{role_name}"
    
    def _get_lambda_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for Lambda"""
        return {
            'LLM_PROVIDER': os.environ.get('LLM_PROVIDER', 'openrouter'),
            'LLM_API_KEY': os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY', ''),
            'LLM_MODEL': os.environ.get('LLM_MODEL', 'openai/gpt-3.5-turbo'),
            'AWS_REGION': self.region,
            'S3_BUCKET': self.aws_config.get('s3_bucket', 'autotasker-logs'),
            'DYNAMODB_TABLE': self.aws_config.get('dynamodb_table', 'autotasker-executions'),
            'FROM_EMAIL': os.environ.get('AWS_SES_EMAIL', ''),
            'TO_EMAIL': os.environ.get('TO_EMAIL', '')
        }
    
    def _create_s3_bucket(self) -> Dict[str, Any]:
        """Create S3 bucket for logs"""
        bucket_name = self.aws_config.get('s3_bucket', 'autotasker-logs')
        
        cmd = ['aws', 's3', 'mb', f's3://{bucket_name}', '--region', self.region]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ S3 bucket created: {bucket_name}")
            return {'bucket_name': bucket_name, 'status': 'created'}
        except subprocess.CalledProcessError as e:
            if 'BucketAlreadyOwnedByYou' in e.stderr:
                print(f"✅ S3 bucket already exists: {bucket_name}")
                return {'bucket_name': bucket_name, 'status': 'exists'}
            else:
                raise
    
    def _create_dynamodb_table(self) -> Dict[str, Any]:
        """Create DynamoDB table for execution metadata"""
        table_name = self.aws_config.get('dynamodb_table', 'autotasker-executions')
        
        table_definition = {
            "TableName": table_name,
            "KeySchema": [
                {"AttributeName": "task_id", "KeyType": "HASH"}
            ],
            "AttributeDefinitions": [
                {"AttributeName": "task_id", "AttributeType": "S"}
            ],
            "BillingMode": "PAY_PER_REQUEST"
        }
        
        cmd = [
            'aws', 'dynamodb', 'create-table',
            '--region', self.region,
            '--cli-input-json', json.dumps(table_definition)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            response = json.loads(result.stdout)
            print(f"✅ DynamoDB table created: {table_name}")
            return response
        except subprocess.CalledProcessError as e:
            if 'ResourceInUseException' in e.stderr:
                print(f"✅ DynamoDB table already exists: {table_name}")
                return {'TableName': table_name, 'status': 'exists'}
            else:
                raise
    
    def _create_lambda_role(self) -> Dict[str, Any]:
        """Create IAM role for Lambda function"""
        role_name = self.aws_config.get('lambda_role_name', 'AutoTaskerLambdaRole')
        
        # Trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create role
        cmd = [
            'aws', 'iam', 'create-role',
            '--role-name', role_name,
            '--assume-role-policy-document', json.dumps(trust_policy),
            '--description', 'AutoTasker AI Lambda execution role'
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            response = json.loads(result.stdout)
            
            # Attach policies
            self._attach_lambda_policies(role_name)
            
            print(f"✅ Lambda role created: {role_name}")
            return response
        except subprocess.CalledProcessError as e:
            if 'EntityAlreadyExists' in e.stderr:
                print(f"✅ Lambda role already exists: {role_name}")
                return {'Role': {'RoleName': role_name, 'status': 'exists'}}
            else:
                raise
    
    def _attach_lambda_policies(self, role_name: str) -> None:
        """Attach necessary policies to Lambda role"""
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
            'arn:aws:iam::aws:policy/AmazonSESFullAccess'
        ]
        
        for policy_arn in policies:
            cmd = [
                'aws', 'iam', 'attach-role-policy',
                '--role-name', role_name,
                '--policy-arn', policy_arn
            ]
            subprocess.run(cmd, check=True, capture_output=True)
    
    def _update_lambda_environment(self) -> None:
        """Update Lambda environment variables"""
        env_vars = self._get_lambda_environment_variables()
        env_json = json.dumps({"Variables": env_vars})
        
        cmd = [
            'aws', 'lambda', 'update-function-configuration',
            '--region', self.region,
            '--function-name', self.function_name,
            '--environment', env_json
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _setup_eventbridge_permissions(self) -> None:
        """Set up EventBridge permissions for Lambda"""
        function_arn = f"arn:aws:lambda:{self.region}:{self._get_aws_account_id()}:function:{self.function_name}"
        
        cmd = [
            'aws', 'lambda', 'add-permission',
            '--region', self.region,
            '--function-name', self.function_name,
            '--statement-id', 'autotasker-eventbridge-permission',
            '--action', 'lambda:InvokeFunction',
            '--principal', 'events.amazonaws.com'
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ EventBridge permissions configured")
        except subprocess.CalledProcessError:
            # Permission might already exist
            print("✅ EventBridge permissions already configured")
    
    def _get_aws_account_id(self) -> str:
        """Get AWS account ID"""
        cmd = ['aws', 'sts', 'get-caller-identity', '--query', 'Account', '--output', 'text']
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()


def deploy_autotasker(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Main deployment function"""
    from backend.utils import load_config
    
    config = load_config(config_path)
    deployer = AutoTaskerDeployer(config)
    
    return deployer.deploy_complete_stack()


if __name__ == "__main__":
    # Example usage
    print("🚀 AutoTasker AI AWS Deployment")
    print("=" * 50)
    
    try:
        result = deploy_autotasker()
        print("\n✅ Deployment completed successfully!")
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        exit(1)
