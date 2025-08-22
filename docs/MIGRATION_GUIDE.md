# 🔄 Migration Guide: From OpenAI to OpenRouter

This guide explains the changes made to support OpenRouter and how to migrate your setup.

## What Changed?

### ✅ New Features Added:
- **OpenRouter Support**: Primary LLM provider with access to multiple models
- **Unified LLM Interface**: Seamless switching between OpenAI and OpenRouter
- **Model Selection**: Easy configuration of different models for different tasks
- **Cost Optimization**: Access to cheaper and free models

### 🔧 Code Changes:
- Added `backend/openrouter_client.py` - OpenRouter API client
- Added `backend/llm_factory.py` - Unified LLM client factory
- Updated all agent files to use the new LLM interface
- Enhanced configuration with provider selection
- Updated Streamlit UI with provider choice

## Quick Migration Steps

### 1. Get OpenRouter API Key (Recommended)

```bash
# Visit https://openrouter.ai
# Sign up and get your API key
# Add to your .env file:
OPENROUTER_API_KEY=sk-or-your-key-here
```

### 2. Update Configuration

#### Option A: Use OpenRouter (Recommended)
```yaml
# config/config.yaml
llm:
  provider: "openrouter"
  openrouter:
    default_model: "openai/gpt-4-turbo-preview"

agents:
  planner:
    model: "openai/gpt-4-turbo-preview"
  summarizer:
    model: "openai/gpt-3.5-turbo"
  dsa_generator:
    model: "meta-llama/codellama-34b"
```

#### Option B: Keep Using OpenAI
```yaml
# config/config.yaml
llm:
  provider: "openai"
  model: "gpt-4-turbo-preview"
```

### 3. Test Your Setup

```bash
# Run the quick start script
python quick_start.py

# Or start the UI
streamlit run frontend/streamlit_app.py
```

## Detailed Configuration Options

### Model Recommendations by Task:

#### **Planning & Complex Tasks**:
```yaml
planner:
  model: "openai/gpt-4-turbo-preview"  # Most capable
```

#### **Fast Summarization**:
```yaml
summarizer:
  model: "openai/gpt-3.5-turbo"       # Fast & efficient
```

#### **Coding Questions**:
```yaml
dsa_generator:
  model: "meta-llama/codellama-34b"   # Specialized for code
```

#### **Budget-Conscious Setup**:
```yaml
# All agents use affordable models
agents:
  planner:
    model: "openai/gpt-3.5-turbo"
  summarizer:
    model: "mistralai/mistral-7b-instruct"  # Free!
  dsa_generator:
    model: "openai/gpt-3.5-turbo"
```

### Environment Variables:

```bash
# .env file

# LLM Provider (choose one)
OPENROUTER_API_KEY=sk-or-your-key-here     # Recommended
OPENAI_API_KEY=sk-your-openai-key-here     # Alternative

# AWS (required for full functionality)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=autotasker-logs
AWS_SES_EMAIL=your-email@domain.com

# Google OAuth (optional)
GOOGLE_CREDENTIALS_PATH=google_auth/credentials.json
GOOGLE_TOKEN_PATH=google_auth/token.json

# Gmail
GMAIL_ADDRESS=your-email@gmail.com
```

## Cost Comparison

### OpenAI Direct Pricing:
- GPT-3.5-turbo: $0.0015/1K input tokens, $0.002/1K output tokens
- GPT-4-turbo: $0.01/1K input tokens, $0.03/1K output tokens

### OpenRouter Pricing (Often Better):
- GPT-3.5-turbo: $0.0015/1K tokens (same)
- GPT-4-turbo: $0.01/1K tokens (better output pricing)
- **Free Models**: Mistral-7B, Zephyr-7B (completely free!)

### Estimated Monthly Costs:
```
Personal Use (100 tasks/month):
- Free models only: $0
- Mixed (free + GPT-3.5): $2-5
- Premium (GPT-4): $10-20

Business Use (1000 tasks/month):
- Optimized setup: $20-50
- Full GPT-4: $100-200
```

## Troubleshooting Migration

### Issue: "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Invalid API key"
```bash
# Check your .env file
cat config/.env | grep API_KEY

# Verify key format
# OpenRouter: sk-or-...
# OpenAI: sk-...
```

### Issue: "Model not found"
```bash
# For OpenRouter, use provider/model format:
# ✅ Correct: "openai/gpt-4"
# ❌ Wrong: "gpt-4"

# Update config.yaml with proper model names
```

### Issue: Agent fails to initialize
```python
# Check logs for specific error
tail -f data/logs/autotasker.log

# Common fixes:
# 1. Verify API key in .env
# 2. Check internet connection
# 3. Verify model name format
```

## Advanced Configuration

### Custom Model Fallbacks:
```yaml
llm:
  provider: "openrouter"
  fallback_models:
    - "openai/gpt-4-turbo-preview"
    - "openai/gpt-3.5-turbo"
    - "mistralai/mistral-7b-instruct"
```

### Per-Agent Fine-tuning:
```yaml
agents:
  planner:
    model: "openai/gpt-4-turbo-preview"
    temperature: 0.3    # More focused
    max_tokens: 2000
  
  dsa_generator:
    model: "meta-llama/codellama-34b"
    temperature: 0.8    # More creative
    max_tokens: 1500
```

### Custom OpenRouter Settings:
```yaml
llm:
  provider: "openrouter"
  openrouter:
    default_model: "openai/gpt-4-turbo-preview"
    app_name: "AutoTasker-AI"
    base_url: "https://openrouter.ai/api/v1"
```

## Rollback Instructions

If you need to rollback to OpenAI-only:

### 1. Update Configuration:
```yaml
# config/config.yaml
llm:
  provider: "openai"
  model: "gpt-4"

agents:
  planner:
    model: "gpt-4"
  summarizer:
    model: "gpt-3.5-turbo"
  dsa_generator:
    model: "gpt-4"
```

### 2. Verify OpenAI Key:
```bash
# Ensure this is set in .env
OPENAI_API_KEY=sk-your-actual-openai-key
```

### 3. Test:
```bash
python quick_start.py
```

## Best Practices

### 1. **Start with Free Models**:
   - Test with `mistralai/mistral-7b-instruct`
   - Upgrade to paid models when satisfied

### 2. **Monitor Usage**:
   - Check OpenRouter dashboard regularly
   - Set up credit alerts

### 3. **Optimize by Task**:
   - Use cheaper models for simple tasks
   - Reserve premium models for complex reasoning

### 4. **Backup Configuration**:
   - Keep a copy of working config.yaml
   - Document your model preferences

## Getting Help

### Resources:
- **OpenRouter Docs**: [openrouter.ai/docs](https://openrouter.ai/docs)
- **Model Comparison**: [openrouter.ai/models](https://openrouter.ai/models)
- **AutoTasker Issues**: [GitHub Issues](https://github.com/your-repo/issues)

### Quick Tests:
```bash
# Test configuration
python quick_start.py

# Test specific agent
python -c "
from agents.planner_agent import PlannerAgent
from backend.utils import load_config
agent = PlannerAgent(load_config())
print('Agent initialized successfully!')
"
```

---

**Happy migrating! 🚀**

OpenRouter provides better flexibility and often better pricing than direct OpenAI access. You now have access to models from OpenAI, Anthropic, Meta, Google, and more through a single API!
