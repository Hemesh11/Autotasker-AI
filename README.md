# 🤖 AutoTasker AI: Intelligent Multi-Agent Workflow Automation System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-green.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AutoTasker AI** is a cutting-edge, self-healing multi-agentic workflow orchestration platform that revolutionizes task automation through natural language understanding. Built with LangGraph for agent coordination, it seamlessly integrates with various APIs and cloud services to execute complex, multi-step workflows autonomously.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Core Components](#-core-components)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Key Features

### Intelligent Automation
- **Natural Language Understanding**: Convert plain English into executable task plans using advanced LLM integration
- **Multi-Agent Orchestration**: Coordinate 8+ specialized agents via LangGraph state machine
- **Smart Scheduling**: Support for one-time, daily, weekly, and interval-based execution with natural language time parsing

### Robustness & Reliability
- **Self-Healing Architecture**: Automatic retry mechanisms with exponential backoff
- **Memory System**: Semantic similarity-based duplicate detection using embeddings
- **Error Recovery**: Intelligent fallback strategies and graceful degradation
- **Comprehensive Logging**: Multi-backend logging (S3, Local, DynamoDB) with performance metrics

### Integration Capabilities
- **Email Automation**: Gmail API integration for reading and sending emails
- **Version Control**: GitHub API for repository analysis, commit tracking, and issue management
- **Cloud Services**: Native AWS integration (Lambda, S3, SES, EventBridge, DynamoDB)
- **Calendar Management**: Google Calendar API for event creation and retrieval
- **Code Generation**: AI-powered DSA problem generation and LeetCode problem recommendations

### Developer Experience
- **Interactive UI**: Modern Streamlit-based web interface with real-time execution monitoring
- **Flexible Configuration**: Environment-based configuration with YAML support
- **Extensive Testing**: Comprehensive test suite with unit and integration tests
- **Performance Monitoring**: Built-in metrics tracking for execution time, success rates, and resource usage

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  (Streamlit Web UI / CLI / API Endpoints)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      Planning Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LLM-Powered Planner Agent                               │   │
│  │  • Natural Language Parsing                              │   │
│  │  • Intent Recognition                                    │   │
│  │  • Task Decomposition                                    │   │
│  │  • Schedule Extraction                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Orchestration Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph Workflow Runner                               │   │
│  │  • State Management                                      │   │
│  │  • Agent Coordination                                    │   │
│  │  • Dependency Resolution                                 │   │
│  │  • Execution Flow Control                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     Agent Execution Layer                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Gmail   │ │  GitHub  │ │   DSA    │ │ LeetCode │          │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Summarizer│ │  Email   │ │  Logger  │ │  Memory  │          │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Integration Layer                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │   Gmail API  │ │  GitHub API  │ │  OpenAI API  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  AWS Lambda  │ │    AWS SES   │ │   AWS S3     │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────┐                             │
│  │  DynamoDB    │ │  EventBridge │                             │
│  └──────────────┘ └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components


### 1. **Planner Agent** 🧠
Transforms natural language prompts into structured, executable task plans using LLM intelligence.

**Capabilities:**
- Natural language parsing and intent recognition
- Task decomposition and prioritization
- Schedule extraction (daily, weekly, one-time, interval-based)
- Parameter inference and validation
- Multi-task dependency resolution

**Supported Operations:**
- Gmail operations (fetch, filter, search)
- GitHub operations (commits, repos, issues)
- LeetCode problem generation
- DSA question creation
- Content summarization
- Email delivery

---

### 2. **LangGraph Runner** 🔄
Orchestrates complex multi-agent workflows using state machine architecture.

**Features:**
- State-based workflow execution
- Agent coordination and sequencing
- Error handling and recovery
- Performance monitoring
- Result aggregation
- Memory integration

**Workflow Nodes:**
- Plan → Execute → Summarize → Email → Log → Store Memory

---

### 3. **Gmail Agent** �
Manages email operations using Gmail API with OAuth 2.0 authentication.

**Operations:**
- Fetch emails with advanced filtering
- Search by sender, subject, date range
- Handle attachments and labels
- Mark as read/unread
- Support for pagination

**Query Patterns:**
```python
# Examples
"Get my unread emails"
"Fetch emails from yesterday"
"Show emails with subject 'meeting'"
```

---

### 4. **GitHub Agent** 🐙
Interacts with GitHub API for repository analysis and version control operations.

