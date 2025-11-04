"""
GitHub Agent: Handles GitHub API operations for repository data, commits, and issues
"""

import logging
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from backend.utils import retry_on_failure


class GitHubAgent:
    """Agent for GitHub operations - fetching commits, issues, and repository data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.GitHubAgent")
        
        # GitHub configuration - check environment variable first, then config
        self.github_token = os.getenv("GITHUB_TOKEN") or config.get("github", {}).get("token") or config.get("github_token")
        self.base_url = "https://api.github.com"
        
        # Set up headers for API requests
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutoTasker-AI/1.0"
        }
        
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
            self.logger.info("GitHub token configured")
            
            # Try to get authenticated user info for smart defaults
            self.authenticated_user = self._get_authenticated_user()
            self.user_repos = None  # Lazy load when needed
        else:
            self.logger.warning("GitHub token not configured - limited functionality available")
            self.authenticated_user = None
            self.user_repos = None
    
    def _get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """Get information about the authenticated GitHub user"""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            user_data = response.json()
            
            self.logger.info(f"Authenticated as GitHub user: {user_data.get('login')}")
            return user_data
            
        except Exception as e:
            self.logger.warning(f"Could not fetch authenticated user info: {e}")
            return None
    
    def _get_user_recent_repo(self) -> Optional[str]:
        """Get the most recently updated repository for the authenticated user"""
        if not self.authenticated_user:
            return None
        
        try:
            username = self.authenticated_user.get("login")
            response = requests.get(
                f"{self.base_url}/users/{username}/repos",
                headers=self.headers,
                params={"sort": "updated", "per_page": 1},
                timeout=10
            )
            response.raise_for_status()
            repos = response.json()
            
            if repos and len(repos) > 0:
                repo_full_name = repos[0].get("full_name")
                self.logger.info(f"Using most recent repository: {repo_full_name}")
                return repo_full_name
            
        except Exception as e:
            self.logger.warning(f"Could not fetch user repositories: {e}")
        
        return None
    
    @retry_on_failure(max_retries=3)
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a GitHub-related task
        
        Args:
            task: Task configuration with parameters
            
        Returns:
            Task execution results
        """
        
        try:
            parameters = task.get("parameters", {})
            operation = parameters.get("operation", "get_commits")
            
            # Route to appropriate operation
            if operation == "get_commits":
                return self.get_repository_commits(parameters)
            elif operation == "get_issues":
                return self.get_repository_issues(parameters)
            elif operation == "get_repo_info":
                return self.get_repository_info(parameters)
            elif operation == "get_user_repos":
                return self.get_user_repositories(parameters)
            elif operation == "search_repositories":
                return self.search_repositories(parameters)
            else:
                return self._generate_mock_github_data(parameters)
                
        except Exception as e:
            self.logger.error(f"GitHub task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Failed to execute GitHub task: {e}"
            }
    
    def get_repository_commits(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get commits from a repository"""
        try:
            repo = parameters.get("repository", "")
            
            # Smart repository detection
            if not repo or repo == "user/repo" or repo == "":
                # Try to get from authenticated user's recent repos
                repo = self._get_user_recent_repo()
                
                if not repo:
                    # Try environment variables first
                    env_owner = os.getenv("GITHUB_DEFAULT_OWNER")
                    env_repo = os.getenv("GITHUB_DEFAULT_REPO")
                    
                    if env_owner and env_repo and env_owner != "your-username":
                        repo = f"{env_owner}/{env_repo}"
                    else:
                        # Try config defaults as fallback
                        github_config = self.config.get("github", {})
                        default_owner = github_config.get("default_owner")
                        default_repo = github_config.get("default_repo")
                        
                        if default_owner and default_repo and default_owner != "your-username":
                            repo = f"{default_owner}/{default_repo}"
                
                if not repo:
                    raise ValueError(
                        "Repository parameter is required. Please either:\n"
                        "1. Set GITHUB_DEFAULT_OWNER and GITHUB_DEFAULT_REPO in .env\n"
                        "2. Configure github.default_owner and github.default_repo in config.yaml\n"
                        "3. Specify repository name in your prompt (e.g., 'Hemesh11/Autotasker-AI')"
                    )
            
            # Handle wildcard pattern (username/*) - get most recent repo for that user
            if "/*" in repo:
                username = repo.split("/")[0]
                try:
                    response = requests.get(
                        f"{self.base_url}/users/{username}/repos",
                        headers=self.headers,
                        params={"sort": "updated", "per_page": 1},
                        timeout=10
                    )
                    response.raise_for_status()
                    repos = response.json()
                    
                    if repos and len(repos) > 0:
                        repo = repos[0].get("full_name")
                        self.logger.info(f"Auto-detected repository for {username}: {repo}")
                    else:
                        raise ValueError(f"No repositories found for user {username}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to auto-detect repository: {e}")
                    raise ValueError(f"Could not find repositories for user {username}")
            
            # Parse repository (owner/repo format)
            if "/" not in repo:
                raise ValueError("Repository must be in 'owner/repo' format")
            
            owner, repo_name = repo.split("/", 1)
            
            # Build API URL
            url = f"{self.base_url}/repos/{owner}/{repo_name}/commits"
            
            # Optional parameters
            params = {}
            if parameters.get("since"):
                params["since"] = parameters["since"]
            if parameters.get("until"):
                params["until"] = parameters["until"]
            if parameters.get("author"):
                params["author"] = parameters["author"]
            
            # Limit results
            params["per_page"] = min(parameters.get("limit", 10), 100)
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            commits = response.json()
            
            # Format commit data
            formatted_commits = []
            for commit in commits:
                formatted_commits.append({
                    "sha": commit["sha"][:8],
                    "message": commit["commit"]["message"].split("\n")[0],  # First line only
                    "author": commit["commit"]["author"]["name"],
                    "date": commit["commit"]["author"]["date"],
                    "url": commit["html_url"]
                })
            
            return {
                "success": True,
                "content": f"Retrieved {len(formatted_commits)} commits from {repo}",
                "data": {
                    "repository": repo,
                    "commits": formatted_commits,
                    "total_commits": len(formatted_commits)
                }
            }
            
        except requests.RequestException as e:
            if not self.github_token:
                return self._generate_mock_commits_data(parameters)
            
            self.logger.error(f"GitHub API request failed: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e}",
                "content": f"Failed to fetch commits: {e}"
            }
        except Exception as e:
            self.logger.error(f"Commit fetching failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Error fetching commits: {e}"
            }
    
    def get_repository_issues(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get issues from a repository"""
        try:
            repo = parameters.get("repository")
            if not repo:
                raise ValueError("Repository parameter is required")
            
            owner, repo_name = repo.split("/", 1)
            url = f"{self.base_url}/repos/{owner}/{repo_name}/issues"
            
            params = {
                "state": parameters.get("state", "open"),
                "per_page": min(parameters.get("limit", 10), 100)
            }
            
            if parameters.get("labels"):
                params["labels"] = parameters["labels"]
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            issues = response.json()
            
            # Format issue data
            formatted_issues = []
            for issue in issues:
                # Skip pull requests (they appear as issues in GitHub API)
                if "pull_request" in issue:
                    continue
                    
                formatted_issues.append({
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "author": issue["user"]["login"],
                    "created_at": issue["created_at"],
                    "url": issue["html_url"],
                    "labels": [label["name"] for label in issue.get("labels", [])]
                })
            
            return {
                "success": True,
                "content": f"Retrieved {len(formatted_issues)} issues from {repo}",
                "data": {
                    "repository": repo,
                    "issues": formatted_issues,
                    "total_issues": len(formatted_issues)
                }
            }
            
        except requests.RequestException as e:
            if not self.github_token:
                return self._generate_mock_issues_data(parameters)
            
            self.logger.error(f"GitHub API request failed: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e}",
                "content": f"Failed to fetch issues: {e}"
            }
        except Exception as e:
            self.logger.error(f"Issue fetching failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Error fetching issues: {e}"
            }
    
    def get_repository_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository information"""
        try:
            repo = parameters.get("repository")
            if not repo:
                raise ValueError("Repository parameter is required")
            
            owner, repo_name = repo.split("/", 1)
            url = f"{self.base_url}/repos/{owner}/{repo_name}"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            repo_data = response.json()
            
            repo_info = {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data.get("description", "No description"),
                "language": repo_data.get("language"),
                "stars": repo_data["stargazers_count"],
                "forks": repo_data["forks_count"],
                "open_issues": repo_data["open_issues_count"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
                "url": repo_data["html_url"],
                "clone_url": repo_data["clone_url"]
            }
            
            return {
                "success": True,
                "content": f"Repository info for {repo}",
                "data": repo_info
            }
            
        except requests.RequestException as e:
            if not self.github_token:
                return self._generate_mock_repo_data(parameters)
            
            self.logger.error(f"GitHub API request failed: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e}",
                "content": f"Failed to fetch repository info: {e}"
            }
        except Exception as e:
            self.logger.error(f"Repository info fetching failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Error fetching repository info: {e}"
            }
    
    def get_user_repositories(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get repositories for a user"""
        try:
            username = parameters.get("username")
            if not username:
                raise ValueError("Username parameter is required")
            
            url = f"{self.base_url}/users/{username}/repos"
            
            params = {
                "per_page": min(parameters.get("limit", 10), 100),
                "sort": parameters.get("sort", "updated"),
                "type": parameters.get("type", "owner")
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            repos = response.json()
            
            # Format repository data
            formatted_repos = []
            repo_list_lines = []
            
            for i, repo in enumerate(repos, 1):
                formatted_repo = {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description") or "No description",
                    "language": repo.get("language") or "Not specified",
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "updated_at": repo["updated_at"],
                    "url": repo["html_url"]
                }
                formatted_repos.append(formatted_repo)
                
                # Create readable line for content
                repo_list_lines.append(
                    f"{i}. {repo['name']}\n"
                    f"   Language: {formatted_repo['language']}, "
                    f"Stars: {formatted_repo['stars']}, Forks: {formatted_repo['forks']}\n"
                    f"   URL: {formatted_repo['url']}"
                )
            
            # Create detailed content string
            content_parts = [
                f"Retrieved {len(formatted_repos)} repositories for {username}:",
                "",
                "\n\n".join(repo_list_lines)
            ]
            
            return {
                "success": True,
                "content": "\n".join(content_parts),
                "data": {
                    "username": username,
                    "repositories": formatted_repos,
                    "total_repos": len(formatted_repos)
                }
            }
            
        except requests.RequestException as e:
            if not self.github_token:
                return self._generate_mock_user_repos_data(parameters)
            
            self.logger.error(f"GitHub API request failed: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e}",
                "content": f"Failed to fetch user repositories: {e}"
            }
        except Exception as e:
            self.logger.error(f"User repositories fetching failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Error fetching user repositories: {e}"
            }
    
    def search_repositories(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for repositories"""
        try:
            query = parameters.get("query")
            if not query:
                raise ValueError("Query parameter is required")
            
            url = f"{self.base_url}/search/repositories"
            
            params = {
                "q": query,
                "per_page": min(parameters.get("limit", 10), 100),
                "sort": parameters.get("sort", "stars"),
                "order": parameters.get("order", "desc")
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            search_results = response.json()
            repos = search_results.get("items", [])
            
            # Format search results
            formatted_repos = []
            for repo in repos:
                formatted_repos.append({
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", "No description"),
                    "language": repo.get("language"),
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "score": repo["score"],
                    "url": repo["html_url"]
                })
            
            return {
                "success": True,
                "content": f"Found {len(formatted_repos)} repositories for query: {query}",
                "data": {
                    "query": query,
                    "repositories": formatted_repos,
                    "total_count": search_results.get("total_count", len(formatted_repos))
                }
            }
            
        except requests.RequestException as e:
            self.logger.error(f"GitHub search failed: {e}")
            return {
                "success": False,
                "error": f"GitHub search error: {e}",
                "content": f"Failed to search repositories: {e}"
            }
        except Exception as e:
            self.logger.error(f"Repository search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"Error searching repositories: {e}"
            }
    
    def _generate_mock_github_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock GitHub data for testing"""
        
        time_range = parameters.get("time_range", "1d")
        max_results = parameters.get("max_results", 5)
        
        # Mock commit data
        mock_commits = []
        for i in range(min(max_results, 5)):
            mock_commits.append({
                "sha": f"abc123{i}",
                "commit": {
                    "message": f"Mock commit {i+1}: Updated feature implementation",
                    "author": {
                        "name": "Developer",
                        "date": (datetime.now() - timedelta(hours=i*2)).isoformat()
                    }
                },
                "author": {
                    "login": "developer"
                }
            })
        
        content = self._format_github_summary(mock_commits)
        
        return {
            "success": True,
            "count": len(mock_commits),
            "content": content,
            "commits": mock_commits,
            "time_range": time_range,
            "mock_data": True
        }
    
    def _format_github_summary(self, commits: List[Dict[str, Any]]) -> str:
        """Format GitHub commits into readable summary"""
        
        if not commits:
            return "No GitHub commits found."
        
        summary_parts = [
            f"=== GITHUB COMMIT SUMMARY ({len(commits)} commits) ===\n"
        ]
        
        for i, commit in enumerate(commits, 1):
            commit_data = commit.get("commit", {})
            author_data = commit_data.get("author", {})
            
            summary_parts.extend([
                f"{i}. COMMIT: {commit.get('sha', 'unknown')[:8]}",
                f"   AUTHOR: {author_data.get('name', 'Unknown')}",
                f"   DATE: {author_data.get('date', 'Unknown')}",
                f"   MESSAGE: {commit_data.get('message', 'No message')}",
                ""
            ])
        
        return "\n".join(summary_parts)
    
    def fetch_commits(self, repo: str, time_range: str = "1d") -> List[Dict[str, Any]]:
        """Fetch recent commits (mock implementation)"""
        
        self.logger.info(f"Fetching commits for {repo} (mock data)")
        
        # Return mock data for now
        return self._generate_mock_github_data({"time_range": time_range})["commits"]
    
    def fetch_issues(self, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """Fetch repository issues (mock implementation)"""
        
        self.logger.info(f"Fetching {state} issues for {repo} (mock data)")
        
        # Mock issue data
        return [
            {
                "number": 1,
                "title": "Mock Issue 1",
                "state": state,
                "body": "This is a mock issue for testing purposes",
                "created_at": datetime.now().isoformat()
            }
        ]
    
    def _generate_mock_commits_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock commit data when GitHub token is not available"""
        repo = parameters.get("repository", "user/repo")
        limit = parameters.get("limit", 5)
        
        mock_commits = []
        for i in range(limit):
            mock_commits.append({
                "sha": f"abc123{i:02d}",
                "message": f"Mock commit {i+1}: Updated feature implementation",
                "author": "MockDeveloper",
                "date": (datetime.now() - timedelta(hours=i*6)).isoformat(),
                "url": f"https://github.com/{repo}/commit/abc123{i:02d}"
            })
        
        return {
            "success": True,
            "content": f"Retrieved {len(mock_commits)} commits from {repo} (mock data)",
            "data": {
                "repository": repo,
                "commits": mock_commits,
                "total_commits": len(mock_commits)
            },
            "mock_data": True
        }
    
    def _generate_mock_issues_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock issue data when GitHub token is not available"""
        repo = parameters.get("repository", "user/repo")
        limit = parameters.get("limit", 5)
        state = parameters.get("state", "open")
        
        mock_issues = []
        for i in range(limit):
            mock_issues.append({
                "number": i + 1,
                "title": f"Mock Issue {i+1}: Feature Request",
                "state": state,
                "author": "MockUser",
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "url": f"https://github.com/{repo}/issues/{i+1}",
                "labels": ["enhancement", "mock"] if i % 2 == 0 else ["bug", "mock"]
            })
        
        return {
            "success": True,
            "content": f"Retrieved {len(mock_issues)} issues from {repo} (mock data)",
            "data": {
                "repository": repo,
                "issues": mock_issues,
                "total_issues": len(mock_issues)
            },
            "mock_data": True
        }
    
    def _generate_mock_repo_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock repository data when GitHub token is not available"""
        repo = parameters.get("repository", "user/repo")
        
        repo_info = {
            "name": repo.split("/")[-1],
            "full_name": repo,
            "description": "Mock repository for AutoTasker AI testing",
            "language": "Python",
            "stars": 42,
            "forks": 7,
            "open_issues": 3,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": datetime.now().isoformat(),
            "url": f"https://github.com/{repo}",
            "clone_url": f"https://github.com/{repo}.git"
        }
        
        return {
            "success": True,
            "content": f"Repository info for {repo} (mock data)",
            "data": repo_info,
            "mock_data": True
        }
    
    def _generate_mock_user_repos_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock user repositories when GitHub token is not available"""
        username = parameters.get("username", "mockuser")
        limit = parameters.get("limit", 5)
        
        mock_repos = []
        for i in range(limit):
            mock_repos.append({
                "name": f"mock-repo-{i+1}",
                "full_name": f"{username}/mock-repo-{i+1}",
                "description": f"Mock repository {i+1} for testing",
                "language": ["Python", "JavaScript", "Java", "Go", "Rust"][i % 5],
                "stars": (i + 1) * 10,
                "forks": i + 1,
                "updated_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "url": f"https://github.com/{username}/mock-repo-{i+1}"
            })
        
        return {
            "success": True,
            "content": f"Retrieved {len(mock_repos)} repositories for {username} (mock data)",
            "data": {
                "username": username,
                "repositories": mock_repos,
                "total_repos": len(mock_repos)
            },
            "mock_data": True
        }
