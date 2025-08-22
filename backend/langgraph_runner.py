"""
AutoTasker AI: Main LangGraph Runner
Orchestrates multi-agent workflows based on natural language prompts
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from agents.planner_agent import PlannerAgent
from agents.tool_selector import ToolSelector
from agents.gmail_agent import GmailAgent
from agents.github_agent import GitHubAgent
from agents.dsa_agent import DSAAgent
from agents.leetcode_agent import LeetCodeAgent
from agents.summarizer_agent import SummarizerAgent
from agents.email_agent import EmailAgent
from agents.logger_agent import LoggerAgent
from agents.retry_agent import RetryAgent
from agents.memory_agent import MemoryAgent
from agents.calendar_agent import CalendarAgent
from backend.utils import load_config, setup_logging


class WorkflowState(TypedDict):
    """State shared across all agents in the workflow"""
    original_prompt: str
    task_plan: Dict[str, Any]
    current_step: int
    execution_results: Dict[str, Any]
    errors: List[str]
    retry_count: int
    email_content: str
    logs: List[Dict[str, Any]]
    memory_check: Dict[str, Any]


class AutoTaskerRunner:
    """Main orchestrator for AutoTasker AI workflows"""
    
    def __init__(self, config: Dict[str, Any] = None, config_path: str = "config/config.yaml"):
        if config is not None:
            self.config = config
        else:
            self.config = load_config(config_path)
        self.logger = setup_logging(self.config.get('logging', {}))
        
        # Initialize agents
        self.planner = PlannerAgent(self.config)
        self.tool_selector = ToolSelector(self.config)
        self.gmail_agent = GmailAgent(self.config)
        self.github_agent = GitHubAgent(self.config)
        self.dsa_agent = DSAAgent(self.config)
        self.leetcode_agent = LeetCodeAgent(self.config)
        self.summarizer_agent = SummarizerAgent(self.config)
        self.email_agent = EmailAgent(self.config)
        self.logger_agent = LoggerAgent(self.config)
        self.retry_agent = RetryAgent(self.config)
        self.memory_agent = MemoryAgent(self.config)
        self.calendar_agent = CalendarAgent(self.config)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("memory_check", self.memory_check_node)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("gmail_task", self.gmail_task_node)
        workflow.add_node("github_task", self.github_task_node)
        workflow.add_node("dsa_task", self.dsa_task_node)
        workflow.add_node("leetcode_task", self.leetcode_task_node)
        workflow.add_node("calendar_task", self.calendar_task_node)
        workflow.add_node("summarizer_task", self.summarizer_task_node)
        workflow.add_node("email_task", self.email_task_node)
        workflow.add_node("logger_task", self.logger_task_node)
        workflow.add_node("retry_handler", self.retry_handler_node)
        
        # Define edges
        workflow.add_edge("memory_check", "planner")
        workflow.add_conditional_edges(
            "planner",
            self.route_tasks,
            {
                "gmail": "gmail_task",
                "github": "github_task", 
                "dsa": "dsa_task",
                "leetcode": "leetcode_task",
                "calendar": "calendar_task",
                "email": "email_task",
                "end": END
            }
        )
        
        # Add retry edges for all task nodes
        for task_node in ["gmail_task", "github_task", "dsa_task", "leetcode_task", "calendar_task", "summarizer_task"]:
            workflow.add_conditional_edges(
                task_node,
                self.check_for_retry,
                {
                    "retry": "retry_handler",
                    "continue": "email_task",
                    "summarize": "summarizer_task"
                }
            )
            
        workflow.add_edge("retry_handler", "planner")
        workflow.add_edge("email_task", "logger_task")
        workflow.add_edge("logger_task", END)
        
        # Set entry point
        workflow.set_entry_point("memory_check")
        
        return workflow.compile()
    
    def memory_check_node(self, state: WorkflowState) -> WorkflowState:
        """Check if similar task was executed recently"""
        try:
            memory_result = self.memory_agent.check_recent_execution(state["original_prompt"])
            state["memory_check"] = memory_result
            
            if memory_result.get("should_skip", False):
                self.logger.info(f"Skipping task due to recent execution: {memory_result}")
                state["execution_results"]["skipped"] = True
                
        except Exception as e:
            self.logger.error(f"Memory check failed: {e}")
            state["errors"].append(f"Memory check error: {str(e)}")
            
        return state
    
    def planner_node(self, state: WorkflowState) -> WorkflowState:
        """Convert natural language prompt to structured task plan"""
        try:
            if state.get("memory_check", {}).get("should_skip", False):
                return state
                
            task_plan = self.planner.create_task_plan(state["original_prompt"])
            state["task_plan"] = task_plan
            state["current_step"] = 0
            
            self.logger.info(f"Generated task plan: {task_plan}")
            
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            state["errors"].append(f"Planning error: {str(e)}")
            
        return state
    
    def route_tasks(self, state: WorkflowState) -> str:
        """Route to appropriate task based on plan"""
        if state.get("memory_check", {}).get("should_skip", False):
            return "end"
            
        task_plan = state.get("task_plan", {})
        tasks = task_plan.get("tasks", [])
        
        if not tasks or state["current_step"] >= len(tasks):
            return "email"
            
        current_task = tasks[state["current_step"]]
        task_type = current_task.get("type", "")
        
        # Route based on task type
        if "gmail" in task_type.lower() or "email" in task_type.lower():
            return "gmail"
        elif "github" in task_type.lower() or "commit" in task_type.lower():
            return "github"
        elif "leetcode" in task_type.lower():
            return "leetcode"
        elif "dsa" in task_type.lower() or "coding" in task_type.lower() or "question" in task_type.lower():
            return "dsa"
        elif "calendar" in task_type.lower() or "meeting" in task_type.lower() or "event" in task_type.lower() or "schedule" in task_type.lower():
            return "calendar"
        else:
            return "email"
    
    def gmail_task_node(self, state: WorkflowState) -> WorkflowState:
        """Execute Gmail-related tasks"""
        try:
            current_task = state["task_plan"]["tasks"][state["current_step"]]
            result = self.gmail_agent.execute_task(current_task)
            
            state["execution_results"][f"gmail_{state['current_step']}"] = result
            state["current_step"] += 1
            
            self.logger.info(f"Gmail task completed: {result}")
            
        except Exception as e:
            self.logger.error(f"Gmail task failed: {e}")
            state["errors"].append(f"Gmail task error: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
            
        return state
    
    def github_task_node(self, state: WorkflowState) -> WorkflowState:
        """Execute GitHub-related tasks"""
        try:
            current_task = state["task_plan"]["tasks"][state["current_step"]]
            result = self.github_agent.execute_task(current_task)
            
            state["execution_results"][f"github_{state['current_step']}"] = result
            state["current_step"] += 1
            
            self.logger.info(f"GitHub task completed: {result}")
            
        except Exception as e:
            self.logger.error(f"GitHub task failed: {e}")
            state["errors"].append(f"GitHub task error: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
            
        return state
    
    def dsa_task_node(self, state: WorkflowState) -> WorkflowState:
        """Execute DSA generation tasks"""
        try:
            current_task = state["task_plan"]["tasks"][state["current_step"]]
            result = self.dsa_agent.execute_task(current_task)
            
            state["execution_results"][f"dsa_{state['current_step']}"] = result
            state["current_step"] += 1
            
            self.logger.info(f"DSA task completed: {result}")
            
        except Exception as e:
            self.logger.error(f"DSA task failed: {e}")
            state["errors"].append(f"DSA task error: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
            
        return state
    
    def leetcode_task_node(self, state: WorkflowState) -> WorkflowState:
        """Execute LeetCode-related tasks"""
        try:
            current_task = state["task_plan"]["tasks"][state["current_step"]]
            result = self.leetcode_agent.execute_task(current_task)
            
            state["execution_results"][f"leetcode_{state['current_step']}"] = result
            state["current_step"] += 1
            
            self.logger.info(f"LeetCode task completed: {result}")
            
        except Exception as e:
            self.logger.error(f"LeetCode task failed: {e}")
            state["errors"].append(f"LeetCode task error: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
            
        return state
    
    def calendar_task_node(self, state: WorkflowState) -> WorkflowState:
        """Execute Calendar-related tasks"""
        try:
            current_task = state["task_plan"]["tasks"][state["current_step"]]
            result = self.calendar_agent.execute_task(current_task)
            
            state["execution_results"][f"calendar_{state['current_step']}"] = result
            state["current_step"] += 1
            
            self.logger.info(f"Calendar task completed: {result}")
            
        except Exception as e:
            self.logger.error(f"Calendar task failed: {e}")
            state["errors"].append(f"Calendar task error: {str(e)}")
            state["retry_count"] = state.get("retry_count", 0) + 1
            
        return state
    
    def summarizer_task_node(self, state: WorkflowState) -> WorkflowState:
        """Execute summarization tasks"""
        try:
            # Get content that needs summarization
            content_to_summarize = []
            for key, result in state["execution_results"].items():
                if isinstance(result, dict) and result.get("content"):
                    content_to_summarize.append(result["content"])
            
            if content_to_summarize:
                summary = self.summarizer_agent.summarize_content(content_to_summarize)
                state["execution_results"]["summary"] = summary
                
                self.logger.info(f"Summarization completed")
            
        except Exception as e:
            self.logger.error(f"Summarization failed: {e}")
            state["errors"].append(f"Summarization error: {str(e)}")
            
        return state
    
    def email_task_node(self, state: WorkflowState) -> WorkflowState:
        """Send email with results"""
        try:
            # Compile email content from all results
            email_content = self._compile_email_content(state)
            result = self.email_agent.send_email(email_content)
            
            state["execution_results"]["email_sent"] = result
            state["email_content"] = email_content["body"]
            
            self.logger.info(f"Email sent successfully")
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {e}")
            state["errors"].append(f"Email sending error: {str(e)}")
            
        return state
    
    def logger_task_node(self, state: WorkflowState) -> WorkflowState:
        """Log execution results"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "prompt": state["original_prompt"],
                "task_plan": state["task_plan"],
                "execution_results": state["execution_results"],
                "errors": state["errors"],
                "retry_count": state.get("retry_count", 0)
            }
            
            self.logger_agent.log_execution(log_entry)
            state["logs"].append(log_entry)
            
            self.logger.info(f"Execution logged successfully")
            
        except Exception as e:
            self.logger.error(f"Logging failed: {e}")
            
        return state
    
    def retry_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Handle retries for failed tasks"""
        try:
            retry_result = self.retry_agent.handle_retry(state)
            
            if retry_result.get("should_retry", False):
                # Reset current step to retry the failed task
                state["current_step"] = max(0, state["current_step"] - 1)
                state["retry_count"] = state.get("retry_count", 0)
            else:
                self.logger.warning(f"Max retries exceeded or retry not recommended")
                
        except Exception as e:
            self.logger.error(f"Retry handling failed: {e}")
            
        return state
    
    def check_for_retry(self, state: WorkflowState) -> str:
        """Check if task needs retry or can continue"""
        max_retries = self.config.get("app", {}).get("max_retries", 3)
        
        if state["errors"] and state.get("retry_count", 0) < max_retries:
            return "retry"
        elif any("gmail" in key for key in state["execution_results"].keys()):
            return "summarize"
        else:
            return "continue"
    
    def _compile_email_content(self, state: WorkflowState) -> Dict[str, str]:
        """Compile email content from execution results"""
        subject = f"AutoTasker AI Results - {datetime.now().strftime('%Y-%m-%d')}"
        
        body_parts = [
            f"Task executed: {state['original_prompt']}\n",
            f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        ]
        
        # Add results from each task
        for key, result in state["execution_results"].items():
            if isinstance(result, dict):
                body_parts.append(f"=== {key.upper()} ===\n")
                if "content" in result:
                    body_parts.append(f"{result['content']}\n\n")
                elif "data" in result:
                    body_parts.append(f"{json.dumps(result['data'], indent=2)}\n\n")
        
        # Add errors if any
        if state["errors"]:
            body_parts.append("=== ERRORS ===\n")
            for error in state["errors"]:
                body_parts.append(f"- {error}\n")
        
        return {
            "subject": subject,
            "body": "".join(body_parts)
        }
    
    def run_workflow(self, prompt: str) -> Dict[str, Any]:
        """Run the complete workflow for a given prompt"""
        initial_state = WorkflowState(
            original_prompt=prompt,
            task_plan={},
            current_step=0,
            execution_results={},
            errors=[],
            retry_count=0,
            email_content="",
            logs=[],
            memory_check={}
        )
        
        self.logger.info(f"Starting workflow for prompt: {prompt}")
        
        try:
            final_state = self.workflow.invoke(initial_state)
            self.logger.info(f"Workflow completed successfully")
            return final_state
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "error": str(e),
                "state": initial_state
            }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="AutoTasker AI - Natural Language Task Automation")
    parser.add_argument("--prompt", required=True, help="Natural language prompt to execute")
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Initialize and run
    runner = AutoTaskerRunner(args.config)
    result = runner.run_workflow(args.prompt)
    
    print(f"Workflow result: {json.dumps(result, indent=2, default=str)}")


if __name__ == "__main__":
    main()
