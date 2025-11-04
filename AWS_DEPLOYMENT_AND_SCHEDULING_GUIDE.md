# 🚀 AWS Deployment & Scheduling Guide

**Complete guide for deploying AutoTasker AI to AWS and understanding scheduling**

---

## 📋 Table of Contents

1. [AWS Deployment Overview](#aws-deployment-overview)
2. [What Changes After AWS Deployment](#what-changes-after-deployment)
3. [Scheduling in AWS](#scheduling-in-aws)
4. [Example: Daily LeetCode at 9am](#example-daily-leetcode-at-9am)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Troubleshooting](#troubleshooting)

---

## 🌐 AWS Deployment Overview

### **Current State (Local)**
```
┌─────────────────────┐
│   Your Computer     │
│                     │
│  ┌──────────────┐   │
│  │  Streamlit   │   │  ← Manual execution
│  │   Frontend   │   │  ← You trigger tasks
│  └──────────────┘   │
│         ↓           │
│  ┌──────────────┐   │
│  │  LangGraph   │   │  ← Runs on your machine
│  │   Backend    │   │  ← Uses your resources
│  └──────────────┘   │
└─────────────────────┘
```

### **After AWS Deployment**
```
┌───────────────────────────────────────────────┐
│               AWS Cloud                        │
│                                               │
│  ┌──────────────┐    ┌───────────────────┐   │
│  │  EventBridge │───→│  Lambda Function  │   │
│  │  Scheduler   │    │  (AutoTasker AI)  │   │
│  └──────────────┘    └───────────────────┘   │
│     Automatic              Cloud Execution    │
│     Triggers               24/7 Available     │
│                                               │
│  ┌──────────────┐    ┌───────────────────┐   │
│  │     S3       │    │      SES          │   │
│  │   Storage    │    │   Email Service   │   │
│  └──────────────┘    └───────────────────┘   │
└───────────────────────────────────────────────┘
           ↓
    📧 Results emailed to you
```

---

## 🔄 What Changes After AWS Deployment?

### **✅ What Stays the SAME**

| Feature | Local | AWS | Notes |
|---------|-------|-----|-------|
| **Prompts** | ✅ Same | ✅ Same | All prompts work identically |
| **Agents** | ✅ Same | ✅ Same | Gmail, GitHub, LeetCode, etc. |
| **Results** | ✅ Email | ✅ Email | Always emailed to you |
| **Quality** | ✅ Same | ✅ Same | Same AI models, same output |

### **🚀 What IMPROVES**

| Feature | Local | AWS | Benefit |
|---------|-------|-----|---------|
| **Availability** | ⏰ Only when computer is on | ⏰ 24/7 always running | Never miss a schedule |
| **Scheduling** | ⚠️ Computer must be on | ✅ Automatic cloud triggers | Runs even when offline |
| **Reliability** | ⚠️ Can crash if computer sleeps | ✅ AWS manages restarts | Production-grade |
| **Scalability** | ⚠️ Limited by your computer | ✅ Auto-scales with AWS | Handle many tasks |
| **Maintenance** | ⚠️ You manage everything | ✅ AWS manages servers | Less work for you |

### **📝 What You CONFIGURE Differently**

| Configuration | Local | AWS |
|---------------|-------|-----|
| **API Keys** | `.env` file | AWS Secrets Manager |
| **Gmail Token** | `google_auth/token.json` | AWS S3 bucket |
| **Logs** | Local `data/logs/` | AWS CloudWatch + S3 |
| **Scheduling** | Manual or local cron | AWS EventBridge |
| **Triggers** | Streamlit UI | EventBridge + API Gateway |

---

## ⏰ Scheduling in AWS: How It Works

### **Example Prompt: "Send me 2 LeetCode questions daily at 9am"**

#### **Local Execution (Before AWS)**
```
1. You run Streamlit frontend
2. You type prompt and click submit
3. System creates schedule in scheduler.py
4. APScheduler runs in background
5. ⚠️ PROBLEM: Computer must stay on!
6. ⚠️ PROBLEM: If computer sleeps, schedule stops
```

#### **AWS Execution (After Deployment)**
```
1. You type prompt once (via Streamlit or API)
2. System creates EventBridge schedule rule
3. EventBridge stores schedule in cloud
4. ✅ Your computer can turn off
5. ✅ Every day at 9am UTC:
   - EventBridge triggers Lambda function
   - Lambda executes LeetCode agent
   - Lambda sends email with results
6. ✅ Runs forever until you delete schedule
```

---

## 📅 Example: Daily LeetCode at 9am

### **How It Works in AWS**

**1. Initial Setup (One Time)**
```bash
# Deploy to AWS
sam build
sam deploy --guided

# Result: Lambda function created in AWS
```

**2. Creating the Schedule (One Time)**
```
Prompt: "Send me 2 LeetCode questions daily at 9am"

What happens:
├─ Planner Agent: Parses "daily at 9am"
├─ Scheduler: Detects daily schedule
├─ AWS EventBridge: Creates cron rule
│  Rule: cron(0 9 * * ? *)
│  Target: AutoTasker Lambda function
│  Payload: {task: "leetcode", count: 2}
└─ Confirmation: "Schedule created!"
```

**3. Daily Execution (Automatic)**
```
Every day at 9:00 AM UTC:

09:00:00 → EventBridge triggers Lambda
09:00:01 → Lambda starts execution
09:00:02 → LeetCode agent fetches 2 problems
09:00:15 → Email agent sends results to you
09:00:16 → Lambda execution complete
09:00:17 → Logs saved to CloudWatch

📧 You receive email with LeetCode questions!
```

**4. Monitoring**
```
AWS Console:
├─ EventBridge → Rules → See your schedule
├─ Lambda → Functions → See execution logs
├─ CloudWatch → Logs → See detailed output
├─ SES → Email Activity → See emails sent
└─ S3 → Logs Bucket → Historical logs
```

**5. Stopping the Schedule**
```
Option 1 - Via Streamlit:
  Go to "Scheduler" tab → Click "Delete Schedule"

Option 2 - Via AWS Console:
  EventBridge → Rules → Disable/Delete rule

Option 3 - Via Prompt:
  "Stop sending me daily LeetCode questions"
```

---

## 🔧 AWS Components Used

### **1. AWS Lambda**
```
Purpose: Run AutoTasker AI code
Trigger: EventBridge, API Gateway, or manual
Duration: Max 15 minutes per execution
Cost: First 1M requests free, then ~$0.20/1M
```

**What it does:**
- Executes your Python code (all agents)
- Connects to Gmail, GitHub, OpenAI APIs
- Sends emails via SES
- Logs to CloudWatch

### **2. AWS EventBridge (Scheduler)**
```
Purpose: Trigger Lambda on schedule
Supports: Cron expressions, rate expressions
Cost: First 1M events free, then ~$1/1M
```

**What it does:**
- Stores your daily/weekly schedules
- Triggers Lambda at exact times
- Handles timezone conversions
- Retry on failure

**Example Rules:**
```
Daily at 9am:     cron(0 9 * * ? *)
Every 5 min:      rate(5 minutes)
Weekly Monday:    cron(0 9 ? * MON *)
Twice daily:      cron(0 9,18 * * ? *)
```

### **3. AWS S3 (Storage)**
```
Purpose: Store logs and Gmail tokens
Cost: First 5GB free, then ~$0.023/GB
```

**What it stores:**
- Gmail OAuth tokens (google_auth/token.json)
- Execution logs
- Memory data (LeetCode history)
- Task history

### **4. AWS SES (Email Service)**
```
Purpose: Send result emails
Cost: First 62,000 emails free (via EC2), then $0.10/1,000
```

**What it does:**
- Sends LeetCode questions
- Sends GitHub summaries
- Sends all task results
- Handles email delivery

### **5. AWS CloudWatch (Monitoring)**
```
Purpose: Store and view logs
Cost: First 5GB free, then ~$0.50/GB
```

**What you can see:**
- Lambda execution logs
- Error messages
- Performance metrics
- Execution duration

### **6. API Gateway (Optional)**
```
Purpose: REST API for triggering tasks
Cost: First 1M calls free, then ~$3.50/1M
```

**What it enables:**
- Trigger tasks via HTTP POST
- Webhook integrations
- Mobile app integration
- External services

---

## 🛠️ Step-by-Step AWS Deployment

### **Prerequisites**
```bash
# Install AWS CLI
# Windows:
Download from: https://aws.amazon.com/cli/

# Install AWS SAM CLI
# Windows (using pip):
pip install aws-sam-cli

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)
```

### **Step 1: Prepare Gmail Token**
```bash
# Upload Gmail token to S3 (needed for Gmail agent)
python aws/upload_gmail_token.py

# This uploads google_auth/token.json to S3
# Lambda will read it from S3 during execution
```

### **Step 2: Build Lambda Package**
```bash
# Build the deployment package
sam build

# This creates:
# ├─ .aws-sam/build/
# │  └─ AutoTaskerFunction/
# │     ├─ All your Python code
# │     ├─ All dependencies
# │     └─ Lambda handler
```

### **Step 3: Deploy to AWS**
```bash
# Deploy for the first time
sam deploy --guided

# Answer prompts:
Stack Name: autotasker-ai
AWS Region: us-east-1
Confirm changes: y
Allow SAM CLI IAM role creation: y
Save arguments to configuration file: y

# Deployment takes 5-10 minutes
```

### **Step 4: Configure Environment Variables**
```bash
# After deployment, set environment variables in AWS Console:
# Lambda → Functions → AutoTaskerFunction → Configuration → Environment variables

Add:
- GITHUB_TOKEN
- GITHUB_DEFAULT_OWNER
- GITHUB_DEFAULT_REPO
- OPENROUTER_API_KEY
- AWS_S3_BUCKET
- AWS_SES_EMAIL
- GMAIL_ADDRESS
```

### **Step 5: Test Deployment**
```bash
# Test via AWS Console:
Lambda → Functions → Test tab → Create test event

Test payload:
{
  "prompt": "Send me 2 LeetCode questions",
  "schedule": "once",
  "time": "immediate"
}

# Or test via local invoke:
sam local invoke AutoTaskerFunction -e events/test_event.json
```

### **Step 6: Set Up Scheduling**
```
Two options:

Option A - Via Streamlit (Recommended):
1. Keep Streamlit running locally
2. It will create EventBridge rules when you submit scheduled tasks
3. Rules stored in AWS, execute in cloud

Option B - Via AWS Console:
1. EventBridge → Rules → Create rule
2. Schedule pattern: cron(0 9 * * ? *)
3. Target: Lambda function (AutoTaskerFunction)
4. Payload: {"prompt": "Send me 2 LeetCode questions"}
```

---

## 📊 Cost Estimate

### **Free Tier (First Year)**
```
AWS Lambda:     1M requests free     → ~30 tasks/day = FREE
EventBridge:    1M events free       → ~10 schedules = FREE
S3:             5GB storage free     → Logs/tokens = FREE
CloudWatch:     5GB logs free        → Monitoring = FREE
SES:            62K emails free      → ~170 emails/day = FREE

Total estimated cost: $0/month (within free tier)
```

### **After Free Tier**
```
Assumptions: 100 tasks/day, 10 active schedules

Lambda:         100 tasks × 30 days = 3,000 executions
                → 3,000/1M × $0.20 = $0.0006

EventBridge:    10 schedules × 30 = 300 triggers
                → FREE (under 1M/month)

S3:             1GB storage
                → $0.023

SES:            100 emails × 30 = 3,000 emails
                → 3,000/1,000 × $0.10 = $0.30

CloudWatch:     500MB logs
                → FREE (under 5GB)

Total estimated cost: ~$0.35/month
```

---

## 🎯 Scheduling Examples in AWS

### **1. Daily Task**
```
Prompt: "Send me 2 LeetCode questions daily at 9am"

EventBridge Rule:
  Name: leetcode-daily-9am
  Schedule: cron(0 9 * * ? *)
  Target: Lambda
  Payload: {
    "prompt": "Send me 2 LeetCode questions",
    "schedule": "daily",
    "time": "09:00"
  }

Result:
  ✅ Runs every day at 9:00 AM UTC
  ✅ Sends email with 2 LeetCode questions
  ✅ Continues until disabled
```

### **2. Weekly Task**
```
Prompt: "Summarize my GitHub commits every Monday at 10am"

EventBridge Rule:
  Name: github-summary-weekly
  Schedule: cron(0 10 ? * MON *)
  Target: Lambda
  Payload: {
    "prompt": "Summarize my GitHub commits from last week",
    "schedule": "weekly",
    "time": "10:00"
  }

Result:
  ✅ Runs every Monday at 10:00 AM UTC
  ✅ Fetches commits from last 7 days
  ✅ Sends summary email
```

### **3. Multiple Times Daily**
```
Prompt: "Send me coding questions at 9am and 6pm daily"

Two EventBridge Rules:
  Rule 1: leetcode-morning
    Schedule: cron(0 9 * * ? *)
  
  Rule 2: leetcode-evening
    Schedule: cron(0 18 * * ? *)

Result:
  ✅ Runs twice daily
  ✅ Morning and evening deliveries
```

### **4. Interval-Based (Limited)**
```
Prompt: "Send me questions now 3 times with 5 min gap"

Implementation:
  Lambda execution with internal loop:
    Iteration 1: Execute immediately
    Wait 5 minutes
    Iteration 2: Execute
    Wait 5 minutes
    Iteration 3: Execute
    Complete

Note: This is ONE Lambda execution, not a schedule
Max duration: 15 minutes (Lambda limit)
```

---

## 🐛 Troubleshooting

### **Issue: Schedule Not Triggering**

**Check:**
```
1. EventBridge Console:
   - Rule exists?
   - Rule is enabled?
   - Target is correct Lambda function?

2. Lambda Console:
   - Function has EventBridge trigger?
   - Environment variables set?

3. CloudWatch Logs:
   - Any error messages?
   - Lambda timing out?
```

**Fix:**
```bash
# Re-create EventBridge rule
aws events put-rule --name leetcode-daily \
  --schedule-expression "cron(0 9 * * ? *)"

# Add Lambda permission
aws lambda add-permission \
  --function-name AutoTaskerFunction \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com
```

### **Issue: Gmail Token Not Found**

**Check:**
```
1. S3 bucket exists?
2. Token file uploaded? (google_auth/token.json)
3. Lambda has S3 read permission?
```

**Fix:**
```bash
# Re-upload token
python aws/upload_gmail_token.py

# Verify upload
aws s3 ls s3://autotasker-logs/google_auth/
```

### **Issue: Email Not Sending**

**Check:**
```
1. SES email verified?
2. SES in production mode or sandbox?
3. AWS_SES_EMAIL set in Lambda environment?
```

**Fix:**
```bash
# Verify email in SES
aws ses verify-email-identity --email-address your@email.com

# Check verification status
aws ses get-identity-verification-attributes \
  --identities your@email.com
```

### **Issue: Lambda Timeout**

**Check:**
```
CloudWatch Logs:
  "Task timed out after 60.00 seconds"
```

**Fix:**
```bash
# Increase Lambda timeout (max 15 minutes)
aws lambda update-function-configuration \
  --function-name AutoTaskerFunction \
  --timeout 300  # 5 minutes
```

---

## 📞 Quick Reference

### **View Logs**
```bash
# Recent logs
aws logs tail /aws/lambda/AutoTaskerFunction --follow

# Specific execution
aws logs filter-log-events \
  --log-group-name /aws/lambda/AutoTaskerFunction \
  --filter-pattern "ERROR"
```

### **List Schedules**
```bash
# All EventBridge rules
aws events list-rules

# Specific rule details
aws events describe-rule --name leetcode-daily
```

### **Manual Trigger**
```bash
# Invoke Lambda manually
aws lambda invoke \
  --function-name AutoTaskerFunction \
  --payload '{"prompt":"Send me 2 LeetCode questions"}' \
  response.json

# View response
cat response.json
```

### **Delete Schedule**
```bash
# Remove EventBridge rule
aws events remove-targets --rule leetcode-daily --ids "1"
aws events delete-rule --name leetcode-daily
```

---

## ✅ Checklist: Before Going Live

- [ ] AWS credentials configured
- [ ] Gmail token uploaded to S3
- [ ] SES email verified
- [ ] Environment variables set in Lambda
- [ ] Test execution successful
- [ ] CloudWatch logs working
- [ ] EventBridge rule created
- [ ] Received test email
- [ ] Costs understood
- [ ] Monitoring set up

---

## 🎉 Summary

### **Deployment = Same Functionality + Cloud Benefits**

| Aspect | Local | AWS |
|--------|-------|-----|
| Prompts | ✅ Same | ✅ Same |
| Agents | ✅ Same | ✅ Same |
| Results | ✅ Email | ✅ Email |
| **Availability** | ⚠️ Manual | ✅ Automatic |
| **Reliability** | ⚠️ Your computer | ✅ AWS infrastructure |
| **Scheduling** | ⚠️ Limited | ✅ Enterprise-grade |

### **For "Daily LeetCode at 9am"**

**Local:**
- ⚠️ Computer must stay on
- ⚠️ If computer sleeps → schedule stops
- ⚠️ Manual restart needed

**AWS:**
- ✅ Runs automatically forever
- ✅ No computer needed
- ✅ Reliable and scalable

---

**🚀 Deploy once, schedule forever! Your AI assistant runs 24/7 in the cloud.**
