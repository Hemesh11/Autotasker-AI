# AWS SAM CLI Installation Guide for Windows

## Method 1: Download MSI Installer (Recommended - Easiest)

### Step 1: Download SAM CLI
1. Open your browser and go to:
   **https://github.com/aws/aws-sam-cli/releases/latest**

2. Download the file named:
   **AWS_SAM_CLI_64_PY3.msi**
   (Usually around 200-300 MB)

### Step 2: Install
1. Double-click the downloaded MSI file
2. Click "Next" through the installation wizard
3. Accept the license agreement
4. Choose installation location (default is fine)
5. Click "Install"
6. Click "Finish"

### Step 3: Verify Installation
Open a **NEW** PowerShell window and run:
```powershell
sam --version
```

You should see something like:
```
SAM CLI, version 1.108.0
```

---

## Method 2: Using pip (If you prefer)

```powershell
# Install SAM CLI via pip
pip install aws-sam-cli

# Verify
sam --version
```

**Note**: The pip method may have dependency conflicts. MSI installer is more reliable.

---

## Method 3: Using Chocolatey (If you want to install Chocolatey first)

### Install Chocolatey first:
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### Then install SAM CLI:
```powershell
choco install aws-sam-cli
```

---

## After Installation

### 1. Configure AWS Credentials (Required)
```powershell
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Get from AWS Console → IAM → Users → Your User → Security Credentials
- **AWS Secret Access Key**: Same place as above
- **Default region**: e.g., `us-east-1` (or your preferred region)
- **Default output format**: `json` (recommended)

### 2. Verify AWS Configuration
```powershell
aws sts get-caller-identity
```

Should show your AWS account info.

### 3. Build and Deploy AutoTasker AI
```powershell
# Use the automated script
.\build_and_deploy_lambda.ps1

# OR manually:
cd "C:\Users\hemes\Desktop\sem 6 project\IMPLEMENTATION"
Rename-Item requirements.txt requirements_local_backup.txt
Copy-Item lambda_requirements.txt requirements.txt
sam build
sam deploy --guided
Remove-Item requirements.txt
Rename-Item requirements_local_backup.txt requirements.txt
```

---

## Troubleshooting

### Issue: "sam: command not found" after installation
**Solution**: Close and reopen PowerShell (PATH needs to refresh)

### Issue: "AWS credentials not configured"
**Solution**: Run `aws configure` and enter your credentials

### Issue: "sam build fails with permission error"
**Solution**: Run PowerShell as Administrator

### Issue: "Cannot find AWS CLI"
**Solution**: Install AWS CLI first from https://aws.amazon.com/cli/

---

## Quick Links

- **SAM CLI Download**: https://github.com/aws/aws-sam-cli/releases/latest
- **AWS CLI Download**: https://aws.amazon.com/cli/
- **SAM Documentation**: https://docs.aws.amazon.com/serverless-application-model/
- **Get AWS Credentials**: AWS Console → IAM → Users → Security Credentials

---

## Next Steps After Installation

1. ✅ Install SAM CLI (this guide)
2. ✅ Configure AWS credentials (`aws configure`)
3. ✅ Build Lambda package (`sam build`)
4. ✅ Deploy to AWS (`sam deploy --guided`)
5. ✅ Test Lambda function
6. ✅ Set up EventBridge schedule (already in template.yaml)

---

## IMPORTANT REMINDER

After deployment:
- **Local Streamlit STILL runs locally** (on your computer)
- **AWS Lambda runs in the cloud** (independently)
- **They are SEPARATE systems**
- **Read LOCAL_VS_AWS_EXECUTION.md for full explanation**

Your computer can be OFF and AWS Lambda will still execute scheduled tasks! 🚀
