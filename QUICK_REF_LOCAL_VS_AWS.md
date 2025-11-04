# 🎯 Quick Reference: Local vs AWS

## Two Separate Systems

### 🖥️ LOCAL (Streamlit)
**Runs on**: Your computer  
**Command**: `streamlit run frontend/streamlit_app.py`  
**Storage**: `logs/` folder on your disk  
**Requires**: Your PC to be ON  
**Use for**: Testing, debugging, manual tasks  

### ☁️ AWS (Lambda)
**Runs on**: AWS Cloud  
**Command**: Automatic (EventBridge triggers)  
**Storage**: S3 bucket + CloudWatch  
**Requires**: Nothing (works when PC is OFF)  
**Use for**: Scheduled tasks, production  

---

## Build & Deploy to AWS

```powershell
# Option 1: Use the automated script
.\build_and_deploy_lambda.ps1

# Option 2: Manual steps
Rename-Item requirements.txt requirements_local_backup.txt
Copy-Item lambda_requirements.txt requirements.txt
sam build
sam deploy --guided
Remove-Item requirements.txt
Rename-Item requirements_local_backup.txt requirements.txt
```

---

## After Deployment

### ❌ MYTH:
*"If I run Streamlit locally, it will use AWS Lambda"*

### ✅ REALITY:
**Local Streamlit = Local execution**  
**AWS Lambda = Cloud execution**  
**They DON'T connect automatically!**

---

## View AWS Results

```powershell
# Lambda logs
aws logs tail /aws/lambda/autotasker-ai-production --follow

# S3 results
aws s3 ls s3://autotasker-ai-storage-{account-id}-production/

# Test Lambda
aws lambda invoke --function-name autotasker-ai-production \
  --payload '{"prompt": "test"}' response.json
```

---

## EventBridge Schedule

**Default**: 9 AM UTC daily  
**Task**: "Execute daily scheduled tasks - send LeetCode questions"  
**Your PC**: Can be OFF  

**To change**:  
AWS Console → EventBridge → Rules → autotasker-daily-schedule-production

---

## Costs (Estimate)

For 1-2 tasks per day:

- Lambda: **FREE** (under 1M requests/month)
- S3: **FREE** (under 5GB storage)
- DynamoDB: **FREE** (under 25GB)
- CloudWatch: **~$1/month** (logs retention)

**Total: ~$1/month or FREE**

---

## Read Full Guide

📖 **LOCAL_VS_AWS_EXECUTION.md** - Complete explanation  
🚀 **AWS_DEPLOYMENT_AND_SCHEDULING_GUIDE.md** - Deployment details
