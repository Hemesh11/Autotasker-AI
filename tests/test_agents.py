"""
Test suite for AutoTasker AI agents
"""

import pytest
import sys
import os

# Add backend to path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from agents.planner_agent import PlannerAgent
from agents.dsa_agent import DSAAgent
from agents.summarizer_agent import SummarizerAgent
from agents.tool_selector import ToolSelector
from agents.memory_agent import MemoryAgent
from agents.retry_agent import RetryAgent


class TestPlannerAgent:
    """Test cases for PlannerAgent"""
    
    @pytest.fixture
    def config(self):
        return {
            "llm": {"api_key": "test_key"},
            "agents": {"planner": {"model": "gpt-4", "temperature": 0.3}}
        }
    
    @pytest.fixture
    def planner_agent(self, config):
        return PlannerAgent(config)
    
    def test_planner_initialization(self, planner_agent):
        assert planner_agent is not None
        assert planner_agent.model == "gpt-4"
        assert planner_agent.temperature == 0.3
    
    def test_create_fallback_plan(self, planner_agent):
        prompt = "Generate 2 coding questions"
        plan = planner_agent._create_fallback_plan(prompt)
        
        assert "tasks" in plan
        assert len(plan["tasks"]) > 0
        assert plan["fallback"] is True
    
    def test_enhance_dsa_task(self, planner_agent):
        task = {"type": "dsa", "description": "Generate questions"}
        enhanced = planner_agent._enhance_task(task, 0)
        
        assert "parameters" in enhanced
        assert "count" in enhanced["parameters"]
        assert enhanced["parameters"]["count"] == 2


class TestDSAAgent:
    """Test cases for DSAAgent"""
    
    @pytest.fixture
    def config(self):
        return {
            "llm": {"api_key": "test_key"},
            "agents": {"dsa_generator": {"model": "gpt-4", "temperature": 0.8}}
        }
    
    @pytest.fixture
    def dsa_agent(self, config):
        return DSAAgent(config)
    
    def test_dsa_initialization(self, dsa_agent):
        assert dsa_agent is not None
        assert len(dsa_agent.topics) > 0
        assert "Arrays" in dsa_agent.topics
    
    def test_create_fallback_question(self, dsa_agent):
        question = dsa_agent._create_fallback_question("arrays", "medium", 1)
        
        assert "title" in question
        assert "problem_statement" in question
        assert "solution" in question
        assert question["fallback"] is True
    
    def test_format_questions_content(self, dsa_agent):
        questions = [
            {"title": "Test Problem", "topic": "arrays", "difficulty": "medium"}
        ]
        content = dsa_agent._format_questions_content(questions)
        
        assert "DAILY CODING QUESTIONS" in content
        assert "Test Problem" in content


class TestSummarizerAgent:
    """Test cases for SummarizerAgent"""
    
    @pytest.fixture
    def config(self):
        return {
            "llm": {"api_key": "test_key"},
            "agents": {"summarizer": {"model": "gpt-3.5-turbo", "temperature": 0.5}}
        }
    
    @pytest.fixture
    def summarizer_agent(self, config):
        return SummarizerAgent(config)
    
    def test_summarizer_initialization(self, summarizer_agent):
        assert summarizer_agent is not None
        assert "email" in summarizer_agent.content_handlers
        assert "github" in summarizer_agent.content_handlers
    
    def test_detect_content_type(self, summarizer_agent):
        email_content = [{"subject": "Test", "from": "test@example.com"}]
        content_type = summarizer_agent._detect_content_type(email_content, {})
        assert content_type == "email"
        
        github_content = [{"commit": {"message": "Fix bug"}}]
        content_type = summarizer_agent._detect_content_type(github_content, {})
        assert content_type == "github"
    
    def test_text_similarity(self, summarizer_agent):
        text1 = "send me coding questions"
        text2 = "send me programming questions"
        similarity = summarizer_agent._calculate_text_similarity(text1, text2)
        assert 0 < similarity < 1


