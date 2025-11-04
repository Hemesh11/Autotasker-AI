# AWS Setup Guide for AutoTasker AI

This guide will help you set up AWS credentials and services for deploying AutoTasker AI to the cloud.

## Prerequisites

- An AWS account (sign up at https://aws.amazon.com)
- Basic understanding of AWS services
- Administrative access to your AWS account

## Step 1: Create AWS Account and Get Credentials

### 1.1 Create AWS Account
1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Fill in your details and complete the signup process
4. Add a payment method (required even for free tier)
5. Verify your phone number
6. Choose the Basic Support plan (free)

### 1.2 Access AWS Console
1. Sign in to AWS Console: https://console.aws.amazon.com
2. Make sure you're in the correct region (recommended: us-east-1)

### 1.3 Create IAM User for AutoTasker AI

**Important**: Never use your root account credentials for applications!

1. Go to IAM service in AWS Console
2. Click "Users" in the left sidebar
3. Click "Create user"
4. Enter username: `autotasker-ai-user`
5. Select "Programmatic access" (API access)
6. Click "Next: Permissions"

### 1.4 Set Permissions for IAM User

1. Choose "Attach existing policies directly"
2. Search for and select these policies:
   - `AWSLambdaFullAccess`
   - `AmazonAPIGatewayFullAccess`
   - `AmazonEventBridgeFullAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonS3FullAccess`
   - `AmazonSESFullAccess`
   - `CloudWatchFullAccess`
   - `SecretsManagerReadWrite`
   - `IAMReadOnlyAccess`

3. Click "Next: Tags" (skip tags for now)
4. Click "Next: Review"
5. Click "Create user"

### 1.5 Download Credentials

**CRITICAL**: Save these credentials securely!

1. On the success page, download the CSV file with credentials
2. Copy the Access Key ID and Secret Access Key
3. Store them securely (you won't be able to see the secret key again)

## Step 2: Configure AWS CLI (Optional but Recommended)

### 2.1 Install AWS CLI
```bash
# Windows (using pip in your conda environment)
pip install awscli

# Verify installation
aws --version
```

### 2.2 Configure AWS CLI
```bash
aws configure
```

Enter your credentials when prompted:
- AWS Access Key ID: [your access key]
- AWS Secret Access Key: [your secret key]
- Default region name: `us-east-1`
- Default output format: `json`

## Step 3: Set Up Required AWS Services

### 3.1 Create S3 Bucket for Storage

1. Go to S3 service in AWS Console
2. Click "Create bucket"
3. Bucket name: `autotasker-ai-storage-[your-name]` (must be globally unique)
4. Region: us-east-1
5. Keep default settings
6. Click "Create bucket"

### 3.2 Set Up SES for Email Delivery

1. Go to SES service in AWS Console
2. Click "Verified identities"
3. Click "Create identity"
4. Choose "Email address"
5. Enter your email address
6. Click "Create identity"
7. Check your email and click the verification link

**Important**: SES starts in sandbox mode. For production:
1. Go to "Account dashboard"
2. Click "Request production access"
3. Fill out the form explaining your use case

### 3.3 Create DynamoDB Table for Memory

1. Go to DynamoDB service in AWS Console
2. Click "Create table"
3. Table name: `autotasker-memory`
4. Partition key: `prompt_signature` (String)
5. Sort key: `timestamp` (String)
6. Keep default settings
7. Click "Create table"

### 3.4 Set Up EventBridge for Scheduling

EventBridge is set up automatically when we deploy Lambda functions. No manual setup needed.

### 3.5 Configure CloudWatch for Monitoring

CloudWatch is enabled by default. No manual setup needed.

## Step 4: Set Up Secrets Manager

### 4.1 Store OpenAI API Key

1. Go to Secrets Manager in AWS Console
2. Click "Store a new secret"
3. Choose "Other type of secret"
4. Add key-value pairs:
   - Key: `OPENAI_API_KEY`
   - Value: [your OpenAI API key]
5. Secret name: `autotasker-ai/openai`
6. Click "Next" and "Store"

### 4.2 Store Gmail Credentials

1. Create another secret in Secrets Manager
2. Choose "Other type of secret"
3. Upload your `credentials.json` file content as JSON
4. Secret name: `autotasker-ai/gmail-credentials`
5. Store the secret

### 4.3 Store GitHub Token

1. Create another secret
2. Add key-value pair:
   - Key: `GITHUB_TOKEN`
   - Value: [your GitHub personal access token]
3. Secret name: `autotasker-ai/github`
4. Store the secret

## Step 5: Update AutoTasker AI Configuration

### 5.1 Create AWS Configuration File

Create a new file: `config/aws-config.yaml`

```yaml
aws:
  region: "us-east-1"
  access_key_id: "YOUR_ACCESS_KEY_ID"
  secret_access_key: "YOUR_SECRET_ACCESS_KEY"
  
  services:
    lambda:
      function_name: "autotasker-ai-main"
      memory_size: 1024
      timeout: 900
      
    dynamodb:
      table_name: "autotasker-memory"
      
    s3:
      bucket_name: "autotasker-ai-storage-YOUR-NAME"
      
    ses:
      from_email: "your-verified-email@example.com"
      region: "us-east-1"
      
    secrets_manager:
      openai_secret: "autotasker-ai/openai"
      gmail_secret: "autotasker-ai/gmail-credentials"
      github_secret: "autotasker-ai/github"
      
    eventbridge:
      rule_prefix: "autotasker-"
      
    cloudwatch:
      log_group: "/aws/lambda/autotasker-ai"
```

### 5.2 Environment Variables

Set these environment variables in your system:

```bash
# Add to your .env file or system environment
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

## Step 6: Verify AWS Setup

### 6.1 Test AWS Connection

Create a test script: `test_aws_connection.py`

```python
import boto3
from botocore.exceptions import ClientError

def test_aws_connection():
    """Test AWS connection and permissions"""
    
    try:
        # Test Lambda
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        lambda_client.list_functions()
        print("✅ Lambda connection successful")
        
        # Test DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('autotasker-memory')
        table.load()
        print("✅ DynamoDB connection successful")
        
        # Test S3
        s3_client = boto3.client('s3')
        s3_client.list_buckets()
        print("✅ S3 connection successful")
        
        # Test SES
        ses_client = boto3.client('ses', region_name='us-east-1')
        ses_client.list_verified_email_addresses()
        print("✅ SES connection successful")
        
        # Test Secrets Manager
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        secrets_client.list_secrets()
        print("✅ Secrets Manager connection successful")
        
        print("\n🎉 All AWS services connected successfully!")
        return True
        
    except ClientError as e:
        print(f"❌ AWS connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_aws_connection()
```

Run this test:
```bash
python test_aws_connection.py
```

## Step 7: Deployment Preparation

### 7.1 Install Required Tools

```bash
# Install AWS SAM CLI (for deployment)
pip install aws-sam-cli

# Install required packages for Lambda
pip install boto3 botocore
```

### 7.2 Create Deployment Package

The project includes deployment scripts in the `aws/` directory:
- `aws/lambda_handler.py` - Main Lambda function
- `aws/deployment.py` - Deployment automation
- `aws/deploy.ps1` - PowerShell deployment script

## Cost Estimates

### Free Tier Limits (First 12 months)
- Lambda: 1M requests + 400,000 GB-seconds per month
- DynamoDB: 25GB storage + 25 units read/write capacity
- S3: 5GB storage + 20,000 GET requests + 2,000 PUT requests
- SES: 62,000 emails per month
- CloudWatch: 10 custom metrics + 5GB log ingestion

### Estimated Monthly Costs (After Free Tier)
- **Light Usage** (1,000 workflows/month): $2-5
- **Medium Usage** (10,000 workflows/month): $15-25
- **Heavy Usage** (100,000 workflows/month): $100-200

## Security Best Practices

1. **Never commit AWS credentials to Git**
2. **Use IAM roles and policies with minimum required permissions**
3. **Enable MFA on your AWS account**
4. **Regularly rotate access keys**
5. **Monitor AWS CloudTrail for suspicious activity**
6. **Use VPC endpoints for enhanced security (optional)**

## Troubleshooting

### Common Issues

1. **"Access Denied" errors**: Check IAM permissions
2. **"Region not found"**: Ensure you're using us-east-1
3. **SES sandbox limitations**: Request production access
4. **Lambda timeout**: Increase timeout in configuration
5. **DynamoDB throttling**: Increase read/write capacity

### Getting Help

1. Check AWS CloudWatch logs for detailed error messages
2. Use AWS CloudTrail to see API calls and errors
3. AWS Documentation: https://docs.aws.amazon.com
4. AWS Support (if you have a support plan)

## Next Steps

After completing this setup:

1. Run the AWS connection test
2. Deploy the Lambda function using `aws/deploy.ps1`
3. Test the deployment with a simple workflow
4. Set up monitoring and alerting
5. Configure automated deployments

Your AWS infrastructure is now ready for AutoTasker AI deployment! 🚀
