# Gmail Setup for AWS Lambda Deployment

## Overview
Gmail authentication in AWS Lambda requires special setup because OAuth 2.0 interactive flow cannot run in serverless environment. This guide explains how to set it up properly.

## How It Works

### Local Development
```
1. You run OAuth flow locally (interactive browser)
2. Credentials saved to google_auth/gmail_token.json
3. Gmail Agent uses local file
```

### AWS Lambda (Production)
```
1. Upload credentials.json to AWS Secrets Manager
2. Upload gmail_token.json to AWS Secrets Manager
3. Gmail Agent retrieves from Secrets Manager
4. Uses refresh token to get new access tokens automatically
```

## Step-by-Step Setup

### Part 1: Local Setup (One-Time)

#### 1. Complete Gmail OAuth Flow Locally
```cmd
cd c:\Users\hemes\Desktop\sem 6 project\IMPLEMENTATION
conda activate autotasker
python test_gmail_agent_individual.py
```

**What happens:**
- Browser opens for Google sign-in
- You authorize AutoTasker AI
- Token saved to `google_auth/gmail_token.json`
- ✅ Gmail now works locally!

#### 2. Verify Files Exist
```cmd
dir google_auth\
```

You should see:
```
✅ credentials.json  (OAuth client credentials)
✅ gmail_token.json   (Your authorized token with refresh_token)
```

---

### Part 2: Upload to AWS Secrets Manager

#### 3. Upload OAuth Credentials
```cmd
# Already done in main setup guide
# Secret name: autotasker/gmail-credentials
# Contains: credentials.json content
```

#### 4. Upload Gmail Token (IMPORTANT!)
```cmd
python aws/upload_gmail_token.py
```

**What this does:**
- Reads `google_auth/gmail_token.json`
- Uploads to AWS Secrets Manager
- Secret name: `autotasker/gmail-token`
- ✅ Gmail will now work in Lambda!

---

### Part 3: Configure Lambda

#### 5. Update Lambda IAM Role
Your Lambda needs permission to access both secrets:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:eu-north-1:*:secret:autotasker/gmail-credentials-*",
        "arn:aws:secretsmanager:eu-north-1:*:secret:autotasker/gmail-token-*"
      ]
    }
  ]
}
```

**In SAM template.yaml**, this is already configured:
```yaml
Policies:
  - SecretsManagerReadWrite  # Grants access to all secrets
```

#### 6. Update Lambda Environment Variables
```yaml
Environment:
  Variables:
    AWS_DEFAULT_REGION: eu-north-1  # Your region
    GMAIL_CREDENTIALS_SECRET: autotasker/gmail-credentials
    GMAIL_TOKEN_SECRET: autotasker/gmail-token
```

---

## How Gmail Agent Detects Environment

The updated Gmail Agent automatically detects where it's running:

```python
# Checks for AWS Lambda environment
self.is_aws = os.getenv('AWS_EXECUTION_ENV') is not None

if self.is_aws:
    # Use AWS Secrets Manager
    credentials = get_from_secrets_manager()
else:
    # Use local files
    credentials = read_from_file()
```

---

## Testing

### Test Locally
```cmd
conda activate autotasker
python test_gmail_agent_individual.py
```

Should use `google_auth/gmail_token.json`

### Test in Lambda
```cmd
# After deploying
sam build
sam deploy

