# AutoTasker AI AWS Deployment (PowerShell)
# Automates the complete deployment of AutoTasker AI to AWS

param(
    [string]$Region = "us-east-1",
    [string]$Environment = "production",
    [string]$ProjectName = "AutoTaskerAI"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 AutoTasker AI AWS Deployment" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check AWS CLI
try {
    aws --version | Out-Null
    Write-Host "✅ AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   https://aws.amazon.com/cli/" -ForegroundColor Red
    exit 1
}

# Check Python
try {
    python --version | Out-Null
    Write-Host "✅ Python found" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS credentials configured" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Please run: aws configure" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Configuration
$StackName = "$ProjectName-$Environment"

Write-Host "📝 Configuration:" -ForegroundColor Yellow
Write-Host "   Project: $ProjectName" -ForegroundColor White
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host "   Environment: $Environment" -ForegroundColor White
Write-Host "   Stack: $StackName" -ForegroundColor White

# Get required parameters
$LLMApiKey = Read-Host "🔑 Enter your LLM API key" -AsSecureString
$LLMApiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($LLMApiKey))
$FromEmail = Read-Host "📧 Enter FROM email address"
$ToEmail = Read-Host "📧 Enter TO email address"

# Validate email addresses for SES
Write-Host "📧 Validating email addresses with SES..." -ForegroundColor Yellow
try {
    aws ses verify-email-identity --email-address $FromEmail --region $Region
    if ($FromEmail -ne $ToEmail) {
        aws ses verify-email-identity --email-address $ToEmail --region $Region
    }
    Write-Host "✅ Email verification initiated" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Email verification may be needed manually" -ForegroundColor Yellow
}

# Step 1: Generate CloudFormation template
Write-Host "📄 Generating CloudFormation template..." -ForegroundColor Yellow
python aws/cloudformation.py

# Step 2: Create deployment package
Write-Host "📦 Creating deployment package..." -ForegroundColor Yellow
$DeployDir = "aws\deploy"
New-Item -ItemType Directory -Force -Path $DeployDir | Out-Null

# Create Lambda layer for dependencies
Write-Host "📚 Creating dependencies layer..." -ForegroundColor Yellow
$LayerDir = "$DeployDir\python"
New-Item -ItemType Directory -Force -Path $LayerDir | Out-Null

# Install dependencies to layer
pip install -r requirements.txt --target $LayerDir --quiet

# Create layer zip
Set-Location $DeployDir
Compress-Archive -Path "python\*" -DestinationPath "dependencies.zip" -Force
Set-Location ..\..

# Create function deployment package
Write-Host "📦 Creating function package..." -ForegroundColor Yellow
$FunctionZip = "$DeployDir\autotasker.zip"

$FilesToZip = @(
    "backend\*",
    "agents\*", 
    "aws\lambda_handler.py",
    "config\config.yaml"
)

Compress-Archive -Path $FilesToZip -DestinationPath $FunctionZip -Force

Write-Host "✅ Deployment packages created" -ForegroundColor Green

# Step 3: Upload artifacts to S3
Write-Host "☁️  Uploading deployment artifacts..." -ForegroundColor Yellow

# Create temporary bucket for deployment artifacts
$TempBucket = "$($ProjectName.ToLower())-deploy-$(Get-Date -Format 'yyyyMMddHHmmss')"
aws s3 mb "s3://$TempBucket" --region $Region

# Upload layer and function
aws s3 cp "$DeployDir\dependencies.zip" "s3://$TempBucket/layers/dependencies.zip"
aws s3 cp $FunctionZip "s3://$TempBucket/functions/autotasker.zip"

Write-Host "✅ Artifacts uploaded to s3://$TempBucket" -ForegroundColor Green

# Step 4: Deploy CloudFormation stack
Write-Host "🏗️  Deploying CloudFormation stack..." -ForegroundColor Yellow

# Update template to use the temporary bucket
$TemplateContent = Get-Content "aws\autotasker-infrastructure.json" -Raw
$TemplateContent = $TemplateContent -replace '\$\{LogsBucket\}', $TempBucket
$TemplateContent | Set-Content "aws\autotasker-infrastructure-temp.json"

$Parameters = @(
    "ParameterKey=ProjectName,ParameterValue=$ProjectName",
    "ParameterKey=Environment,ParameterValue=$Environment", 
    "ParameterKey=LLMApiKey,ParameterValue=$LLMApiKeyPlain",
    "ParameterKey=FromEmail,ParameterValue=$FromEmail",
    "ParameterKey=ToEmail,ParameterValue=$ToEmail"
)

aws cloudformation create-stack `
    --stack-name $StackName `
    --template-body "file://aws/autotasker-infrastructure-temp.json" `
    --capabilities CAPABILITY_NAMED_IAM `
    --parameters $Parameters `
    --region $Region

Write-Host "⏳ Waiting for stack deployment to complete..." -ForegroundColor Yellow
aws cloudformation wait stack-create-complete --stack-name $StackName --region $Region

# Step 5: Get outputs
Write-Host "📊 Getting deployment outputs..." -ForegroundColor Yellow
$OutputsJson = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query 'Stacks[0].Outputs'
$Outputs = $OutputsJson | ConvertFrom-Json

$LambdaArn = ($Outputs | Where-Object { $_.OutputKey -eq "LambdaFunctionArn" }).OutputValue
$S3Bucket = ($Outputs | Where-Object { $_.OutputKey -eq "S3BucketName" }).OutputValue
$DynamoDBTable = ($Outputs | Where-Object { $_.OutputKey -eq "DynamoDBTableName" }).OutputValue
$DashboardUrl = ($Outputs | Where-Object { $_.OutputKey -eq "DashboardURL" }).OutputValue

# Step 6: Clean up temporary bucket
Write-Host "🧹 Cleaning up temporary resources..." -ForegroundColor Yellow
aws s3 rm "s3://$TempBucket" --recursive
aws s3 rb "s3://$TempBucket"
Remove-Item "aws\autotasker-infrastructure-temp.json" -Force

# Step 7: Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
$TestEvent = @{
    prompt = "Generate a simple coding question and email it to me"
    task_id = "deployment-test"
    test = $true
} | ConvertTo-Json

$TestEvent | Out-File -FilePath "$DeployDir\test-event.json" -Encoding UTF8

try {
    aws lambda invoke `
        --function-name "$ProjectName-runner-$Environment" `
        --payload "file://$DeployDir/test-event.json" `
        --region $Region `
        "$DeployDir\test-response.json"
    
    Write-Host "✅ Test invocation successful" -ForegroundColor Green
    Get-Content "$DeployDir\test-response.json"
} catch {
    Write-Host "⚠️  Test invocation failed, but deployment may still be successful" -ForegroundColor Yellow
}

# Step 8: Display summary
Write-Host ""
Write-Host "🎉 AutoTasker AI Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Deployment Summary:" -ForegroundColor Yellow
Write-Host "   Stack Name: $StackName" -ForegroundColor White
Write-Host "   Region: $Region" -ForegroundColor White
Write-Host "   Lambda Function: $LambdaArn" -ForegroundColor White
Write-Host "   S3 Bucket: $S3Bucket" -ForegroundColor White
Write-Host "   DynamoDB Table: $DynamoDBTable" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitoring:" -ForegroundColor Yellow
Write-Host "   CloudWatch Dashboard: $DashboardUrl" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify email addresses in SES if you haven't already" -ForegroundColor White
Write-Host "2. Test the function with: aws lambda invoke --function-name $ProjectName-runner-$Environment --payload '{`"prompt`":`"test`"}' response.json" -ForegroundColor White
Write-Host "3. Create EventBridge rules for scheduled tasks" -ForegroundColor White
Write-Host "4. Update your local .env file with the deployed resources:" -ForegroundColor White
Write-Host ""
Write-Host "   # Add to config/.env" -ForegroundColor Gray
Write-Host "   AWS_LAMBDA_FUNCTION_NAME=$ProjectName-runner-$Environment" -ForegroundColor Gray
Write-Host "   AWS_S3_BUCKET=$S3Bucket" -ForegroundColor Gray
Write-Host "   AWS_DYNAMODB_TABLE=$DynamoDBTable" -ForegroundColor Gray
Write-Host ""
Write-Host "🚀 Your AutoTasker AI is now running in the cloud!" -ForegroundColor Green
