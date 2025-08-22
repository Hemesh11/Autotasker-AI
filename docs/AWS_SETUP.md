# AWS Credentials Setup Guide

This guide will help you obtain the necessary AWS credentials for AutoTasker AI.

## Prerequisites

1. **AWS Account**: You need an active AWS account. If you don't have one:
   - Go to [aws.amazon.com](https://aws.amazon.com)
   - Click "Create an AWS Account"
   - Follow the registration process (requires credit card)

## Getting AWS Credentials

### Step 1: Create IAM User

1. **Log into AWS Console**:
   - Go to [aws.amazon.com](https://aws.amazon.com)
   - Click "Sign In to the Console"
   - Enter your root account credentials

2. **Navigate to IAM**:
   - In the AWS Console, search for "IAM"
   - Click on "IAM" (Identity and Access Management)

3. **Create New User**:
   - Click "Users" in the left sidebar
   - Click "Create user"
   - Enter username (e.g., "autotasker-user")
   - Select "Programmatic access" (for API keys)
   - Click "Next"

### Step 2: Assign Permissions

1. **Attach Policies**:
   - Choose "Attach existing policies directly"
   - Search for and select these policies:
     - `AmazonS3FullAccess` (for file storage)
     - `AmazonSESFullAccess` (for email sending)
     - Or create a custom policy with minimal required permissions

2. **Custom Policy (Recommended)**:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:GetObject",
                   "s3:PutObject",
                   "s3:DeleteObject",
                   "s3:ListBucket"
               ],
               "Resource": [
                   "arn:aws:s3:::autotasker-logs",
                   "arn:aws:s3:::autotasker-logs/*"
               ]
           },
           {
               "Effect": "Allow",
               "Action": [
                   "ses:SendEmail",
                   "ses:SendRawEmail",
                   "ses:VerifyEmailIdentity"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

3. **Complete User Creation**:
   - Click "Next: Tags" (optional)
   - Click "Next: Review"
   - Click "Create user"

### Step 3: Get Access Keys

1. **Download Credentials**:
   - After user creation, you'll see the success page
   - **IMPORTANT**: Download the CSV file or copy the credentials immediately
   - You'll see:
     - `Access Key ID` (e.g., AKIAIOSFODNN7EXAMPLE)
     - `Secret Access Key` (e.g., wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY)

2. **Save Credentials Securely**:
   - Store these in a secure location
   - Never commit them to version control
   - You cannot view the secret key again after this page

## Required AWS Resources

### 1. S3 Bucket for Logs

1. **Navigate to S3**:
   - Search for "S3" in AWS Console
   - Click on "S3"

2. **Create Bucket**:
   - Click "Create bucket"
   - Enter bucket name: `autotasker-logs` (or your preferred name)
   - Choose your preferred region (e.g., us-east-1)
   - Leave other settings as default
   - Click "Create bucket"

### 2. SES Email Setup

1. **Navigate to SES**:
   - Search for "SES" in AWS Console
   - Click on "Simple Email Service"

2. **Verify Email Address**:
   - Click "Email Addresses" in the left sidebar
   - Click "Verify a New Email Address"
   - Enter your email address (this will be used to send emails)
   - Check your email and click the verification link

3. **Note**: SES starts in sandbox mode (can only send to verified emails)
   - To send to any email, request production access
   - Go to "Sending Statistics" → "Request a Sending Quota Increase"

## Environment Variables Setup

Add these credentials to your `.env` file:

```bash
# AWS Credentials (from IAM user creation)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# AWS Configuration
AWS_REGION=us-east-1                    # Choose your preferred region
AWS_S3_BUCKET=autotasker-logs          # Your S3 bucket name
AWS_SES_EMAIL=your-email@domain.com    # Your verified SES email
```

## Security Best Practices

1. **Principle of Least Privilege**:
   - Only grant necessary permissions
   - Use custom policies instead of full access

2. **Key Rotation**:
   - Rotate access keys periodically
   - Delete unused keys

3. **Environment Variables**:
   - Never hardcode credentials in code
   - Use environment variables or AWS IAM roles

4. **Monitor Usage**:
   - Check AWS billing regularly
   - Set up billing alerts

## Free Tier Limits

AWS Free Tier includes:
- **S3**: 5 GB storage, 20,000 GET requests, 2,000 PUT requests
- **SES**: 200 emails per day (when sending from EC2)
- **General**: 12 months free for many services

## Troubleshooting

### Common Issues:

1. **"Access Denied" Errors**:
   - Check IAM policy permissions
   - Verify bucket/resource names match

2. **SES Sending Fails**:
   - Ensure email address is verified
   - Check if still in sandbox mode

3. **Region Mismatch**:
   - Ensure all resources are in the same region
   - Update AWS_REGION in .env file

### Getting Help:

- AWS Documentation: [docs.aws.amazon.com](https://docs.aws.amazon.com)
- AWS Support: Available in AWS Console
- Community Forums: AWS re:Post

## Cost Estimation

For typical AutoTasker AI usage:
- **S3**: ~$0.01-0.05/month for logs
- **SES**: ~$0.10 per 1,000 emails
- **Total**: Usually under $1/month for personal use

---

**Next Steps**: After obtaining these credentials, update your `.env` file and test the connection using the AutoTasker AI configuration panel.
