"""
Planner Agent: Converts natural language prompts into structured task plans
"""

import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except ImportError:
    # Try loading without dotenv
    env_path = "config/.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"')

# Add project root to Python path for direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

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
        
        # CRITICAL: Pre-process common patterns that LLM often gets wrong
        prompt_lower = prompt.lower()
        
        # Pattern 1: List/Show repositories
        if any(word in prompt_lower for word in ['list', 'show', 'get', 'fetch']) and \
           any(word in prompt_lower for word in ['repositories', 'repos', 'repository']):
            # Check if it's asking for ALL repos (not a specific one)
            if not any(word in prompt_lower for word in ['commits', 'issues', 'info about', 'details', 'status']):
                self.logger.info("🎯 Detected 'list repositories' pattern - creating direct plan")
                return self._create_list_repos_plan(prompt)
        
        # Otherwise, use LLM to plan
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
- github: Get repository data, commits, or issues (requires 'repository' parameter in 'owner/repo' format)
- dsa: Generate Data Structures & Algorithms coding questions
- leetcode: Get LeetCode problems, study plans, and recommendations
- summarize: Summarize content from other tasks
- email: Send final results via email
- schedule: Set up recurring tasks
- calendar: Create, update, or fetch Google Calendar events (use for scheduling meetings and viewing existing events)

Task Type Details:
- leetcode: Use for LeetCode problems, study plans, daily coding challenges, interview prep (use "count" parameter for number of questions)
- dsa: Use for custom coding questions and algorithm explanations (use "count" parameter for number of questions)
- gmail: For email fetching and processing (use 'query', 'max_results', 'time_range' parameters)
- github: For repository analysis and commit tracking
- calendar: For CREATING new events (with start_time/end_time) OR LISTING/FETCHING existing events (with operation parameter)

CRITICAL LeetCode Parameters:
When creating a leetcode task, use:
- "count": Number of problems to get (e.g., 3 for three problems)
- "difficulty_level": "easy", "medium", "hard", or "intermediate"
- "topics": Array of topics (optional)

Example LeetCode Task:
{
  "type": "leetcode",
  "parameters": {
    "count": 3,
    "difficulty_level": "medium"
  }
}

CRITICAL DSA Parameters:
When creating a dsa task, use:
- "count": Number of questions to generate (e.g., 3 for three questions)
- "difficulty": "easy", "medium", or "hard"
- "topics": Array of topics like ["arrays", "strings", "algorithms"]

Example DSA Task:
{
  "type": "dsa",
  "parameters": {
    "count": 3,
    "difficulty": "medium",
    "topics": ["arrays", "strings"]
  }
}

CRITICAL Calendar Parameters:
When creating a calendar task, you MUST extract and include these parameters:
- "summary": Event title/name (e.g., "Meeting", "hemesh DA")
- "start_time": ISO datetime string "YYYY-MM-DDTHH:MM:SS" (e.g., "2025-11-07T17:30:00")
- "end_time": ISO datetime string "YYYY-MM-DDTHH:MM:SS" (calculate from start_time + duration)
- "description": Additional event details (optional)
- "duration_minutes": Duration in minutes if specified (e.g., 40 for "40 minutes")

CRITICAL DATE/TIME PARSING FOR CALENDAR:
- Extract the EXACT date from user's request (e.g., "November 7th" = "2025-11-07")
- Extract the EXACT time from user's request (e.g., "5:30 pm" = "17:30:00", "5:30 am" = "05:30:00")
- Calculate end_time by adding duration to start_time
- Use 24-hour format: 1am=01:00, 2pm=14:00, 5:30pm=17:30, 11:59pm=23:59
- Month mapping: Jan=01, Feb=02, Mar=03, Apr=04, May=05, Jun=06, Jul=07, Aug=08, Sep=09, Oct=10, Nov=11, Dec=12

Example Calendar Task:
User says: "Schedule meeting on November 7th at 5:30 pm for 20 minutes"
{
  "type": "calendar",
  "parameters": {
    "summary": "Meeting",
    "start_time": "2025-11-07T17:30:00",
    "end_time": "2025-11-07T17:50:00",
    "duration_minutes": 20
  }
}

Example Calendar Task with Name:
User says: "Schedule meeting with name hemesh DA on November 8th at 5:30 pm for 40 minutes"
{
  "type": "calendar",
  "parameters": {
    "summary": "hemesh DA",
    "start_time": "2025-11-08T17:30:00",
    "end_time": "2025-11-08T18:10:00",
    "duration_minutes": 40
  }
}