**Operations:**
- List user repositories
- Fetch commit history with filtering
- Retrieve issues and pull requests
- Get repository statistics
- Search repositories by query

**Smart Features:**
- Auto-detection of authenticated user
- Username extraction from prompts
- Wildcard repository patterns
- Formatted output for email delivery

---

### 5. **DSA Agent** 💻
Generates custom Data Structures & Algorithms coding problems using LLM.

**Features:**
- Difficulty levels: Easy, Medium, Hard
- Topic-based generation (arrays, strings, trees, graphs, DP, etc.)
- Complete problem structure:
  - Problem statement
  - Input/Output examples
  - Constraints
  - Solution approach
  - Working code with explanations
  - Time/Space complexity analysis
  - Hints and edge cases

---

### 6. **LeetCode Agent** 🎯
Provides LeetCode problem recommendations and study plans.

**Capabilities:**
- Problem recommendations by difficulty
- Topic-based filtering
- Study plan generation
- Interview preparation tracks
- Daily coding challenges

---

### 7. **Summarizer Agent** 📝
Creates intelligent summaries of content using LLM.

**Summarization Types:**
- Email summaries (key points, action items)
- GitHub commit summaries
- Combined multi-source summaries
- Structured output formatting

---

### 8. **Email Agent** 📨
Handles email delivery via Gmail API or AWS SES.

**Features:**
- Multi-backend support (Gmail, AWS SES, File)
- HTML and plain text formatting
- Automatic fallback mechanisms
- Attachment support (future)
- Template-based emails

---

### 9. **Logger Agent** 📊
Centralized logging with multiple backend support.

**Backends:**
- AWS S3 (production)
- Local filesystem (development)
- AWS DynamoDB (structured logs)
- Console output

**Logged Information:**
- Execution metrics
- Performance data
- Error traces
- Agent interactions
- User prompts and results

---

### 10. **Memory Agent** 🧠
Prevents duplicate executions using semantic similarity detection.

**Technology:**
- Sentence transformers for embeddings
- Cosine similarity matching
- Configurable similarity threshold
- Persistent storage

**Benefits:**
- Avoid redundant task execution
- Smart prompt matching
- Historical context awareness

---

### 11. **Retry Agent** 🔁
Implements intelligent retry logic with exponential backoff.

**Features:**
- Configurable retry attempts
- Exponential backoff strategy
- Error classification
- Recovery mechanisms
- Circuit breaker pattern

---

## 📦 Getting Started

### Prerequisites

- **Python**: 3.9 or higher
- **pip**: Latest version
- **API Keys**:
  - OpenAI or OpenRouter API key (for LLM)
  - AWS credentials (optional, for cloud features)
  - GitHub token (optional, for GitHub integration)
  - Google OAuth credentials (optional, for Gmail)

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/Hemesh11/Autotasker-AI.git
cd Autotasker-AI

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### Minimal Setup (Quick Start)

For testing with just OpenAI/OpenRouter:

```bash
# Create config/.env with minimal configuration
echo "OPENAI_API_KEY=your-api-key-here" > config/.env
# OR
echo "OPENROUTER_API_KEY=your-api-key-here" > config/.env

# Run the application
streamlit run frontend/streamlit_app.py
```

---

## ⚙️ Configuration


### Configuration Priority

1. Environment variables (`.env` file)
2. YAML configuration (`config/config.yaml`)
3. Default values

### Essential Configuration

#### 1. LLM Provider (Required)

**Option A: OpenRouter (Recommended)** 🌟

OpenRouter provides access to multiple LLM providers with competitive pricing:

```bash
# config/.env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free  # Free tier available
```

**Benefits:**
- Free models available (Meta Llama, Mistral, etc.)
- Access to GPT-4, Claude, Gemini, and 100+ models
- Better pricing than direct providers
- No separate API keys needed

📖 **[OpenRouter Setup Guide](docs/OPENROUTER_SETUP.md)**

**Option B: OpenAI Direct**

```bash
# config/.env
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo
```

---

#### 2. AWS Configuration (Optional)

Required for: Email sending (SES), Log storage (S3), Scheduling (EventBridge)

```bash
# config/.env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=autotasker-logs
AWS_SES_EMAIL=your-verified-email@domain.com
```

📖 **[AWS Setup Guide](docs/AWS_SETUP.md)**

---

#### 3. GitHub Integration (Optional)

For repository operations and commit analysis:

