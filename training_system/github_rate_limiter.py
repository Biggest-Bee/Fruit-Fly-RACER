"""
GitHub API Rate Limit Manager
Manages GitHub API rate limits for search and general API calls according to GitHub's rate limiting policies.

Rate Limits:
- Search API:
  * Authenticated: 30 requests per minute
  * Unauthenticated: 10 requests per minute

- General API (repos, files, commits, stats):
  * Authenticated: 5,000 requests per hour (83/min average)
  * Unauthenticated: 60 requests per hour (1/min average)
  * GitHub Apps (Enterprise Cloud): 15,000 requests per hour (250/min average)

- Secondary Rate Limits (point system):
  * REST API: 900 points per minute to a single endpoint
  * GraphQL API: 2,000 points per minute
  * Content Creation: 80 requests per minute
  * Concurrency: Max 100 requests simultaneously
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque


class GitHubRateLimiter:
    """
    Manages GitHub API rate limits with strict adherence to GitHub's policies.
    """
    
    # Search API limits
    SEARCH_LIMIT_AUTHENTICATED = 30  # per minute
    SEARCH_LIMIT_UNAUTHENTICATED = 10  # per minute
    
    # General API limits
    GENERAL_LIMIT_AUTHENTICATED = 5000  # per hour
    GENERAL_LIMIT_UNAUTHENTICATED = 60  # per hour
    GENERAL_LIMIT_GITHUB_APP = 15000  # per hour (Enterprise Cloud)
    
    # Secondary rate limits (point system)
    SECONDARY_REST_LIMIT = 900  # points per minute per endpoint
    SECONDARY_GRAPHQL_LIMIT = 2000  # points per minute
    SECONDARY_CONTENT_CREATION = 80  # requests per minute
    SECONDARY_CONCURRENCY = 100  # max simultaneous requests
    
    # Point costs for different operations (estimated)
    POINT_COSTS = {
        "search": 5,
        "get_repo": 1,
        "get_file": 1,
        "get_commit": 1,
        "list_commits": 2,
        "get_branch": 1,
        "create_issue": 3,
        "create_comment": 2,
        "get_contents": 1,
        "clone_repo": 10,
    }
    
    def __init__(self, authenticated: bool = True, is_github_app: bool = False,
                 github_token: Optional[str] = None):
        """
        Initialize the GitHub rate limiter.
        
        Args:
            authenticated: Whether using an authenticated token
            is_github_app: Whether using GitHub App authentication (Enterprise Cloud)
            github_token: Optional GitHub token for authentication
        """
        self.authenticated = authenticated
        self.is_github_app = is_github_app
        self.github_token = github_token
        
        # Determine limits based on authentication type
        if is_github_app:
            self.search_limit = self.SEARCH_LIMIT_AUTHENTICATED
            self.general_limit = self.GENERAL_LIMIT_GITHUB_APP
        elif authenticated:
            self.search_limit = self.SEARCH_LIMIT_AUTHENTICATED
            self.general_limit = self.GENERAL_LIMIT_AUTHENTICATED
        else:
            self.search_limit = self.SEARCH_LIMIT_UNAUTHENTICATED
            self.general_limit = self.GENERAL_LIMIT_UNAUTHENTICATED
        
        # Search API tracking (per minute)
        self.search_requests = deque()
        self.search_limit_window = 60.0  # 60 seconds
        
        # General API tracking (per hour)
        self.general_requests = deque()
        self.general_limit_window = 3600.0  # 3600 seconds (1 hour)
        
        # Secondary rate limit tracking (per minute)
        self.secondary_points = deque()
        self.secondary_limit_window = 60.0
        self.current_secondary_points = 0
        
        # Content creation tracking (per minute)
        self.content_creation_requests = deque()
        self.content_creation_window = 60.0
        
        # Concurrency tracking
        self.active_requests = 0
        
        # Endpoint-specific point tracking
        self.endpoint_points: Dict[str, deque] = {}
        
        # Statistics
        self.total_requests = 0
        self.total_search_requests = 0
        self.total_general_requests = 0
        self.rate_limit_hits = 0
        self.secondary_limit_hits = 0
        
        print(f"GitHub Rate Limiter initialized:")
        print(f"  Authentication: {'GitHub App' if is_github_app else 'Authenticated' if authenticated else 'Unauthenticated'}")
        print(f"  Search limit: {self.search_limit} requests/minute")
        print(f"  General limit: {self.general_limit} requests/hour")
        print(f"  Secondary limit: {self.SECONDARY_REST_LIMIT} points/minute")
    
    def _clean_old_entries(self, entries: deque, window: float) -> deque:
        """Remove entries older than the time window."""
        cutoff = time.time() - window
        while entries and entries[0] < cutoff:
            entries.popleft()
        return entries
    
    def _get_search_requests_count(self) -> int:
        """Get count of search requests in the current window."""
        self.search_requests = self._clean_old_entries(self.search_requests, self.search_limit_window)
        return len(self.search_requests)
    
    def _get_general_requests_count(self) -> int:
        """Get count of general requests in the current window."""
        self.general_requests = self._clean_old_entries(self.general_requests, self.general_limit_window)
        return len(self.general_requests)
    
    def _get_content_creation_count(self) -> int:
        """Get count of content creation requests in the current window."""
        self.content_creation_requests = self._clean_old_entries(
            self.content_creation_requests, self.content_creation_window
        )
        return len(self.content_creation_requests)
    
    def _get_secondary_points_count(self) -> int:
        """Get count of secondary points in the current window."""
        self.secondary_points = self._clean_old_entries(
            self.secondary_points, self.secondary_limit_window
        )
        return sum(entry[1] for entry in self.secondary_points)
    
    def _get_endpoint_points_count(self, endpoint: str) -> int:
        """Get point count for a specific endpoint."""
        if endpoint not in self.endpoint_points:
            self.endpoint_points[endpoint] = deque()
        
        self.endpoint_points[endpoint] = self._clean_old_entries(
            self.endpoint_points[endpoint], self.secondary_limit_window
        )
        return sum(entry[1] for entry in self.endpoint_points[endpoint])
    
    def can_make_search_request(self) -> Tuple[bool, Optional[float]]:
        """
        Check if a search request can be made.
        
        Returns:
            (can_make, wait_time) - whether request can be made and time to wait if not
        """
        current_count = self._get_search_requests_count()
        
        if current_count >= self.search_limit:
            # Calculate wait time until oldest request expires
            oldest_request = self.search_requests[0]
            wait_time = oldest_request + self.search_limit_window - time.time()
            return False, max(0.0, wait_time)
        
        return True, 0.0
    
    def can_make_general_request(self) -> Tuple[bool, Optional[float]]:
        """
        Check if a general API request can be made.
        
        Returns:
            (can_make, wait_time) - whether request can be made and time to wait if not
        """
        current_count = self._get_general_requests_count()
        
        if current_count >= self.general_limit:
            # Calculate wait time until oldest request expires
            oldest_request = self.general_requests[0]
            wait_time = oldest_request + self.general_limit_window - time.time()
            return False, max(0.0, wait_time)
        
        return True, 0.0
    
    def can_make_secondary_request(self, operation: str, endpoint: str = "default") -> Tuple[bool, Optional[float]]:
        """
        Check if a request can be made considering secondary rate limits.
        
        Args:
            operation: Type of operation (e.g., "search", "get_repo", "clone_repo")
            endpoint: API endpoint being called
            
        Returns:
            (can_make, wait_time) - whether request can be made and time to wait if not
        """
        # Check concurrency
        if self.active_requests >= self.SECONDARY_CONCURRENCY:
            return False, 1.0  # Wait 1 second and retry
        
        # Get point cost for this operation
        point_cost = self.POINT_COSTS.get(operation, 1)
        
        # Check content creation limit
        if operation in ["create_issue", "create_comment"]:
            content_count = self._get_content_creation_count()
            if content_count >= self.SECONDARY_CONTENT_CREATION:
                oldest = self.content_creation_requests[0]
                wait_time = oldest + self.content_creation_window - time.time()
                return False, max(0.0, wait_time)
        
        # Check endpoint-specific point limit
        endpoint_points = self._get_endpoint_points_count(endpoint)
        if endpoint_points + point_cost > self.SECONDARY_REST_LIMIT:
            if self.endpoint_points[endpoint]:
                oldest = self.endpoint_points[endpoint][0]
                wait_time = oldest + self.secondary_limit_window - time.time()
                return False, max(0.0, wait_time)
            return False, 60.0
        
        # Check overall secondary point limit
        total_points = self._get_secondary_points_count()
        if total_points + point_cost > self.SECONDARY_REST_LIMIT:
            if self.secondary_points:
                oldest = self.secondary_points[0]
                wait_time = oldest + self.secondary_limit_window - time.time()
                return False, max(0.0, wait_time)
            return False, 60.0
        
        return True, 0.0
    
    def record_search_request(self):
        """Record a search API request."""
        self.search_requests.append(time.time())
        self.total_search_requests += 1
        self.total_requests += 1
    
    def record_general_request(self):
        """Record a general API request."""
        self.general_requests.append(time.time())
        self.total_general_requests += 1
        self.total_requests += 1
    
    def record_secondary_request(self, operation: str, endpoint: str = "default"):
        """
        Record a request against secondary limits.
        
        Args:
            operation: Type of operation
            endpoint: API endpoint
        """
        point_cost = self.POINT_COSTS.get(operation, 1)
        
        # Record in secondary points
        self.secondary_points.append((time.time(), point_cost))
        
        # Record in endpoint-specific points
        if endpoint not in self.endpoint_points:
            self.endpoint_points[endpoint] = deque()
        self.endpoint_points[endpoint].append((time.time(), point_cost))
        
        # Record content creation if applicable
        if operation in ["create_issue", "create_comment"]:
            self.content_creation_requests.append(time.time())
    
    def start_request(self):
        """Mark a request as started (for concurrency tracking)."""
        self.active_requests += 1
    
    def end_request(self):
        """Mark a request as ended (for concurrency tracking)."""
        self.active_requests = max(0, self.active_requests - 1)
    
    def can_make_request(self, operation: str, is_search: bool = False, 
                        endpoint: str = "default") -> Tuple[bool, Optional[float], str]:
        """
        Comprehensive check if a request can be made.
        
        Args:
            operation: Type of operation
            is_search: Whether this is a search API request
            endpoint: API endpoint
            
        Returns:
            (can_make, wait_time, reason) - whether request can be made, wait time, and reason if not
        """
        # Check search limit first if applicable
        if is_search:
            can_make, wait_time = self.can_make_search_request()
            if not can_make:
                self.rate_limit_hits += 1
                return False, wait_time, f"Search rate limit exceeded. Wait {wait_time:.1f}s"
        
        # Check general limit
        can_make, wait_time = self.can_make_general_request()
        if not can_make:
            self.rate_limit_hits += 1
            return False, wait_time, f"General rate limit exceeded. Wait {wait_time:.1f}s"
        
        # Check secondary limits
        can_make, wait_time = self.can_make_secondary_request(operation, endpoint)
        if not can_make:
            self.secondary_limit_hits += 1
            return False, wait_time, f"Secondary rate limit exceeded. Wait {wait_time:.1f}s"
        
        return True, 0.0, "Request allowed"
    
    def make_request(self, operation: str, is_search: bool = False, 
                     endpoint: str = "default", max_wait: float = 300.0) -> bool:
        """
        Attempt to make a request, waiting if necessary.
        
        Args:
            operation: Type of operation
            is_search: Whether this is a search API request
            endpoint: API endpoint
            max_wait: Maximum time to wait for rate limit (default 5 minutes)
            
        Returns:
            True if request was allowed, False if max_wait exceeded
        """
        start_wait = time.time()
        
        while True:
            can_make, wait_time, reason = self.can_make_request(operation, is_search, endpoint)
            
            if can_make:
                # Record the request
                if is_search:
                    self.record_search_request()
                else:
                    self.record_general_request()
                self.record_secondary_request(operation, endpoint)
                self.start_request()
                return True
            
            # Check if we've waited too long
            if time.time() - start_wait + wait_time > max_wait:
                print(f"Max wait time exceeded for {operation}: {reason}")
                return False
            
            # Wait and retry
            if wait_time > 0:
                time.sleep(min(wait_time, 5.0))  # Sleep in chunks to check limits
    
    def finish_request(self):
        """Mark a request as finished."""
        self.end_request()
    
    def get_status(self) -> Dict:
        """Get current rate limit status."""
        search_remaining = self.search_limit - self._get_search_requests_count()
        general_remaining = self.general_limit - self._get_general_requests_count()
        secondary_remaining = self.SECONDARY_REST_LIMIT - self._get_secondary_points_count()
        
        return {
            "authenticated": self.authenticated,
            "is_github_app": self.is_github_app,
            "search": {
                "limit": self.search_limit,
                "used": self._get_search_requests_count(),
                "remaining": max(0, search_remaining),
                "window": "1 minute"
            },
            "general": {
                "limit": self.general_limit,
                "used": self._get_general_requests_count(),
                "remaining": max(0, general_remaining),
                "window": "1 hour"
            },
            "secondary": {
                "limit": self.SECONDARY_REST_LIMIT,
                "used": self._get_secondary_points_count(),
                "remaining": max(0, secondary_remaining),
                "window": "1 minute"
            },
            "concurrency": {
                "active": self.active_requests,
                "limit": self.SECONDARY_CONCURRENCY
            },
            "statistics": {
                "total_requests": self.total_requests,
                "total_search_requests": self.total_search_requests,
                "total_general_requests": self.total_general_requests,
                "rate_limit_hits": self.rate_limit_hits,
                "secondary_limit_hits": self.secondary_limit_hits
            }
        }
    
    def save_state(self, filepath: str):
        """Save rate limiter state to file."""
        state = {
            "authenticated": self.authenticated,
            "is_github_app": self.is_github_app,
            "search_requests": list(self.search_requests),
            "general_requests": list(self.general_requests),
            "secondary_points": [(t, p) for t, p in self.secondary_points],
            "content_creation_requests": list(self.content_creation_requests),
            "total_requests": self.total_requests,
            "total_search_requests": self.total_search_requests,
            "total_general_requests": self.total_general_requests,
            "rate_limit_hits": self.rate_limit_hits,
            "secondary_limit_hits": self.secondary_limit_hits,
            "saved_at": time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"Rate limiter state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load rate limiter state from file."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.search_requests = deque(state.get("search_requests", []))
            self.general_requests = deque(state.get("general_requests", []))
            self.secondary_points = deque(
                [(t, p) for t, p in state.get("secondary_points", [])]
            )
            self.content_creation_requests = deque(
                state.get("content_creation_requests", [])
            )
            self.total_requests = state.get("total_requests", 0)
            self.total_search_requests = state.get("total_search_requests", 0)
            self.total_general_requests = state.get("total_general_requests", 0)
            self.rate_limit_hits = state.get("rate_limit_hits", 0)
            self.secondary_limit_hits = state.get("secondary_limit_hits", 0)
            
            print(f"Rate limiter state loaded from {filepath}")
            
        except FileNotFoundError:
            print(f"No state file found at {filepath}, starting fresh")
        except Exception as e:
            print(f"Error loading state: {e}")
    
    def reset(self):
        """Reset all rate limit tracking."""
        self.search_requests.clear()
        self.general_requests.clear()
        self.secondary_points.clear()
        self.content_creation_requests.clear()
        self.endpoint_points.clear()
        self.active_requests = 0
        self.total_requests = 0
        self.total_search_requests = 0
        self.total_general_requests = 0
        self.rate_limit_hits = 0
        self.secondary_limit_hits = 0
        
        print("Rate limiter reset")


if __name__ == "__main__":
    # Test the rate limiter
    print("Testing GitHub Rate Limiter...")
    
    # Test with authenticated token
    limiter = GitHubRateLimiter(authenticated=True, github_token="test_token")
    
    # Test search requests
    print("\nTesting search requests...")
    for i in range(5):
        can_make, wait_time, reason = limiter.can_make_request("search", is_search=True)
        print(f"  Request {i+1}: {reason}")
        if can_make:
            limiter.make_request("search", is_search=True)
            limiter.finish_request()
    
    # Test general requests
    print("\nTesting general requests...")
    for i in range(5):
        can_make, wait_time, reason = limiter.can_make_request("get_repo")
        print(f"  Request {i+1}: {reason}")
        if can_make:
            limiter.make_request("get_repo")
            limiter.finish_request()
    
    # Get status
    print("\nCurrent status:")
    status = limiter.get_status()
    print(json.dumps(status, indent=2))
    
    print("\nGitHub Rate Limiter test completed!")
