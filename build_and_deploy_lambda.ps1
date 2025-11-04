# AWS Lambda Build Script
# This script handles the requirements file switching for Lambda deployment

Write-Host "`n=== AutoTasker AI - Lambda Build Script ===" -ForegroundColor Cyan
Write-Host "This script will build and deploy AutoTasker AI to AWS Lambda`n" -ForegroundColor White

# Check if SAM CLI is installed
Write-Host "[1/6] Checking SAM CLI installation..." -ForegroundColor Yellow
try {
    $samVersion = sam --version
    Write-Host "✅ SAM CLI found: $samVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ SAM CLI not found! Please install from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" -ForegroundColor Red
    exit 1
}

# Check if AWS CLI is configured
Write-Host "`n[2/6] Checking AWS credentials..." -ForegroundColor Yellow
try {
    $awsIdentity = aws sts get-caller-identity --query 'Account' --output text 2>$null
    if ($awsIdentity) {
        Write-Host "✅ AWS credentials configured (Account: $awsIdentity)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ AWS credentials not found. Please run: aws configure" -ForegroundColor Red
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne 'y') { exit 1 }
    }
} catch {
    Write-Host "⚠️ Could not verify AWS credentials" -ForegroundColor Red
}

# Backup original requirements.txt
Write-Host "`n[3/6] Switching to Lambda-specific requirements..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    if (Test-Path "requirements_local_backup.txt") {
        Remove-Item "requirements_local_backup.txt" -Force
    }
    Rename-Item "requirements.txt" "requirements_local_backup.txt"
    Write-Host "✅ Backed up local requirements to requirements_local_backup.txt" -ForegroundColor Green
}

# Copy Lambda requirements
if (Test-Path "lambda_requirements.txt") {
    Copy-Item "lambda_requirements.txt" "requirements.txt"
    Write-Host "✅ Using lambda_requirements.txt (no Streamlit)" -ForegroundColor Green
} else {
    Write-Host "❌ lambda_requirements.txt not found!" -ForegroundColor Red
    # Restore backup
    if (Test-Path "requirements_local_backup.txt") {
        Rename-Item "requirements_local_backup.txt" "requirements.txt"
    }
    exit 1
}

# Build Lambda
Write-Host "`n[4/6] Building Lambda function..." -ForegroundColor Yellow
Write-Host "This may take 2-3 minutes..." -ForegroundColor Gray
sam build

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Build failed!" -ForegroundColor Red
    Write-Host "Restoring local requirements..." -ForegroundColor Yellow
    Remove-Item "requirements.txt" -Force
    Rename-Item "requirements_local_backup.txt" "requirements.txt"
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

# Ask user if they want to deploy
Write-Host "`n[5/6] Deploy to AWS?" -ForegroundColor Yellow
$deploy = Read-Host "Deploy now? (Y/n)"

if ($deploy -eq '' -or $deploy -eq 'y' -or $deploy -eq 'Y') {
    Write-Host "`nDeploying to AWS..." -ForegroundColor Yellow
    Write-Host "You will be prompted for configuration (API keys, region, etc.)`n" -ForegroundColor Gray
    
    sam deploy --guided
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Deployment successful!" -ForegroundColor Green
        
        # Show useful info
        Write-Host "`n=== Important Information ===" -ForegroundColor Cyan
        Write-Host "1. View logs: aws logs tail /aws/lambda/autotasker-ai-production --follow" -ForegroundColor White
        Write-Host "2. Test Lambda: aws lambda invoke --function-name autotasker-ai-production --payload '{`"prompt`": `"test`"}' response.json" -ForegroundColor White
        Write-Host "3. List S3 results: aws s3 ls s3://autotasker-ai-storage-{account-id}-production/" -ForegroundColor White
        Write-Host "4. EventBridge: AWS Console -> EventBridge -> Rules -> autotasker-daily-schedule-production" -ForegroundColor White
    } else {
        Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    }
} else {
    Write-Host "Skipping deployment. Run 'sam deploy --guided' manually later." -ForegroundColor Gray
}

# Restore local requirements
Write-Host "`n[6/6] Restoring local requirements..." -ForegroundColor Yellow
Remove-Item "requirements.txt" -Force
Rename-Item "requirements_local_backup.txt" "requirements.txt"
Write-Host "✅ Restored requirements.txt for local development" -ForegroundColor Green

Write-Host "`n=== Build Process Complete ===" -ForegroundColor Cyan
Write-Host "`nIMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "- Your LOCAL Streamlit still runs on YOUR computer" -ForegroundColor White
Write-Host "- AWS Lambda runs in the CLOUD independently" -ForegroundColor White
Write-Host "- They are SEPARATE systems (not automatically connected)" -ForegroundColor White
Write-Host "- EventBridge will trigger Lambda daily at 9 AM UTC" -ForegroundColor White
Write-Host "- Your computer can be OFF for scheduled tasks" -ForegroundColor White
Write-Host "`nRead LOCAL_VS_AWS_EXECUTION.md for detailed explanation`n" -ForegroundColor Cyan
