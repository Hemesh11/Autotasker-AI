"""
Helper script to upload Gmail OAuth token to AWS Secrets Manager
Run this AFTER you've completed Gmail OAuth flow locally
"""

import json
import boto3
import os
import sys

def upload_gmail_token_to_secrets_manager():
    """Upload Gmail token from local file to AWS Secrets Manager"""
    
    # Configuration
    token_file_path = "google_auth/gmail_token.json"
    secret_name = "autotasker/gmail-token"
    region_name = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    print("=" * 60)
    print("Gmail Token Upload to AWS Secrets Manager")
    print("=" * 60)
    
    # Check if token file exists
    if not os.path.exists(token_file_path):
        print(f"❌ Error: Token file not found: {token_file_path}")
        print("\n📋 Steps to fix:")
        print("1. Run Gmail OAuth flow locally first:")
        print("   python test_gmail_agent_individual.py")
        print("2. This will create the gmail_token.json file")
        print("3. Then run this script again")
        sys.exit(1)
    
    # Read token file
    try:
        with open(token_file_path, 'r') as f:
            token_data = json.load(f)
        print(f"✅ Loaded token from: {token_file_path}")
    except Exception as e:
        print(f"❌ Error reading token file: {e}")
        sys.exit(1)
    
    # Validate token data
    required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret']
    missing_fields = [field for field in required_fields if field not in token_data]
    
    if missing_fields:
        print(f"⚠️  Warning: Token file missing fields: {missing_fields}")
        print("This may cause issues. Continuing anyway...")
    
    # Connect to AWS Secrets Manager
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        print(f"✅ Connected to AWS Secrets Manager in region: {region_name}")
    except Exception as e:
        print(f"❌ Error connecting to AWS: {e}")
        print("\n📋 Make sure:")
        print("1. AWS CLI is configured: aws configure")
        print("2. Your AWS credentials are set correctly")
        sys.exit(1)
    
    # Upload to Secrets Manager
    try:
        # Check if secret already exists
        try:
            client.describe_secret(SecretId=secret_name)
            print(f"⚠️  Secret '{secret_name}' already exists. Updating...")
            
            # Update existing secret
            response = client.put_secret_value(
                SecretId=secret_name,
                SecretString=json.dumps(token_data)
            )
            print(f"✅ Updated existing secret: {secret_name}")
            
        except client.exceptions.ResourceNotFoundException:
            # Create new secret
            print(f"Creating new secret: {secret_name}")
            response = client.create_secret(
                Name=secret_name,
                Description='Gmail OAuth token for AutoTasker AI',
                SecretString=json.dumps(token_data)
            )
            print(f"✅ Created new secret: {secret_name}")
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Gmail token uploaded to AWS Secrets Manager")
        print("=" * 60)
        print(f"\nSecret Name: {secret_name}")
        print(f"Region: {region_name}")
        print(f"ARN: {response.get('ARN', 'N/A')}")
        
        print("\n📋 Next Steps:")
        print("1. Your Gmail Agent will now work in AWS Lambda")
        print("2. Deploy your Lambda function using SAM:")
        print("   sam build && sam deploy")
        print("3. Test the deployed function")
        
        print("\n💡 Note:")
        print("The refresh token allows Lambda to get new access tokens automatically")
        print("No need to re-upload unless you revoke access in Google Console")
        
    except Exception as e:
        print(f"❌ Error uploading to Secrets Manager: {e}")
        sys.exit(1)

if __name__ == "__main__":
    upload_gmail_token_to_secrets_manager()
