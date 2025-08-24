"""
Planner Agent: Converts natural language prompts into structured task plans
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.utils import retry_on_failure
from backend.llm_factory import create_llm_client, get_chat_completion, LLMClientFactory


class PlannerAgent:
    """Converts natural language into structured, executable task plans"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PlannerAgent")
        
        # Initialize LLM client (supports both OpenAI and OpenRouter)
        self.client = create_llm_client(config)
        
        # Get appropriate model for this agent
        self.model = LLMClientFactory.get_model_name(config, "planner")
        self.temperature = config.get("agents", {}).get("planner", {}).get("temperature", 0.3)
        
    @retry_on_failure(max_retries=3)
    def create_task_plan(self, prompt: str) -> Dict[str, Any]:
        """
        Convert natural language prompt into structured task plan
        
        Args:
            prompt: Natural language description of what to do
            
        Returns:
            Structured task plan with steps and metadata
        """
        
        system_prompt = self._get_planning_system_prompt()
        user_prompt = self._format_user_prompt(prompt)
        
        try:
            # Use unified chat completion interface
            plan_text = get_chat_completion(
                client=self.client,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=2000
            )
            task_plan = self._parse_plan_response(plan_text)
            
            self.logger.info(f"Created task plan with {len(task_plan.get('tasks', []))} steps")
            
            return task_plan
            
        except Exception as e:
            self.logger.error(f"Failed to create task plan: {e}")
            return self._create_fallback_plan(prompt)
    
    def _get_planning_system_prompt(self) -> str:
        """Get the system prompt for task planning"""
        return """You are AutoTasker AI's Task Planner. Your job is to convert natural language requests into structured, executable task plans.

Available Task Types:
- gmail: Fetch, filter, or process emails from Gmail
- github: Get repository data, commits, or issues
- dsa: Generate Data Structures & Algorithms coding questions
- leetcode: Get LeetCode problems, study plans, and recommendations
- summarize: Summarize content from other tasks
- email: Send final results via email
- schedule: Set up recurring tasks

Task Type Details:
- leetcode: Use for LeetCode problems, study plans, daily coding challenges, interview prep
- dsa: Use for custom coding questions and algorithm explanations
- gmail: For email fetching and processing
- github: For repository analysis and commit tracking

For each task, specify:
1. type: The task type from above
2. description: What this step does
3. parameters: Specific parameters needed
4. dependencies: Which previous tasks this depends on (if any)
5. priority: 1 (high) to 3 (low)

Always include an email task at the end to send results.

Respond with ONLY a JSON object in this format:
{
  "intent": "Brief description of user's goal",
  "schedule": "daily|weekly|once|custom",
  "time": "HH:MM format if scheduled",
  "tasks": [
    {
      "id": "unique_task_id",
      "type": "task_type",
      "description": "What this task does",
      "parameters": {
        "key": "value"
      },
      "dependencies": ["task_id1"],
      "priority": 1
    }
  ],
  "estimated_duration": "X minutes"
}"""
    
    def _format_user_prompt(self, prompt: str) -> str:
        """Format the user prompt with additional context"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""Current time: {current_time}

User request: "{prompt}"

Please create a structured task plan for this request. Consider:
1. What data needs to be fetched (emails, GitHub data, etc.)
2. What processing is needed (summarization, generation, etc.)
3. How results should be delivered (email)
4. Any scheduling requirements

Create the most efficient plan possible."""
    
    def _parse_plan_response(self, plan_text: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured plan"""
        try:
            # Try to extract JSON from the response
            plan_text = plan_text.strip()
            
            # Find JSON block if wrapped in markdown
            if "```json" in plan_text:
                start = plan_text.find("```json") + 7
                end = plan_text.find("```", start)
                plan_text = plan_text[start:end].strip()
            elif "```" in plan_text:
                start = plan_text.find("```") + 3
                end = plan_text.find("```", start)
                plan_text = plan_text[start:end].strip()
            
            # Parse JSON
            task_plan = json.loads(plan_text)
            
            # Validate and enhance the plan
            task_plan = self._validate_and_enhance_plan(task_plan)
            
            return task_plan
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse plan JSON: {e}")
            self.logger.debug(f"Raw response: {plan_text}")
            return self._create_emergency_plan()
        except Exception as e:
            self.logger.error(f"Error processing plan: {e}")
            return self._create_emergency_plan()
    
    def _validate_and_enhance_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the task plan"""
        
        # Ensure required fields exist
        if "tasks" not in plan:
            plan["tasks"] = []
        
        if "intent" not in plan:
            plan["intent"] = "Execute user request"
        
        if "schedule" not in plan:
            plan["schedule"] = "once"
        
        # Validate and enhance tasks
        enhanced_tasks = []
        for i, task in enumerate(plan["tasks"]):
            enhanced_task = self._enhance_task(task, i)
            enhanced_tasks.append(enhanced_task)
        
        plan["tasks"] = enhanced_tasks
        
        # Add metadata
        plan["created_at"] = datetime.now().isoformat()
        plan["total_tasks"] = len(plan["tasks"])
        
        # Ensure there's an email task at the end
        if not any(task.get("type") == "email" for task in plan["tasks"]):
            plan["tasks"].append({
                "id": f"email_final",
                "type": "email",
                "description": "Send results via email",
                "parameters": {},
                "dependencies": [task["id"] for task in plan["tasks"][-2:]] if plan["tasks"] else [],
                "priority": 1
            })
            plan["total_tasks"] += 1
        
        return plan
    
    def _enhance_task(self, task: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Enhance individual task with defaults and validation"""
        
        # Ensure required fields
        if "id" not in task:
            task["id"] = f"task_{index}"
        
        if "type" not in task:
            task["type"] = "email"
        
        if "description" not in task:
            task["description"] = f"Execute {task['type']} task"
        
        if "parameters" not in task:
            task["parameters"] = {}
        
        if "dependencies" not in task:
            task["dependencies"] = []
        
        if "priority" not in task:
            task["priority"] = 2
        
        # Add type-specific enhancements
        if task["type"] == "gmail":
            self._enhance_gmail_task(task)
        elif task["type"] == "github":
            self._enhance_github_task(task)
        elif task["type"] == "dsa":
            self._enhance_dsa_task(task)
        elif task["type"] == "leetcode":
            self._enhance_leetcode_task(task)
        elif task["type"] == "email":
            self._enhance_email_task(task)
        
        return task
    
    def _enhance_gmail_task(self, task: Dict[str, Any]) -> None:
        """Add Gmail-specific parameters"""
        params = task["parameters"]
        
        if "max_results" not in params:
            params["max_results"] = 10
        
        if "time_range" not in params:
            params["time_range"] = "1d"  # Last 1 day
        
        if "query" not in params:
            params["query"] = "is:unread"
    
    def _enhance_github_task(self, task: Dict[str, Any]) -> None:
        """Add GitHub-specific parameters"""
        params = task["parameters"]
        
        if "time_range" not in params:
            params["time_range"] = "1d"
        
        if "max_results" not in params:
            params["max_results"] = 5
    
    def _enhance_dsa_task(self, task: Dict[str, Any]) -> None:
        """Add DSA generation parameters"""
        params = task["parameters"]
        
        if "count" not in params:
            params["count"] = 2
        
        if "difficulty" not in params:
            params["difficulty"] = "medium"
        
        if "topics" not in params:
            params["topics"] = ["arrays", "strings", "algorithms"]
    
    def _enhance_email_task(self, task: Dict[str, Any]) -> None:
        """Add email-specific parameters"""
        params = task["parameters"]
        
        if "to" not in params:
            params["to"] = "user"  # Will be resolved by email agent
        
        if "format" not in params:
            params["format"] = "html"
    
    def _enhance_leetcode_task(self, task: Dict[str, Any]) -> None:
        """Add LeetCode-specific parameters"""
        params = task["parameters"]
        
        if "count" not in params:
            params["count"] = 3
        
        if "difficulty_level" not in params:
            params["difficulty_level"] = "intermediate"
        
        if "topics" not in params:
            params["topics"] = []
        
        if "schedule_time" not in params:
            params["schedule_time"] = "09:00"
        
        if "email_delivery" not in params:
            params["email_delivery"] = True

    def _create_fallback_plan(self, prompt: str) -> Dict[str, Any]:
        """Create a simple fallback plan when planning fails"""
        
        self.logger.warning("Creating fallback plan due to planning failure")
        
        # Determine likely task type from prompt keywords
        prompt_lower = prompt.lower()
        
        tasks = []
        
        # Check for send email requests
        if any(word in prompt_lower for word in ["send", "email to", "compose", "write email"]):
            tasks.append({
                "id": "gmail_send",
                "type": "gmail",
                "description": "Send email",
                "parameters": {
                    "operation": "send_email",
                    "subject": "AutoTasker AI - Fallback Email",
                    "body": f"This email was generated from your request: '{prompt}'\n\nAutoTasker AI is working with a fallback plan due to API limitations."
                },
                "dependencies": [],
                "priority": 1
            })
        elif any(word in prompt_lower for word in ["email", "gmail", "inbox"]):
            tasks.append({
                "id": "gmail_fetch",
                "type": "gmail",
                "description": "Fetch recent emails",
                "parameters": {"operation": "get_emails", "max_results": 10, "time_range": "1d"},
                "dependencies": [],
                "priority": 1
            })
        
        if any(word in prompt_lower for word in ["github", "commit", "repository"]):
            tasks.append({
                "id": "github_fetch",
                "type": "github", 
                "description": "Fetch GitHub data",
                "parameters": {"time_range": "1d"},
                "dependencies": [],
                "priority": 1
            })
        
        if any(word in prompt_lower for word in ["leetcode", "leetcode questions", "study plan", "coding problems"]):
            tasks.append({
                "id": "leetcode_generate",
                "type": "leetcode",
                "description": "Generate LeetCode recommendations",
                "parameters": {"count": 3, "difficulty_level": "intermediate"},
                "dependencies": [],
                "priority": 1
            })
        elif any(word in prompt_lower for word in ["dsa", "coding", "algorithm", "question"]):
            tasks.append({
                "id": "dsa_generate",
                "type": "dsa",
                "description": "Generate coding questions",
                "parameters": {"count": 2, "difficulty": "medium"},
                "dependencies": [],
                "priority": 1
            })
        
        # Add email task
        tasks.append({
            "id": "email_send",
            "type": "email",
            "description": "Send results via email",
            "parameters": {},
            "dependencies": [task["id"] for task in tasks],
            "priority": 1
        })
        
        return {
            "intent": "Execute user request (fallback plan)",
            "schedule": "once",
            "tasks": tasks,
            "created_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "fallback": True
        }
    
    def _create_emergency_plan(self) -> Dict[str, Any]:
        """Create minimal emergency plan when all else fails"""
        return {
            "intent": "Emergency plan - send notification",
            "schedule": "once",
            "tasks": [{
                "id": "emergency_email",
                "type": "email",
                "description": "Send error notification",
                "parameters": {"subject": "AutoTasker AI - Planning Error"},
                "dependencies": [],
                "priority": 1
            }],
            "created_at": datetime.now().isoformat(),
            "total_tasks": 1,
            "emergency": True
        }
