"""
DSA Agent: Generates Data Structures and Algorithms coding questions
"""

import json
import logging
import random
import os
import sys
from typing import Dict, List, Any, Optional

# Add project root to Python path for direct execution
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

try:
    from backend.utils import retry_on_failure
    from backend.llm_factory import create_llm_client, get_chat_completion, LLMClientFactory
except ImportError:
    # Fallback for direct execution
    def retry_on_failure(max_retries=3):
        def decorator(func):
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        continue
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    # Simple OpenRouter client for standalone testing
    def create_llm_client(config):
        try:
            import openai
            api_key = os.getenv('OPENROUTER_API_KEY') or config.get('llm', {}).get('api_key')
            if not api_key:
                raise ValueError("OpenRouter API key not found")
            return openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        except ImportError:
            return None
    
    def get_chat_completion(client, messages, model, temperature=0.7, max_tokens=1500):
        if not client:
            raise ValueError("No LLM client available")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    class LLMClientFactory:
        @staticmethod
        def get_model_name(config, agent_type):
            return config.get('llm', {}).get('model', 'meta-llama/llama-3.3-70b-instruct')


class DSAAgent:
    """Agent for generating coding questions and problems"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.DSAAgent")
        
        # Initialize LLM client (supports both OpenAI and OpenRouter)
        self.client = create_llm_client(config)
        
        # Get appropriate model for this agent
        self.model = LLMClientFactory.get_model_name(config, "dsa_generator")
        self.temperature = config.get("agents", {}).get("dsa_generator", {}).get("temperature", 0.8)
        
        # Common DSA topics and patterns
        self.topics = [
            "Arrays", "Strings", "Linked Lists", "Stacks", "Queues",
            "Trees", "Graphs", "Dynamic Programming", "Greedy Algorithms",
            "Binary Search", "Two Pointers", "Sliding Window", "Hash Tables",
            "Heap", "Trie", "Backtracking", "Bit Manipulation"
        ]
        
        self.difficulty_levels = {
            "easy": "Beginner-friendly, basic algorithms",
            "medium": "Intermediate level, requires good understanding",
            "hard": "Advanced level, complex problem-solving"
        }
    
    @retry_on_failure(max_retries=3)
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute DSA generation task
        
        Args:
            task: Task configuration with parameters
            
        Returns:
            Generated coding questions
        """
        
        parameters = task.get("parameters", {})
        
        try:
            count = parameters.get("count", 2)
            difficulty = parameters.get("difficulty", "medium")
            topics = parameters.get("topics", ["arrays", "algorithms"])
            
            questions = self.generate_questions(count, difficulty, topics)
            
            if not questions:
                return {
                    "success": False,
                    "error": "Failed to generate questions",
                    "content": "No coding questions were generated"
                }
            
            content = self._format_questions_content(questions)
            
            self.logger.info(f"Generated {len(questions)} DSA questions")
            
            return {
                "success": True,
                "count": len(questions),
                "content": content,
                "questions": questions,
                "difficulty": difficulty,
                "topics": topics
            }
            
        except Exception as e:
            self.logger.error(f"DSA task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to generate coding questions: {e}"
            }
    
    def generate_questions(self, count: int, difficulty: str, topics: List[str]) -> List[Dict[str, Any]]:
        """
        Generate coding questions using LLM
        
        Args:
            count: Number of questions to generate
            difficulty: Difficulty level (easy/medium/hard)
            topics: List of topics to focus on
            
        Returns:
            List of generated questions
        """
        
        questions = []
        
        for i in range(count):
            try:
                # Select a random topic for variety
                selected_topic = random.choice(topics) if topics else random.choice(self.topics)
                
                question = self._generate_single_question(difficulty, selected_topic, i + 1)
                if question:
                    questions.append(question)
                    
            except Exception as e:
                self.logger.error(f"Failed to generate question {i+1}: {e}")
                continue
        
        return questions
    
    def _generate_single_question(self, difficulty: str, topic: str, question_num: int) -> Optional[Dict[str, Any]]:
        """Generate a single coding question"""
        
        system_prompt = self._get_dsa_system_prompt()
        user_prompt = self._format_dsa_user_prompt(difficulty, topic, question_num)
        
        try:
            # Use unified chat completion interface
            question_text = get_chat_completion(
                client=self.client,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=1500
            )
            
            question_data = self._parse_question_response(question_text, topic, difficulty)
            
            return question_data
            
        except Exception as e:
            self.logger.error(f"Failed to generate question via LLM: {e}")
            return self._create_fallback_question(topic, difficulty, question_num)
    
    def _get_dsa_system_prompt(self) -> str:
        """Get system prompt for DSA question generation"""
        return """You are an expert coding interview question generator. Create original, high-quality Data Structures and Algorithms problems.

Use this EXACT format with clear section markers:

TITLE: [Problem title here]

PROBLEM:
[Clear description of the problem]

EXAMPLE 1:
Input: [example input]
Output: [example output]
Explanation: [why this output]

EXAMPLE 2:
Input: [example input]
Output: [example output]
Explanation: [why this output]

CONSTRAINTS:
- [constraint 1]
- [constraint 2]

APPROACH:
[High-level solution approach]

CODE:
```python
def solution(...):
    # Clean, commented code
    pass
```

COMPLEXITY:
Time: O(...)
Space: O(...)

HINTS:
- [hint 1]
- [hint 2]

Make problems practical, interview-relevant, and educational."""
    
    def _format_dsa_user_prompt(self, difficulty: str, topic: str, question_num: int) -> str:
        """Format user prompt for question generation"""
        
        difficulty_desc = self.difficulty_levels.get(difficulty, "medium level")
        
        return f"""Generate an original coding question #{question_num}:

Topic: {topic}
Difficulty: {difficulty} ({difficulty_desc})

Requirements:
- Create a unique problem not commonly found online
- Make it interview-appropriate for {difficulty} level
- Focus on {topic} concepts and techniques
- Include multiple test cases
- Provide clean, efficient solution
- Add educational value with explanations

The problem should test core {topic} understanding while being solvable in a coding interview setting."""
    
    def _parse_question_response(self, response_text: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LLM response into structured question data using text parsing"""
        
        try:
            # Parse structured text response instead of JSON
            question_data = self._parse_structured_text(response_text)
            
            # Add metadata
            question_data["topic"] = topic
            question_data["difficulty"] = difficulty
            question_data["generated_at"] = "auto"
            
            # Validate and ensure required fields
            question_data = self._validate_and_fix_question_data(question_data)
            
            return question_data
            
        except Exception as e:
            self.logger.warning(f"Structured text parsing failed: {e}, using fallback")
            return self._extract_fallback_from_text(response_text, topic, difficulty)
    
    def _parse_structured_text(self, text: str) -> Dict[str, Any]:
        """Parse structured text response with clear section markers"""
        
        lines = text.split('\n')
        result = {}
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if line.startswith('TITLE:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'title'
                current_content = [line[6:].strip()]
                
            elif line.startswith('PROBLEM:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'problem_statement'
                current_content = []
                
            elif line.startswith('EXAMPLE '):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'examples'
                if 'examples' not in result:
                    result['examples'] = []
                current_content = [line]
                
            elif line.startswith('CONSTRAINTS:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'constraints'
                current_content = []
                
            elif line.startswith('APPROACH:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'approach'
                current_content = []
                
            elif line.startswith('CODE:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'code'
                current_content = []
                
            elif line.startswith('COMPLEXITY:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'complexity'
                current_content = []
                
            elif line.startswith('HINTS:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'hints'
                current_content = []
                
            else:
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            result[current_section] = '\n'.join(current_content).strip()
        
        # Process examples into structured format
        if 'examples' in result:
            result['examples'] = self._parse_examples_from_text(result['examples'])
        
        # Process constraints into list
        if 'constraints' in result:
            constraints_text = result['constraints']
            result['constraints'] = [line.strip('- ').strip() for line in constraints_text.split('\n') if line.strip()]
        
        # Process hints into list
        if 'hints' in result:
            hints_text = result['hints']
            result['hints'] = [line.strip('- ').strip() for line in hints_text.split('\n') if line.strip()]
        
        # Structure solution section
        if 'approach' in result and 'code' in result and 'complexity' in result:
            complexity_text = result['complexity']
            time_match = complexity_text.split('Time:')[-1].split('Space:')[0].strip() if 'Time:' in complexity_text else 'O(n)'
            space_match = complexity_text.split('Space:')[-1].strip() if 'Space:' in complexity_text else 'O(1)'
            
            result['solution'] = {
                'approach': result['approach'],
                'code': result['code'].replace('```python', '').replace('```', '').strip(),
                'time_complexity': time_match,
                'space_complexity': space_match
            }
        
        return result
    
    def _parse_examples_from_text(self, examples_text: str) -> List[Dict[str, str]]:
        """Parse examples from text format"""
        
        examples = []
        lines = examples_text.split('\n')
        current_example = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('EXAMPLE '):
                if current_example:
                    examples.append(current_example)
                current_example = {}
            elif line.startswith('Input:'):
                current_example['input'] = line[6:].strip()
            elif line.startswith('Output:'):
                current_example['output'] = line[7:].strip()
            elif line.startswith('Explanation:'):
                current_example['explanation'] = line[12:].strip()
        
        if current_example:
            examples.append(current_example)
        
        return examples if examples else [{"input": "sample input", "output": "sample output", "explanation": "explanation"}]
    
    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """Extract JSON from LLM response using multiple strategies"""
        
        # Strategy 1: Look for ```json code block
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end > start:
                return response_text[start:end].strip()
        
        # Strategy 2: Look for { } block
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            # Find matching closing brace
            brace_count = 0
            end = start
            for i, char in enumerate(response_text[start:], start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if end > start:
                json_candidate = response_text[start:end]
                # Try to fix common JSON issues
                json_candidate = self._fix_common_json_issues(json_candidate)
                return json_candidate
        
        return None
    
    def _fix_common_json_issues(self, json_text: str) -> str:
        """Fix common JSON formatting issues"""
        
        # Remove trailing commas before } or ]
        import re
        json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
        
        # Fix unquoted keys (simple cases)
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)
        
        # Fix already quoted keys that got double-quoted
        json_text = re.sub(r'""(\w+)"":', r'"\1":', json_text)
        
        return json_text
    
    def _validate_and_fix_question_data(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix question data structure"""
        
        # Ensure required fields exist
        if "title" not in question_data:
            question_data["title"] = "Coding Challenge"
        
        if "problem_statement" not in question_data:
            question_data["problem_statement"] = "Solve this coding problem."
        
        if "examples" not in question_data or not question_data["examples"]:
            question_data["examples"] = [
                {
                    "input": "sample input",
                    "output": "expected output",
                    "explanation": "solve step by step"
                }
            ]
        
        if "solution" not in question_data:
            question_data["solution"] = {
                "approach": "Think through the problem step by step",
                "code": "# Implement your solution here",
                "time_complexity": "O(n)",
                "space_complexity": "O(1)"
            }
        
        if "constraints" not in question_data:
            question_data["constraints"] = ["Follow standard constraints"]
        
        if "hints" not in question_data:
            question_data["hints"] = ["Consider the problem requirements", "Think about edge cases"]
        
        return question_data
    
    def _extract_fallback_from_text(self, text: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Extract question info from unstructured text as fallback"""
        
        lines = text.split('\n')
        
        # Try to extract basic info
        title = "Coding Challenge"
        problem_statement = text[:500] + "..." if len(text) > 500 else text
        
        # Look for title
        for line in lines[:5]:
            if any(word in line.lower() for word in ["title", "problem", "question"]):
                title = line.split(":")[-1].strip() if ":" in line else line.strip()
                break
        
        return {
            "title": title,
            "problem_statement": problem_statement,
            "examples": [{"input": "example input", "output": "example output", "explanation": "solve step by step"}],
            "constraints": ["Follow standard constraints"],
            "solution": {
                "approach": f"Apply {topic} techniques",
                "code": f"# Solution for {title}\n# Implement your solution here",
                "time_complexity": "O(n)",
                "space_complexity": "O(1)"
            },
            "hints": [f"Think about {topic} properties", "Consider edge cases"],
            "topic": topic,
            "difficulty": difficulty,
            "fallback": True
        }
    
    def _create_fallback_question(self, topic: str, difficulty: str, question_num: int) -> Dict[str, Any]:
        """Create a simple fallback question when generation fails"""
        
        fallback_questions = {
            "arrays": {
                "title": "Array Sum Problem",
                "problem_statement": "Given an array of integers, find two numbers that add up to a target sum.",
                "solution_hint": "Use hash table for O(n) solution"
            },
            "strings": {
                "title": "String Palindrome Check", 
                "problem_statement": "Determine if a given string is a palindrome, ignoring spaces and case.",
                "solution_hint": "Use two pointers from start and end"
            },
            "trees": {
                "title": "Binary Tree Traversal",
                "problem_statement": "Implement inorder traversal of a binary tree.",
                "solution_hint": "Use recursion or stack for iterative approach"
            }
        }
        
        template = fallback_questions.get(topic.lower(), fallback_questions["arrays"])
        
        return {
            "title": f"{template['title']} #{question_num}",
            "problem_statement": template["problem_statement"],
            "examples": [
                {
                    "input": "sample input",
                    "output": "expected output", 
                    "explanation": "step by step solution"
                }
            ],
            "constraints": ["Standard problem constraints apply"],
            "solution": {
                "approach": template["solution_hint"],
                "code": f"# {template['title']} solution\n# Implement your approach here",
                "time_complexity": "O(n)",
                "space_complexity": "O(1)"
            },
            "hints": [template["solution_hint"], "Consider edge cases"],
            "topic": topic,
            "difficulty": difficulty,
            "fallback": True
        }
    
    def _format_questions_content(self, questions: List[Dict[str, Any]]) -> str:
        """Format questions into readable content for email"""
        
        if not questions:
            return "No coding questions generated."
        
        content_parts = [
            f"=== DAILY CODING QUESTIONS ({len(questions)} problems) ===\n"
        ]
        
        for i, question in enumerate(questions, 1):
            content_parts.extend([
                f"PROBLEM #{i}: {question.get('title', 'Coding Problem')}",
                f"Topic: {question.get('topic', 'General')} | Difficulty: {question.get('difficulty', 'Medium')}",
                "",
                "PROBLEM STATEMENT:",
                question.get('problem_statement', 'No description available'),
                "",
                "EXAMPLES:",
            ])
            
            examples = question.get('examples', [])
            for j, example in enumerate(examples[:2], 1):  # Limit to 2 examples
                content_parts.extend([
                    f"Example {j}:",
                    f"Input: {example.get('input', 'N/A')}",
                    f"Output: {example.get('output', 'N/A')}",
                    f"Explanation: {example.get('explanation', 'N/A')}",
                    ""
                ])
            
            # Add solution info
            solution = question.get('solution', {})
            if solution:
                content_parts.extend([
                    "APPROACH:",
                    solution.get('approach', 'Think step by step'),
                    "",
                    f"Time Complexity: {solution.get('time_complexity', 'O(n)')}",
                    f"Space Complexity: {solution.get('space_complexity', 'O(1)')}",
                    ""
                ])
            
            # Add hints
            hints = question.get('hints', [])
            if hints:
                content_parts.append("HINTS:")
                for hint in hints[:2]:  # Limit to 2 hints
                    content_parts.append(f"• {hint}")
                content_parts.append("")
            
            content_parts.append("=" * 50)
            content_parts.append("")
        
        return "\n".join(content_parts)


# Example usage and testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
    load_dotenv(env_path)
    
    print("🧠 AutoTasker AI - DSA Agent Test")
    print("=" * 50)
    
    # Check if OpenRouter API key is available
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OpenRouter API key not found in environment variables")
        print("Please set OPENROUTER_API_KEY in config/.env file")
        sys.exit(1)
    
    print("✅ OpenRouter API key found")
    
    # Test configuration
    config = {
        'llm': {
            'provider': 'openrouter',
            'model': 'meta-llama/llama-3.3-70b-instruct',
            'api_key': api_key
        },
        'agents': {
            'dsa_generator': {
                'model': 'meta-llama/llama-3.3-70b-instruct',
                'temperature': 0.8
            }
        }
    }
    
    print(f"🤖 Using model: {config['llm']['model']}")
    
    try:
        # Create DSA agent
        agent = DSAAgent(config)
        print("✅ DSA Agent initialized successfully")
        
        # Test 1: Generate coding questions
        print("\n📝 Test 1: Generating coding questions...")
        task = {
            "parameters": {
                "count": 2,
                "difficulty": "medium",
                "topics": ["arrays", "strings"]
            }
        }
        
        result = agent.execute_task(task)
        
        if result.get('success'):
            print("✅ Questions generated successfully!")
            print(f"📊 Generated {result.get('count', 0)} questions")
            print("\n" + "="*50)
            print("GENERATED CONTENT:")
            print("="*50)
            print(result.get('content', 'No content'))
        else:
            print(f"❌ Failed to generate questions: {result.get('error')}")
            
        # Test 2: Fallback question
        print("\n📝 Test 2: Testing fallback question generation...")
        fallback_question = agent._create_fallback_question("trees", "easy", 1)
        print("✅ Fallback question created:")
        print(f"Title: {fallback_question.get('title')}")
        print(f"Topic: {fallback_question.get('topic')}")
        print(f"Difficulty: {fallback_question.get('difficulty')}")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 DSA Agent testing completed!")
