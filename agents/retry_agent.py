"""
Retry Agent: Handles task failures and retry logic
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime


class RetryAgent:
    """Agent for handling task failures and implementing retry strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RetryAgent")
        
        # Retry configuration
        self.max_retries = config.get("app", {}).get("max_retries", 3)
        self.base_delay = config.get("retry", {}).get("base_delay", 1.0)
        self.max_delay = config.get("retry", {}).get("max_delay", 60.0)
        self.backoff_multiplier = config.get("retry", {}).get("backoff_multiplier", 2.0)
        
        # Retry strategies
        self.retry_strategies = {
            "exponential_backoff": self._exponential_backoff_delay,
            "fixed_delay": self._fixed_delay,
            "linear_backoff": self._linear_backoff_delay
        }
        
        # Error patterns that suggest retrying
        self.retryable_errors = [
            "timeout",
            "rate limit",
            "connection",
            "temporary",
            "unavailable",
            "network",
            "502",
            "503", 
            "504"
        ]
        
        # Error patterns that suggest NOT retrying
        self.non_retryable_errors = [
            "authentication",
            "unauthorized", 
            "forbidden",
            "not found",
            "invalid",
            "malformed",
            "400",
            "401",
            "403",
            "404"
        ]
    
    def handle_retry(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle retry logic for failed tasks
        
        Args:
            state: Current workflow state with errors
            
        Returns:
            Retry decision and recommendations
        """
        
        try:
            errors = state.get("errors", [])
            retry_count = state.get("retry_count", 0)
            current_step = state.get("current_step", 0)
            
            if not errors:
                return {
                    "should_retry": False,
                    "reason": "No errors to retry"
                }
            
            # Check retry limits
            if retry_count >= self.max_retries:
                return {
                    "should_retry": False,
                    "reason": f"Maximum retries ({self.max_retries}) exceeded",
                    "final_failure": True
                }
            
            # Analyze errors to determine if retry is worthwhile
            retry_analysis = self._analyze_errors_for_retry(errors)
            
            if not retry_analysis["retryable"]:
                return {
                    "should_retry": False,
                    "reason": f"Errors are non-retryable: {retry_analysis['reason']}",
                    "error_analysis": retry_analysis
                }
            
            # Calculate retry delay
            delay = self._calculate_retry_delay(retry_count, retry_analysis["error_type"])
            
            # Determine retry strategy
            strategy = self._determine_retry_strategy(state, retry_analysis)
            
            self.logger.info(f"Retry {retry_count + 1}/{self.max_retries} recommended with {delay}s delay")
            
            return {
                "should_retry": True,
                "retry_count": retry_count + 1,
                "delay_seconds": delay,
                "strategy": strategy,
                "reason": retry_analysis["reason"],
                "error_analysis": retry_analysis,
                "recommendations": self._get_retry_recommendations(state, retry_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Retry analysis failed: {e}")
            return {
                "should_retry": False,
                "reason": f"Retry analysis error: {str(e)}"
            }
    
    def _analyze_errors_for_retry(self, errors: List[str]) -> Dict[str, Any]:
        """Analyze errors to determine if retry is appropriate"""
        
        if not errors:
            return {
                "retryable": False,
                "reason": "No errors to analyze",
                "error_type": "none"
            }
        
        # Combine all errors for analysis
        all_errors = " ".join(errors).lower()
        
        # Check for non-retryable patterns first
        for pattern in self.non_retryable_errors:
            if pattern in all_errors:
                return {
                    "retryable": False,
                    "reason": f"Non-retryable error pattern: {pattern}",
                    "error_type": "permanent",
                    "pattern_matched": pattern
                }
        
        # Check for retryable patterns
        retryable_matches = []
        for pattern in self.retryable_errors:
            if pattern in all_errors:
                retryable_matches.append(pattern)
        
        if retryable_matches:
            return {
                "retryable": True,
                "reason": f"Retryable error patterns found: {', '.join(retryable_matches)}",
                "error_type": "temporary",
                "patterns_matched": retryable_matches
            }
        
        # If no specific patterns matched, analyze error content
        error_analysis = self._analyze_error_content(all_errors)
        
        return {
            "retryable": error_analysis["retryable"],
            "reason": error_analysis["reason"],
            "error_type": error_analysis["error_type"],
            "confidence": error_analysis["confidence"]
        }
    
    def _analyze_error_content(self, error_text: str) -> Dict[str, Any]:
        """Analyze error content for retry decision"""
        
        # Simple heuristics for error analysis
        temporary_indicators = [
            "failed to connect",
            "timed out",
            "server error",
            "service unavailable",
            "try again",
            "internal error"
        ]
        
        permanent_indicators = [
            "invalid credentials",
            "access denied",
            "not authorized",
            "does not exist",
            "bad request",
            "malformed"
        ]
        
        temporary_score = sum(1 for indicator in temporary_indicators if indicator in error_text)
        permanent_score = sum(1 for indicator in permanent_indicators if indicator in error_text)
        
        if permanent_score > temporary_score:
            return {
                "retryable": False,
                "reason": "Error appears to be permanent",
                "error_type": "permanent",
                "confidence": min(permanent_score * 0.3, 1.0)
            }
        elif temporary_score > 0:
            return {
                "retryable": True,
                "reason": "Error appears to be temporary",
                "error_type": "temporary", 
                "confidence": min(temporary_score * 0.3, 1.0)
            }
        else:
            # Default to retryable with low confidence
            return {
                "retryable": True,
                "reason": "Unknown error type, defaulting to retryable",
                "error_type": "unknown",
                "confidence": 0.2
            }
    
    def _calculate_retry_delay(self, retry_count: int, error_type: str) -> float:
        """Calculate appropriate delay before retry"""
        
        strategy = "exponential_backoff"
        
        # Adjust strategy based on error type
        if error_type == "rate_limit":
            strategy = "exponential_backoff"
        elif error_type == "network":
            strategy = "fixed_delay"
        
        delay_func = self.retry_strategies.get(strategy, self._exponential_backoff_delay)
        return delay_func(retry_count)
    
    def _exponential_backoff_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.base_delay * (self.backoff_multiplier ** retry_count)
        return min(delay, self.max_delay)
    
    def _fixed_delay(self, retry_count: int) -> float:
        """Calculate fixed delay"""
        return self.base_delay
    
    def _linear_backoff_delay(self, retry_count: int) -> float:
        """Calculate linear backoff delay"""
        delay = self.base_delay * (retry_count + 1)
        return min(delay, self.max_delay)
    
    def _determine_retry_strategy(self, state: Dict[str, Any], 
                                error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best retry strategy for the current situation"""
        
        strategy = {
            "approach": "standard_retry",
            "modifications": [],
            "fallback_options": []
        }
        
        # Analyze current task and errors
        current_step = state.get("current_step", 0)
        task_plan = state.get("task_plan", {})
        tasks = task_plan.get("tasks", [])
        
        if current_step < len(tasks):
            current_task = tasks[current_step]
            task_type = current_task.get("type", "")
            
            # Task-specific retry strategies
            if task_type == "gmail":
                strategy = self._gmail_retry_strategy(error_analysis)
            elif task_type == "github":
                strategy = self._github_retry_strategy(error_analysis)
            elif task_type == "dsa":
                strategy = self._dsa_retry_strategy(error_analysis)
            elif task_type == "email":
                strategy = self._email_retry_strategy(error_analysis)
        
        return strategy
    
    def _gmail_retry_strategy(self, error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Gmail-specific retry strategy"""
        
        strategy = {
            "approach": "gmail_retry",
            "modifications": [],
            "fallback_options": ["reduce_query_scope", "use_different_credentials"]
        }
        
        # Gmail API specific handling
        if "quota" in error_analysis.get("reason", "").lower():
            strategy["modifications"].append("reduce_request_size")
            strategy["modifications"].append("add_quota_delay")
        
        if "authentication" in error_analysis.get("reason", "").lower():
            strategy["fallback_options"].append("refresh_oauth_token")
        
        return strategy
    
    def _github_retry_strategy(self, error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """GitHub-specific retry strategy"""
        
        strategy = {
            "approach": "github_retry",
            "modifications": [],
            "fallback_options": ["reduce_request_count", "use_different_endpoint"]
        }
        
        # GitHub API specific handling
        if "rate limit" in error_analysis.get("reason", "").lower():
            strategy["modifications"].append("respect_rate_limits")
            strategy["modifications"].append("add_longer_delay")
        
        return strategy
    
    def _dsa_retry_strategy(self, error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """DSA generation retry strategy"""
        
        strategy = {
            "approach": "llm_retry",
            "modifications": [],
            "fallback_options": ["use_fallback_questions", "reduce_complexity"]
        }
        
        # LLM-specific handling
        if "token" in error_analysis.get("reason", "").lower():
            strategy["modifications"].append("reduce_prompt_size")
        
        if "model" in error_analysis.get("reason", "").lower():
            strategy["fallback_options"].append("switch_to_backup_model")
        
        return strategy
    
    def _email_retry_strategy(self, error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Email sending retry strategy"""
        
        strategy = {
            "approach": "email_retry",
            "modifications": [],
            "fallback_options": ["switch_email_service", "save_to_file"]
        }
        
        # Email service specific handling
        if "quota" in error_analysis.get("reason", "").lower():
            strategy["modifications"].append("reduce_email_size")
        
        if "authentication" in error_analysis.get("reason", "").lower():
            strategy["fallback_options"].append("use_alternative_sender")
        
        return strategy
    
    def _get_retry_recommendations(self, state: Dict[str, Any], 
                                 error_analysis: Dict[str, Any]) -> List[str]:
        """Get specific recommendations for retry attempts"""
        
        recommendations = []
        
        # General recommendations
        if error_analysis.get("error_type") == "temporary":
            recommendations.append("Wait for service to recover")
        
        if "rate limit" in error_analysis.get("reason", "").lower():
            recommendations.append("Reduce request frequency")
            recommendations.append("Add longer delays between requests")
        
        if "authentication" in error_analysis.get("reason", "").lower():
            recommendations.append("Check API credentials")
            recommendations.append("Refresh authentication tokens")
        
        if "network" in error_analysis.get("reason", "").lower():
            recommendations.append("Check internet connection")
            recommendations.append("Try alternative network path")
        
        # Task-specific recommendations
        current_step = state.get("current_step", 0)
        task_plan = state.get("task_plan", {})
        tasks = task_plan.get("tasks", [])
        
        if current_step < len(tasks):
            current_task = tasks[current_step]
            task_type = current_task.get("type", "")
            
            if task_type == "gmail":
                recommendations.append("Verify Gmail API permissions")
                recommendations.append("Check OAuth token validity")
            elif task_type == "github":
                recommendations.append("Verify GitHub token permissions")
                recommendations.append("Check repository access rights")
            elif task_type == "dsa":
                recommendations.append("Verify OpenAI API key")
                recommendations.append("Check token usage limits")
        
        return recommendations
    
    def execute_retry_with_delay(self, delay_seconds: float) -> None:
        """Execute delay before retry"""
        
        if delay_seconds > 0:
            self.logger.info(f"Waiting {delay_seconds} seconds before retry...")
            time.sleep(delay_seconds)
    
    def log_retry_attempt(self, retry_info: Dict[str, Any]) -> None:
        """Log retry attempt details"""
        
        self.logger.warning(
            f"Retry attempt {retry_info.get('retry_count', 0)} - "
            f"Reason: {retry_info.get('reason', 'Unknown')} - "
            f"Strategy: {retry_info.get('strategy', {}).get('approach', 'default')}"
        )
    
    def should_give_up(self, state: Dict[str, Any]) -> bool:
        """Determine if we should give up on retries"""
        
        retry_count = state.get("retry_count", 0)
        errors = state.get("errors", [])
        
        # Give up if max retries reached
        if retry_count >= self.max_retries:
            return True
        
        # Give up if we detect permanent errors
        if errors:
            all_errors = " ".join(errors).lower()
            for pattern in self.non_retryable_errors:
                if pattern in all_errors:
                    return True
        
        return False