```bash
# config/.env
GITHUB_TOKEN=ghp_your-personal-access-token
GITHUB_DEFAULT_OWNER=your-username
GITHUB_DEFAULT_REPO=your-default-repo
```

**Generate Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Copy and paste into `.env`

---

#### 4. Gmail Integration (Optional)

For email fetching and sending:

```bash
# config/.env
GMAIL_ADDRESS=your-email@gmail.com
```

**Setup OAuth:**
1. Enable Gmail API in Google Cloud Console
2. Download `credentials.json`
3. Place in `google_auth/` directory
4. First run will prompt for authorization

📖 **[Gmail OAuth Guide](google_auth/README.md)**

---

### Configuration File Structure

```
config/
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Template for environment variables
└── config.yaml           # Application configuration
```

---

## 🎯 Usage Examples

### Web Interface (Streamlit)

```bash
# Start the application
streamlit run frontend/streamlit_app.py

# Access at http://localhost:8501
```

**Interface Features:**
- Natural language prompt input
- Real-time execution monitoring
- Performance metrics visualization
- Execution history
- Configuration management
- Log viewer

---

### Command Line Interface

```bash
# Basic execution
python backend/langgraph_runner.py --prompt "Get my unread emails and summarize them"

# With scheduling
python backend/langgraph_runner.py --prompt "Send me 3 LeetCode problems daily at 9AM"

# Verbose output
python backend/langgraph_runner.py --prompt "List my GitHub repositories" --verbose
```

---

### Example Prompts by Category

#### 📧 Email Operations
```
✅ "Fetch my unread emails"
✅ "Get emails from yesterday"
✅ "Show me emails with subject 'meeting'"
✅ "Fetch emails from last week and summarize them"
```

#### 🐙 GitHub Operations
```
✅ "List my GitHub repositories"
✅ "Show commits from Hemesh11/Autotasker-AI"
✅ "Get my GitHub activity from last week"
✅ "List all repositories for username sam-ry"
✅ "Summarize my recent commits and email the report"
```

#### 💻 Coding Practice
```
✅ "Send me 3 medium LeetCode problems"
✅ "Generate 2 array coding questions"
✅ "Give me 5 easy DSA problems on trees"
✅ "Send me coding questions daily at 9AM"
```

#### ⏰ Scheduled Tasks
```
✅ "Send me LeetCode questions daily at 9AM"
✅ "Generate 3 coding questions at 10:30AM"
✅ "Get my GitHub commits every Monday at 6PM"
✅ "Email my unread emails every day at 8AM"
```

#### 🔗 Multi-Agent Workflows
```
✅ "Get my emails and GitHub commits, summarize both, and email me the report"
✅ "Generate 2 LeetCode and 2 DSA questions, then email them"
✅ "Fetch yesterday's emails, summarize them, and send summary"
✅ "List my repositories, analyze recent commits, and email results"
```

#### ⚡ Advanced Patterns
```
✅ "Send me questions now 3 times with 5 min gap"
✅ "Get emails every 10 minutes, 5 times"
✅ "Generate coding problems tonight at 11:47PM"
✅ "Schedule daily standup summary at 2:30PM"
```

📖 **[Complete Prompts Guide](COMPREHENSIVE_PROMPTS_GUIDE.md)** - 200+ example prompts

---

## 📂 Project Structure