CRITICAL: Calendar LIST/FETCH Operations:
When user asks to VIEW/LIST/FETCH existing calendar events (NOT create new ones):
- Use "operation": "list" or "fetch" or "get"
- DO NOT include start_time/end_time (those are for creating events)
- Include time_range if specified (e.g., "today", "tomorrow", "this week")

Example Calendar LIST Task:
User says: "What's on my calendar today?"
{
  "type": "calendar",
  "description": "Fetch today's calendar events",
  "parameters": {
    "operation": "list",
    "time_range": "today"
  }
}

Example Calendar LIST Task:
User says: "Show my calendar for tomorrow"
{
  "type": "calendar",
  "description": "Show tomorrow's calendar events",
  "parameters": {
    "operation": "list",
    "time_range": "tomorrow"
  }
}

CRITICAL GitHub Parameters:
When creating a github task, you MUST include:
- "repository": "owner/repo" format (e.g., "Hemesh11/Autotasker-AI")
- If user mentions a username (e.g., "Hemesh11"), use it as the owner
- If no repository is specified, the system will auto-detect from the authenticated user's recent repositories
- DO NOT use "username" parameter - always use "repository" parameter

GitHub Operations (MUST specify correct operation):
- get_commits: Get commits from a specific repository (default if no operation specified)
- get_issues: Get issues from a repository
- get_repo_info: Get detailed info about a specific repository
- get_user_repos: **LIST ALL REPOSITORIES** for a user (DO NOT use "repository" parameter, use "username" only)
- search_repositories: Search for repositories by query

CRITICAL: When user says "list", "show", "get" with "repositories" or "repos":
→ Use operation: "get_user_repos" with "username" parameter (NOT "repository")
→ DO NOT use "get_repo_info" - that's only for ONE specific repository

GitHub Parameters:
- repository: (for commits/issues/repo_info) "owner/repo" format
- username: (REQUIRED for get_user_repos) the GitHub username (e.g., "Hemesh11")
- time_range: (optional) "1d", "7d", "30d" for date range
- max_results: (optional) number of results to fetch (default 10, max 100)
- operation: (required) one of the operations above
- query: (for search_repositories) search query string

Example: List Repositories
{
  "type": "github",
  "parameters": {
    "operation": "get_user_repos",
    "username": "Hemesh11",
    "max_results": 20
  }
}

Example: Get Commits
{
  "type": "github",
  "parameters": {
    "repository": "Hemesh11/Autotasker-AI",
    "operation": "get_commits",
    "time_range": "7d",
    "max_results": 10
  }
}

Example: Get Single Repo Info
{
  "type": "github",
  "parameters": {
    "repository": "Hemesh11/Autotasker-AI",
    "operation": "get_repo_info"
  }
}

