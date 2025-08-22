#!/bin/bash

# AutoTasker AI AWS Deployment Script
# Automates the complete deployment of AutoTasker AI to AWS

set -e  # Exit on any error

echo "🚀 AutoTasker AI AWS Deployment"
echo "================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run: aws configure"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Configuration
PROJECT_NAME="AutoTaskerAI"
REGION=${AWS_REGION:-us-east-1}
ENVIRONMENT=${ENVIRONMENT:-production}
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

echo "📝 Configuration:"
echo "   Project: $PROJECT_NAME"
echo "   Region: $REGION"
echo "   Environment: $ENVIRONMENT"
echo "   Stack: $STACK_NAME"

# Get required parameters
read -p "🔑 Enter your LLM API key: " -s LLM_API_KEY
echo
read -p "📧 Enter FROM email address: " FROM_EMAIL
read -p "📧 Enter TO email address: " TO_EMAIL

# Validate email addresses for SES
echo "📧 Validating email addresses with SES..."
aws ses verify-email-identity --email-address "$FROM_EMAIL" --region "$REGION" || echo "⚠️  Email verification initiated for $FROM_EMAIL"
if [ "$FROM_EMAIL" != "$TO_EMAIL" ]; then
    aws ses verify-email-identity --email-address "$TO_EMAIL" --region "$REGION" || echo "⚠️  Email verification initiated for $TO_EMAIL"
fi

# Step 1: Generate CloudFormation template
echo "📄 Generating CloudFormation template..."
python3 aws/cloudformation.py

# Step 2: Create deployment package
echo "📦 Creating deployment package..."
DEPLOY_DIR="aws/deploy"
mkdir -p "$DEPLOY_DIR"

# Create Lambda layer for dependencies
echo "📚 Creating dependencies layer..."
LAYER_DIR="$DEPLOY_DIR/python"
mkdir -p "$LAYER_DIR"

# Install dependencies to layer
pip3 install -r requirements.txt --target "$LAYER_DIR" --quiet

# Create layer zip
cd "$DEPLOY_DIR"
zip -r dependencies.zip python/ -q
cd ../..

# Create function deployment package
echo "📦 Creating function package..."
FUNCTION_ZIP="$DEPLOY_DIR/autotasker.zip"

zip -r "$FUNCTION_ZIP" \
    backend/ \
    agents/ \
    aws/lambda_handler.py \
    config/config.yaml \
    -x "*.pyc" "*/__pycache__/*" "*.git*" -q

echo "✅ Deployment packages created"

# Step 3: Upload artifacts to S3
echo "☁️  Uploading deployment artifacts..."

# Create temporary bucket for deployment artifacts
TEMP_BUCKET="${PROJECT_NAME,,}-deploy-$(date +%s)"
aws s3 mb "s3://$TEMP_BUCKET" --region "$REGION"

# Upload layer and function
aws s3 cp "$DEPLOY_DIR/dependencies.zip" "s3://$TEMP_BUCKET/layers/dependencies.zip"
aws s3 cp "$FUNCTION_ZIP" "s3://$TEMP_BUCKET/functions/autotasker.zip"

echo "✅ Artifacts uploaded to s3://$TEMP_BUCKET"

# Step 4: Deploy CloudFormation stack
echo "🏗️  Deploying CloudFormation stack..."

# Update template to use the temporary bucket
sed -i.bak "s/\${LogsBucket}/$TEMP_BUCKET/g" aws/autotasker-infrastructure.json

aws cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-body file://aws/autotasker-infrastructure.json \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameters \
        ParameterKey=ProjectName,ParameterValue="$PROJECT_NAME" \
        ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
        ParameterKey=LLMApiKey,ParameterValue="$LLM_API_KEY" \
        ParameterKey=FromEmail,ParameterValue="$FROM_EMAIL" \
        ParameterKey=ToEmail,ParameterValue="$TO_EMAIL" \
    --region "$REGION"

echo "⏳ Waiting for stack deployment to complete..."
aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$REGION"

# Step 5: Get outputs
echo "📊 Getting deployment outputs..."
OUTPUTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].Outputs')

LAMBDA_ARN=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="LambdaFunctionArn") | .OutputValue')
S3_BUCKET=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="S3BucketName") | .OutputValue')
DYNAMODB_TABLE=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DynamoDBTableName") | .OutputValue')
DASHBOARD_URL=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DashboardURL") | .OutputValue')

# Step 6: Clean up temporary bucket
echo "🧹 Cleaning up temporary resources..."
aws s3 rm "s3://$TEMP_BUCKET" --recursive
aws s3 rb "s3://$TEMP_BUCKET"

# Restore original template
mv aws/autotasker-infrastructure.json.bak aws/autotasker-infrastructure.json

# Step 7: Test the deployment
echo "🧪 Testing deployment..."
TEST_EVENT=$(cat << EOF
{
  "prompt": "Generate a simple coding question and email it to me",
  "task_id": "deployment-test",
  "test": true
}
EOF
)

aws lambda invoke \
    --function-name "${PROJECT_NAME}-runner-${ENVIRONMENT}" \
    --payload "$TEST_EVENT" \
    --region "$REGION" \
    "$DEPLOY_DIR/test-response.json"

if [ $? -eq 0 ]; then
    echo "✅ Test invocation successful"
    cat "$DEPLOY_DIR/test-response.json"
else
    echo "⚠️  Test invocation failed, but deployment may still be successful"
fi

# Step 8: Display summary
echo ""
echo "🎉 AutoTasker AI Deployment Complete!"
echo "====================================="
echo ""
echo "📋 Deployment Summary:"
echo "   Stack Name: $STACK_NAME"
echo "   Region: $REGION"
echo "   Lambda Function: $LAMBDA_ARN"
echo "   S3 Bucket: $S3_BUCKET"
echo "   DynamoDB Table: $DYNAMODB_TABLE"
echo ""
echo "📊 Monitoring:"
echo "   CloudWatch Dashboard: $DASHBOARD_URL"
echo ""
echo "🔧 Next Steps:"
echo "1. Verify email addresses in SES if you haven't already"
echo "2. Test the function with: aws lambda invoke --function-name ${PROJECT_NAME}-runner-${ENVIRONMENT} --payload '{\"prompt\":\"test\"}' response.json"
echo "3. Create EventBridge rules for scheduled tasks"
echo "4. Update your local .env file with the deployed resources:"
echo ""
echo "   # Add to config/.env"
echo "   AWS_LAMBDA_FUNCTION_NAME=${PROJECT_NAME}-runner-${ENVIRONMENT}"
echo "   AWS_S3_BUCKET=$S3_BUCKET"
echo "   AWS_DYNAMODB_TABLE=$DYNAMODB_TABLE"
echo ""
echo "🚀 Your AutoTasker AI is now running in the cloud!"
