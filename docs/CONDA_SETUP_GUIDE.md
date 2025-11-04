# AutoTasker AI - Conda Environment Setup Guide

## Overview
This guide provides step-by-step instructions for setting up AutoTasker AI in a conda environment on Windows using cmd prompt.

## Prerequisites
- Windows 10/11
- Anaconda or Miniconda installed
- Git (optional, for cloning)
- Admin privileges (for some installations)

## Step 1: Create and Activate Conda Environment

Open **cmd prompt** and run:

```cmd
# Create new conda environment with Python 3.11
conda create -n autotasker python=3.11 -y

# Activate the environment
conda activate autotasker

# Verify Python version
python --version
```

## Step 2: Navigate to Project Directory

```cmd
# Navigate to your project directory
cd "C:\Users\hemes\Desktop\sem 6 project\IMPLEMENTATION"

# Verify you're in the right directory
dir
```

## Step 3: Install Dependencies

### Option A: Install from requirements.txt (Recommended)
```cmd
pip install -r requirements.txt
```

### Option B: Install dependencies manually
```cmd
# Core dependencies
pip install streamlit>=1.28.0
pip install langchain>=0.1.0
pip install langgraph>=0.0.40
pip install openai>=1.10.0
pip install requests>=2.28.0

# Google APIs
pip install google-auth>=2.17.0
pip install google-auth-oauthlib>=1.0.0
pip install google-auth-httplib2>=0.2.0
pip install google-api-python-client>=2.0.0

# AWS
pip install boto3>=1.34.0

# Data processing
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install python-dotenv>=1.0.0
pip install pyyaml>=6.0

# Additional utilities
pip install APScheduler>=3.10.0
pip install plotly>=5.17.0
pip install difflib
pip install fuzzywuzzy
pip install python-levenshtein
```

## Step 4: Environment Variables Setup

Create a `.env` file in the project root:

```cmd
# Create .env file
echo. > .env
```

Edit the `.env` file with notepad or your preferred editor:

```cmd
notepad .env
```

Add the following content:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
GITHUB_TOKEN=your_github_token_here

# Google OAuth (paths relative to project root)
GOOGLE_CREDENTIALS_PATH=google_auth/credentials.json
GMAIL_TOKEN_PATH=google_auth/gmail_token.json
CALENDAR_TOKEN_PATH=google_auth/calendar_token.json

# Gmail Configuration
GMAIL_SENDER_EMAIL=your_email@gmail.com

# AWS Configuration (for production deployment)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET=autotasker-bucket
AWS_DYNAMODB_TABLE=autotasker-executions

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

## Step 5: Google OAuth Setup

### Gmail and Calendar API Setup

1. **Create Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API and Calendar API

2. **Create OAuth 2.0 Credentials:**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file

3. **Setup credentials:**
   ```cmd
   # Create google_auth directory if it doesn't exist
   mkdir google_auth

   # Copy your downloaded credentials file
   copy "path\to\your\downloaded\credentials.json" "google_auth\credentials.json"
   ```

4. **Test Gmail authentication:**
   ```cmd
   python gmail_interactive.py
   ```

## Step 6: Verify Installation

Test all components:

```cmd
# Test LLM connection
python test_llm_connection.py

# Test backend components
python test_backend_components.py

# Test individual agents
python test_planner_agent_individual.py
python test_gmail_agent_individual.py
python test_github_agent.py
```

## Step 7: Run AutoTasker AI

### Start the Streamlit Frontend

```cmd
# Make sure you're in the project directory and conda environment is activated
conda activate autotasker
cd "C:\Users\hemes\Desktop\sem 6 project\IMPLEMENTATION"

# Run the enhanced Streamlit app
streamlit run frontend/streamlit_app_enhanced.py
```

### Alternative: Run using VS Code task
If you have VS Code open with this workspace:
- Press `Ctrl+Shift+P`
- Type "Tasks: Run Task"
- Select "Run AutoTasker AI - Streamlit Frontend"

## Step 8: Production Deployment (AWS)

For AWS deployment, follow these additional steps:

### Install AWS CLI (if not already installed)
```cmd
# Download and install AWS CLI from: https://aws.amazon.com/cli/
# Or install via conda
conda install -c conda-forge awscli
```

### Configure AWS credentials
```cmd
aws configure
```

### Deploy to AWS Lambda
```cmd
# Install additional deployment dependencies
pip install lambda-uploader
pip install zappa

# Package and deploy (detailed steps in AWS_SETUP_GUIDE.md)
python aws/deployment.py
```

## Troubleshooting

### Common Issues and Solutions

1. **"Module not found" errors:**
   ```cmd
   # Ensure conda environment is activated
   conda activate autotasker
   
   # Reinstall problematic package
   pip install --upgrade [package_name]
   ```

2. **Google authentication errors:**
   ```cmd
   # Delete existing tokens and re-authenticate
   del google_auth\gmail_token.json
   del google_auth\calendar_token.json
   python gmail_interactive.py
   ```

3. **Streamlit not starting:**
   ```cmd
   # Check if port is available
   netstat -an | findstr :8501
   
   # Start on different port
   streamlit run frontend/streamlit_app_enhanced.py --server.port 8502
   ```

4. **AWS deployment issues:**
   ```cmd
   # Verify AWS credentials
   aws sts get-caller-identity
   
   # Check permissions
   aws iam get-user
   ```

## Environment Management

### Useful conda commands:
```cmd
# List conda environments
conda env list

# Update packages
conda update --all

# Export environment
conda env export > environment.yml

# Create from exported environment
conda env create -f environment.yml

# Remove environment
conda env remove -n autotasker
```

### Deactivate environment:
```cmd
conda deactivate
```

## Performance Optimization

### For better performance in conda environment:

1. **Install conda-forge packages when possible:**
   ```cmd
   conda install -c conda-forge numpy pandas
   ```

2. **Use conda for large packages:**
   ```cmd
   conda install -c conda-forge pytorch
   ```

3. **Keep environment clean:**
   ```cmd
   conda clean --all
   ```

## Production Checklist

Before deploying to production:

- [ ] All tests pass (`pytest tests/`)
- [ ] Environment variables configured
- [ ] Google OAuth working
- [ ] AWS credentials configured
- [ ] SSL certificates configured (for HTTPS)
- [ ] Monitoring and logging enabled
- [ ] Backup strategy implemented
- [ ] Security review completed

## Support

If you encounter issues:

1. Check logs in `data/logs/` directory
2. Run individual test files to isolate problems
3. Verify all environment variables are set correctly
4. Ensure all APIs are accessible and credentials are valid

## Next Steps

After successful setup:

1. **Configure Agents:** Customize agent settings in `config/config.yaml`
2. **Setup Scheduling:** Configure automated tasks using the scheduler
3. **Monitor Performance:** Use the Streamlit dashboard for monitoring
4. **Scale Up:** Deploy to AWS for production-grade scaling

---

**Happy Automating with AutoTasker AI!** 🤖✨
