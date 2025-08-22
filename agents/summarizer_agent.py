"""
Summarizer Agent: Summarizes content using LLM
"""

import logging
from typing import Dict, List, Any, Optional, Union

from backend.utils import retry_on_failure, truncate_text
from backend.llm_factory import create_llm_client, get_chat_completion, LLMClientFactory


class SummarizerAgent:
    """Agent for summarizing various types of content"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SummarizerAgent")
        
        # Initialize LLM client (supports both OpenAI and OpenRouter)
        self.client = create_llm_client(config)
        
        # Get appropriate model for this agent
        self.model = LLMClientFactory.get_model_name(config, "summarizer")
        self.temperature = config.get("agents", {}).get("summarizer", {}).get("temperature", 0.5)
        
        # Content type handlers
        self.content_handlers = {
            "email": self._summarize_emails,
            "github": self._summarize_github_data,
            "general": self._summarize_general_content
        }
    
    @retry_on_failure(max_retries=3)
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute summarization task
        
        Args:
            task: Task configuration with content to summarize
            
        Returns:
            Summarization results
        """
        
        try:
            # Get content from task parameters or previous results
            content = self._extract_content_from_task(task)
            
            if not content:
                return {
                    "success": False,
                    "error": "No content provided for summarization",
                    "content": "No content available to summarize"
                }
            
            # Determine content type
            content_type = self._detect_content_type(content, task)
            
            # Summarize content
            summary = self.summarize_content(content, content_type)
            
            self.logger.info(f"Summarized {len(content)} items of type {content_type}")
            
            return {
                "success": True,
                "content_type": content_type,
                "original_count": len(content) if isinstance(content, list) else 1,
                "content": summary,
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"Summarization task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to summarize content: {e}"
            }
    
    def summarize_content(self, content: Union[List[Any], str, Dict[str, Any]], 
                         content_type: str = "general") -> str:
        """
        Summarize content based on its type
        
        Args:
            content: Content to summarize
            content_type: Type of content (email, github, general)
            
        Returns:
            Generated summary
        """
        
        # Use appropriate handler
        handler = self.content_handlers.get(content_type, self._summarize_general_content)
        
        try:
            return handler(content)
        except Exception as e:
            self.logger.error(f"Content summarization failed: {e}")
            return f"Failed to generate summary: {str(e)}"
    
    def _extract_content_from_task(self, task: Dict[str, Any]) -> Any:
        """Extract content to summarize from task"""
        
        # Check task parameters
        parameters = task.get("parameters", {})
        if "content" in parameters:
            return parameters["content"]
        
        # Check for specific content types in parameters
        for key in ["emails", "github_data", "text", "data"]:
            if key in parameters:
                return parameters[key]
        
        # Check task description for content hints
        description = task.get("description", "").lower()
        if "email" in description:
            return parameters.get("email_content", [])
        elif "github" in description:
            return parameters.get("github_content", [])
        
        return None
    
    def _detect_content_type(self, content: Any, task: Dict[str, Any]) -> str:
        """Detect the type of content to determine summarization approach"""
        
        # Check task description for hints
        description = task.get("description", "").lower()
        
        if "email" in description or "gmail" in description:
            return "email"
        elif "github" in description or "commit" in description:
            return "github"
        
        # Check content structure
        if isinstance(content, list) and content:
            first_item = content[0]
            if isinstance(first_item, dict):
                # Check for email-like structure
                if any(key in first_item for key in ["subject", "from", "to", "body"]):
                    return "email"
                # Check for GitHub-like structure
                elif any(key in first_item for key in ["commit", "message", "author", "sha"]):
                    return "github"
        
        return "general"
    
    def _summarize_emails(self, emails: List[Dict[str, Any]]) -> str:
        """Summarize email content"""
        
        if not emails:
            return "No emails to summarize."
        
        # Prepare email data for summarization
        email_summaries = []
        
        for email in emails[:10]:  # Limit to 10 emails
            email_info = {
                "from": email.get("from", "Unknown"),
                "subject": email.get("subject", "No Subject"),
                "date": email.get("date", "Unknown"),
                "snippet": email.get("snippet", email.get("body", ""))[:200]
            }
            email_summaries.append(email_info)
        
        # Create prompt for email summarization
        system_prompt = self._get_email_summary_prompt()
        user_prompt = self._format_email_content_for_llm(email_summaries)
        
        return self._generate_summary_with_llm(system_prompt, user_prompt)
    
    def _summarize_github_data(self, github_data: List[Dict[str, Any]]) -> str:
        """Summarize GitHub commits/issues data"""
        
        if not github_data:
            return "No GitHub data to summarize."
        
        # Prepare GitHub data for summarization
        github_summaries = []
        
        for item in github_data[:15]:  # Limit to 15 items
            if "commit" in item or "message" in item:
                # Commit data
                github_info = {
                    "type": "commit",
                    "message": item.get("message", item.get("commit", {}).get("message", "")),
                    "author": item.get("author", item.get("commit", {}).get("author", {}).get("name", "Unknown")),
                    "date": item.get("date", item.get("commit", {}).get("author", {}).get("date", "Unknown"))
                }
            else:
                # Issue or other data
                github_info = {
                    "type": "issue",
                    "title": item.get("title", "Unknown"),
                    "state": item.get("state", "Unknown"),
                    "body": item.get("body", "")[:200]
                }
            
            github_summaries.append(github_info)
        
        # Create prompt for GitHub summarization
        system_prompt = self._get_github_summary_prompt()
        user_prompt = self._format_github_content_for_llm(github_summaries)
        
        return self._generate_summary_with_llm(system_prompt, user_prompt)
    
    def _summarize_general_content(self, content: Union[str, List[Any], Dict[str, Any]]) -> str:
        """Summarize general content"""
        
        # Convert content to string if needed
        if isinstance(content, list):
            content_str = "\n".join([str(item) for item in content])
        elif isinstance(content, dict):
            content_str = str(content)
        else:
            content_str = str(content)
        
        # Truncate if too long
        content_str = truncate_text(content_str, 3000)
        
        system_prompt = self._get_general_summary_prompt()
        user_prompt = f"Please summarize the following content:\n\n{content_str}"
        
        return self._generate_summary_with_llm(system_prompt, user_prompt)
    
    def _generate_summary_with_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Generate summary using LLM"""
        
        try:
            # Use unified chat completion interface
            summary = get_chat_completion(
                client=self.client,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=1000
            )
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"LLM summarization failed: {e}")
            return f"Failed to generate summary using LLM: {str(e)}"
    
    def _get_email_summary_prompt(self) -> str:
        """Get system prompt for email summarization"""
        return """You are an email summarization assistant. Your task is to create a concise, informative summary of email content.