```
AutoTasker-AI/
│
├── frontend/                    # User Interface
│   ├── streamlit_app.py        # Main Streamlit application
│   └── components/             # UI components
│
├── backend/                     # Core Application Logic
│   ├── langgraph_runner.py     # LangGraph orchestration
│   ├── scheduler.py            # Task scheduling
│   ├── llm_factory.py          # LLM client management
│   └── utils.py                # Utility functions
│
├── agents/                      # Specialized Agents
│   ├── planner_agent.py        # Natural language parsing
│   ├── gmail_agent.py          # Email operations
│   ├── github_agent.py         # GitHub operations
│   ├── dsa_agent.py            # DSA problem generation
│   ├── leetcode_agent.py       # LeetCode recommendations
│   ├── summarizer_agent.py     # Content summarization
│   ├── email_agent.py          # Email sending
│   ├── logger_agent.py         # Logging operations
│   ├── memory_agent.py         # Duplicate detection
│   ├── retry_agent.py          # Retry logic
│   └── calendar_agent.py       # Google Calendar
│
├── config/                      # Configuration
│   ├── .env                    # Environment variables (create this)
│   ├── .env.example            # Environment template
│   └── config.yaml             # Application config
│
├── google_auth/                 # Google OAuth
│   ├── credentials.json        # Google credentials (add this)
│   ├── token.pickle            # OAuth token (generated)
│   └── README.md               # Setup instructions
│
├── data/                        # Data Storage
│   ├── logs/                   # Execution logs
│   ├── emails/                 # Saved emails
│   └── memory/                 # Memory storage
│
├── memory/                      # Memory Management
│   ├── execution_memory.json   # Execution history
│   └── embeddings/             # Semantic embeddings
│
├── tests/                       # Test Suite
│   ├── test_agents.py          # Agent tests
│   ├── test_planner.py         # Planner tests
│   ├── test_scheduler.py       # Scheduler tests
│   └── test_integration.py     # Integration tests
│
├── docs/                        # Documentation
│   ├── AWS_SETUP.md            # AWS configuration
│   ├── OPENROUTER_SETUP.md     # OpenRouter guide
│   ├── ARCHITECTURE.md         # System architecture
│   └── API_REFERENCE.md        # API documentation
│
├── aws/                         # AWS Deployment
│   ├── lambda_function.py      # Lambda handler
│   ├── template.yaml           # SAM template
│   └── events/                 # EventBridge rules
│
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── COMPREHENSIVE_PROMPTS_GUIDE.md  # Prompt examples
├── .gitignore                  # Git ignore rules
└── LICENSE                     # MIT License
```

---

## 📚 Documentation

### Core Documentation
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and component interaction
- **[API Reference](docs/API_REFERENCE.md)** - Agent APIs and interfaces
- **[Comprehensive Prompts Guide](COMPREHENSIVE_PROMPTS_GUIDE.md)** - 200+ example prompts

### Setup Guides
- **[OpenRouter Setup](docs/OPENROUTER_SETUP.md)** - LLM provider configuration
- **[AWS Setup](docs/AWS_SETUP.md)** - Cloud services configuration
- **[Gmail OAuth](google_auth/README.md)** - Email integration setup

### Deployment Guides
- **[AWS Deployment](AWS_DEPLOYMENT_README.txt)** - Lambda and EventBridge
- **[Production Checklist](PRODUCTION_DEPLOYMENT_CHECKLIST.md)** - Pre-deployment steps
- **[Quick Start](QUICK_START_TESTING.md)** - Getting started quickly

---

## 🧪 Testing


### Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_agents.py -v          # Agent tests
python -m pytest tests/test_planner.py -v         # Planner tests
python -m pytest tests/test_scheduler.py -v       # Scheduler tests
python -m pytest tests/test_integration.py -v     # Integration tests

# Run with coverage
python -m pytest tests/ --cov=backend --cov=agents --cov-report=html

# Run specific agent tests
python test_gmail_agent_individual.py
python test_github_agent_comprehensive.py
python test_planner_agent_individual.py
```

### Manual Testing Scripts

```bash
# Test individual components
python quick_test_list_repos.py           # GitHub repository listing
python test_llm_connection.py             # LLM connectivity
python test_natural_language_scheduling.py # Schedule parsing

# Test complete workflows
python test_complete_integration.py        # Full workflow test
python test_production_ready.py           # Production readiness
```

### Test Coverage

- **Unit Tests**: Individual agent functionality
- **Integration Tests**: Multi-agent workflows
- **End-to-End Tests**: Complete user scenarios
- **Performance Tests**: Execution time and resource usage
- **Error Handling Tests**: Retry and recovery mechanisms

---

## 🚀 Deployment

### Local Deployment

```bash
# Development mode with auto-reload
streamlit run frontend/streamlit_app.py --server.runOnSave true

# Production mode
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### AWS Lambda Deployment

**Prerequisites:**
- AWS CLI configured
- SAM CLI installed
- S3 bucket for deployment artifacts

```bash
# Build the application
sam build

# Deploy to AWS
sam deploy --guided

# Update function
sam deploy
```

**What gets deployed:**
- Lambda function for task execution
- EventBridge rules for scheduling
- DynamoDB table for logs
- S3 bucket for artifacts
- IAM roles and permissions

📖 **[AWS Deployment Guide](AWS_DEPLOYMENT_README.txt)**

### Docker Deployment (Optional)

