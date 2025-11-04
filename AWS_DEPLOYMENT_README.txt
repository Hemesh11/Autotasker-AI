# AutoTasker AI - AWS SAM Deployment

## Quick Start

### 1. Prerequisites
```cmd
conda activate autotasker
aws configure  # Set your AWS credentials
sam --version  # Verify SAM CLI installed
```

### 2. Build
```cmd
sam build
```

### 3. Deploy
```cmd
sam deploy --guided
```

### 4. Test
```cmd
curl -X POST https://[your-api-url]/prod/execute \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"test deployment\"}"
```

## Files Created

- `template.yaml` - AWS SAM template defining all resources
- `samconfig.toml` - SAM CLI configuration
- `events/test-event.json` - Test event for local testing
- `events/scheduled-event.json` - Scheduled event format
- `DEPLOYMENT_CHECKLIST.txt` - Complete deployment guide

## Local Testing

```cmd
# Test Lambda function locally
sam local invoke AutoTaskerFunction -e events/test-event.json

# Start API Gateway locally
sam local start-api

# Then test with:
curl -X POST http://localhost:3000/execute \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"test\"}"
```

## Deployed Resources

After deployment, you'll have:

- **Lambda Function**: `autotasker-ai-production`
- **API Gateway**: `autotasker-api-production` 
- **DynamoDB Table**: `autotasker-memory-production`
- **S3 Bucket**: `autotasker-ai-storage-[account-id]-production`
- **EventBridge Rule**: Daily execution at 9 AM UTC
- **CloudWatch Logs**: `/aws/lambda/autotasker-ai-production`
- **CloudWatch Alarms**: Error and throttle monitoring

## Configuration

### API Keys (Required)
Set during deployment:
- `OpenRouterApiKey` - Your OpenRouter API key
- `OpenAIApiKey` - Your OpenAI API key (alternative)
- `GitHubToken` - GitHub personal access token (optional)
- `GmailAddress` - Your Gmail address

### Secrets Manager (Required)
Must be created before deployment:
- `autotasker/gmail-credentials` - Gmail OAuth credentials
- `autotasker/gmail-token` - Gmail OAuth token

Upload token with:
```cmd
python aws/upload_gmail_token.py
```

## Monitoring

### View Logs
```cmd
sam logs -n AutoTaskerFunction --tail
```

### CloudWatch Console
```
AWS Console → CloudWatch → Log groups → /aws/lambda/autotasker-ai-production
```

### Metrics
```
AWS Console → Lambda → autotasker-ai-production → Monitoring
```

## Cost Estimate

**Free Tier (First 12 months):**
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- DynamoDB: 25 GB storage free
- S3: 5 GB storage free

**After Free Tier:**
- Light usage (100 workflows/month): ~$2-5
- Medium usage (1,000 workflows/month): ~$8-15
- Heavy usage (10,000 workflows/month): ~$50-100

## Update Deployment

```cmd
# Make code changes
# Test locally
sam build
sam deploy  # No --guided needed
```

## Rollback

```cmd
# Delete stack and all resources
sam delete --stack-name autotasker-ai-stack
```

## Troubleshooting

**Build Fails:**
- Check Python version: `python --version` (need 3.11+)
- Reinstall dependencies: `pip install -r requirements.txt`

**Deploy Fails:**
- Verify AWS credentials: `aws sts get-caller-identity`
- Check IAM permissions
- Review CloudFormation events in AWS Console

**Lambda Errors:**
- Check CloudWatch Logs
- Verify Secrets Manager secrets exist
- Ensure API keys are correct

## Support

- Full Guide: `docs/AWS_DEPLOYMENT_GUIDE.md`
- Gmail Setup: `docs/GMAIL_AWS_SETUP.md`
- Deployment Checklist: `DEPLOYMENT_CHECKLIST.txt`
- GitHub: https://github.com/Hemesh11/Autotasker-AI

## Next Steps

1. ✅ Complete AWS services setup (S3, DynamoDB, SES, Secrets Manager)
2. ✅ Upload Gmail token: `python aws/upload_gmail_token.py`
3. ✅ Build: `sam build`
4. ✅ Deploy: `sam deploy --guided`
5. ✅ Test API endpoint
6. ✅ Verify scheduled execution
7. ✅ Set up CloudWatch alarms
8. ✅ Monitor costs

**Your AutoTasker AI is ready for AWS deployment! 🚀**