For email summaries:
1. Group emails by sender or topic when possible
2. Highlight important or urgent items
3. Include key dates and deadlines
4. Mention action items or requests
5. Keep the summary organized and easy to scan

Format the summary with clear sections and bullet points for readability."""
    
    def _get_github_summary_prompt(self) -> str:
        """Get system prompt for GitHub data summarization"""
        return """You are a development activity summarization assistant. Your task is to create a clear summary of GitHub repository activity.

For GitHub summaries:
1. Categorize commits by feature, bugfix, or maintenance
2. Highlight significant changes or new features
3. Mention active contributors
4. Include important dates and milestones
5. Identify patterns or trends in development activity

Format the summary to help developers understand recent project progress."""
    
    def _get_general_summary_prompt(self) -> str:
        """Get system prompt for general content summarization"""
        return """You are a content summarization assistant. Create clear, concise summaries that capture the key points and essential information.

Guidelines:
1. Identify main topics and themes
2. Preserve important details and context
3. Use clear, professional language
4. Structure the summary logically
5. Maintain accuracy while being concise

Provide a summary that someone could read to quickly understand the original content."""
    
    def _format_email_content_for_llm(self, emails: List[Dict[str, Any]]) -> str:
        """Format email data for LLM processing"""
        
        lines = [f"Please summarize these {len(emails)} emails:\n"]
        
        for i, email in enumerate(emails, 1):
            lines.extend([
                f"Email {i}:",
                f"From: {email['from']}",
                f"Subject: {email['subject']}",
                f"Date: {email['date']}",
                f"Content: {email['snippet']}",
                ""
            ])
        
        return "\n".join(lines)
    
    def _format_github_content_for_llm(self, github_data: List[Dict[str, Any]]) -> str:
        """Format GitHub data for LLM processing"""
        
        lines = [f"Please summarize this GitHub activity ({len(github_data)} items):\n"]
        
        for i, item in enumerate(github_data, 1):
            if item["type"] == "commit":
                lines.extend([
                    f"Commit {i}:",
                    f"Author: {item['author']}",
                    f"Message: {item['message']}",
                    f"Date: {item['date']}",
                    ""
                ])
            else:
                lines.extend([
                    f"Issue {i}:",
                    f"Title: {item['title']}",
                    f"State: {item['state']}",
                    f"Description: {item['body']}",
                    ""
                ])
        
        return "\n".join(lines)
    
    def create_bullet_point_summary(self, content: Union[str, List[Any]]) -> str:
        """Create a bullet-point style summary"""
        
        summary = self.summarize_content(content, "general")
        
        # Add bullet point formatting if not already present
        if "•" not in summary and "-" not in summary:
            # Split into sentences and format as bullets
            sentences = summary.split(". ")
            bullet_points = [f"• {sentence.strip()}." for sentence in sentences if sentence.strip()]
            return "\n".join(bullet_points)
        
        return summary
    
    def create_structured_summary(self, content: Union[str, List[Any]], 
                                sections: List[str] = None) -> Dict[str, str]:
        """Create a structured summary with specific sections"""
        
        if not sections:
            sections = ["Key Points", "Important Details", "Action Items"]
        
        summary = self.summarize_content(content, "general")
        
        # Simple section-based parsing (could be enhanced with more sophisticated NLP)
        structured = {}
        
        for section in sections:
            # This is a simplified approach - in practice, you'd use more sophisticated parsing
            structured[section] = f"Content related to {section.lower()} from the summary"
        
        # For now, put the main summary in the first section
        if sections:
            structured[sections[0]] = summary
        
        return structured
