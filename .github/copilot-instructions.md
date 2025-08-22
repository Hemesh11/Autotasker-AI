# AutoTasker AI - Copilot Instructions

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview

AutoTasker AI is a self-healing, multi-agentic workflow orchestrator that converts natural language prompts into automated tasks across various APIs and cloud services. The system uses LangGraph for agent orchestration, with specialized agents for different tasks.

## Architecture

### Core Components
- **LangGraph Runner**: Main orchestrator in `backend/langgraph_runner.py`
- **Agents**: Specialized task handlers in `agents/` directory
- **Frontend**: Streamlit UI in `frontend/streamlit_app.py`
- **Configuration**: YAML and environment-based config in `config/`

### Agent Types
- **Planner Agent**: Converts natural language to structured task plans
- **Gmail Agent**: Email operations using Gmail API
- **GitHub Agent**: Repository data and commit analysis
- **DSA Agent**: Generates coding questions using LLM
- **Summarizer Agent**: Content summarization with LLM
- **Email Agent**: Sends results via Gmail API or AWS SES
- **Logger Agent**: Execution logging to multiple backends
- **Memory Agent**: Prevents duplicate executions
- **Retry Agent**: Handles failures and implements retry logic

## Development Guidelines

### Code Style
- Use type hints for all function parameters and returns
- Follow Python naming conventions (snake_case for functions/variables)
- Add comprehensive docstrings for all classes and methods
- Use logging instead of print statements
- Handle exceptions gracefully with appropriate error messages

### Agent Development
- All agents should inherit from a common pattern
- Implement `execute_task(task: Dict[str, Any]) -> Dict[str, Any]` method
- Use retry decorators for external API calls
- Return consistent result format with success/error indicators
- Log important operations and errors

### LLM Integration
- Use OpenAI client for LLM operations
- Implement proper prompt engineering with system/user messages
- Handle API errors and implement fallback responses
- Use appropriate temperature settings for different tasks
- Implement token limit awareness

### Configuration
- Store sensitive data in environment variables
- Use config.yaml for application settings
- Implement proper OAuth flows for Google services
- Support multiple backend configurations (local, cloud)

### Testing
- Write unit tests for all agent methods
- Mock external API calls in tests
- Test error conditions and retry logic
- Include integration tests for workflow execution

### Error Handling
- Implement comprehensive error catching
- Provide meaningful error messages
- Use retry mechanisms for transient failures
- Implement graceful degradation when services are unavailable

## API Integrations

### Gmail API
- Use OAuth 2.0 for authentication
- Implement proper scope management
- Handle rate limiting and quota errors
- Support both reading and sending emails

### OpenAI API
- Manage API key securely
- Implement proper error handling for rate limits
- Use appropriate models for different tasks
- Handle token limit exceptions

### AWS Services
- Support multiple AWS services (S3, SES, Lambda)
- Use boto3 for AWS integrations
- Handle AWS credential management
- Implement proper error handling for AWS services

## Frontend Development

### Streamlit UI
- Use clean, intuitive interface design
- Implement proper error display and user feedback
- Support real-time task execution monitoring
- Provide configuration management interface

### State Management
- Use session state for task history
- Implement proper data persistence
- Handle UI refresh scenarios gracefully

## Deployment Considerations

### Environment Setup
- Support multiple deployment environments
- Use environment-specific configurations
- Implement proper secret management
- Support both local and cloud deployment

### Monitoring
- Implement comprehensive logging
- Support multiple log backends
- Provide execution statistics and monitoring
- Implement health checks for all services

## Security Best Practices

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Implement proper OAuth flows
- Validate all user inputs
- Use secure communication for API calls

## Performance Optimization

- Implement caching where appropriate
- Use async operations for I/O bound tasks
- Optimize LLM token usage
- Implement proper rate limiting

## When writing code for this project:

1. Always check for existing utility functions in `backend/utils.py`
2. Use the established error handling patterns
3. Follow the agent architecture patterns
4. Implement proper logging throughout
5. Consider retry logic for external service calls
6. Use type hints and comprehensive docstrings
7. Handle configuration through the established config system
8. Test both success and failure scenarios
