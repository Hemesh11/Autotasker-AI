"""
OpenRouter API Client for AutoTasker AI

This module provides a unified interface for using OpenRouter API as a drop-in replacement
for OpenAI's API. OpenRouter provides access to multiple LLMs through a single API.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterResponse:
    """Wrapper for OpenRouter API responses to match OpenAI format"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str = "stop"


class OpenRouterClient:
    """
    OpenRouter API client that mimics OpenAI's interface for easy drop-in replacement.
    
    OpenRouter provides access to multiple models including:
    - GPT-4, GPT-3.5-turbo (OpenAI)
    - Claude (Anthropic)
    - Llama 2 (Meta)
    - PaLM (Google)
    - And many more
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "openai/gpt-3.5-turbo",
        app_name: str = "AutoTasker-AI"
    ):
        """
        Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key (or get from OPENROUTER_API_KEY env var)
            base_url: OpenRouter API base URL
            default_model: Default model to use for requests
            app_name: Application name for tracking
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
            
        self.base_url = base_url
        self.default_model = default_model
        self.app_name = app_name
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://autotasker-ai.app",  # Optional: for rankings
            "X-Title": app_name  # Optional: for rankings
        }
        
        # Create chat completions object to match OpenAI interface
        self.chat = ChatCompletions(self)
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenRouter API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(f"OpenRouter API error: {e}")
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter"""
        try:
            url = f"{self.base_url}/models"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to get OpenRouter models: {e}")
            return []


class ChatCompletions:
    """Chat completions interface matching OpenAI's format"""
    
    def __init__(self, client: OpenRouterClient):
        self.client = client
    
    def create(
        self,
        model: Optional[str] = None,
        messages: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs
    ) -> OpenRouterResponse:
        """
        Create chat completion using OpenRouter API
        
        Args:
            model: Model to use (defaults to client's default_model)
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            **kwargs: Additional parameters
            
        Returns:
            OpenRouterResponse object with content and metadata
        """
        if not messages:
            raise ValueError("Messages are required")
        
        # Use default model if none specified
        model = model or self.client.default_model
        
        # Prepare request data
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
        }
        
        # Add optional parameters
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        # Add any additional kwargs
        data.update(kwargs)
        
        try:
            response = self.client._make_request("chat/completions", data)
            
            # Extract response data
            choice = response["choices"][0]
            message = choice["message"]
            usage = response.get("usage", {})
            
            return OpenRouterResponse(
                content=message["content"],
                model=response.get("model", model),
                usage=usage,
                finish_reason=choice.get("finish_reason", "stop")
            )
            
        except Exception as e:
            logger.error(f"OpenRouter chat completion failed: {e}")
            raise


def create_openrouter_client(config: Dict[str, Any]) -> OpenRouterClient:
    """
    Factory function to create OpenRouter client from config
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured OpenRouter client
    """
    # Get API key from config or environment
    api_key = (
        config.get("llm", {}).get("api_key") or 
        config.get("openrouter_api_key") or
        os.getenv("OPENROUTER_API_KEY")
    )
    
    # Get model preference
    default_model = (
        config.get("llm", {}).get("model") or
        "openai/gpt-3.5-turbo"
    )
    
    return OpenRouterClient(
        api_key=api_key,
        default_model=default_model
    )


# Popular OpenRouter models for different use cases
RECOMMENDED_MODELS = {
    "fast": "openai/gpt-3.5-turbo",           # Fast and cost-effective
    "balanced": "openai/gpt-4-turbo-preview", # Good balance of speed/quality
    "powerful": "openai/gpt-4",               # Most capable
    "creative": "anthropic/claude-3-sonnet",  # Good for creative tasks
    "coding": "meta-llama/codellama-34b",     # Specialized for code
    "free": "mistralai/mistral-7b-instruct",  # Free tier option
}

def get_model_recommendation(task_type: str = "balanced") -> str:
    """Get recommended model for specific task type"""
    return RECOMMENDED_MODELS.get(task_type, RECOMMENDED_MODELS["balanced"])
