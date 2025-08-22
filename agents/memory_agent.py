"""
Memory Agent: Manages task history and prevents duplicate executions
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend.utils import save_json_file, load_json_file


class MemoryAgent:
    """Agent for managing execution memory and preventing duplicates"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.MemoryAgent")
        
        # Memory configuration
        self.retention_days = config.get("memory", {}).get("retention_days", 30)
        self.similarity_threshold = config.get("memory", {}).get("similarity_threshold", 0.8)
        self.use_vector_store = config.get("memory", {}).get("use_vector_store", False)
        
        # Storage paths
        self.memory_dir = "memory"
        self.execution_history_file = os.path.join(self.memory_dir, "execution_history.json")
        self.prompt_signatures_file = os.path.join(self.memory_dir, "prompt_signatures.json")
        
        # In-memory cache
        self.recent_executions = []
        self.prompt_signatures = {}
        
        # Initialize storage
        self._initialize_memory_storage()
        self._load_memory_data()
    
    def _initialize_memory_storage(self) -> None:
        """Initialize memory storage directories and files"""
        
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Create empty files if they don't exist
        if not os.path.exists(self.execution_history_file):
            save_json_file([], self.execution_history_file)
        
        if not os.path.exists(self.prompt_signatures_file):
            save_json_file({}, self.prompt_signatures_file)
    
    def _load_memory_data(self) -> None:
        """Load memory data from storage"""
        
        try:
            self.recent_executions = load_json_file(self.execution_history_file) or []
            self.prompt_signatures = load_json_file(self.prompt_signatures_file) or {}
            
            # Clean old data
            self._cleanup_old_memory_data()
            
            self.logger.info(f"Loaded {len(self.recent_executions)} execution records from memory")
            
        except Exception as e:
            self.logger.error(f"Failed to load memory data: {e}")
            self.recent_executions = []
            self.prompt_signatures = {}
    
    def check_recent_execution(self, prompt: str) -> Dict[str, Any]:
        """
        Check if a similar task was executed recently
        
        Args:
            prompt: The prompt to check
            
        Returns:
            Memory check results
        """
        
        try:
            # Generate prompt signature
            prompt_signature = self._generate_prompt_signature(prompt)
            
            # Check for exact matches first
            exact_match = self._find_exact_match(prompt_signature)
            if exact_match:
                return {
                    "should_skip": True,
                    "reason": "Exact prompt executed recently",
                    "last_execution": exact_match,
                    "similarity": 1.0,
                    "match_type": "exact"
                }
            
            # Check for similar prompts
            similar_match = self._find_similar_execution(prompt)
            if similar_match:
                similarity = similar_match["similarity"]
                
                if similarity >= self.similarity_threshold:
                    return {
                        "should_skip": True,
                        "reason": f"Similar prompt (similarity: {similarity:.2f}) executed recently",
                        "last_execution": similar_match["execution"],
                        "similarity": similarity,
                        "match_type": "similar"
                    }
                else:
                    return {
                        "should_skip": False,
                        "reason": f"Similar prompt found but below threshold (similarity: {similarity:.2f})",
                        "similar_execution": similar_match["execution"],
                        "similarity": similarity,
                        "match_type": "below_threshold"
                    }
            
            # No matches found
            return {
                "should_skip": False,
                "reason": "No recent similar executions found",
                "similarity": 0.0,
                "match_type": "none"
            }
            
        except Exception as e:
            self.logger.error(f"Memory check failed: {e}")
            return {
                "should_skip": False,
                "reason": f"Memory check error: {str(e)}",
                "error": True
            }
    
    def record_execution(self, execution_data: Dict[str, Any]) -> None:
        """
        Record a new execution in memory
        
        Args:
            execution_data: Execution data to record
        """
        
        try:
            # Generate prompt signature
            prompt = execution_data.get("prompt", "")
            prompt_signature = self._generate_prompt_signature(prompt)
            
            # Create memory record
            memory_record = {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "prompt_signature": prompt_signature,
                "task_plan": execution_data.get("task_plan", {}),
                "success": len(execution_data.get("errors", [])) == 0,
                "execution_id": execution_data.get("execution_id", "unknown"),
                "duration": execution_data.get("duration", "unknown"),
                "agent_types": self._extract_agent_types(execution_data)
            }
            
            # Add to recent executions
            self.recent_executions.insert(0, memory_record)
            
            # Update prompt signatures
            self.prompt_signatures[prompt_signature] = {
                "first_seen": memory_record["timestamp"],
                "last_seen": memory_record["timestamp"],
                "count": self.prompt_signatures.get(prompt_signature, {}).get("count", 0) + 1,
                "success_count": self.prompt_signatures.get(prompt_signature, {}).get("success_count", 0) + (1 if memory_record["success"] else 0)
            }
            
            # Save to storage
            self._save_memory_data()
            
            self.logger.info(f"Recorded execution in memory: {execution_data.get('execution_id', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to record execution: {e}")
    
    def _generate_prompt_signature(self, prompt: str) -> str:
        """Generate a signature for prompt matching"""
        
        # Normalize prompt
        normalized = prompt.lower().strip()
        
        # Remove common variations
        normalized = normalized.replace("every day", "daily")
        normalized = normalized.replace("each day", "daily")
        normalized = normalized.replace(" at ", " ")
        normalized = normalized.replace("am", "")
        normalized = normalized.replace("pm", "")
        
        # Remove time patterns
        import re
        normalized = re.sub(r'\d{1,2}:\d{2}', '', normalized)
        normalized = re.sub(r'\d{1,2}\s*(am|pm)', '', normalized)
        
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _find_exact_match(self, prompt_signature: str) -> Optional[Dict[str, Any]]:
        """Find exact prompt signature match in recent history"""
        
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        for execution in self.recent_executions:
            execution_time = datetime.fromisoformat(execution["timestamp"])
            
            if execution_time < cutoff_time:
                continue
            
            if execution.get("prompt_signature") == prompt_signature:
                return execution
        
        return None
    
    def _find_similar_execution(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Find similar executions using text similarity"""
        
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        best_match = None
        best_similarity = 0.0
        
        for execution in self.recent_executions:
            execution_time = datetime.fromisoformat(execution["timestamp"])
            
            if execution_time < cutoff_time:
                continue
            
            # Calculate similarity
            similarity = self._calculate_text_similarity(prompt, execution.get("prompt", ""))
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = execution
        
        if best_match and best_similarity > 0.5:  # Minimum similarity for consideration
            return {
                "execution": best_match,
                "similarity": best_similarity
            }
        
        return None
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_agent_types(self, execution_data: Dict[str, Any]) -> List[str]:
        """Extract agent types used in execution"""
        
        agent_types = set()
        
        # Check task plan for agent hints
        task_plan = execution_data.get("task_plan", {})
        tasks = task_plan.get("tasks", [])
        
        for task in tasks:
            task_type = task.get("type", "")
            if task_type:
                agent_types.add(task_type)
        
        # Check execution results for agent evidence
        execution_results = execution_data.get("execution_results", {})
        for key in execution_results.keys():
            if "gmail" in key:
                agent_types.add("gmail")
            elif "github" in key:
                agent_types.add("github")
            elif "dsa" in key:
                agent_types.add("dsa")
            elif "email" in key:
                agent_types.add("email")
        
        return list(agent_types)
    
    def _cleanup_old_memory_data(self) -> None:
        """Clean up old memory data"""
        
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        
        # Filter recent executions
        filtered_executions = []
        for execution in self.recent_executions:
            try:
                execution_time = datetime.fromisoformat(execution["timestamp"])
                if execution_time >= cutoff_time:
                    filtered_executions.append(execution)
            except (ValueError, KeyError):
                # Skip invalid entries
                continue
        
        # Update if anything was cleaned
        if len(filtered_executions) != len(self.recent_executions):
            old_count = len(self.recent_executions)
            self.recent_executions = filtered_executions
            self.logger.info(f"Cleaned up {old_count - len(filtered_executions)} old memory records")
        
        # Clean up prompt signatures that are no longer referenced
        active_signatures = {exec.get("prompt_signature") for exec in self.recent_executions}
        old_signatures = set(self.prompt_signatures.keys()) - active_signatures
        
        for signature in old_signatures:
            del self.prompt_signatures[signature]
    
    def _save_memory_data(self) -> None:
        """Save memory data to storage"""
        
        try:
            save_json_file(self.recent_executions, self.execution_history_file)
            save_json_file(self.prompt_signatures, self.prompt_signatures_file)
        except Exception as e:
            self.logger.error(f"Failed to save memory data: {e}")
    
    def get_execution_patterns(self) -> Dict[str, Any]:
        """
        Analyze execution patterns from memory
        
        Returns:
            Pattern analysis results
        """
        
        if not self.recent_executions:
            return {
                "total_executions": 0,
                "patterns": []
            }
        
        # Analyze patterns
        patterns = {
            "most_common_agents": self._analyze_agent_usage(),
            "success_patterns": self._analyze_success_patterns(),
            "time_patterns": self._analyze_time_patterns(),
            "prompt_patterns": self._analyze_prompt_patterns()
        }
        
        return {
            "total_executions": len(self.recent_executions),
            "patterns": patterns,
            "retention_period_days": self.retention_days
        }
    
    def _analyze_agent_usage(self) -> Dict[str, int]:
        """Analyze which agents are used most frequently"""
        
        agent_counts = {}
        
        for execution in self.recent_executions:
            for agent_type in execution.get("agent_types", []):
                agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
        
        # Sort by usage
        return dict(sorted(agent_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_success_patterns(self) -> Dict[str, Any]:
        """Analyze success/failure patterns"""
        
        total = len(self.recent_executions)
        successful = len([e for e in self.recent_executions if e.get("success", False)])
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "failure_rate": ((total - successful) / total * 100) if total > 0 else 0
        }
    
    def _analyze_time_patterns(self) -> Dict[str, Any]:
        """Analyze execution time patterns"""
        
        if not self.recent_executions:
            return {}
        
        # Group by hour of day
        hour_counts = {}
        
        for execution in self.recent_executions:
            try:
                timestamp = datetime.fromisoformat(execution["timestamp"])
                hour = timestamp.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except (ValueError, KeyError):
                continue
        
        # Find peak hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "executions_by_hour": hour_counts,
            "peak_hours": sorted_hours[:3] if sorted_hours else [],
            "total_unique_hours": len(hour_counts)
        }
    
    def _analyze_prompt_patterns(self) -> Dict[str, Any]:
        """Analyze prompt patterns and frequencies"""
        
        # Analyze most common words
        all_words = []
        for execution in self.recent_executions:
            prompt = execution.get("prompt", "").lower()
            words = prompt.split()
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = {}
        for word in all_words:
            if len(word) > 3:  # Only count meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get most common words
        common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_words": len(all_words),
            "unique_words": len(word_counts),
            "most_common_words": common_words,
            "unique_prompt_signatures": len(self.prompt_signatures)
        }
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force cleanup of all memory data"""
        
        old_executions = len(self.recent_executions)
        old_signatures = len(self.prompt_signatures)
        
        self.recent_executions = []
        self.prompt_signatures = {}
        
        self._save_memory_data()
        
        return {
            "cleaned_executions": old_executions,
            "cleaned_signatures": old_signatures,
            "timestamp": datetime.now().isoformat()
        }