class TestToolSelector:
    """Test cases for ToolSelector"""
    
    @pytest.fixture
    def config(self):
        return {}
    
    @pytest.fixture
    def tool_selector(self, config):
        return ToolSelector(config)
    
    def test_tool_selector_initialization(self, tool_selector):
        assert tool_selector is not None
        assert "gmail" in tool_selector.task_mappings
        assert "dsa" in tool_selector.task_mappings
    
    def test_select_agents_for_task(self, tool_selector):
        task = {"type": "gmail", "description": "fetch emails"}
        agents = tool_selector.select_agents_for_task(task)
        assert "gmail_agent" in agents
        assert "logger_agent" in agents
    
    def test_get_execution_order(self, tool_selector):
        tasks = [
            {"id": "task1", "dependencies": [], "priority": 1},
            {"id": "task2", "dependencies": ["task1"], "priority": 2}
        ]
        order = tool_selector.get_execution_order(tasks)
        assert order == ["task1", "task2"]


class TestMemoryAgent:
    """Test cases for MemoryAgent"""
    
    @pytest.fixture
    def config(self):
        return {
            "memory": {
                "retention_days": 30,
                "similarity_threshold": 0.8
            }
        }
    
    @pytest.fixture
    def memory_agent(self, config):
        return MemoryAgent(config)
    
    def test_memory_initialization(self, memory_agent):
        assert memory_agent is not None
        assert memory_agent.retention_days == 30
        assert memory_agent.similarity_threshold == 0.8
    
    def test_generate_prompt_signature(self, memory_agent):
        prompt1 = "Send me coding questions every day at 9AM"
        prompt2 = "Send me coding questions daily at 9:00 am"
        
        sig1 = memory_agent._generate_prompt_signature(prompt1)
        sig2 = memory_agent._generate_prompt_signature(prompt2)
        
        # Should generate same signature for similar prompts
        assert sig1 == sig2
    
    def test_check_recent_execution_no_match(self, memory_agent):
        result = memory_agent.check_recent_execution("unique new prompt")
        assert result["should_skip"] is False
        assert result["match_type"] == "none"


class TestRetryAgent:
    """Test cases for RetryAgent"""
    
    @pytest.fixture
    def config(self):
        return {
            "app": {"max_retries": 3},
            "retry": {"base_delay": 1.0, "backoff_multiplier": 2.0}
        }
    
    @pytest.fixture
    def retry_agent(self, config):
        return RetryAgent(config)
    
    def test_retry_initialization(self, retry_agent):
        assert retry_agent is not None
        assert retry_agent.max_retries == 3
        assert retry_agent.base_delay == 1.0
    
    def test_analyze_retryable_errors(self, retry_agent):
        errors = ["Connection timeout", "Network error"]
        analysis = retry_agent._analyze_errors_for_retry(errors)
        assert analysis["retryable"] is True
        assert "timeout" in analysis["patterns_matched"]
    
    def test_analyze_non_retryable_errors(self, retry_agent):
        errors = ["Authentication failed", "Invalid credentials"]
        analysis = retry_agent._analyze_errors_for_retry(errors)
        assert analysis["retryable"] is False
        assert analysis["error_type"] == "permanent"
    
    def test_exponential_backoff(self, retry_agent):
        delay1 = retry_agent._exponential_backoff_delay(0)
        delay2 = retry_agent._exponential_backoff_delay(1)
        delay3 = retry_agent._exponential_backoff_delay(2)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0


# Integration tests
class TestIntegration:
    """Integration test cases"""
    
    @pytest.fixture
    def config(self):
        return {
            "llm": {"api_key": "test_key"},
            "app": {"max_retries": 3},
            "agents": {
                "planner": {"model": "gpt-4", "temperature": 0.3}
            }
        }
    
    def test_agent_interaction(self, config):
        """Test basic agent interaction"""
        planner = PlannerAgent(config)
        tool_selector = ToolSelector(config)
        
        # Create a plan
        plan = planner._create_fallback_plan("Generate coding questions")
        
        # Select tools for tasks
        task_agents = tool_selector.select_agents_for_tasks(plan["tasks"])
        
        assert len(task_agents) == len(plan["tasks"])
        for task_id, agents in task_agents.items():
            assert len(agents) > 0
            assert "logger_agent" in agents


if __name__ == "__main__":
    pytest.main([__file__])
