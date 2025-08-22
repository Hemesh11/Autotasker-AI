# OpenRouter API Setup Guide

OpenRouter is the **recommended** LLM provider for AutoTasker AI. It provides access to multiple AI models through a single API, often with better pricing and availability than direct provider APIs.

## Why Choose OpenRouter?

✅ **Multiple Models**: Access GPT-4, Claude, Llama, and more through one API  
✅ **Better Pricing**: Often cheaper than direct OpenAI API  
✅ **Higher Limits**: Better rate limits and availability  
✅ **Free Tier**: Some models available for free  
✅ **Simple Migration**: Easy to switch between models  

## Getting Your OpenRouter API Key

### Step 1: Create Account

1. **Visit OpenRouter**:
   - Go to [openrouter.ai](https://openrouter.ai)
   - Click "Sign Up" or "Get Started"

2. **Registration**:
   - Create account with email/password
   - Or sign up with Google/GitHub
   - Verify your email address

### Step 2: Get API Key

1. **Access Dashboard**:
   - After login, go to your dashboard
   - Or visit [openrouter.ai/keys](https://openrouter.ai/keys)

2. **Create API Key**:
   - Click "Create Key" or "New API Key"
   - Give it a name (e.g., "AutoTasker AI")
   - Copy the generated key (starts with `sk-or-...`)
   - **Save it securely** - you won't see it again!

### Step 3: Add Credits (Optional)

OpenRouter offers both free and paid models:

1. **Free Models**: Some models are completely free
2. **Paid Models**: Add credits for premium models
   - Go to "Credits" or "Billing" in dashboard
   - Add credits via credit card (minimum ~$5)
   - Credits are used across all models

## Model Selection Guide

### For AutoTasker AI, we recommend:

#### **Free Options** (No credits needed):
- `mistralai/mistral-7b-instruct` - Good for basic tasks
- `huggingfaceh4/zephyr-7b-beta` - Decent for planning

#### **Low-Cost Options** (~$0.001-0.002 per 1K tokens):
- `openai/gpt-3.5-turbo` - Fast, reliable, cost-effective
- `meta-llama/llama-2-70b-chat` - Good alternative to GPT

#### **High-Quality Options** (~$0.01-0.03 per 1K tokens):
- `openai/gpt-4-turbo-preview` - **Recommended balance**
- `openai/gpt-4` - Most capable
- `anthropic/claude-3-sonnet` - Great for creative tasks

#### **Specialized Options**:
- `meta-llama/codellama-34b` - Best for coding tasks
- `anthropic/claude-instant-v1` - Fast responses

## Configuration Setup

### Option 1: Environment Variables

Add to your `.env` file:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-your-api-key-here

# Optional: Set preferred models
OPENROUTER_DEFAULT_MODEL=openai/gpt-4-turbo-preview
```

### Option 2: Config File

Update `config/config.yaml`:

```yaml
llm:
  provider: "openrouter"
  openrouter:
    default_model: "openai/gpt-4-turbo-preview"
    app_name: "AutoTasker-AI"

agents:
  planner:
    model: "openai/gpt-4-turbo-preview"  # High-quality planning
  summarizer:
    model: "openai/gpt-3.5-turbo"       # Fast summarization  
  dsa_generator:
    model: "meta-llama/codellama-34b"   # Coding questions
```

## Using AutoTasker AI

### First Time Setup:

1. **Update Environment**:
   ```bash
   # In your .env file
   OPENROUTER_API_KEY=sk-or-your-actual-key-here
   ```

2. **Test Configuration**:
   - Run AutoTasker AI
   - Go to Configuration tab
   - Select "OpenRouter (Recommended)"
   - Enter your API key
   - Choose a model

3. **Start with Free Models**:
   - Use `mistralai/mistral-7b-instruct` for testing
   - Upgrade to paid models when ready

## Cost Management

### Typical Usage Costs:

- **Planning Tasks**: ~$0.01-0.05 per complex prompt
- **Email Summaries**: ~$0.001-0.01 per email
- **DSA Questions**: ~$0.01-0.03 per question
- **Daily Usage**: Usually $0.10-1.00 for personal use

### Cost Optimization Tips:

1. **Start with Cheaper Models**:
   - Use `gpt-3.5-turbo` for most tasks
   - Reserve `gpt-4` for complex planning

2. **Monitor Usage**:
   - Check dashboard regularly
   - Set up credit alerts

3. **Optimize Prompts**:
   - Be concise and specific
   - Avoid unnecessary context

## Migration from OpenAI

If you're switching from OpenAI:

### Model Mapping:
- `gpt-3.5-turbo` → `openai/gpt-3.5-turbo`
- `gpt-4` → `openai/gpt-4`
- `gpt-4-turbo-preview` → `openai/gpt-4-turbo-preview`

### Simple Migration:
1. Get OpenRouter API key
2. Update `.env` file
3. Change model names to include provider prefix
4. Test functionality

## Troubleshooting

### Common Issues:

1. **"Invalid API Key"**:
   - Check key starts with `sk-or-`
   - Verify key is copied correctly
   - Check environment variable name

2. **"Insufficient Credits"**:
   - Add credits in OpenRouter dashboard
   - Or switch to free models

3. **"Model Not Found"**:
   - Check model name format: `provider/model-name`
   - Verify model is available on OpenRouter

4. **Rate Limiting**:
   - OpenRouter has generous limits
   - Check dashboard for current limits
   - Consider upgrading plan if needed

### Getting Help:

- **Documentation**: [openrouter.ai/docs](https://openrouter.ai/docs)
- **Discord**: OpenRouter community Discord
- **Support**: Contact through website

## Advanced Features

### Model Fallbacks:
Configure multiple models for redundancy:

```yaml
llm:
  provider: "openrouter"
  fallback_models:
    - "openai/gpt-4-turbo-preview"
    - "openai/gpt-3.5-turbo"
    - "mistralai/mistral-7b-instruct"
```

### Custom Parameters:
Fine-tune model behavior:

```python
# In agent configuration
response = get_chat_completion(
    client=self.client,
    messages=messages,
    model="openai/gpt-4-turbo-preview",
    temperature=0.7,      # Creativity level
    max_tokens=2000,      # Response length
    top_p=0.9,           # Nucleus sampling
    frequency_penalty=0.1 # Reduce repetition
)
```

---

**Next Steps**: 
1. Get your OpenRouter API key
2. Update your `.env` file  
3. Test with a simple task
4. Explore different models for different use cases
