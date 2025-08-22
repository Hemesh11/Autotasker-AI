"""
Tool Selector: Maps tasks to appropriate agent nodes
"""

import os
import logging
from typing import Dict, List, Any, Optional


class ToolSelector:
    """Selects appropriate agents/tools based on task requirements"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ToolSelector")
        
        # Define task type mappings
        self.task_mappings = {
            # Email related
            "gmail": ["gmail_agent"],
            "email": ["email_agent"],
            "mail": ["gmail_agent"],
            "inbox": ["gmail_agent"],
            
            # Code generation
            "dsa": ["dsa_agent"],
            "leetcode": ["dsa_agent"],
            "coding": ["dsa_agent"],
            "algorithm": ["dsa_agent"],
            "programming": ["dsa_agent"],
            "questions": ["dsa_agent"],
            
            # GitHub related
            "github": ["github_agent"],
            "git": ["github_agent"],
            "commit": ["github_agent"],
            "repository": ["github_agent"],
            "repo": ["github_agent"],
            
            # Content processing
            "summarize": ["summarizer_agent"],
            "summary": ["summarizer_agent"],
            "analyze": ["summarizer_agent"],
            
            # Utility
            "log": ["logger_agent"],
            "memory": ["memory_agent"],
            "retry": ["retry_agent"]
        }
        
        # Agent capabilities
        self.agent_capabilities = {
            "gmail_agent": {
                "can_fetch_emails": True,
                "can_search_emails": True,
                "can_send_emails": True,
                "requires_auth": True,
                "data_sources": ["gmail"]
            },
            "github_agent": {
                "can_fetch_commits": True,
                "can_fetch_issues": True,
                "can_fetch_repos": True,
                "requires_auth": True,
                "data_sources": ["github"]
            },
            "dsa_agent": {
                "can_generate_questions": True,
                "can_create_problems": True,
                "requires_llm": True,
                "data_sources": ["llm"]
            },
            "summarizer_agent": {
                "can_summarize_text": True,
                "can_analyze_content": True,
                "requires_llm": True,
                "data_sources": ["llm"]
            },
            "email_agent": {
                "can_send_emails": True,
                "can_format_content": True,
                "supports_html": True,
                "data_sources": ["gmail", "ses"]
            },
            "logger_agent": {
                "can_log_execution": True,
                "can_store_data": True,
                "supports_multiple_backends": True,
                "data_sources": ["sheets", "s3", "local"]
            },
            "memory_agent": {
                "can_check_history": True,
                "can_store_state": True,
                "can_prevent_duplicates": True,
                "data_sources": ["sheets", "local"]
            },
            "retry_agent": {
                "can_handle_failures": True,
                "can_retry_tasks": True,
                "can_adapt_strategy": True,
                "data_sources": ["internal"]
            }
        }
    
    def select_agents_for_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Select appropriate agents for a list of tasks
        
        Args:
            tasks: List of task definitions
            
        Returns:
            Mapping of task IDs to required agents
        """
        
        task_agent_mapping = {}
        
        for task in tasks:
            task_id = task.get("id", "unknown")
            agents = self.select_agents_for_task(task)
            task_agent_mapping[task_id] = agents
            
            self.logger.debug(f"Task {task_id} mapped to agents: {agents}")
        
        return task_agent_mapping
    
    def select_agents_for_task(self, task: Dict[str, Any]) -> List[str]:
        """
        Select appropriate agents for a single task
        
        Args:
            task: Task definition
            
        Returns:
            List of agent names needed for this task
        """
        
        task_type = task.get("type", "").lower()
        description = task.get("description", "").lower()
        
        # Direct mapping by task type
        if task_type in self.task_mappings:
            return self.task_mappings[task_type].copy()
        
        # Fuzzy matching by keywords in description
        matched_agents = set()
        
        for keyword, agents in self.task_mappings.items():
            if keyword in description or keyword in task_type:
                matched_agents.update(agents)
        
        # If no matches, try to infer from task content
        if not matched_agents:
            matched_agents = self._infer_agents_from_content(task)
        
        # Always ensure logger agent is included for tracking
        matched_agents.add("logger_agent")
        
        return list(matched_agents)
    
    def _infer_agents_from_content(self, task: Dict[str, Any]) -> set:
        """Infer required agents from task content"""
        
        agents = set()
        
        # Check parameters for clues
        parameters = task.get("parameters", {})
        
        # Look for data source indicators
        if any(key in parameters for key in ["email", "gmail", "inbox"]):
            agents.add("gmail_agent")
        
        if any(key in parameters for key in ["github", "repo", "commit"]):
            agents.add("github_agent")
        
        if any(key in parameters for key in ["count", "questions", "difficulty"]):
            agents.add("dsa_agent")
        
        # Check for content that needs summarization
        if "summarize" in task.get("description", "").lower():
            agents.add("summarizer_agent")
        
        # Default to email agent if no specific agent found
        if not agents:
            agents.add("email_agent")
        
        return agents
    
    def get_agent_dependencies(self, agent_name: str) -> List[str]:
        """
        Get dependencies for an agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            List of prerequisite agents
        """
        
        dependencies = {
            "gmail_agent": [],
            "github_agent": [],
            "dsa_agent": [],
            "summarizer_agent": ["gmail_agent", "github_agent"],  # Needs content to summarize
            "email_agent": [],  # Can work independently
            "logger_agent": [],
            "memory_agent": [],
            "retry_agent": []
        }
        
        return dependencies.get(agent_name, [])
    
    def validate_agent_requirements(self, agent_name: str) -> Dict[str, Any]:
        """
        Validate if agent requirements are met
        
        Args:
            agent_name: Name of the agent to validate
            
        Returns:
            Validation results
        """
        
        capabilities = self.agent_capabilities.get(agent_name, {})
        validation_results = {
            "agent": agent_name,
            "available": True,
            "issues": []
        }
        
        # Check authentication requirements
        if capabilities.get("requires_auth") and agent_name == "gmail_agent":
            # Check for Gmail credentials
            gmail_creds = self.config.get("google", {}).get("credentials_path")
            if not gmail_creds:
                validation_results["issues"].append("Gmail credentials not configured")
        
        if capabilities.get("requires_auth") and agent_name == "github_agent":
            # Check for GitHub token
            github_token = self.config.get("github", {}).get("token") or os.getenv("GITHUB_TOKEN")
            if not github_token:
                validation_results["issues"].append("GitHub token not configured")
        
        # Check LLM requirements
        if capabilities.get("requires_llm"):
            # Check for either OpenAI or OpenRouter API key
            openai_key = self.config.get("llm", {}).get("api_key")
            openrouter_key = self.config.get("llm", {}).get("openrouter_api_key")
            
            if not openai_key and not openrouter_key:
                validation_results["issues"].append("LLM API key not configured (OpenAI or OpenRouter required)")
        
        # Check AWS requirements for certain agents
        if agent_name in ["logger_agent", "email_agent"]:
            aws_config = self.config.get("aws", {})
            if not aws_config.get("region"):
                validation_results["issues"].append("AWS region not configured")
        
        validation_results["available"] = len(validation_results["issues"]) == 0
        
        return validation_results
    
    def get_execution_order(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """
        Determine optimal execution order for tasks
        
        Args:
            tasks: List of task definitions
            
        Returns:
            Ordered list of task IDs
        """
        
        # Build dependency graph
        task_dependencies = {}
        for task in tasks:
            task_id = task.get("id")
            dependencies = task.get("dependencies", [])
            priority = task.get("priority", 2)
            
            task_dependencies[task_id] = {
                "deps": dependencies,
                "priority": priority,
                "type": task.get("type")
            }
        
        # Topological sort with priority
        ordered_tasks = []
        completed = set()
        
        while len(completed) < len(tasks):
            # Find tasks that can be executed (all dependencies met)
            ready_tasks = []
            
            for task_id, info in task_dependencies.items():
                if task_id not in completed:
                    deps_met = all(dep in completed for dep in info["deps"])
                    if deps_met:
                        ready_tasks.append((task_id, info["priority"]))
            
            if not ready_tasks:
                # Circular dependency or error - add remaining tasks
                remaining = [tid for tid in task_dependencies.keys() if tid not in completed]
                ordered_tasks.extend(remaining)
                break
            
            # Sort by priority (1 = high, 3 = low)
            ready_tasks.sort(key=lambda x: x[1])
            
            # Add highest priority task
            next_task = ready_tasks[0][0]
            ordered_tasks.append(next_task)
            completed.add(next_task)
        
        return ordered_tasks
    
    def get_parallel_execution_groups(self, tasks: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Group tasks that can be executed in parallel
        
        Args:
            tasks: List of task definitions
            
        Returns:
            List of execution groups (tasks in same group can run in parallel)
        """
        
        ordered_tasks = self.get_execution_order(tasks)
        task_dict = {t.get("id"): t for t in tasks}
        
        execution_groups = []
        remaining_tasks = ordered_tasks.copy()
        completed = set()
        
        while remaining_tasks:
            # Find tasks that can start now (dependencies met)
            current_group = []
            
            for task_id in remaining_tasks.copy():
                task = task_dict.get(task_id, {})
                dependencies = task.get("dependencies", [])
                
                if all(dep in completed for dep in dependencies):
                    current_group.append(task_id)
                    remaining_tasks.remove(task_id)
            
            if current_group:
                execution_groups.append(current_group)
                completed.update(current_group)
            else:
                # Fallback - add remaining tasks one by one
                if remaining_tasks:
                    execution_groups.append([remaining_tasks.pop(0)])
        
        return execution_groups
