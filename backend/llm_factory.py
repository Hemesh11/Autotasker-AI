"""
LLM Client Factory for AutoTasker AI

This module provides a unified interface for creating LLM clients,
supporting both OpenAI and OpenRouter APIs seamlessly.
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from openai import OpenAI
from backend.openrouter_client import OpenRouterClient, create_openrouter_client

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory for creating LLM clients based on configuration"""
    
    @staticmethod
    def create_client(config: Dict[str, Any]) -> Union[OpenAI, OpenRouterClient]:
        """
        Create appropriate LLM client based on configuration
        
        Args:
            config: Application configuration dictionary
            
        Returns:
            Either OpenAI or OpenRouter client
        """
        # Determine which provider to use
        provider = config.get("llm", {}).get("provider", "openrouter").lower()
        
        if provider == "openai":
            return LLMClientFactory._create_openai_client(config)
        elif provider == "openrouter":
            return LLMClientFactory._create_openrouter_client(config)
        else:
            # Default to OpenRouter for better model selection
            logger.warning(f"Unknown provider '{provider}', defaulting to OpenRouter")
            return LLMClientFactory._create_openrouter_client(config)
    
    @staticmethod
    def _create_openai_client(config: Dict[str, Any]) -> OpenAI:
        """Create OpenAI client"""
        api_key = (
            config.get("llm", {}).get("api_key") or 
            config.get("openai_api_key") or
            os.getenv("OPENAI_API_KEY")
        )
        
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        return OpenAI(api_key=api_key)
    
    @staticmethod
    def _create_openrouter_client(config: Dict[str, Any]) -> OpenRouterClient:
        """Create OpenRouter client"""
        return create_openrouter_client(config)
    
    @staticmethod
    def get_model_name(config: Dict[str, Any], agent_type: Optional[str] = None) -> str:
        """
        Get appropriate model name for the provider and agent type
        
        Args:
            config: Application configuration
            agent_type: Specific agent type (planner, summarizer, etc.)
            
        Returns:
            Model name appropriate for the configured provider
        """
        provider = config.get("llm", {}).get("provider", "openrouter").lower()
        
        # Try to get agent-specific model first
        if agent_type:
            agent_model = config.get("agents", {}).get(agent_type, {}).get("model")
            if agent_model:
                return agent_model
        
        # Fall back to default model
        if provider == "openrouter":
            return config.get("llm", {}).get("openrouter", {}).get("default_model") or \
                   config.get("llm", {}).get("model") or \
                   "openai/gpt-3.5-turbo"
        else:
            # For OpenAI, remove provider prefix if present
            model = config.get("llm", {}).get("model") or "gpt-3.5-turbo"
            if "/" in model:
                return model.split("/")[-1]  # Remove "openai/" prefix
            return model


def create_llm_client(config: Dict[str, Any]) -> Union[OpenAI, OpenRouterClient]:
    """
    Convenience function to create LLM client
    
    Args:
        config: Application configuration
        
    Returns:
        Configured LLM client
    """
    return LLMClientFactory.create_client(config)


def get_chat_completion(
    client: Union[OpenAI, OpenRouterClient],
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> str:
    """
    Unified interface for getting chat completions from either client
    
    Args:
        client: OpenAI or OpenRouter client
        messages: List of message dictionaries
        model: Model to use (optional)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Returns:
        Generated text content
    """
    try:
        # Common parameters
        params = {
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        
        if model:
            params["model"] = model
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        # Make API call
        response = client.chat.create(**params)
        
        # Extract content based on client type
        if isinstance(client, OpenAI):
            return response.choices[0].message.content
        else:  # OpenRouterClient
            return response.content
            
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise Exception(f"LLM API error: {e}")
