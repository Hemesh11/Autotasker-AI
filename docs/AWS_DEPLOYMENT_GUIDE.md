# AWS Setup Guide for AutoTasker AI

## Overview
This guide will help you set up AWS infrastructure for AutoTasker AI's serverless deployment, enabling 24/7 operation with automatic scaling and cost optimization.

## Prerequisites
- AWS Account (Free tier eligible)
- AWS CLI installed
- Basic understanding of AWS services

## Step 1: Create AWS Account and Get Credentials

### 1.1 Create AWS Account
1. Go to [AWS Console](https://aws.amazon.com/console/)
2. Click "Create an AWS account"
3. Follow the registration process
4. Add payment method (required even for free tier)
5. Complete phone verification

### 1.2 Create IAM User for AutoTasker AI

**Important:** Never use root credentials for applications!

1. **Login to AWS Console**
   - Go to [AWS Console](https://console.aws.amazon.com/)
   - Login with your root account

2. **Navigate to IAM Service**
   - Search for "IAM" in the services search bar
   - Click on "IAM" service

3. **Create IAM User**
   - Click "Users" in the left sidebar
   - Click "Create user"
   - Username: `autotasker-ai-user`
   - Select "Programmatic access"
   - Click "Next"

4. **Attach Policies**
   - Click "Attach policies directly"
   - Search and select these policies:
     ```
     AWSLambdaFullAccess
     AmazonAPIGatewayFullAccess
     AmazonEventBridgeFullAccess
     AmazonDynamoDBFullAccess
     AmazonS3FullAccess
     AmazonSESFullAccess
     CloudWatchFullAccess
     SecretsManagerReadWrite
     IAMReadOnlyAccess
     ```
   - Click "Next"

5. **Review and Create**
   - Review the user details
   - Click "Create user"

6. **Download Credentials**
   - **IMPORTANT:** Download the CSV file with Access Key ID and Secret Access Key
   - Store this file securely - you won't be able to download it again
   - Example credentials format:
     ```
     Access Key ID: AKIAIOSFODNN7EXAMPLE
     Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
     ```

### 1.3 Configure AWS CLI

1. **Install AWS CLI**
   ```bash
   # Windows (using chocolatey)
   choco install awscli
   
   # Or download from: https://aws.amazon.com/cli/
   ```

2. **Configure AWS CLI**
   ```bash
   aws configure
   ```
   
   Enter your credentials:
   ```
   AWS Access Key ID: [Your Access Key ID]
   AWS Secret Access Key: [Your Secret Access Key]
   Default region name: us-east-1
   Default output format: json
   ```

3. **Test Configuration**
   ```bash
   aws sts get-caller-identity
   ```
   
   Should return your user information.

## Step 2: Required Environment Variables

Create a `.env` file in your project root with these variables:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=us-east-1

# AutoTasker Configuration
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token

# Gmail Configuration (will be stored in AWS Secrets Manager)
GMAIL_CREDENTIALS_PATH=google_auth/credentials.json
```

## Step 3: AWS Services Setup

### 3.1 Create S3 Bucket for Storage

1. **Navigate to S3**
   - Go to AWS Console → S3

2. **Create Bucket**
   - Click "Create bucket"
   - Bucket name: `autotasker-ai-storage-[your-unique-id]`
   - Region: `us-east-1`
   - Keep default settings
   - Click "Create bucket"

### 3.2 Setup DynamoDB for Memory Storage

1. **Navigate to DynamoDB**
   - Go to AWS Console → DynamoDB

2. **Create Table**
   - Click "Create table"
   - Table name: `autotasker-memory`
   - Partition key: `user_id` (String)
   - Sort key: `task_signature` (String)
   - Use default settings
   - Click "Create table"

### 3.3 Setup AWS SES for Email

1. **Navigate to SES**
   - Go to AWS Console → Simple Email Service

2. **Verify Email Address**
   - Click "Email Addresses" → "Verify a New Email Address"
   - Enter your email address
   - Check your email and click the verification link

3. **Request Production Access (Optional)**
   - By default, SES is in sandbox mode
   - For production, request production access

### 3.4 Setup Secrets Manager

1. **Navigate to Secrets Manager**
   - Go to AWS Console → Secrets Manager

2. **Store Gmail Credentials**
   - Click "Store a new secret"
   - Select "Other type of secrets"
   - Upload your `google_auth/credentials.json` content
   - Secret name: `autotasker/gmail-credentials`
   - Click "Store"

## Step 4: Create AWS SAM Template

Create `template.yaml` in your project root:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  OpenAIApiKey:
    Type: String
    NoEcho: true
    Description: OpenAI API Key
  
  GitHubToken:
    Type: String
    NoEcho: true
    Description: GitHub Personal Access Token

Resources:
  # Lambda Function for AutoTasker AI
  AutoTaskerFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: autotasker-ai-main
      CodeUri: .
      Handler: aws/lambda_handler.lambda_handler
      Runtime: python3.9
      Timeout: 900
      MemorySize: 1024
      Environment:
        Variables:
          OPENAI_API_KEY: !Ref OpenAIApiKey
          GITHUB_TOKEN: !Ref GitHubToken
          S3_BUCKET: !Ref AutoTaskerS3Bucket
          DYNAMODB_TABLE: !Ref AutoTaskerMemoryTable
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref AutoTaskerMemoryTable
        - S3CrudPolicy:
            BucketName: !Ref AutoTaskerS3Bucket
        - SESCrudPolicy:
            IdentityName: "*"
        - SecretsManagerReadWrite
      Events:
        ApiGateway:
          Type: Api
          Properties:
            Path: /execute
            Method: post

  # API Gateway
  AutoTaskerApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Cors:
        AllowMethods: "'POST, GET, OPTIONS'"
        AllowHeaders: "'Content-Type'"
        AllowOrigin: "'*'"

  # DynamoDB Table
  AutoTaskerMemoryTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: autotasker-memory
      AttributeDefinitions:
        - AttributeName: user_id
          AttributeType: S
        - AttributeName: task_signature
          AttributeType: S
      KeySchema:
        - AttributeName: user_id
          KeyType: HASH
        - AttributeName: task_signature
          KeyType: RANGE
      BillingMode: PAY_PER_REQUEST

  # S3 Bucket
  AutoTaskerS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'autotasker-ai-storage-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldVersions
            Status: Enabled
            NoncurrentVersionExpirationInDays: 30

  # EventBridge Rule for Scheduled Tasks
  DailyScheduleRule:
    Type: AWS::Events::Rule
    Properties:
      Name: autotasker-daily-schedule
      Description: "Daily execution for AutoTasker AI"
      ScheduleExpression: "cron(0 9 * * ? *)"  # 9 AM daily
      State: ENABLED
      Targets:
        - Arn: !GetAtt AutoTaskerFunction.Arn
          Id: AutoTaskerDailyTarget
          Input: |
            {
              "scheduled": true,
              "prompt": "Execute daily scheduled tasks"
            }

  # CloudWatch Log Group
  AutoTaskerLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/${AutoTaskerFunction}'
      RetentionInDays: 30

Outputs:
  ApiGatewayUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${AutoTaskerApi}.execute-api.${AWS::Region}.amazonaws.com/prod"
  
  LambdaFunctionArn:
    Description: "Lambda Function ARN"
    Value: !GetAtt AutoTaskerFunction.Arn
  
  S3BucketName:
    Description: "S3 Bucket Name"
    Value: !Ref AutoTaskerS3Bucket
  
  DynamoDBTableName:
    Description: "DynamoDB Table Name"
    Value: !Ref AutoTaskerMemoryTable
```

## Step 5: Create AWS Lambda Handler

Create `aws/lambda_handler.py`:

```python
import json
import os
import sys
import logging
from typing import Dict, Any

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from backend.langgraph_runner import AutoTaskerRunner
from backend.utils import load_config

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global variables for Lambda container reuse
runner = None
config = None

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler for AutoTasker AI
    """
    global runner, config
    
    try:
        # Initialize runner if not already done (container reuse)
        if not runner or not config:
            config = load_aws_config()
            runner = AutoTaskerRunner(config)
            logger.info("AutoTasker AI initialized successfully")
        
        # Extract request data
        if 'body' in event:
            # API Gateway request
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            prompt = body.get('prompt', '')
            task_id = body.get('task_id', 'api_request')
        else:
            # Direct invocation or EventBridge
            prompt = event.get('prompt', '')
            task_id = event.get('task_id', 'scheduled_task')
        
        if not prompt:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'No prompt provided'
                })
            }
        
        # Execute workflow
        logger.info(f"Executing workflow for prompt: {prompt[:100]}...")
        result = runner.run_workflow(prompt)
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'task_id': task_id,
                'result': result
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def load_aws_config() -> Dict[str, Any]:
    """Load configuration for AWS environment"""
    
    config = {
        'app': {
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'recursion_limit': int(os.getenv('RECURSION_LIMIT', '50'))
        },
        'openai': {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        },
        'github': {
            'token': os.getenv('GITHUB_TOKEN')
        },
        'aws': {
            'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            's3_bucket': os.getenv('S3_BUCKET'),
            'dynamodb_table': os.getenv('DYNAMODB_TABLE', 'autotasker-memory')
        },
        'gmail': {
            'credentials_secret': 'autotasker/gmail-credentials'
        }
    }
    
    return config
```

## Step 6: Create Requirements for Lambda

Create `requirements.txt` for Lambda deployment:

```txt
langchain
langgraph
openai
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
boto3
requests
pyyaml
python-dotenv
```

## Step 7: Deployment Scripts

Create `aws/deploy.sh` (Linux/Mac):

```bash
#!/bin/bash

echo "Deploying AutoTasker AI to AWS Lambda..."

# Install AWS SAM CLI if not installed
if ! command -v sam &> /dev/null; then
    echo "AWS SAM CLI not found. Please install it first."
    echo "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Build the application
echo "Building SAM application..."
sam build

# Deploy the application
echo "Deploying to AWS..."
sam deploy --guided

echo "Deployment complete!"
echo "Check AWS Console for your deployed resources."
```

Create `aws/deploy.ps1` (Windows):

```powershell
Write-Host "Deploying AutoTasker AI to AWS Lambda..." -ForegroundColor Green

# Check if SAM CLI is installed
if (!(Get-Command "sam" -ErrorAction SilentlyContinue)) {
    Write-Host "AWS SAM CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
}

# Build the application
Write-Host "Building SAM application..." -ForegroundColor Yellow
sam build

# Deploy the application
Write-Host "Deploying to AWS..." -ForegroundColor Yellow
sam deploy --guided

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Check AWS Console for your deployed resources."
```

## Step 8: Local Testing Before Deployment

1. **Test Lambda Locally**
   ```bash
   sam local start-api
   ```

2. **Test with curl**
   ```bash
   curl -X POST http://localhost:3000/execute \
     -H "Content-Type: application/json" \
     -d '{"prompt": "send me 2 leetcode questions"}'
   ```

## Step 9: Deployment Commands

1. **Install AWS SAM CLI**
   - Download from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

2. **Deploy to AWS**
   ```bash
   # Build the application
   sam build
   
   # Deploy (first time - guided)
   sam deploy --guided
   
   # Follow prompts:
   # - Stack name: autotasker-ai-stack
   # - AWS Region: us-east-1
   # - Confirm changes before deploy: Y
   # - Allow SAM CLI IAM role creation: Y
   # - Save parameters to samconfig.toml: Y
   ```

3. **Future Deployments**
   ```bash
   sam deploy
   ```

## Step 10: Post-Deployment Setup

1. **Get API Gateway URL**
   - Check CloudFormation outputs
   - Or run: `sam list endpoints --output table`

2. **Update Frontend Configuration**
   - Update your Streamlit app to use the API Gateway URL for production

3. **Test Deployed System**
   ```bash
   curl -X POST https://your-api-gateway-url/prod/execute \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test deployment"}'
   ```

## Cost Estimation

**Free Tier Eligible:**
- Lambda: 1M requests, 400,000 GB-seconds per month
- API Gateway: 1M requests per month
- DynamoDB: 25GB storage, 25 read/write capacity units
- S3: 5GB storage, 20,000 requests

**Estimated Monthly Costs (after free tier):**
- Light usage (100 workflows): $2-5
- Medium usage (1,000 workflows): $8-15
- Heavy usage (10,000 workflows): $50-100

## Monitoring and Logs

1. **CloudWatch Logs**
   - Go to AWS Console → CloudWatch → Log groups
   - Find `/aws/lambda/autotasker-ai-main`

2. **API Gateway Monitoring**
   - Go to AWS Console → API Gateway → Your API → Monitoring

3. **Lambda Monitoring**
   - Go to AWS Console → Lambda → autotasker-ai-main → Monitoring

## Troubleshooting

**Common Issues:**

1. **Permission Errors**
   - Check IAM policies
   - Ensure user has required permissions

2. **Lambda Timeout**
   - Increase timeout in template.yaml
   - Optimize code for faster execution

3. **API Gateway 502 Error**
   - Check Lambda logs
   - Verify handler function name

4. **DynamoDB Access Denied**
   - Check IAM policies include DynamoDB permissions
   - Verify table name matches configuration

## Security Best Practices

1. **API Keys**
   - Store in AWS Secrets Manager
   - Never commit to code

2. **IAM Policies**
   - Use principle of least privilege
   - Regular audit of permissions

3. **Network Security**
   - Consider VPC deployment for sensitive workloads
   - Use AWS WAF for API protection

## Next Steps

1. Set up monitoring and alerting
2. Configure backup strategies
3. Implement CI/CD pipeline
4. Scale based on usage patterns
5. Optimize costs based on actual usage

---

**Need Help?**
- AWS Documentation: https://docs.aws.amazon.com/
- AWS Support: https://aws.amazon.com/support/
- AutoTasker AI Issues: Create issue in project repository
