# LeetCode Agent Setup & Configuration

The LeetCode Agent uses a hybrid data source system to provide the best possible questions and recommendations.

## Data Sources (Priority Order)

### 1. 🌐 LeetCode GraphQL API (Primary)
- **Best quality**: Real LeetCode problems with actual data
- **Requires**: LeetCode session cookie
- **Provides**: Live problem data, acceptance rates, company tags

### 2. 🤖 LLM Generation (First Fallback)
- **AI-generated content**: Custom problems matching criteria
- **Always available**: Uses OpenRouter/LLM
- **Provides**: Unlimited variety, contextually relevant problems

### 3. 📚 Curated Problems Database (Final Fallback)
- **High quality**: Manually curated popular problems
- **Always available**: No external dependencies
- **Provides**: Well-known interview problems with descriptions

## Configuration

### Basic Setup (Required)
Add to your `config/.env` file:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Enhanced Setup (Optional)
For GraphQL API access, add your LeetCode session cookie:

1. **Get LeetCode Session Cookie:**
   - Login to leetcode.com
   - Open browser DevTools (F12)
   - Go to Application/Storage → Cookies
   - Copy the `LEETCODE_SESSION` cookie value

2. **Add to config/.env:**
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
LEETCODE_SESSION_COOKIE=your_leetcode_session_cookie_here
```

**That's it!** The agent will automatically read from environment variables.

3. **Optional: Update config.yaml (not required):**
If you prefer centralized config management, you can optionally add:
```yaml
leetcode:
  session_cookie: ${LEETCODE_SESSION_COOKIE}
```
But this is **not necessary** - the agent works fine with just the .env file.

## Data Source Indicators

When questions are returned, they include source indicators:

### 1. GraphQL API (🌐)
- **Speed**: 200-500ms per request
- **Accuracy**: 100% real LeetCode problems
- **Requirements**: Valid session cookie
- **Limitations**: Rate limits, session expiration

### 2. Curated Database (📚)
- **Speed**: Instant
- **Accuracy**: Hand-picked popular problems
- **Requirements**: None
- **Limitations**: Limited problem set (~50 problems)

### 3. LLM Generation (🤖)
- **Speed**: 2-5 seconds per problem
- **Accuracy**: AI-generated, LeetCode-style problems
- **Requirements**: OpenRouter API key
- **Limitations**: Not real LeetCode problems

## Testing the Setup

```bash
# Test with basic setup (curated + LLM)
python agents/leetcode_agent.py

# Test specific scenarios
python test_leetcode_agent.py daily    # Daily questions
python test_leetcode_agent.py topic    # Topic-specific
python test_leetcode_agent.py study    # Study plan
```

## Configuration Examples

### For Development/Testing
```python
config = {
    'leetcode': {
        # No session cookie = uses curated DB + LLM
    }
}
```

### For Production with LeetCode Access
```python
config = {
    'leetcode': {
        'session_cookie': os.getenv('LEETCODE_SESSION_COOKIE')
    }
}
```

### Environment Variables
```bash
# .env file
LEETCODE_SESSION_COOKIE=your_session_cookie_value_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

## Data Source Indicators

In the output, you'll see these indicators:

- **🌐** = Real LeetCode API
- **📚** = Curated Database  
- **🤖** = AI Generated
- **📝** = Fallback

## Troubleshooting

### GraphQL API Issues
```
❌ GraphQL failed: 401 Unauthorized
✅ Falling back to curated database
```
**Solution**: Check your session cookie is valid and not expired.

### Rate Limiting
```
❌ GraphQL failed: 429 Too Many Requests
✅ Falling back to curated database
```
**Solution**: Wait a few minutes or use curated database mode.

### No Problems Generated
```
❌ No LeetCode questions were generated
```
**Solution**: Check OpenRouter API key for LLM fallback.

## Best Practices

1. **Always have fallbacks**: Don't rely only on GraphQL API
2. **Monitor session expiration**: LeetCode sessions expire periodically
3. **Use environment variables**: Keep credentials secure
4. **Test regularly**: Verify all data sources work
5. **Cache responses**: Avoid repeated API calls for same problems

## Performance Comparison

| Data Source | Speed | Accuracy | Reliability | Setup Complexity |
|-------------|-------|----------|-------------|------------------|
| GraphQL API | Fast | 100% | Medium | High |
| Curated DB | Instant | 100% | High | None |
| LLM Generation | Slow | 85% | High | Medium |

## Integration with Main Workflow

The agent automatically integrates with:
- **Streamlit Frontend**: Real-time problem generation
- **Email Delivery**: Daily question scheduling  
- **Memory System**: Duplicate prevention
- **Study Plans**: Structured learning paths

Choose the setup that best fits your needs!
