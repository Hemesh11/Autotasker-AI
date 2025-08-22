"""
LeetCode Agent: Manages LeetCode problem recommendations and study plans
Handles scheduled delivery, memory management, and structured DSA preparation

Data Sources (in priority order):
1. LeetCode GraphQL API (requires session cookie)
2. LLM generation (AI-generated problems)
3. Curated problems database (final fallback)
"""

import json
import logging
import random
import os
import sys
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import hashlib

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


class LeetCodeGraphQLClient:
    """GraphQL client for accessing LeetCode API"""
    
    def __init__(self, session_cookie: Optional[str] = None):
        self.session_cookie = session_cookie
        self.base_url = "https://leetcode.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if self.session_cookie:
            self.headers["Cookie"] = f"LEETCODE_SESSION={self.session_cookie}"
    
    def get_problems_by_topic(self, topic: str, difficulty: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get problems from LeetCode GraphQL API"""
        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
            problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
            ) {
                total: totalNum
                questions: data {
                    acRate
                    difficulty
                    freqBar
                    frontendQuestionId: questionFrontendId
                    isFavor
                    paidOnly: isPaidOnly
                    status
                    title
                    titleSlug
                    topicTags {
                        name
                        id
                        slug
                    }
                    hasSolution
                    hasVideoSolution
                }
            }
        }
        """
        
        # Add randomization to get different results
        skip_offset = random.randint(0, min(50, limit * 2))  # Random offset to get variety
        
        variables = {
            "categorySlug": "",
            "limit": limit * 2,  # Request more to filter and get variety
            "skip": skip_offset,
            "filters": {
                "difficulty": difficulty.upper(),
                "tags": [topic.replace("_", "-")]
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
                formatted_questions = self._format_graphql_questions(questions)
                
                # Shuffle and return the requested amount to ensure variety
                random.shuffle(formatted_questions)
                return formatted_questions[:limit]
            else:
                raise Exception(f"GraphQL API returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"GraphQL request failed: {str(e)}")
    
    def get_problem_details(self, title_slug: str) -> Dict[str, Any]:
        """Get detailed problem information"""
        query = """
        query questionContent($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                content
                mysqlSchemas
                dataSchemas
                sampleTestCase
                exampleTestcases
                companyTagStats
            }
        }
        """
        
        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": {"titleSlug": title_slug}},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("question", {})
            else:
                return {}
                
        except Exception:
            return {}
    
    def _format_graphql_questions(self, questions: List[Dict]) -> List[Dict[str, Any]]:
        """Format GraphQL response to our standard format"""
        formatted = []
        
        for q in questions:
            if q.get("paidOnly", False):  # Skip premium problems
                continue
                
            formatted_q = {
                "title": q.get("title", ""),
                "number": q.get("frontendQuestionId", ""),
                "link": f"https://leetcode.com/problems/{q.get('titleSlug', '')}/",
                "difficulty": q.get("difficulty", "Medium").lower(),
                "topic": self._extract_primary_topic(q.get("topicTags", [])),
                "companies": self._extract_companies(q),
                "frequency": self._calculate_frequency(q.get("freqBar")),
                "acceptance_rate": f"{q.get('acRate', 0):.1f}%",
                "data_source": "leetcode_graphql",
                "generated_at": datetime.now().isoformat()
            }
            formatted.append(formatted_q)
            
        return formatted
    
    def _extract_primary_topic(self, topic_tags: List[Dict]) -> str:
        """Extract primary topic from topic tags"""
        if not topic_tags:
            return "arrays"
        return topic_tags[0].get("slug", "arrays").replace("-", "_")
    
    def _extract_companies(self, question: Dict) -> str:
        """Extract company information"""
        # This would need the detailed query to get company stats
        return "Google, Amazon, Microsoft"  # Default fallback
    
    def _calculate_frequency(self, freq_bar) -> str:
        """Calculate frequency from freqBar value"""
        if freq_bar is None:
            return "Medium"
        if freq_bar > 50:
            return "High"
        elif freq_bar > 20:
            return "Medium"
        else:
            return "Low"


class CuratedProblemsDatabase:
    """Curated database of popular LeetCode problems"""
    
    def __init__(self):
        self.problems_db = {
            "arrays": {
                "easy": [
                    {
                        "title": "Two Sum",
                        "number": "1",
                        "link": "https://leetcode.com/problems/two-sum/",
                        "difficulty": "easy",
                        "topic": "arrays",
                        "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
                        "test_cases": "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].",
                        "companies": "Amazon, Google, Apple, Microsoft, Facebook",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Best Time to Buy and Sell Stock",
                        "number": "121",
                        "link": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
                        "difficulty": "easy",
                        "topic": "arrays",
                        "description": "You are given an array prices where prices[i] is the price of a given stock on the ith day. You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.",
                        "test_cases": "Input: prices = [7,1,5,3,6,4]\nOutput: 5\nExplanation: Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5.",
                        "companies": "Amazon, Bloomberg, Microsoft, Facebook, Apple",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Contains Duplicate",
                        "number": "217",
                        "link": "https://leetcode.com/problems/contains-duplicate/",
                        "difficulty": "easy",
                        "topic": "arrays",
                        "description": "Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.",
                        "test_cases": "Input: nums = [1,2,3,1]\nOutput: true\nExplanation: The element 1 occurs at indices 0 and 3.",
                        "companies": "Google, Amazon, Microsoft, Apple, Airbnb",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Maximum Subarray",
                        "number": "53",
                        "link": "https://leetcode.com/problems/maximum-subarray/",
                        "difficulty": "easy",
                        "topic": "arrays",
                        "description": "Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.",
                        "test_cases": "Input: nums = [-2,1,-3,4,-1,2,1,-5,4]\nOutput: 6\nExplanation: [4,-1,2,1] has the largest sum = 6.",
                        "companies": "Amazon, Microsoft, Google, Apple, Facebook",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Plus One",
                        "number": "66",
                        "link": "https://leetcode.com/problems/plus-one/",
                        "difficulty": "easy",
                        "topic": "arrays",
                        "description": "You are given a large integer represented as an integer array digits, where each digits[i] is the ith digit of the integer. The digits are ordered from most significant to least significant in left-to-right order. The large integer does not contain any leading zero. Increment the large integer by one and return the resulting array of digits.",
                        "test_cases": "Input: digits = [1,2,3]\nOutput: [1,2,4]\nExplanation: The array represents the integer 123. Incrementing by one gives 123 + 1 = 124.",
                        "companies": "Google, Amazon, Microsoft, Apple",
                        "frequency": "Medium",
                        "data_source": "curated_database"
                    }
                ],
                "medium": [
                    {
                        "title": "3Sum",
                        "number": "15",
                        "link": "https://leetcode.com/problems/3sum/",
                        "difficulty": "medium",
                        "topic": "arrays",
                        "description": "Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.",
                        "test_cases": "Input: nums = [-1,0,1,2,-1,-4]\nOutput: [[-1,-1,2],[-1,0,1]]\nExplanation: The distinct triplets are [-1,0,1] and [-1,-1,2].",
                        "companies": "Facebook, Amazon, Microsoft, Google, Adobe",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Container With Most Water",
                        "number": "11",
                        "link": "https://leetcode.com/problems/container-with-most-water/",
                        "difficulty": "medium",
                        "topic": "arrays",
                        "description": "You are given an integer array height of length n. There are n vertical lines drawn such that the two endpoints of the ith line are (i, 0) and (i, height[i]). Find two lines that together with the x-axis form a container that contains the most water.",
                        "test_cases": "Input: height = [1,8,6,2,5,4,8,3,7]\nOutput: 49\nExplanation: The above vertical lines are represented by array [1,8,6,2,5,4,8,3,7]. In this case, the max area of water (blue section) the container can contain is 49.",
                        "companies": "Amazon, Google, Facebook, Microsoft, Bloomberg",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Product of Array Except Self",
                        "number": "238",
                        "link": "https://leetcode.com/problems/product-of-array-except-self/",
                        "difficulty": "medium",
                        "topic": "arrays",
                        "description": "Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].",
                        "test_cases": "Input: nums = [1,2,3,4]\nOutput: [24,12,8,6]\nExplanation: answer[0] = 2*3*4 = 24, answer[1] = 1*3*4 = 12, answer[2] = 1*2*4 = 8, answer[3] = 1*2*3 = 6",
                        "companies": "Amazon, Google, Facebook, Microsoft, Apple",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Maximum Product Subarray",
                        "number": "152",
                        "link": "https://leetcode.com/problems/maximum-product-subarray/",
                        "difficulty": "medium",
                        "topic": "arrays",
                        "description": "Given an integer array nums, find a contiguous non-empty subarray within the array that has the largest product, and return the product.",
                        "test_cases": "Input: nums = [2,3,-2,4]\nOutput: 6\nExplanation: [2,3] has the largest product 6.",
                        "companies": "Amazon, Google, Microsoft, Facebook, LinkedIn",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Find Minimum in Rotated Sorted Array",
                        "number": "153",
                        "link": "https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/",
                        "difficulty": "medium",
                        "topic": "arrays",
                        "description": "Suppose an array of length n sorted in ascending order is rotated between 1 and n times. Given the sorted rotated array nums of unique elements, return the minimum element of this array.",
                        "test_cases": "Input: nums = [3,4,5,1,2]\nOutput: 1\nExplanation: The original array was [1,2,3,4,5] rotated 3 times.",
                        "companies": "Amazon, Google, Microsoft, Apple, Facebook",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ],
                "hard": [
                    {
                        "title": "Trapping Rain Water",
                        "number": "42",
                        "link": "https://leetcode.com/problems/trapping-rain-water/",
                        "difficulty": "hard",
                        "topic": "arrays",
                        "description": "Given n non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.",
                        "test_cases": "Input: height = [0,1,0,2,1,0,1,3,2,1,2,1]\nOutput: 6\nExplanation: The above elevation map (black section) is represented by array [0,1,0,2,1,0,1,3,2,1,2,1]. In this case, 6 units of rain water (blue section) are being trapped.",
                        "companies": "Amazon, Google, Facebook, Microsoft, Apple",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ]
            },
            "strings": {
                "easy": [
                    {
                        "title": "Valid Anagram",
                        "number": "242",
                        "link": "https://leetcode.com/problems/valid-anagram/",
                        "difficulty": "easy",
                        "topic": "strings",
                        "description": "Given two strings s and t, return true if t is an anagram of s, and false otherwise.",
                        "test_cases": "Input: s = \"anagram\", t = \"nagaram\"\nOutput: true\nExplanation: Both strings contain the same characters with the same frequency.",
                        "companies": "Amazon, Google, Microsoft, Facebook, Bloomberg",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Valid Palindrome",
                        "number": "125",
                        "link": "https://leetcode.com/problems/valid-palindrome/",
                        "difficulty": "easy",
                        "topic": "strings",
                        "description": "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.",
                        "test_cases": "Input: s = \"A man, a plan, a canal: Panama\"\nOutput: true\nExplanation: \"amanaplanacanalpanama\" is a palindrome.",
                        "companies": "Amazon, Microsoft, Google, Facebook, Apple",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ],
                "medium": [
                    {
                        "title": "Longest Substring Without Repeating Characters",
                        "number": "3",
                        "link": "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
                        "difficulty": "medium",
                        "topic": "strings",
                        "description": "Given a string s, find the length of the longest substring without repeating characters.",
                        "test_cases": "Input: s = \"abcabcbb\"\nOutput: 3\nExplanation: The answer is \"abc\", with the length of 3.",
                        "companies": "Amazon, Google, Facebook, Microsoft, Bloomberg",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Group Anagrams",
                        "number": "49",
                        "link": "https://leetcode.com/problems/group-anagrams/",
                        "difficulty": "medium",
                        "topic": "strings",
                        "description": "Given an array of strings strs, group the anagrams together. You can return the answer in any order.",
                        "test_cases": "Input: strs = [\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"]\nOutput: [[\"bat\"],[\"nat\",\"tan\"],[\"ate\",\"eat\",\"tea\"]]\nExplanation: Anagrams are grouped together.",
                        "companies": "Amazon, Google, Facebook, Microsoft, Uber",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ],
                "hard": [
                    {
                        "title": "Minimum Window Substring",
                        "number": "76",
                        "link": "https://leetcode.com/problems/minimum-window-substring/",
                        "difficulty": "hard",
                        "topic": "strings",
                        "description": "Given two strings s and t of lengths m and n respectively, return the minimum window substring of s such that every character in t (including duplicates) is included in the window.",
                        "test_cases": "Input: s = \"ADOBECODEBANC\", t = \"ABC\"\nOutput: \"BANC\"\nExplanation: The minimum window substring \"BANC\" includes 'A', 'B', and 'C' from string t.",
                        "companies": "Amazon, Google, Facebook, Microsoft, Uber",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ]
            },
            "dynamic_programming": {
                "easy": [
                    {
                        "title": "Climbing Stairs",
                        "number": "70",
                        "link": "https://leetcode.com/problems/climbing-stairs/",
                        "difficulty": "easy",
                        "topic": "dynamic_programming",
                        "description": "You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
                        "test_cases": "Input: n = 2\nOutput: 2\nExplanation: There are two ways to climb to the top.\n1. 1 step + 1 step\n2. 2 steps",
                        "companies": "Amazon, Google, Microsoft, Adobe, Apple",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ],
                "medium": [
                    {
                        "title": "House Robber",
                        "number": "198",
                        "link": "https://leetcode.com/problems/house-robber/",
                        "difficulty": "medium",
                        "topic": "dynamic_programming",
                        "description": "You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed. Adjacent houses have security systems connected and it will automatically contact the police if two adjacent houses were broken into on the same night.",
                        "test_cases": "Input: nums = [1,2,3,1]\nOutput: 4\nExplanation: Rob house 1 (money = 1) and then rob house 3 (money = 3).\nTotal amount you can rob = 1 + 3 = 4.",
                        "companies": "Amazon, Google, Microsoft, Facebook, Airbnb",
                        "frequency": "High",
                        "data_source": "curated_database"
                    },
                    {
                        "title": "Coin Change",
                        "number": "322",
                        "link": "https://leetcode.com/problems/coin-change/",
                        "difficulty": "medium",
                        "topic": "dynamic_programming",
                        "description": "You are given an integer array coins representing coins of different denominations and an integer amount representing a total amount of money. Return the fewest number of coins that you need to make up that amount.",
                        "test_cases": "Input: coins = [1,3,4], amount = 6\nOutput: 2\nExplanation: The amount of 6 could be made up by 3 + 3 = 6, using 2 coins.",
                        "companies": "Amazon, Google, Microsoft, Facebook, Uber",
                        "frequency": "High",
                        "data_source": "curated_database"
                    }
                ]
            }
        }
    
    def get_problems(self, topic: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        """Get problems from curated database"""
        topic_problems = self.problems_db.get(topic, {})
        difficulty_problems = topic_problems.get(difficulty, [])
        
        # Return up to 'count' problems, but don't cycle - return what we have
        if not difficulty_problems:
            return []
        
        selected = []
        available_problems = difficulty_problems.copy()
        
        # Shuffle to get variety
        random.shuffle(available_problems)
        
        for i in range(min(count, len(available_problems))):
            problem = available_problems[i].copy()
            problem["generated_at"] = datetime.now().isoformat()
            selected.append(problem)
        
        return selected
    
    def get_all_topics(self) -> List[str]:
        """Get all available topics"""
        return list(self.problems_db.keys())
    
    def get_problem_count(self, topic: str, difficulty: str) -> int:
        """Get count of problems for topic and difficulty"""
        return len(self.problems_db.get(topic, {}).get(difficulty, []))


class LeetCodeAgent:
    """Agent for LeetCode problem recommendations and study planning"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.LeetCodeAgent")
        
        # Initialize LLM client
        self.client = create_llm_client(config)
        self.model = LLMClientFactory.get_model_name(config, "leetcode_agent")
        self.temperature = config.get("agents", {}).get("leetcode_agent", {}).get("temperature", 0.7)
        
        # Initialize data sources
        self._init_data_sources()
        
        # Memory file for tracking sent questions
        self.memory_file = os.path.join(
            os.path.dirname(__file__), 
            '..', 'memory', 'leetcode_history.json'
        )
        
        # Ensure memory directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        # Load memory
        self.sent_questions = self._load_memory()
        
        # DSA topic structure for structured plans
        self.dsa_curriculum = {
            "beginner": [
                {"topic": "Arrays", "days": 3, "priority": ["Two Sum", "Best Time to Buy and Sell Stock", "Contains Duplicate"]},
                {"topic": "Strings", "days": 2, "priority": ["Valid Anagram", "Valid Palindrome", "Longest Common Prefix"]},
                {"topic": "Linked Lists", "days": 2, "priority": ["Reverse Linked List", "Merge Two Sorted Lists", "Linked List Cycle"]},
                {"topic": "Stacks", "days": 2, "priority": ["Valid Parentheses", "Implement Stack using Queues"]},
                {"topic": "Binary Trees", "days": 3, "priority": ["Maximum Depth of Binary Tree", "Same Tree", "Invert Binary Tree"]}
            ],
            "intermediate": [
                {"topic": "Two Pointers", "days": 2, "priority": ["3Sum", "Container With Most Water", "Trapping Rain Water"]},
                {"topic": "Sliding Window", "days": 2, "priority": ["Longest Substring Without Repeating Characters", "Minimum Window Substring"]},
                {"topic": "Binary Search", "days": 2, "priority": ["Search in Rotated Sorted Array", "Find Minimum in Rotated Sorted Array"]},
                {"topic": "Dynamic Programming", "days": 4, "priority": ["Climbing Stairs", "House Robber", "Coin Change", "Longest Increasing Subsequence"]},
                {"topic": "Graphs", "days": 3, "priority": ["Number of Islands", "Course Schedule", "Clone Graph"]}
            ],
            "advanced": [
                {"topic": "Advanced DP", "days": 4, "priority": ["Edit Distance", "Regular Expression Matching", "Burst Balloons"]},
                {"topic": "Trees & Graphs", "days": 3, "priority": ["Serialize and Deserialize Binary Tree", "Word Ladder", "Alien Dictionary"]},
                {"topic": "Backtracking", "days": 2, "priority": ["N-Queens", "Word Search", "Combination Sum"]},
                {"topic": "Heap", "days": 2, "priority": ["Merge k Sorted Lists", "Top K Frequent Elements", "Find Median from Data Stream"]},
                {"topic": "Trie", "days": 2, "priority": ["Implement Trie", "Word Search II", "Design Add and Search Words Data Structure"]}
            ]
        }
        
        # Company-specific high-frequency questions
        self.company_priorities = {
            "faang": ["Two Sum", "Reverse Linked List", "Valid Parentheses", "Maximum Subarray", "Merge Intervals"],
            "top_tech": ["3Sum", "Longest Substring Without Repeating Characters", "Container With Most Water", "Product of Array Except Self"],
            "interviews": ["Climbing Stairs", "House Robber", "Coin Change", "Number of Islands", "Course Schedule"]
        }
        
        # Difficulty distribution for balanced learning
        self.difficulty_distribution = {
            "beginner": {"easy": 0.7, "medium": 0.3, "hard": 0.0},
            "intermediate": {"easy": 0.3, "medium": 0.6, "hard": 0.1},
            "advanced": {"easy": 0.1, "medium": 0.5, "hard": 0.4}
        }
    
    def _init_data_sources(self):
        """Initialize different data sources for LeetCode problems"""
        # LeetCode session cookie from config (optional)
        leetcode_session = self.config.get("leetcode", {}).get("session_cookie")
        
        # Initialize data sources in priority order
        self.graphql_client = LeetCodeGraphQLClient(leetcode_session) if leetcode_session else None
        self.curated_db = CuratedProblemsDatabase()
        
        # Log available data sources
        sources = []
        if self.graphql_client:
            sources.append("GraphQL API")
        sources.extend(["LLM Generation", "Curated Database"])
        
        self.logger.info(f"Initialized data sources: {', '.join(sources)}")
    
    def _get_problems_from_sources(self, topic: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        """Get problems using hybrid approach: GraphQL → LLM → Curated DB"""
        problems = []
        
        # Try GraphQL first (if session available) with multiple attempts for variety
        if self.graphql_client:
            try:
                self.logger.info(f"Attempting GraphQL fetch for {topic}/{difficulty}")
                # Try multiple times with different offsets to get variety
                for attempt in range(2):
                    graphql_problems = self.graphql_client.get_problems_by_topic(topic, difficulty, count + 2)
                    if graphql_problems:
                        # Filter out any problems we already have
                        existing_titles = {p.get('title', '') for p in problems}
                        new_problems = [p for p in graphql_problems if p.get('title', '') not in existing_titles]
                        problems.extend(new_problems[:count - len(problems)])
                        
                        if len(problems) >= count:
                            break
                
                if problems:
                    self.logger.info(f"✅ Got {len(problems)} problems from GraphQL API")
                    return problems[:count]
                else:
                    self.logger.warning("GraphQL returned no valid problems, falling back")
            except Exception as e:
                self.logger.warning(f"GraphQL failed: {e}, falling back to LLM generation")
        
        # Try LLM generation (first fallback)
        if len(problems) < count:
            try:
                self.logger.info(f"Attempting LLM generation for {topic}/{difficulty}")
                attempts_needed = count - len(problems)
                
                for i in range(attempts_needed):
                    problem = self._generate_leetcode_question_llm(topic, difficulty, i + 1)
                    if problem:
                        # Check for duplicates within this batch
                        existing_titles = {p.get('title', '') for p in problems}
                        if problem.get('title', '') not in existing_titles:
                            problems.append(problem)
                
                if problems:
                    self.logger.info(f"✅ Generated {len(problems)} problems using LLM")
                    if len(problems) >= count:
                        return problems[:count]
            except Exception as e:
                self.logger.warning(f"LLM generation failed: {e}, falling back to curated database")
        
        # Final fallback to curated database
        if len(problems) < count:
            try:
                self.logger.info(f"Using curated database as fallback for {topic}/{difficulty}")
                attempts_needed = count - len(problems)
                curated_problems = self.curated_db.get_problems(topic, difficulty, attempts_needed)
                
                if curated_problems:
                    # Filter out duplicates
                    existing_titles = {p.get('title', '') for p in problems}
                    new_curated = [p for p in curated_problems if p.get('title', '') not in existing_titles]
                    problems.extend(new_curated[:attempts_needed])
                    self.logger.info(f"✅ Got {len(new_curated)} new problems from curated database")
            except Exception as e:
                self.logger.error(f"Curated database failed: {e}")
        
        # Emergency fallback - create a basic problem if still empty
        if not problems:
            self.logger.warning("All data sources failed, creating emergency fallback")
            problems.append(self._create_emergency_fallback_question(topic, difficulty))
        
        return problems[:count]
    
    @retry_on_failure(max_retries=3)
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LeetCode task based on natural language input
        
        Args:
            task: Task configuration with natural language description
            
        Returns:
            Generated LeetCode recommendations or study plan
        """
        
        try:
            description = task.get("description", "")
            task_type = self._analyze_task_type(description)
            
            self.logger.info(f"Executing LeetCode task: {task_type}")
            
            if task_type == "daily_questions":
                return self._handle_daily_questions(description)
            elif task_type == "study_plan":
                return self._handle_study_plan(description)
            elif task_type == "topic_specific":
                return self._handle_topic_specific(description)
            elif task_type == "difficulty_specific":
                return self._handle_difficulty_specific(description)
            else:
                return self._handle_general_request(description)
                
        except Exception as e:
            self.logger.error(f"LeetCode task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to execute LeetCode task: {str(e)}"
            }
    
    def _analyze_task_type(self, description: str) -> str:
        """Analyze natural language to determine task type"""
        
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["daily", "every day", "each day", "schedule"]):
            return "daily_questions"
        elif any(word in description_lower for word in ["plan", "20 days", "study plan", "curriculum", "roadmap"]):
            return "study_plan"
        elif any(word in description_lower for word in ["topic", "arrays", "strings", "trees", "graphs", "dp"]):
            return "topic_specific"
        elif any(word in description_lower for word in ["easy", "medium", "hard", "difficulty"]):
            return "difficulty_specific"
        else:
            return "general_request"
    
    def _handle_daily_questions(self, description: str) -> Dict[str, Any]:
        """Handle daily question requests"""
        
        # Parse the request for details
        request_details = self._parse_daily_request(description)
        
        # Generate questions for today
        questions = self._generate_daily_questions(
            count=request_details["count"],
            difficulty_level=request_details["difficulty_level"],
            topics=request_details["topics"]
        )
        
        if not questions:
            return {
                "success": False,
                "error": "Failed to generate questions",
                "content": "No LeetCode questions were generated"
            }
        
        # Save to memory
        self._save_questions_to_memory(questions)
        
        # Format content
        content = self._format_daily_questions_content(questions, request_details)
        
        return {
            "success": True,
            "type": "daily_questions",
            "count": len(questions),
            "content": content,
            "questions": questions,
            "schedule_info": request_details
        }
    
    def _handle_study_plan(self, description: str) -> Dict[str, Any]:
        """Handle structured study plan requests"""
        
        plan_details = self._parse_study_plan_request(description)
        study_plan = self._generate_study_plan(
            days=plan_details["days"],
            level=plan_details["level"],
            questions_per_day=plan_details["questions_per_day"]
        )
        
        content = self._format_study_plan_content(study_plan, plan_details)
        
        return {
            "success": True,
            "type": "study_plan",
            "content": content,
            "study_plan": study_plan,
            "plan_details": plan_details
        }
    
    def _handle_topic_specific(self, description: str) -> Dict[str, Any]:
        """Handle topic-specific requests"""
        
        topic_details = self._parse_topic_request(description)
        questions = self._generate_topic_questions(
            topic=topic_details["topic"],
            count=topic_details["count"],
            difficulty=topic_details["difficulty"]
        )
        
        content = self._format_topic_questions_content(questions, topic_details)
        
        return {
            "success": True,
            "type": "topic_specific",
            "content": content,
            "questions": questions,
            "topic_details": topic_details
        }
    
    def _handle_difficulty_specific(self, description: str) -> Dict[str, Any]:
        """Handle difficulty-specific requests"""
        
        diff_details = self._parse_difficulty_request(description)
        questions = self._generate_difficulty_questions(
            difficulty=diff_details["difficulty"],
            count=diff_details["count"],
            topics=diff_details["topics"]
        )
        
        content = self._format_difficulty_questions_content(questions, diff_details)
        
        return {
            "success": True,
            "type": "difficulty_specific",
            "content": content,
            "questions": questions,
            "difficulty_details": diff_details
        }
    
    def _handle_general_request(self, description: str) -> Dict[str, Any]:
        """Handle general LeetCode requests"""
        
        questions = self._generate_general_questions(description)
        content = self._format_general_questions_content(questions, description)
        
        return {
            "success": True,
            "type": "general_request",
            "content": content,
            "questions": questions
        }
    
    def _parse_daily_request(self, description: str) -> Dict[str, Any]:
        """Parse daily question request details"""
        
        # Use LLM to extract structured information
        prompt = f"""
        Parse this LeetCode daily question request and extract details:
        "{description}"
        
        Extract and return a JSON object with:
        - count: number of questions per day (default 3)
        - difficulty_level: beginner/intermediate/advanced (default intermediate)
        - topics: array of specific topics if mentioned (default [])
        - schedule_time: time if mentioned (default "09:00")
        - email_delivery: true/false if email delivery mentioned (default true)
        
        Return only the JSON object.
        """
        
        try:
            response = get_chat_completion(
                client=self.client,
                messages=[
                    {"role": "system", "content": "Extract request details as JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=300
            )
            
            # Clean and parse JSON
            response = response.strip()
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            
            details = json.loads(response)
            
        except:
            # Fallback parsing
            details = {
                "count": 3,
                "difficulty_level": "intermediate",
                "topics": [],
                "schedule_time": "09:00",
                "email_delivery": True
            }
        
        return details
    
    def _parse_study_plan_request(self, description: str) -> Dict[str, Any]:
        """Parse study plan request details"""
        
        prompt = f"""
        Parse this LeetCode study plan request:
        "{description}"
        
        Extract and return a JSON object with:
        - days: number of days (default 20)
        - level: beginner/intermediate/advanced (default intermediate)
        - questions_per_day: questions per day (default 5)
        - focus_areas: array of focus areas if mentioned
        - company_prep: company name if mentioned (faang, google, amazon, etc.)
        
        Return only the JSON object.
        """
        
        try:
            response = get_chat_completion(
                client=self.client,
                messages=[
                    {"role": "system", "content": "Extract study plan details as JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=300
            )
            
            response = response.strip()
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            
            details = json.loads(response)
            
        except:
            details = {
                "days": 20,
                "level": "intermediate",
                "questions_per_day": 5,
                "focus_areas": [],
                "company_prep": None
            }
        
        return details
    
    def _parse_topic_request(self, description: str) -> Dict[str, Any]:
        """Parse topic-specific request details"""
        
        # Simple keyword-based parsing for topics
        description_lower = description.lower()
        
        topic_keywords = {
            "arrays": ["array", "arrays"],
            "strings": ["string", "strings"],
            "linked_lists": ["linked list", "linkedlist"],
            "trees": ["tree", "trees", "binary tree"],
            "graphs": ["graph", "graphs"],
            "dynamic_programming": ["dp", "dynamic programming", "dynamic"],
            "backtracking": ["backtrack", "backtracking"],
            "two_pointers": ["two pointer", "two pointers"],
            "sliding_window": ["sliding window", "window"],
            "binary_search": ["binary search", "search"]
        }
        
        detected_topic = "arrays"  # default
        for topic, keywords in topic_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                detected_topic = topic
                break
        
        # Extract count and difficulty
        count = 5  # default
        difficulty = "medium"  # default
        
        if "easy" in description_lower:
            difficulty = "easy"
        elif "hard" in description_lower:
            difficulty = "hard"
        
        # Extract number
        import re
        numbers = re.findall(r'\b(\d+)\b', description)
        if numbers:
            count = int(numbers[0])
        
        return {
            "topic": detected_topic,
            "count": count,
            "difficulty": difficulty
        }
    
    def _parse_difficulty_request(self, description: str) -> Dict[str, Any]:
        """Parse difficulty-specific request details"""
        
        description_lower = description.lower()
        
        difficulty = "medium"
        if "easy" in description_lower:
            difficulty = "easy"
        elif "hard" in description_lower:
            difficulty = "hard"
        
        count = 5
        import re
        numbers = re.findall(r'\b(\d+)\b', description)
        if numbers:
            count = int(numbers[0])
        
        return {
            "difficulty": difficulty,
            "count": count,
            "topics": []
        }
    
    def _generate_daily_questions(self, count: int, difficulty_level: str, topics: List[str]) -> List[Dict[str, Any]]:
        """Generate daily LeetCode questions"""
        
        questions = []
        used_questions = set()  # Track questions within this generation session
        attempts = 0
        max_attempts = count * 5  # Allow more attempts to avoid duplicates
        
        # Get difficulty distribution
        diff_dist = self.difficulty_distribution.get(difficulty_level, self.difficulty_distribution["intermediate"])
        
        # Try to get diverse questions from different sources
        sources_tried = set()
        
        while len(questions) < count and attempts < max_attempts:
            attempts += 1
            
            # Select difficulty based on distribution
            difficulty = self._select_difficulty_by_distribution(diff_dist)
            
            # Select topic - ensure variety
            if topics:
                topic = random.choice(topics)
            else:
                available_topics = ["arrays", "strings", "trees", "dynamic_programming", "graphs", "two_pointers"]
                # Try to pick a topic we haven't used yet
                unused_topics = [t for t in available_topics if t not in sources_tried]
                topic = random.choice(unused_topics if unused_topics else available_topics)
                sources_tried.add(topic)
            
            # Generate question
            generated_questions = self._get_problems_from_sources(topic, difficulty, 1)
            if generated_questions:
                question = generated_questions[0]
                question_id = f"{question.get('number', '')}-{question.get('title', '')}"
                
                # Check both session duplicates and memory duplicates
                if (question_id not in used_questions and 
                    not self._is_question_recently_sent(question)):
                    questions.append(question)
                    used_questions.add(question_id)
                    self.logger.info(f"Added question: {question.get('title', 'Unknown')} (source: {question.get('data_source')})")
                else:
                    self.logger.debug(f"Skipped duplicate: {question.get('title', 'Unknown')}")
        
        # If we still don't have enough questions, force add from curated DB with different topics/difficulties
        if len(questions) < count:
            self.logger.warning(f"Only got {len(questions)}/{count} unique questions, adding curated fallbacks")
            
            # Try different combinations of topics and difficulties
            fallback_combos = [
                ("arrays", "easy"), ("strings", "medium"), ("trees", "easy"),
                ("dynamic_programming", "medium"), ("graphs", "easy"), ("two_pointers", "medium")
            ]
            
            for topic, diff in fallback_combos:
                if len(questions) >= count:
                    break
                try:
                    fallback_problems = self.curated_db.get_problems(topic, diff, 2)
                    for problem in fallback_problems:
                        if len(questions) >= count:
                            break
                        question_id = f"{problem.get('number', '')}-{problem.get('title', '')}"
                        if (question_id not in used_questions and 
                            not self._is_question_recently_sent(problem)):
                            questions.append(problem)
                            used_questions.add(question_id)
                            self.logger.info(f"Added curated fallback: {problem.get('title')} ({topic}/{diff})")
                except Exception as e:
                    self.logger.error(f"Curated fallback failed for {topic}/{diff}: {e}")
        
        # Final emergency fallback if still not enough
        if len(questions) < count:
            self.logger.warning(f"Still need {count - len(questions)} more questions, using emergency fallbacks")
            emergency_topics = ["arrays", "strings", "trees"]
            for i, topic in enumerate(emergency_topics):
                if len(questions) >= count:
                    break
                emergency_q = self._create_emergency_fallback_question(topic, "medium")
                emergency_q["number"] = str(1000 + i)  # Ensure unique numbers
                questions.append(emergency_q)
                self.logger.info(f"Added emergency fallback: {emergency_q.get('title')}")
        
        return questions
    
    def _generate_study_plan(self, days: int, level: str, questions_per_day: int) -> Dict[str, Any]:
        """Generate structured study plan"""
        
        curriculum = self.dsa_curriculum.get(level, self.dsa_curriculum["intermediate"])
        
        plan = {
            "total_days": days,
            "level": level,
            "questions_per_day": questions_per_day,
            "daily_schedule": []
        }
        
        # Distribute curriculum across days
        days_per_topic = days // len(curriculum)
        
        current_day = 1
        for topic_info in curriculum:
            topic_days = min(days_per_topic, topic_info["days"])
            
            for day in range(topic_days):
                if current_day > days:
                    break
                
                day_plan = {
                    "day": current_day,
                    "topic": topic_info["topic"],
                    "focus": f"Day {day + 1} of {topic_info['topic']}",
                    "questions": self._select_questions_for_topic_day(
                        topic_info["topic"], 
                        questions_per_day,
                        day,
                        topic_info.get("priority", [])
                    )
                }
                
                plan["daily_schedule"].append(day_plan)
                current_day += 1
        
        return plan
    
    def _generate_topic_questions(self, topic: str, count: int, difficulty: str) -> List[Dict[str, Any]]:
        """Generate questions for specific topic"""
        
        questions = []
        attempts = 0
        max_attempts = count * 2
        
        while len(questions) < count and attempts < max_attempts:
            attempts += 1
            problems = self._get_problems_from_sources(topic, difficulty, 1)
            if problems:
                question = problems[0]
                if not self._is_question_recently_sent(question):
                    questions.append(question)
        
        # Force add from curated DB if needed
        if len(questions) < count:
            try:
                fallback_problems = self.curated_db.get_problems(topic, difficulty, count - len(questions))
                for problem in fallback_problems:
                    if len(questions) >= count:
                        break
                    questions.append(problem)
            except Exception as e:
                self.logger.error(f"Topic fallback failed: {e}")
        
        return questions
    
    def _generate_difficulty_questions(self, difficulty: str, count: int, topics: List[str]) -> List[Dict[str, Any]]:
        """Generate questions for specific difficulty"""
        
        questions = []
        attempts = 0
        max_attempts = count * 2
        
        while len(questions) < count and attempts < max_attempts:
            attempts += 1
            topic = random.choice(topics) if topics else self._select_balanced_topic()
            problems = self._get_problems_from_sources(topic, difficulty, 1)
            if problems:
                question = problems[0]
                if not self._is_question_recently_sent(question):
                    questions.append(question)
        
        # Force add from curated DB if needed
        if len(questions) < count:
            fallback_topics = topics if topics else ["arrays", "strings", "trees"]
            for topic in fallback_topics:
                if len(questions) >= count:
                    break
                try:
                    fallback_problems = self.curated_db.get_problems(topic, difficulty, count - len(questions))
                    for problem in fallback_problems:
                        if len(questions) >= count:
                            break
                        questions.append(problem)
                except Exception as e:
                    self.logger.error(f"Difficulty fallback failed for topic {topic}: {e}")
        
        return questions
    
    def _generate_general_questions(self, description: str) -> List[Dict[str, Any]]:
        """Generate general LeetCode questions"""
        
        questions = []
        popular_topics = ["arrays", "strings", "trees", "dynamic_programming"]
        attempts = 0
        max_attempts = 10
        
        while len(questions) < 5 and attempts < max_attempts:
            attempts += 1
            topic = random.choice(popular_topics)
            problems = self._get_problems_from_sources(topic, "medium", 1)
            if problems:
                question = problems[0]
                if not self._is_question_recently_sent(question):
                    questions.append(question)
        
        # Force add from curated DB if needed
        if len(questions) < 5:
            for topic in popular_topics:
                if len(questions) >= 5:
                    break
                try:
                    fallback_problems = self.curated_db.get_problems(topic, "medium", 5 - len(questions))
                    for problem in fallback_problems:
                        if len(questions) >= 5:
                            break
                        questions.append(problem)
                except Exception as e:
                    self.logger.error(f"General fallback failed for topic {topic}: {e}")
        
        return questions
    
    def _generate_leetcode_question_llm(self, topic: str, difficulty: str, question_num: int) -> Optional[Dict[str, Any]]:
        """Generate a single LeetCode question using LLM"""
        
        prompt = f"""
        Generate a real LeetCode problem for:
        Topic: {topic}
        Difficulty: {difficulty}
        
        Provide response in this exact format:
        TITLE: [Problem title]
        NUMBER: [LeetCode problem number if known, or generate realistic one]
        LINK: https://leetcode.com/problems/[problem-slug]/
        DIFFICULTY: {difficulty}
        TOPIC: {topic}
        
        DESCRIPTION:
        [Brief problem description]
        
        TEST CASES:
        Input: [example input]
        Output: [example output]
        Explanation: [brief explanation]
        
        COMPANIES: [Companies that frequently ask this question]
        FREQUENCY: [High/Medium/Low interview frequency]
        
        Focus on real, well-known LeetCode problems that are frequently asked in interviews.
        """
        
        try:
            response = get_chat_completion(
                client=self.client,
                messages=[
                    {"role": "system", "content": "Generate real LeetCode problems with accurate details."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=800
            )
            
            if response and response.strip():
                question_data = self._parse_leetcode_response(response, topic, difficulty)
                return question_data
            else:
                self.logger.warning("Empty response from LLM, using fallback")
                return self._create_fallback_leetcode_question(topic, difficulty, question_num)
            
        except Exception as e:
            self.logger.error(f"Failed to generate LeetCode question: {e}")
            return self._create_fallback_leetcode_question(topic, difficulty, question_num)
    
    def _parse_leetcode_response(self, response: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Parse LeetCode question response"""
        
        lines = response.split('\n')
        result = {
            "topic": topic,
            "difficulty": difficulty,
            "generated_at": datetime.now().isoformat()
        }
        
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('TITLE:'):
                result['title'] = line[6:].strip()
            elif line.startswith('NUMBER:'):
                result['number'] = line[7:].strip()
            elif line.startswith('LINK:'):
                result['link'] = line[5:].strip()
            elif line.startswith('DIFFICULTY:'):
                result['difficulty'] = line[11:].strip()
            elif line.startswith('TOPIC:'):
                result['topic'] = line[6:].strip()
            elif line.startswith('DESCRIPTION:'):
                current_section = 'description'
                current_content = []
            elif line.startswith('TEST CASES:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                current_section = 'test_cases'
                current_content = []
            elif line.startswith('COMPANIES:'):
                if current_section:
                    result[current_section] = '\n'.join(current_content).strip()
                result['companies'] = line[10:].strip()
            elif line.startswith('FREQUENCY:'):
                result['frequency'] = line[10:].strip()
            else:
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            result[current_section] = '\n'.join(current_content).strip()
        
        # Ensure required fields
        if 'title' not in result:
            result['title'] = f"{topic.title()} Problem"
        if 'number' not in result:
            result['number'] = str(random.randint(1, 3000))
        if 'link' not in result:
            slug = result['title'].lower().replace(' ', '-').replace(',', '').replace(':', '')
            result['link'] = f"https://leetcode.com/problems/{slug}/"
        
        # Mark as LLM generated
        result['data_source'] = 'llm_generated'
        
        return result
    
    def _create_emergency_fallback_question(self, topic: str, difficulty: str) -> Dict[str, Any]:
        """Create emergency fallback question when all sources fail"""
        
        emergency_questions = {
            "arrays": "Two Sum - Find two numbers in array that sum to target",
            "strings": "Valid Anagram - Check if two strings are anagrams", 
            "trees": "Maximum Depth of Binary Tree - Find max depth of tree",
            "dynamic_programming": "Climbing Stairs - Count ways to climb stairs",
            "graphs": "Number of Islands - Count connected islands in grid",
            "linked_lists": "Reverse Linked List - Reverse a singly linked list"
        }
        
        title = emergency_questions.get(topic, "Basic Coding Problem")
        slug = title.lower().replace(' ', '-').replace(',', '').replace(':', '')
        
        return {
            "title": title,
            "number": str(random.randint(1, 100)),
            "link": f"https://leetcode.com/problems/{slug}/",
            "difficulty": difficulty,
            "topic": topic,
            "description": f"This is an emergency fallback problem for {topic}. Please check LeetCode for similar problems.",
            "test_cases": "Input: Example input\nOutput: Example output\nExplanation: Basic test case",
            "companies": "Various Tech Companies",
            "frequency": "Medium",
            "generated_at": datetime.now().isoformat(),
            "data_source": "emergency_fallback"
        }

    def _create_fallback_leetcode_question(self, topic: str, difficulty: str, question_num: int) -> Dict[str, Any]:
        """Create fallback LeetCode question"""
        
        fallback_questions = {
            "arrays": {
                "easy": {"title": "Two Sum", "number": "1"},
                "medium": {"title": "3Sum", "number": "15"},
                "hard": {"title": "4Sum", "number": "18"}
            },
            "strings": {
                "easy": {"title": "Valid Anagram", "number": "242"},
                "medium": {"title": "Longest Substring Without Repeating Characters", "number": "3"},
                "hard": {"title": "Minimum Window Substring", "number": "76"}
            },
            "trees": {
                "easy": {"title": "Maximum Depth of Binary Tree", "number": "104"},
                "medium": {"title": "Binary Tree Level Order Traversal", "number": "102"},
                "hard": {"title": "Serialize and Deserialize Binary Tree", "number": "297"}
            }
        }
        
        topic_questions = fallback_questions.get(topic, fallback_questions["arrays"])
        question_info = topic_questions.get(difficulty, topic_questions["medium"])
        
        slug = question_info["title"].lower().replace(' ', '-')
        
        return {
            "title": question_info["title"],
            "number": question_info["number"],
            "link": f"https://leetcode.com/problems/{slug}/",
            "difficulty": difficulty,
            "topic": topic,
            "description": f"Solve the {question_info['title']} problem on LeetCode.",
            "test_cases": "Input: Example input\nOutput: Example output\nExplanation: Solve step by step",
            "companies": "Google, Facebook, Amazon",
            "frequency": "High",
            "generated_at": datetime.now().isoformat(),
            "fallback": True,
            "data_source": "curated_fallback"
        }
    
    def _select_difficulty_by_distribution(self, distribution: Dict[str, float]) -> str:
        """Select difficulty based on distribution"""
        
        rand = random.random()
        cumulative = 0
        
        for difficulty, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                return difficulty
        
        return "medium"  # fallback
    
    def _select_balanced_topic(self) -> str:
        """Select topic with balanced distribution"""
        
        topics = ["arrays", "strings", "trees", "dynamic_programming", "graphs", "two_pointers"]
        return random.choice(topics)
    
    def _select_questions_for_topic_day(self, topic: str, count: int, day: int, priority_questions: List[str]) -> List[Dict[str, Any]]:
        """Select questions for a specific topic day in study plan"""
        
        questions = []
        
        # Use priority questions first if available
        if priority_questions and day == 0:
            for priority_q in priority_questions[:count]:
                question = {
                    "title": priority_q,
                    "number": str(random.randint(1, 3000)),
                    "link": f"https://leetcode.com/problems/{priority_q.lower().replace(' ', '-')}/",
                    "difficulty": "medium",
                    "topic": topic,
                    "priority": True,
                    "data_source": "curriculum_priority",
                    "generated_at": datetime.now().isoformat()
                }
                questions.append(question)
        
        # Fill remaining with generated questions
        attempts = 0
        max_attempts = count * 2
        
        while len(questions) < count and attempts < max_attempts:
            attempts += 1
            try:
                difficulty = self._select_difficulty_by_distribution(
                    self.difficulty_distribution["intermediate"]
                )
                problems = self._get_problems_from_sources(topic, difficulty, 1)
                if problems:
                    questions.append(problems[0])
            except Exception as e:
                self.logger.error(f"Failed to get question for study plan: {e}")
                # Add emergency fallback
                emergency_q = self._create_emergency_fallback_question(topic, "medium")
                questions.append(emergency_q)
        
        return questions[:count]
    
    def _is_question_recently_sent(self, question: Dict[str, Any]) -> bool:
        """Check if question was recently sent to avoid repetition"""
        
        question_id = f"{question.get('number', '')}-{question.get('title', '')}"
        return question_id in self.sent_questions
    
    def _save_questions_to_memory(self, questions: List[Dict[str, Any]]) -> None:
        """Save sent questions to memory"""
        
        for question in questions:
            question_id = f"{question.get('number', '')}-{question.get('title', '')}"
            self.sent_questions.add(question_id)
        
        # Save to file
        try:
            with open(self.memory_file, 'w') as f:
                json.dump({
                    "sent_questions": list(self.sent_questions),
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save memory: {e}")
    
    def _load_memory(self) -> Set[str]:
        """Load memory of sent questions"""
        
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get("sent_questions", []))
        except Exception as e:
            self.logger.error(f"Failed to load memory: {e}")
        
        return set()
    
    def _format_daily_questions_content(self, questions: List[Dict[str, Any]], request_details: Dict[str, Any]) -> str:
        """Format daily questions for email content"""
        
        content_parts = [
            "🧠 DAILY LEETCODE CHALLENGES",
            "=" * 50,
            f"📅 Date: {datetime.now().strftime('%B %d, %Y')}",
            f"📊 Questions: {len(questions)}",
            f"🎯 Level: {request_details.get('difficulty_level', 'intermediate').title()}",
            "",
        ]
        
        for i, question in enumerate(questions, 1):
            # Add data source indicator
            data_source = question.get('data_source', 'unknown')
            source_indicator = {
                'leetcode_graphql': '🌐',
                'curated_database': '📚', 
                'llm_generated': '🤖',
                'curated_fallback': '📝'
            }.get(data_source, '❓')
            
            content_parts.extend([
                f"PROBLEM #{i}: {question.get('title', 'LeetCode Problem')} {source_indicator}",
                f"🔢 Number: #{question.get('number', 'N/A')}",
                f"🔗 Link: {question.get('link', 'https://leetcode.com')}",
                f"📈 Difficulty: {question.get('difficulty', 'Medium').title()}",
                f"🏷️ Topic: {question.get('topic', 'General').title()}",
                f"🏢 Companies: {question.get('companies', 'Top Tech Companies')}",
                f"🔥 Frequency: {question.get('frequency', 'Medium')}",
                f"📊 Source: {data_source.replace('_', ' ').title()}",
                "",
                "DESCRIPTION:",
                question.get('description', 'Check the LeetCode link for full problem description.'),
                "",
                "TEST CASES:",
                question.get('test_cases', 'See LeetCode for examples and test cases.'),
                "",
                "=" * 50,
                ""
            ])
        
        content_parts.extend([
            "",
            "🔍 DATA SOURCES LEGEND:",
            "🌐 Real LeetCode API  📚 Curated Database  🤖 AI Generated  📝 Fallback  🚨 Emergency  ⭐ Priority",
            "",
            "💡 TIPS:",
            "• Read the problem carefully and understand constraints",
            "• Start with brute force, then optimize", 
            "• Practice explaining your solution out loud",
            "• Time yourself - aim for 20-30 minutes per medium problem",
            "",
            "🎯 Happy Coding! Keep practicing consistently! 🚀"
        ])
        
        return "\n".join(content_parts)
    
    def _format_study_plan_content(self, study_plan: Dict[str, Any], plan_details: Dict[str, Any]) -> str:
        """Format study plan content"""
        
        content_parts = [
            f"🎯 {plan_details['days']}-DAY LEETCODE STUDY PLAN",
            "=" * 50,
            f"📅 Level: {study_plan['level'].title()}",
            f"📊 Questions per day: {study_plan['questions_per_day']}",
            f"🎯 Total questions: {study_plan['questions_per_day'] * study_plan['total_days']}",
            "",
            "DAILY BREAKDOWN:",
            ""
        ]
        
        for day_plan in study_plan['daily_schedule'][:7]:  # Show first week
            content_parts.extend([
                f"Day {day_plan['day']}: {day_plan['topic']}",
                f"Focus: {day_plan['focus']}",
                f"Questions: {len(day_plan['questions'])} problems",
                ""
            ])
        
        if len(study_plan['daily_schedule']) > 7:
            content_parts.append(f"... and {len(study_plan['daily_schedule']) - 7} more days")
        
        content_parts.extend([
            "",
            "📚 CURRICULUM OVERVIEW:",
            "• Structured progression from basics to advanced",
            "• Company-specific high-frequency problems included",
            "• Balanced difficulty distribution",
            "• No repeated questions in your history",
            "",
            "🎯 Start your coding journey today! 🚀"
        ])
        
        return "\n".join(content_parts)
    
    def _format_topic_questions_content(self, questions: List[Dict[str, Any]], topic_details: Dict[str, Any]) -> str:
        """Format topic-specific questions content"""
        
        content_parts = [
            f"🎯 {topic_details['topic'].upper()} LEETCODE PROBLEMS",
            "=" * 50,
            f"📊 Questions: {len(questions)}",
            f"📈 Difficulty: {topic_details['difficulty'].title()}",
            "",
        ]
        
        for i, question in enumerate(questions, 1):
            # Add data source indicator
            data_source = question.get('data_source', 'unknown')
            source_indicator = {
                'leetcode_graphql': '🌐',
                'curated_database': '📚', 
                'llm_generated': '🤖',
                'curated_fallback': '📝'
            }.get(data_source, '❓')
            
            content_parts.extend([
                f"PROBLEM #{i}: {question.get('title', 'LeetCode Problem')} {source_indicator}",
                f"🔢 Number: #{question.get('number', 'N/A')}",
                f"🔗 Link: {question.get('link', 'https://leetcode.com')}",
                f"📈 Difficulty: {question.get('difficulty', 'Medium').title()}",
                f"📊 Source: {data_source.replace('_', ' ').title()}",
                "",
                "=" * 30,
                ""
            ])
        
        return "\n".join(content_parts)
    
    def _format_difficulty_questions_content(self, questions: List[Dict[str, Any]], diff_details: Dict[str, Any]) -> str:
        """Format difficulty-specific questions content"""
        
        content_parts = [
            f"🎯 {diff_details['difficulty'].upper()} LEETCODE PROBLEMS",
            "=" * 50,
            f"📊 Questions: {len(questions)}",
            "",
        ]
        
        for i, question in enumerate(questions, 1):
            # Add data source indicator
            data_source = question.get('data_source', 'unknown')
            source_indicator = {
                'leetcode_graphql': '🌐',
                'curated_database': '📚', 
                'llm_generated': '🤖',
                'curated_fallback': '📝'
            }.get(data_source, '❓')
            
            content_parts.extend([
                f"PROBLEM #{i}: {question.get('title', 'LeetCode Problem')} {source_indicator}",
                f"🔢 Number: #{question.get('number', 'N/A')}",
                f"🔗 Link: {question.get('link', 'https://leetcode.com')}",
                f"🏷️ Topic: {question.get('topic', 'General').title()}",
                f"📊 Source: {data_source.replace('_', ' ').title()}",
                "",
                "=" * 30,
                ""
            ])
        
        return "\n".join(content_parts)
    
    def _format_general_questions_content(self, questions: List[Dict[str, Any]], description: str) -> str:
        """Format general questions content"""
        
        content_parts = [
            "🧠 LEETCODE RECOMMENDATIONS",
            "=" * 50,
            f"📊 Questions: {len(questions)}",
            f"📝 Based on: {description}",
            "",
        ]
        
        for i, question in enumerate(questions, 1):
            # Add data source indicator
            data_source = question.get('data_source', 'unknown')
            source_indicator = {
                'leetcode_graphql': '🌐',
                'curated_database': '📚', 
                'llm_generated': '🤖',
                'curated_fallback': '📝'
            }.get(data_source, '❓')
            
            content_parts.extend([
                f"PROBLEM #{i}: {question.get('title', 'LeetCode Problem')} {source_indicator}",
                f"🔢 Number: #{question.get('number', 'N/A')}",
                f"🔗 Link: {question.get('link', 'https://leetcode.com')}",
                f"📈 Difficulty: {question.get('difficulty', 'Medium').title()}",
                f"🏷️ Topic: {question.get('topic', 'General').title()}",
                f"📊 Source: {data_source.replace('_', ' ').title()}",
                "",
                "=" * 30,
                ""
            ])
        
        return "\n".join(content_parts)


# Example usage and testing
if __name__ == "__main__":
    import os
    import traceback
    from dotenv import load_dotenv
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
    load_dotenv(env_path)
    
    print("🧠 AutoTasker AI - LeetCode Agent Test")
    print("=" * 50)
    
    # Check if OpenRouter API key is available
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OpenRouter API key not found in environment variables")
        print("Please set OPENROUTER_API_KEY in config/.env file")
        sys.exit(1)
    
    print("✅ OpenRouter API key found")
    
    # Test configuration with optional LeetCode session
    config = {
        'llm': {
            'provider': 'openrouter',
            'model': 'meta-llama/llama-3.3-70b-instruct',
            'api_key': api_key
        },
        'agents': {
            'leetcode_agent': {
                'model': 'meta-llama/llama-3.3-70b-instruct',
                'temperature': 0.7
            }
        },
        'leetcode': {
            # Optional: Add your LeetCode session cookie for GraphQL API access
            'session_cookie': os.getenv('LEETCODE_SESSION_COOKIE')  # Reads from .env file
        }
    }
    
    print(f"🤖 Using model: {config['llm']['model']}")
    
    # Check data sources priority
    session_cookie = config.get('leetcode', {}).get('session_cookie')
    print("\n📊 DATA SOURCE PRIORITY ORDER:")
    print("1. 🌐 LeetCode GraphQL API", "(Enabled)" if session_cookie else "(Disabled - no session cookie)")
    print("2. 🤖 LLM Generation (Enabled - first fallback)")
    print("3. 📚 Curated Database (Enabled - final fallback)")
    
    try:
        # Create LeetCode agent
        agent = LeetCodeAgent(config)
        print("\n✅ LeetCode Agent initialized successfully")
        
        # Interactive test menu
        while True:
            print("\n" + "=" * 60)
            print("🧪 SELECT TEST TO RUN:")
            print("=" * 60)
            print("1. 📅 Daily Questions (3 questions)")
            print("2. 📚 Study Plan (20-day plan)")
            print("3. 🏷️  Topic-Specific (arrays, medium)")
            print("4. 📈 Difficulty-Specific (easy problems)")
            print("5. 🔍 Data Source Demo (curated database)")
            print("6. 💾 Memory Status")
            print("7. � Run All Tests")
            print("0. ❌ Exit")
            print("=" * 60)
            
            choice = input("Enter your choice (0-7): ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!")
                break
            elif choice == "1":
                print("\n📝 RUNNING: Daily Questions Test")
                print("=" * 50)
                task = {
                    "description": "Send me 3 LeetCode questions every day at 9 AM to my email, intermediate level"
                }
                
                result = agent.execute_task(task)
                
                if result.get('success'):
                    print("✅ Daily questions generated successfully!")
                    print(f"📊 Generated {result.get('count', 0)} questions")
                    print(f"🎯 Type: {result.get('type')}")
                    print("\n" + "="*60)
                    print("FULL CONTENT OUTPUT:")
                    print("="*60)
                    print(result.get('content', 'No content'))
                    print("="*60)
                    
                    # Show questions data
                    if 'questions' in result:
                        print("\n📋 QUESTIONS DATA:")
                        for i, q in enumerate(result['questions'], 1):
                            print(f"\nQuestion {i}:")
                            for key, value in q.items():
                                print(f"  {key}: {value}")
                else:
                    print(f"❌ Failed: {result.get('error')}")
                    
            elif choice == "2":
                print("\n📝 RUNNING: Study Plan Test")
                print("=" * 50)
                task = {
                    "description": "Create a 20-day LeetCode study plan for intermediate level with 5 questions per day"
                }
                
                result = agent.execute_task(task)
                
                if result.get('success'):
                    print("✅ Study plan generated successfully!")
                    print(f"🎯 Type: {result.get('type')}")
                    print("\n" + "="*60)
                    print("FULL CONTENT OUTPUT:")
                    print("="*60)
                    print(result.get('content', 'No content'))
                    print("="*60)
                    
                    # Show full study plan data
                    if 'study_plan' in result:
                        plan = result['study_plan']
                        print(f"\n📋 FULL STUDY PLAN DATA:")
                        print(f"Total Days: {plan['total_days']}")
                        print(f"Level: {plan['level']}")
                        print(f"Questions per Day: {plan['questions_per_day']}")
                        print(f"Total Schedule Items: {len(plan['daily_schedule'])}")
                        
                        print("\nFIRST 3 DAYS DETAILED:")
                        for day_plan in plan['daily_schedule'][:3]:
                            print(f"\nDay {day_plan['day']}:")
                            print(f"  Topic: {day_plan['topic']}")
                            print(f"  Focus: {day_plan['focus']}")
                            print(f"  Questions: {len(day_plan['questions'])}")
                            for i, q in enumerate(day_plan['questions'][:2], 1):
                                print(f"    {i}. {q.get('title', 'N/A')} ({q.get('data_source', 'unknown')})")
                else:
                    print(f"❌ Failed: {result.get('error')}")
                    
            elif choice == "3":
                print("\n📝 RUNNING: Topic-Specific Test (Arrays, Medium)")
                print("=" * 50)
                task = {
                    "description": "Give me 3 medium arrays problems"
                }
                
                result = agent.execute_task(task)
                
                if result.get('success'):
                    print("✅ Topic questions generated successfully!")
                    print(f"🎯 Type: {result.get('type')}")
                    print(f"📊 Generated {len(result.get('questions', []))} questions")
                    print("\n" + "="*60)
                    print("FULL CONTENT OUTPUT:")
                    print("="*60)
                    print(result.get('content', 'No content'))
                    print("="*60)
                    
                    # Show full questions data
                    if 'questions' in result:
                        print("\n📋 FULL QUESTIONS DATA:")
                        for i, q in enumerate(result['questions'], 1):
                            print(f"\nQuestion {i} - Full Data:")
                            for key, value in q.items():
                                print(f"  {key}: {value}")
                else:
                    print(f"❌ Failed: {result.get('error')}")
                    
            elif choice == "4":
                print("\n📝 RUNNING: Difficulty-Specific Test (Easy)")
                print("=" * 50)
                task = {
                    "description": "Show me 2 easy problems for beginners"
                }
                
                result = agent.execute_task(task)
                
                if result.get('success'):
                    print("✅ Difficulty questions generated successfully!")
                    print(f"🎯 Type: {result.get('type')}")
                    print(f"📊 Generated {len(result.get('questions', []))} questions")
                    print("\n" + "="*60)
                    print("FULL CONTENT OUTPUT:")
                    print("="*60)
                    print(result.get('content', 'No content'))
                    print("="*60)
                else:
                    print(f"❌ Failed: {result.get('error')}")
                    
            elif choice == "5":
                print("\n📝 RUNNING: Data Source Demo")
                print("=" * 50)
                print("🔍 Testing curated database directly:")
                
                print("\n📚 CURATED DATABASE CONTENT:")
                topics = agent.curated_db.get_all_topics()
                print(f"Available topics: {topics}")
                
                for topic in topics:
                    print(f"\n🏷️ {topic.upper()}:")
                    for difficulty in ['easy', 'medium', 'hard']:
                        count = agent.curated_db.get_problem_count(topic, difficulty)
                        if count > 0:
                            print(f"  {difficulty}: {count} problems")
                            # Show all problems for this difficulty
                            problems = agent.curated_db.get_problems(topic, difficulty, count)
                            for i, p in enumerate(problems, 1):
                                print(f"    {i}. {p['title']} (#{p['number']}) - {p['data_source']}")
                
                # Test hybrid data source
                print("\n� TESTING HYBRID DATA SOURCE:")
                test_problems = agent._get_problems_from_sources("arrays", "easy", 2)
                print(f"Retrieved {len(test_problems)} problems:")
                for i, p in enumerate(test_problems, 1):
                    print(f"  {i}. {p['title']} - Source: {p.get('data_source', 'unknown')}")
                    
            elif choice == "6":
                print("\n📝 RUNNING: Memory Status Check")
                print("=" * 50)
                print(f"📊 Questions in memory: {len(agent.sent_questions)}")
                print(f"💾 Memory file: {agent.memory_file}")
                print(f"📂 Memory file exists: {os.path.exists(agent.memory_file)}")
                
                if agent.sent_questions:
                    print("\n🗂️ RECENT QUESTIONS IN MEMORY:")
                    for i, q_id in enumerate(list(agent.sent_questions)[-5:], 1):
                        print(f"  {i}. {q_id}")
                else:
                    print("📭 No questions in memory yet")
                    
            elif choice == "7":
                print("\n📝 RUNNING: All Tests")
                print("=" * 50)
                print("⚠️  Note: This will run all tests sequentially...")
                confirm = input("Continue? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Run tests 1-4 automatically
                    for test_num in ['1', '2', '3', '4']:
                        print(f"\n🔄 Auto-running test {test_num}...")
                        # Simulate selecting each test
                        choice = test_num
                        continue
                else:
                    print("❌ Cancelled")
            else:
                print("❌ Invalid choice. Please enter 0-7.")
            
            input("\n⏸️  Press Enter to continue...")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        traceback.print_exc()
    
    print("\n🎉 LeetCode Agent testing completed!")
