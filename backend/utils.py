"""
Utility functions for AutoTasker AI
"""

import os
import yaml
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    # Load environment variables
    load_dotenv("config/.env")
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Override with environment variables where available
        _override_with_env_vars(config)
        
        return config
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found, using defaults")
        return _get_default_config()
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return _get_default_config()


def _override_with_env_vars(config: Dict[str, Any]) -> None:
    """Override config values with environment variables"""
    env_mappings = {
        "OPENAI_API_KEY": ["llm", "api_key"],
        "OPENROUTER_API_KEY": ["llm", "openrouter_api_key"],
        "GITHUB_TOKEN": ["github", "token"],
        "AWS_REGION": ["aws", "region"],
        "AWS_S3_BUCKET": ["aws", "s3_bucket"],
        "DEBUG": ["app", "debug"],
        "LOG_LEVEL": ["logging", "level"],
        "MAX_RETRIES": ["app", "max_retries"],
    }
    
    for env_var, config_path in env_mappings.items():
        value = os.getenv(env_var)
        if value:
            # Navigate to nested config
            current = config
            for key in config_path[:-1]:
                current = current.setdefault(key, {})
            
            # Convert value to appropriate type
            if env_var in ["DEBUG"]:
                value = value.lower() in ["true", "1", "yes"]
            elif env_var in ["MAX_RETRIES"]:
                value = int(value)
            
            current[config_path[-1]] = value


def _get_default_config() -> Dict[str, Any]:
    """Get default configuration"""
    return {
        "app": {
            "name": "AutoTasker AI",
            "debug": True,
            "max_retries": 3,
            "timeout_seconds": 30
        },
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


def setup_logging(logging_config: Dict[str, Any]) -> logging.Logger:
    """Set up logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_file = logging_config.get("file_path", "data/logs/autotasker.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure file handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, logging_config.get("level", "INFO")))
    file_handler.setFormatter(logging.Formatter(
        logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ))
    
    # Configure stream handler with error handling for Unicode
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, logging_config.get("level", "INFO")))
    stream_handler.setFormatter(logging.Formatter(
        logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ))
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, logging_config.get("level", "INFO")),
        handlers=[file_handler, stream_handler]
    )
    
    logger = logging.getLogger("AutoTasker")
    return logger


def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are present"""
    # Check for LLM API keys (either OpenAI or OpenRouter)
    llm_key_present = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    
    # Required AWS keys
    aws_keys = [
        "AWS_ACCESS_KEY_ID", 
        "AWS_SECRET_ACCESS_KEY"
    ]
    
    validation_results = {
        "LLM_API_KEY": llm_key_present,  # Either OpenAI or OpenRouter
    }
    
    for key in aws_keys:
        validation_results[key] = bool(os.getenv(key))
    
    return validation_results


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime from string"""
    return datetime.strptime(dt_str, format_str)


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_emails_from_text(text: str) -> List[str]:
    """Extract email addresses from text"""
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def clean_html(html_content: str) -> str:
    """Remove HTML tags from content"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_content)


def create_task_id(prompt: str) -> str:
    """Create a unique task ID based on prompt and timestamp"""
    import hashlib
    
    # Create hash from prompt
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"task_{timestamp}_{prompt_hash}"


def save_json_file(data: Any, file_path: str) -> None:
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)


def load_json_file(file_path: str) -> Any:
    """Load data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return None


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure directory exists, create if not"""
    os.makedirs(directory_path, exist_ok=True)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (simple implementation)"""
    import re
    from collections import Counter
    
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out common stop words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
        'did', 'use', 'way', 'she', 'many', 'oil', 'sit', 'word', 'back',
        'when', 'much', 'went', 'been', 'call', 'each', 'find', 'said', 'will'
    }
    
    filtered_words = [word for word in words if word not in stop_words]
    word_counts = Counter(filtered_words)
    
    return [word for word, count in word_counts.most_common(max_keywords)]


class TaskTimer:
    """Context manager for timing task execution"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logging.info(f"Task '{self.task_name}' completed in {duration:.2f} seconds")
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


def clean_llm_response(response: str) -> str:
    """
    Clean LLM response to extract JSON content
    
    Args:
        response: Raw LLM response that may contain markdown or extra text
        
    Returns:
        Cleaned response content
    """
    import re
    
    # Remove markdown code blocks
    if "```json" in response:
        # Extract content between ```json and ```
        pattern = r'```json\s*(.*?)\s*```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
    elif "```" in response:
        # Extract content between any ``` blocks
        pattern = r'```.*?\s*(.*?)\s*```'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # Remove common prefixes and suffixes
    response = response.strip()
    response = re.sub(r'^(Here\'s|Here is|The response is):\s*', '', response, flags=re.IGNORECASE)
    response = re.sub(r'^Response:\s*', '', response, flags=re.IGNORECASE)
    
    return response.strip()


def parse_llm_json(response: str) -> Any:
    """
    Parse JSON from LLM response with error handling
    
    Args:
        response: LLM response that should contain JSON
        
    Returns:
        Parsed JSON data
        
    Raises:
        ValueError: If JSON cannot be parsed
    """
    try:
        cleaned = clean_llm_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {e}\nContent: {cleaned[:200]}")