For each task, specify:
1. type: The task type from above
2. description: What this step does
3. parameters: Specific parameters needed (follow the format above!)
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
        
        # Extract and normalize time from prompt for better planning
        extracted_time = self._extract_time_from_prompt(prompt)
        time_context = f"\nExtracted time: {extracted_time}" if extracted_time else ""
        
        return f"""Current time: {current_time}{time_context}

User request: "{prompt}"

Please create a structured task plan for this request. Consider:
1. What data needs to be fetched (emails, GitHub data, etc.)
2. What processing is needed (summarization, generation, etc.)
3. How results should be delivered (email)
4. Any scheduling requirements (IMPORTANT: If user specifies a time, use that EXACT time)
5. Immediate execution patterns (e.g., "send now 3 times with 5 min gap")

CRITICAL: If the user specifies an exact time (like "11:47pm"), use that time in schedule_time parameter.
If user says "now" with repetitions, use immediate execution with intervals.

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
        elif task["type"] == "calendar":
            self._enhance_calendar_task(task)
        
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
        
        # Get operation first to determine how to handle parameters
        operation = params.get("operation", "get_commits")
        
        # Special handling for get_user_repos - requires "username", NOT "repository"
        if operation == "get_user_repos":
            # Make sure username is present
            if "username" not in params:
                # Try to get from environment or config
                env_owner = os.getenv("GITHUB_DEFAULT_OWNER")
                if env_owner and env_owner != "your-username":
                    params["username"] = env_owner
                    self.logger.info(f"Added username '{env_owner}' for get_user_repos operation")
                else:
                    # Try config
                    github_config = self.config.get("github", {})
                    default_owner = github_config.get("default_owner", "")
                    if default_owner and default_owner != "your-username":
                        params["username"] = default_owner
            
            # CRITICAL: Remove "repository" if it exists - get_user_repos ONLY needs username
            if "repository" in params:
                params.pop("repository")
                self.logger.info("✓ Removed 'repository' parameter for get_user_repos operation")
            
            # Set default max_results for listing
            if "max_results" not in params:
                params["max_results"] = 20
            
            # DO NOT add any repository parameter - username is all we need!
            return
        
        # For other operations (get_commits, get_issues, get_repo_info), need "repository"
        
        # Fix: If LLM provided "username" instead of "repository", convert it
        if "username" in params and "repository" not in params:
            username = params.pop("username")  # Remove username
            params["repository"] = f"{username}/*"  # Will trigger auto-detect for this user
            self.logger.info(f"Converted username '{username}' to repository pattern for auto-detection")
        
        # Add default repository if not specified
        if "repository" not in params:
                # Try environment variables first
                env_owner = os.getenv("GITHUB_DEFAULT_OWNER")
                env_repo = os.getenv("GITHUB_DEFAULT_REPO")
                
                if env_owner and env_repo and env_owner != "your-username":
                    params["repository"] = f"{env_owner}/{env_repo}"
                else:
                    # Try config as fallback
                    github_config = self.config.get("github", {})
                    default_owner = github_config.get("default_owner", "")
                    default_repo = github_config.get("default_repo", "")
                    
                    if default_owner and default_repo and default_owner != "your-username":
                        params["repository"] = f"{default_owner}/{default_repo}"
                    else:
                        # Use empty string to trigger auto-detection in GitHub agent
                        params["repository"] = ""
                        self.logger.info("No repository specified - will auto-detect from authenticated user")
        
        # Set default operation if not specified
        if "operation" not in params:
            # Infer from description
            desc_lower = task.get("description", "").lower()
            if "issue" in desc_lower:
                params["operation"] = "get_issues"
            elif "repo" in desc_lower and "info" in desc_lower:
                params["operation"] = "get_repo_info"
            else:
                params["operation"] = "get_commits"  # Default
        
        if "time_range" not in params:
            params["time_range"] = "1d"
        
        if "max_results" not in params:
            params["max_results"] = 5
    
    def _enhance_dsa_task(self, task: Dict[str, Any]) -> None:
        """Add DSA generation parameters"""
        params = task["parameters"]
        
        # Handle both "count" and "num_questions" (LLM might use either)
        if "num_questions" in params and "count" not in params:
            params["count"] = params["num_questions"]
            del params["num_questions"]  # Remove duplicate
        
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
        
        # Handle both "count" and "num_questions" (LLM might use either)
        if "num_questions" in params and "count" not in params:
            params["count"] = params["num_questions"]
            del params["num_questions"]  # Remove duplicate
        
        if "count" not in params:
            params["count"] = 3
        
        if "difficulty_level" not in params:
            params["difficulty_level"] = "intermediate"
        
        if "topics" not in params:
            params["topics"] = []
        
        # Extract time from task description or use default
        if "schedule_time" not in params:
            extracted_time = self._extract_time_from_prompt(task.get("description", ""))
            params["schedule_time"] = extracted_time if extracted_time else "09:00"
        
        if "email_delivery" not in params:
            params["email_delivery"] = True

    def _enhance_calendar_task(self, task: Dict[str, Any]) -> None:
        """Add Calendar-specific parameters and defaults"""
        params = task["parameters"]

        # Default timezone from config or environment
        tz = os.getenv("TIMEZONE") or self.config.get("timezone") or "Asia/Kolkata"
        params.setdefault("timeZone", tz)

        # Check if this is a LIST operation (not CREATE)
        operation = params.get("operation", "").lower()
        is_list_operation = operation in ["list", "fetch", "get", "show", "view"]
        
        # For LIST operations, only keep operation and time_range parameters
        if is_list_operation:
            # Remove CREATE-specific parameters that shouldn't be in LIST operations
            params.pop("summary", None)
            params.pop("start_time", None)
            params.pop("end_time", None)
            params.pop("duration_minutes", None)
            params.pop("reminders", None)
            params.pop("attendees", None)
            params.pop("description", None)
            # Keep only: operation, time_range, timeZone
            return
        
        # For CREATE operations, add defaults
        # Ensure summary exists
        if "summary" not in params or not params.get("summary"):
            params["summary"] = task.get("description", "Meeting") or "Meeting"

        # Normalize start_time/end_time
        start = params.get("start_time")
        end = params.get("end_time")

        # If only duration provided, compute end_time accordingly
        if start and not end:
            # If duration_minutes provided, use it; else default 60 minutes
            try:
                duration = int(params.get("duration_minutes", 60))
            except Exception:
                duration = 60
            try:
                # Try parsing naive ISO-like strings
                from datetime import datetime, timedelta
                if isinstance(start, str) and len(start) >= 10:
                    # If date-only or date+time
                    fmt = "%Y-%m-%dT%H:%M:%S" if "T" in start else "%Y-%m-%d %H:%M:%S"
                    dt = datetime.strptime(start, fmt)
                    dt_end = dt + timedelta(minutes=duration)
                    params["end_time"] = dt_end.strftime(fmt)
                else:
                    # Leave as-is; calendar agent will infer end time
                    params["end_time"] = params.get("end_time")
            except Exception:
                # Best-effort: leave end_time empty; calendar agent will fallback
                params["end_time"] = params.get("end_time")

        # Default reminders (only for CREATE operations)
        if "reminders" not in params:
            params["reminders"] = [{"method": "popup", "minutes": 15}]

        # Ensure attendees list exists (only for CREATE operations)
        if "attendees" not in params:
            params["attendees"] = []
    
    def _extract_time_from_prompt(self, text: str) -> Optional[str]:
        """
        Extract time from text in various formats
        Supports: 11:47pm, 11:47 PM, 23:47, 9AM, 2:30pm, etc.
        """
        import re
        
        text_lower = text.lower()
        
        # Pattern 1: HH:MM am/pm or HH:MMam/pm
        pattern1 = r'(\d{1,2}):(\d{2})\s*(am|pm)'
        match = re.search(pattern1, text_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(3)
            
            # Convert to 24-hour format
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        # Pattern 2: H am/pm or Ham/pm (e.g., "9am", "2PM")
        pattern2 = r'(\d{1,2})\s*(am|pm)'
        match = re.search(pattern2, text_lower)
        if match:
            hour = int(match.group(1))
            ampm = match.group(2)
            
            # Convert to 24-hour format
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return f"{hour:02d}:00"
        
        # Pattern 3: 24-hour format HH:MM
        pattern3 = r'(\d{1,2}):(\d{2})(?!\s*(am|pm))'
        match = re.search(pattern3, text_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        
        return None

    def _create_fallback_plan(self, prompt: str) -> Dict[str, Any]:
        """Create a simple fallback plan when planning fails"""
        
        self.logger.warning("Creating fallback plan due to planning failure")
        
        # Determine likely task type from prompt keywords
        prompt_lower = prompt.lower()
        
        tasks = []
        
        if any(word in prompt_lower for word in ["email", "gmail", "inbox"]):
            tasks.append({
                "id": "gmail_fetch",
                "type": "gmail",
                "description": "Fetch recent emails",
                "parameters": {"max_results": 10, "time_range": "1d"},
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
    
    def _create_list_repos_plan(self, prompt: str) -> Dict[str, Any]:
        """
        Create a specialized plan for listing GitHub repositories
        This bypasses the LLM to ensure correct operation is used
        """
        # Extract username if mentioned, otherwise use default
        username = None
        
        # Try to extract username from prompt
        import re
        
        # Try multiple patterns to extract username
        patterns = [
            r'(?:with\s+)?username\s+(\S+)',  # "with username sam-ry" or "username sam-ry"
            r'for\s+(?:user\s+)?(\S+)',       # "for sam-ry" or "for user sam-ry"
            r'of\s+(?:user\s+)?(\S+)',        # "of sam-ry" or "of user sam-ry"
            r'user\s+(\S+)',                   # "user sam-ry"
        ]
        
        for pattern in patterns:
            username_match = re.search(pattern, prompt.lower())
            if username_match:
                username = username_match.group(1)
                self.logger.info(f"✓ Extracted username from prompt: '{username}'")
                break
        
        # If not found, try environment or config
        if not username:
            username = os.getenv("GITHUB_DEFAULT_OWNER")
            if not username or username == "your-username":
                github_config = self.config.get("github", {})
                username = github_config.get("default_owner", "")
        
        # Fallback to generic if still not found
        if not username or username == "your-username":
            username = "user"  # GitHub agent will use authenticated user
        
        self.logger.info(f"📋 Creating list repos plan for username: {username}")
        
        return {
            "intent": "List all GitHub repositories",
            "schedule": "once",
            "time": None,
            "tasks": [
                {
                    "id": "github_list",
                    "type": "github",
                    "description": f"List all repositories for {username}",
                    "parameters": {
                        "operation": "get_user_repos",
                        "username": username,
                        "max_results": 30
                    },
                    "dependencies": [],
                    "priority": 1
                },
                {
                    "id": "email_send",
                    "type": "email",
                    "description": "Send repository list via email",
                    "parameters": {
                        "to": "user",
                        "format": "html"
                    },
                    "dependencies": ["github_list"],
                    "priority": 2
                }
            ],
            "estimated_duration": "1 minute",
            "created_at": datetime.now().isoformat(),
            "total_tasks": 2,
            "direct_plan": True
        }
