# AutoTasker AI: A Self-Healing, Multi-Agentic Workflow Orchestrator

AutoTasker AI is an intelligent workflow orchestrator that converts natural language prompts into automated tasks across APIs and cloud services. It uses LangGraph for agent orchestration, AWS services, and Google APIs to create a self-healing, multi-agent system.

## 🚀 Features

- **Natural Language Processing**: Convert plain English requests into structured task plans
- **Multi-Agent Architecture**: Specialized agents for different tasks (Gmail, GitHub, DSA generation, etc.)
- **Self-Healing**: Automatic retry and recovery mechanisms when tasks fail
- **Memory System**: Remembers past executions to avoid duplicates and learn from history
- **Cloud Integration**: Works with AWS (Lambda, S3, SES, DynamoDB) and Google services (Gmail, Sheets, Drive)
- **Flexible Scheduling**: Daily automation with AWS EventBridge or local APScheduler

## 🏗️ Architecture

```
User Prompt → LLM Planner → LangGraph Runner → Specialized Agents → Execution Result
```

### Core Components:
- **Planner Agent**: Converts natural language to structured task plans
- **LangGraph Runner**: Orchestrates multi-agent workflows
- **Gmail Agent**: Email fetching and processing
- **GitHub Agent**: Repository data and commit summaries
- **DSA Agent**: Generates coding questions using LLM
- **Summarizer Agent**: Content summarization
- **Email Agent**: Sends results via Gmail API or AWS SES
- **Logger Agent**: Stores execution logs
- **Retry Agent**: Handles failures and retries
- **Memory Agent**: Prevents duplicate executions

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd autotasker-ai

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Configure Google OAuth
# Place your credentials.json in google_auth/
```

## 🔧 Configuration

### 1. LLM API Setup (Choose One)

#### Option A: OpenRouter (Recommended) 🌟
- **Free models available**: No cost to get started
- **Multiple models**: Access to GPT-4, Claude, Llama, and more
- **Better pricing**: Often cheaper than direct provider APIs

1. Get API key from [openrouter.ai](https://openrouter.ai)
2. Add to `config/.env`:
   ```bash
   OPENROUTER_API_KEY=sk-or-your-key-here
   ```
3. See [OpenRouter Setup Guide](docs/OPENROUTER_SETUP.md) for details

#### Option B: OpenAI Direct
1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Add to `config/.env`:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

### 2. AWS Credentials
Required for email sending and log storage:

1. Create AWS account and IAM user
2. Add to `config/.env`:
   ```bash
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=us-east-1
   AWS_S3_BUCKET=autotasker-logs
   AWS_SES_EMAIL=your-email@domain.com
   ```
3. See [AWS Setup Guide](docs/AWS_SETUP.md) for step-by-step instructions

### 3. Google OAuth (Optional)
For Gmail integration:
- Follow instructions in `google_auth/README.md`

## 🎯 Usage

### Via Streamlit UI
```bash
streamlit run frontend/streamlit_app.py
```

### Via Terminal
```bash
python backend/langgraph_runner.py --prompt "Send me 2 LeetCode questions daily at 9AM"
```

### Example Prompts
- "Every day at 9AM, send me 2 LeetCode questions and summarize yesterday's emails"
- "Generate 3 DSA problems and email them to me"
- "Summarize my GitHub commits from last week and send via email"

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Test specific agents
python -m pytest tests/test_agents.py
```

## 📁 Project Structure

```
autotasker-ai/
├── frontend/           # Streamlit UI
├── backend/           # Core logic and agents
├── agents/            # Individual agent implementations
├── google_auth/       # Google OAuth setup
├── scheduler/         # Task scheduling
├── config/            # Configuration files
├── memory/            # Memory and state management
├── data/              # Sample data and logs
├── tests/             # Unit tests
└── docs/              # Documentation
```

## 🚀 Getting Started

1. Set up your environment and API keys
2. Run the Streamlit app: `streamlit run frontend/streamlit_app.py`
3. Enter a natural language prompt
4. Watch AutoTasker AI break it down and execute the tasks!

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.