```dockerfile
# Dockerfile (create this)
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "frontend/streamlit_app.py"]
```

```bash
# Build and run
docker build -t autotasker-ai .
docker run -p 8501:8501 --env-file config/.env autotasker-ai
```

---

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` file to version control
2. **API Keys**: Rotate keys regularly and use least-privilege access
3. **OAuth Tokens**: Store securely and refresh periodically
4. **AWS IAM**: Use role-based access control
5. **Input Validation**: All user inputs are sanitized
6. **Error Messages**: Don't expose sensitive information in errors

---

## 📊 Performance Metrics

### Typical Performance

- **Planning**: 1-3 seconds (LLM-dependent)
- **Email Fetching**: 2-5 seconds (Gmail API)
- **GitHub Operations**: 1-3 seconds (GitHub API)
- **DSA Generation**: 15-30 seconds (LLM generation)
- **LeetCode Fetch**: 2-4 seconds (LeetCode API)
- **Email Sending**: 1-2 seconds (SES) or 3-5 seconds (Gmail)

### Optimization Tips

1. **Use OpenRouter free models** for development
2. **Cache LLM responses** when possible
3. **Batch API requests** for efficiency
4. **Use async operations** for parallel execution
5. **Monitor rate limits** to avoid throttling

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "OpenAI API key not found"**
```bash
# Solution: Add to config/.env
echo "OPENAI_API_KEY=your-key-here" >> config/.env
```

**Issue: "Gmail authentication failed"**
```bash
# Solution: Re-authorize Gmail
rm google_auth/token.pickle
# Restart application and authorize again
```

**Issue: "GitHub repository auto-detection failed"**
```bash
# Solution: Set default repository
echo "GITHUB_DEFAULT_OWNER=your-username" >> config/.env
echo "GITHUB_DEFAULT_REPO=your-repo" >> config/.env
```

**Issue: "Schedule not executing at specified time"**
```bash
# Solution: Check time format
# Correct: "at 10:02am", "at 14:30", "today at 9pm"
# Incorrect: "around 10am", "morning"
```

**Issue: "Count parameter not respected"**
```bash
# Solution: Be specific in prompt
# Correct: "Generate 3 coding questions"
# LLM will now correctly use count=3
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/Autotasker-AI.git
cd Autotasker-AI

# Create a branch
git checkout -b feature/your-feature-name

# Make changes and test
python -m pytest tests/

# Commit and push
git commit -m "Add: your feature description"
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### Contribution Guidelines

1. **Code Style**: Follow PEP 8 guidelines
2. **Type Hints**: Use type annotations for all functions
3. **Documentation**: Add docstrings to all classes and methods
4. **Testing**: Write tests for new features
5. **Commits**: Use conventional commit messages
6. **PR Description**: Clearly describe changes and rationale

### Areas for Contribution

- 🆕 **New Agents**: Add support for more APIs (Slack, Jira, etc.)
- 🔧 **Features**: Enhanced scheduling, better error handling
- 📖 **Documentation**: Improve guides and examples
- 🧪 **Testing**: Increase test coverage
- 🎨 **UI/UX**: Improve Streamlit interface
- 🐛 **Bug Fixes**: Report and fix bugs

---

## � License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Hemesh11

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
```

---

## 🙏 Acknowledgments

- **LangChain/LangGraph** - Agent orchestration framework
- **OpenAI/OpenRouter** - LLM providers
- **Streamlit** - Web framework
- **Google APIs** - Gmail and Calendar integration
- **GitHub API** - Version control integration
- **AWS Services** - Cloud infrastructure

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/Hemesh11/Autotasker-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Hemesh11/Autotasker-AI/discussions)
- **Email**: hemeshcse2005@gmail.com
- **Documentation**: [docs/](docs/)

---

## 🗺️ Roadmap

### Version 2.0 (Planned)
- [ ] Voice command support
- [ ] Mobile app interface
- [ ] More integrations (Slack, Jira, Trello)
- [ ] Advanced analytics dashboard
- [ ] Multi-user support
- [ ] Workflow templates marketplace

### Version 1.1 (In Progress)
- [x] Enhanced username extraction
- [x] Improved scheduling parser
- [x] Better count parameter handling
- [x] Detailed email formatting
- [ ] Attachment support
- [ ] Calendar event modification

---

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

---

**Built with ❤️ by Hemesh11**

*AutoTasker AI - Automating the Future, One Task at a Time* 🚀
