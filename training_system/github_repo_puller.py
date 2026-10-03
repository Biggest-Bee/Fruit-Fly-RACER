"""
GitHub Repository Puller
Handles pulling repositories from GitHub using the rate limiter to stay within API limits.
"""

import os
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .github_rate_limiter import GitHubRateLimiter


class GitHubRepoPuller:
    """
    Pulls repositories from GitHub with rate limit management.
    """
    
    def __init__(self, rate_limiter: GitHubRateLimiter, workspace_dir: str = "github_repos"):
        """
        Initialize the GitHub repo puller.
        
        Args:
            rate_limiter: GitHubRateLimiter instance for managing API limits
            workspace_dir: Directory to store cloned repositories
        """
        self.rate_limiter = rate_limiter
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        self.cloned_repos: Dict[str, str] = {}  # repo_url -> local_path
        
        print(f"GitHub Repo Puller initialized with workspace: {self.workspace_dir}")
    
    def _get_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        return repo_url.split("/")[-1]
    
    def _get_owner(self, repo_url: str) -> str:
        """Extract owner from repository URL."""
        parts = repo_url.rstrip("/").replace(".git", "").split("/")
        return parts[-2] if len(parts) >= 2 else "unknown"
    
    def clone_repository(self, repo_url: str, branch: Optional[str] = None,
                        depth: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Clone a repository from GitHub.
        
        Args:
            repo_url: GitHub repository URL
            branch: Optional branch to clone
            depth: Optional clone depth (shallow clone)
            
        Returns:
            (success, message, local_path) - success status, message, and local path if successful
        """
        # Check rate limits before cloning
        can_make, wait_time, reason = self.rate_limiter.can_make_request(
            "clone_repo", endpoint="clone"
        )
        
        if not can_make:
            return False, f"Rate limit exceeded: {reason}", None
        
        # Start the request
        self.rate_limiter.start_request()
        
        try:
            repo_name = self._get_repo_name(repo_url)
            local_path = self.workspace_dir / repo_name
            
            # Remove existing clone if it exists
            if local_path.exists():
                shutil.rmtree(local_path)
            
            # Build git clone command
            cmd = ["git", "clone"]
            
            if branch:
                cmd.extend(["--branch", branch])
            
            if depth:
                cmd.extend(["--depth", str(depth)])
            
            cmd.append(repo_url)
            cmd.append(str(local_path))
            
            # Execute clone
            print(f"Cloning {repo_url}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.cloned_repos[repo_url] = str(local_path)
                self.rate_limiter.record_secondary_request("clone_repo", "clone")
                return True, f"Successfully cloned {repo_name}", str(local_path)
            else:
                return False, f"Clone failed: {result.stderr}", None
            
        except subprocess.TimeoutExpired:
            return False, "Clone operation timed out", None
        except Exception as e:
            return False, f"Clone error: {str(e)}", None
        finally:
            self.rate_limiter.finish_request()
    
    def search_repositories(self, query: str, language: Optional[str] = None,
                          sort: str = "stars", order: str = "desc",
                          per_page: int = 10) -> Tuple[bool, List[Dict], str]:
        """
        Search for repositories on GitHub.
        
        Args:
            query: Search query
            language: Optional language filter
            sort: Sort by (stars, forks, updated)
            order: Order (asc, desc)
            per_page: Number of results per page
            
        Returns:
            (success, results, message) - success status, list of repo info, and message
        """
        # This would use GitHub API for search
        # For now, return a placeholder
        self.rate_limiter.make_request("search", is_search=True, endpoint="search")
        self.rate_limiter.finish_request()
        
        return True, [], "Search API not yet implemented (requires GitHub API client)"
    
    def get_repository_info(self, repo_url: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Get information about a repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            (success, repo_info, message) - success status, repo info dict, and message
        """
        can_make, wait_time, reason = self.rate_limiter.can_make_request(
            "get_repo", endpoint="repositories"
        )
        
        if not can_make:
            return False, None, f"Rate limit exceeded: {reason}"
        
        self.rate_limiter.make_request("get_repo", endpoint="repositories")
        
        # Placeholder - would use GitHub API
        repo_info = {
            "name": self._get_repo_name(repo_url),
            "owner": self._get_owner(repo_url),
            "url": repo_url,
            "clone_url": repo_url
        }
        
        self.rate_limiter.finish_request()
        
        return True, repo_info, "Repository info retrieved"
    
    def get_file_contents(self, repo_url: str, file_path: str) -> Tuple[bool, Optional[str], str]:
        """
        Get contents of a file from a repository.
        
        Args:
            repo_url: GitHub repository URL
            file_path: Path to file within repository
            
        Returns:
            (success, content, message) - success status, file content, and message
        """
        repo_name = self._get_repo_name(repo_url)
        local_path = self.cloned_repos.get(repo_url)
        
        if not local_path:
            # Try to clone first
            success, message, path = self.clone_repository(repo_url)
            if not success:
                return False, None, message
            local_path = path
        
        try:
            file_full_path = Path(local_path) / file_path
            if not file_full_path.exists():
                return False, None, f"File not found: {file_path}"
            
            with open(file_full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.rate_limiter.make_request("get_file", endpoint="contents")
            self.rate_limiter.finish_request()
            
            return True, content, f"Successfully read {file_path}"
            
        except Exception as e:
            return False, None, f"Error reading file: {str(e)}"
    
    def list_repository_files(self, repo_url: str, path: str = "") -> Tuple[bool, List[str], str]:
        """
        List files in a repository directory.
        
        Args:
            repo_url: GitHub repository URL
            path: Path within repository (empty for root)
            
        Returns:
            (success, files, message) - success status, list of file paths, and message
        """
        repo_name = self._get_repo_name(repo_url)
        local_path = self.cloned_repos.get(repo_url)
        
        if not local_path:
            success, message, path = self.clone_repository(repo_url)
            if not success:
                return False, [], message
            local_path = path
        
        try:
            dir_path = Path(local_path) / path if path else Path(local_path)
            if not dir_path.exists() or not dir_path.is_dir():
                return False, [], f"Directory not found: {path}"
            
            files = []
            for item in dir_path.iterdir():
                relative_path = item.relative_to(local_path)
                files.append(str(relative_path))
            
            self.rate_limiter.make_request("get_contents", endpoint="contents")
            self.rate_limiter.finish_request()
            
            return True, files, f"Listed {len(files)} items"
            
        except Exception as e:
            return False, [], f"Error listing files: {str(e)}"
    
    def get_commit_history(self, repo_url: str, max_count: int = 10) -> Tuple[bool, List[Dict], str]:
        """
        Get commit history for a repository.
        
        Args:
            repo_url: GitHub repository URL
            max_count: Maximum number of commits to retrieve
            
        Returns:
            (success, commits, message) - success status, list of commit info, and message
        """
        repo_name = self._get_repo_name(repo_url)
        local_path = self.cloned_repos.get(repo_url)
        
        if not local_path:
            success, message, path = self.clone_repository(repo_url)
            if not success:
                return False, [], message
            local_path = path
        
        try:
            cmd = ["git", "-C", local_path, "log", f"-{max_count}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return False, [], f"Git log failed: {result.stderr}"
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        })
            
            self.rate_limiter.make_request("list_commits", endpoint="commits")
            self.rate_limiter.finish_request()
            
            return True, commits, f"Retrieved {len(commits)} commits"
            
        except Exception as e:
            return False, [], f"Error getting commit history: {str(e)}"
    
    def cleanup_repository(self, repo_url: str) -> bool:
        """
        Remove a cloned repository from local storage.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            True if cleanup was successful
        """
        repo_name = self._get_repo_name(repo_url)
        local_path = self.cloned_repos.get(repo_url)
        
        if local_path and Path(local_path).exists():
            try:
                shutil.rmtree(local_path)
                del self.cloned_repos[repo_url]
                print(f"Cleaned up {repo_name}")
                return True
            except Exception as e:
                print(f"Error cleaning up {repo_name}: {e}")
                return False
        
        return False
    
    def cleanup_all(self):
        """Remove all cloned repositories."""
        for repo_url in list(self.cloned_repos.keys()):
            self.cleanup_repository(repo_url)
    
    def get_status(self) -> Dict:
        """Get current status of the repo puller."""
        return {
            "workspace_dir": str(self.workspace_dir),
            "cloned_repos": len(self.cloned_repos),
            "repositories": list(self.cloned_repos.keys()),
            "rate_limiter_status": self.rate_limiter.get_status()
        }


if __name__ == "__main__":
    # Test the GitHub repo puller
    print("Testing GitHub Repo Puller...")
    
    # Create rate limiter
    rate_limiter = GitHubRateLimiter(authenticated=True)
    
    # Create repo puller
    puller = GitHubRepoPuller(rate_limiter, workspace_dir="test_repos")
    
    # Test getting repository info
    print("\nTesting get_repository_info...")
    success, repo_info, message = puller.get_repository_info(
        "https://github.com/torvalds/linux"
    )
    print(f"  Success: {success}")
    print(f"  Message: {message}")
    if repo_info:
        print(f"  Repo info: {repo_info}")
    
    # Test status
    print("\nCurrent status:")
    status = puller.get_status()
    print(status)
    
    # Cleanup
    puller.cleanup_all()
    
    print("\nGitHub Repo Puller test completed!")