# Test with curl
curl -X POST https://your-api-gateway-url/prod/execute \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"send me test email\"}"
```

Should use AWS Secrets Manager

---

## Troubleshooting

### Error: "Token file not found"
**Local:** Run OAuth flow: `python test_gmail_agent_individual.py`

**Lambda:** Upload token: `python aws/upload_gmail_token.py`

### Error: "Failed to retrieve from Secrets Manager"
**Check:**
1. Secret exists: AWS Console → Secrets Manager
2. Secret name matches: `autotasker/gmail-token`
3. Lambda has permission: Check IAM role
4. Region matches: `eu-north-1` (your region)

### Error: "Refresh token missing"
**Problem:** Token doesn't have refresh_token

**Fix:**
1. Delete `google_auth/gmail_token.json`
2. Run OAuth flow again: `python test_gmail_agent_individual.py`
3. Make sure you see "access_type=offline" in OAuth URL
4. Re-upload: `python aws/upload_gmail_token.py`

### Error: "Invalid grant" in Lambda
**Problem:** Refresh token expired or revoked

**Fix:**
1. Run OAuth flow locally again
2. Upload new token: `python aws/upload_gmail_token.py`

---

## Security Best Practices

### ✅ DO:
- Store tokens in AWS Secrets Manager
- Use IAM policies for access control
- Enable CloudTrail logging
- Rotate tokens periodically (every 6-12 months)
- Delete local tokens after upload (optional)

### ❌ DON'T:
- Commit tokens to Git (already in .gitignore)
- Share tokens in plain text
- Use root AWS credentials
- Leave tokens in Lambda environment variables

---

## Token Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│ 1. ONE-TIME LOCAL SETUP                                 │
│    Run: python test_gmail_agent_individual.py          │
│    Creates: google_auth/gmail_token.json               │
│    Contains: access_token + refresh_token              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. UPLOAD TO AWS (ONE-TIME)                            │
│    Run: python aws/upload_gmail_token.py               │
│    Creates: autotasker/gmail-token in Secrets Manager │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. LAMBDA RUNTIME (AUTOMATIC)                          │
│    - Retrieves token from Secrets Manager             │
│    - Uses refresh_token to get new access_token       │
│    - Access token expires every 1 hour                │
│    - Refresh token lasts indefinitely (until revoked) │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Reference

### Files Involved
```
Local:
  google_auth/credentials.json  → OAuth client config
  google_auth/gmail_token.json  → Your authorized token

AWS Secrets Manager:
  autotasker/gmail-credentials  → OAuth client config
  autotasker/gmail-token       → Your authorized token
```

### Key Commands
```cmd
# Initial OAuth (one-time)
python test_gmail_agent_individual.py

# Upload to AWS (one-time)
python aws/upload_gmail_token.py

# Deploy to Lambda
sam build && sam deploy

# Test Lambda
curl -X POST {api-gateway-url}/prod/execute \
  -d "{\"prompt\": \"test gmail\"}"
```

### Important Environment Variables
```properties
# Local (.env)
GMAIL_ADDRESS=hemeshcse2005@gmail.com
GMAIL_CREDENTIALS_PATH=google_auth/credentials.json

# Lambda (SAM template)
AWS_DEFAULT_REGION=eu-north-1
GMAIL_CREDENTIALS_SECRET=autotasker/gmail-credentials
GMAIL_TOKEN_SECRET=autotasker/gmail-token
```

---

## FAQ

**Q: Do I need to re-upload the token every time?**  
A: No! Only once. The refresh token allows Lambda to get new access tokens automatically.

**Q: What if I revoke access in Google Console?**  
A: Run OAuth flow locally again, then re-upload token.

**Q: Can I use Gmail in Lambda without this setup?**  
A: No. OAuth 2.0 requires initial interactive authorization which can't run in Lambda.

**Q: Is the token safe in Secrets Manager?**  
A: Yes! AWS Secrets Manager encrypts all secrets at rest and in transit.

**Q: How long does the refresh token last?**  
A: Indefinitely, until you revoke it in Google Console.

---

## Summary Checklist

- [ ] ✅ Gmail credentials.json in `google_auth/`
- [ ] ✅ Run OAuth locally: `python test_gmail_agent_individual.py`
- [ ] ✅ gmail_token.json created successfully
- [ ] ✅ Upload credentials to Secrets Manager (already done in main guide)
- [ ] ✅ Upload token to Secrets Manager: `python aws/upload_gmail_token.py`
- [ ] ✅ Verify both secrets exist in AWS Console
- [ ] ✅ Lambda IAM role has SecretsManager permissions
- [ ] ✅ Deploy Lambda: `sam build && sam deploy`
- [ ] ✅ Test Lambda with Gmail task

**Your Gmail Agent is now ready for AWS Lambda! 🚀**
