"""
API Usage Manager
Manages API usage tracking, quota management, and training pause/resume
"""

import time
import json
from typing import Dict, List, Optional
from datetime import datetime

class APIUsageManager:
    """
    Manages API usage tracking, quota management, and training pause/resume
    """
    
    def __init__(self, daily_quota: int = 1000):
        """
        Initialize the API usage manager
        
        Args:
            daily_quota: Daily API quota limit
        """
        self.daily_quota = daily_quota
        self.current_usage = 0
        self.quota_exhausted = False
        
        # Usage tracking
        self.usage_history = []
        self.usage_by_type = {
            "instruction": 0,
            "evaluation": 0,
            "hint": 0,
            "other": 0
        }
        
        # Session tracking
        self.session_start_time = time.time()
        self.session_usage = 0
        self.active_sessions = []
        
        # Quota reset tracking
        self.last_reset_time = time.time()
        self.quota_reset_interval = 86400  # 24 hours in seconds
        
        # Training state
        self.training_paused = False
        self.pause_reason = None
        self.auto_resume = True  # Automatically resume when quota renews
        
        print(f"API usage manager initialized with daily quota: {daily_quota}")
    
    def record_api_call(self, call_type: str, cost: int = 1) -> Dict:
        """
        Record an API call and update usage
        
        Args:
            call_type: Type of API call (instruction, evaluation, hint, other)
            cost: Cost of the API call in quota units
            
        Returns:
            Usage information after the call
        """
        # Check if quota needs reset
        self._check_quota_reset()
        
        # Check if quota is exhausted
        if self.quota_exhausted:
            return {
                "success": False,
                "reason": "Quota exhausted",
                "current_usage": self.current_usage,
                "quota": self.daily_quota
            }
        
        # Check if this call would exceed quota
        if self.current_usage + cost > self.daily_quota:
            self._quota_exhausted()
            return {
                "success": False,
                "reason": "Quota would be exceeded",
                "current_usage": self.current_usage,
                "quota": self.daily_quota
            }
        
        # Record usage
        self.current_usage += cost
        self.session_usage += cost
        
        # Update usage by type
        if call_type in self.usage_by_type:
            self.usage_by_type[call_type] += cost
        else:
            self.usage_by_type["other"] += cost
        
        # Record in history
        usage_record = {
            "timestamp": time.time(),
            "call_type": call_type,
            "cost": cost,
            "total_usage": self.current_usage
        }
        self.usage_history.append(usage_record)
        
        # Check if quota is now exhausted
        if self.current_usage >= self.daily_quota:
            self._quota_exhausted()
        
        return {
            "success": True,
            "call_type": call_type,
            "cost": cost,
            "current_usage": self.current_usage,
            "quota": self.daily_quota,
            "remaining": self.daily_quota - self.current_usage,
            "quota_exhausted": self.quota_exhausted
        }
    
    def _quota_exhausted(self):
        """Handle quota exhaustion"""
        self.quota_exhausted = True
        self.training_paused = True
        self.pause_reason = "API quota exhausted"
        
        print("API quota exhausted - training paused")
    
    def _check_quota_reset(self):
        """Check if quota should be reset based on time"""
        current_time = time.time()
        time_since_reset = current_time - self.last_reset_time
        
        if time_since_reset >= self.quota_reset_interval:
            self.reset_quota()
    
    def reset_quota(self):
        """Reset API quota"""
        self.current_usage = 0
        self.quota_exhausted = False
        self.last_reset_time = time.time()
        self.usage_by_type = {key: 0 for key in self.usage_by_type}
        
        # Auto-resume training if enabled
        if self.auto_resume and self.training_paused:
            self.training_paused = False
            self.pause_reason = None
            print("Training automatically resumed - quota renewed")
        
        print("API quota reset")
    
    def get_usage_status(self) -> Dict:
        """
        Get current usage status
        
        Returns:
            Usage status information
        """
        remaining = self.daily_quota - self.current_usage
        usage_percentage = (self.current_usage / self.daily_quota) * 100 if self.daily_quota > 0 else 0
        
        return {
            "current_usage": self.current_usage,
            "daily_quota": self.daily_quota,
            "remaining": remaining,
            "usage_percentage": usage_percentage,
            "quota_exhausted": self.quota_exhausted,
            "training_paused": self.training_paused,
            "pause_reason": self.pause_reason,
            "usage_by_type": self.usage_by_type,
            "session_usage": self.session_usage,
            "session_duration": time.time() - self.session_start_time
        }
    
    def can_make_api_call(self, cost: int = 1) -> Dict:
        """
        Check if an API call can be made
        
        Args:
            cost: Cost of the API call
            
        Returns:
            Whether the call can be made and details
        """
        self._check_quota_reset()
        
        if self.quota_exhausted:
            return {
                "can_call": False,
                "reason": "Quota exhausted",
                "quota_renewal_time": self.last_reset_time + self.quota_reset_interval
            }
        
        if self.current_usage + cost > self.daily_quota:
            return {
                "can_call": False,
                "reason": "Insufficient quota",
                "required": cost,
                "available": self.daily_quota - self.current_usage
            }
        
        return {
            "can_call": True,
            "reason": "Quota available",
            "available": self.daily_quota - self.current_usage
        }
    
    def pause_training(self, reason: str = "Manual pause"):
        """
        Manually pause training
        
        Args:
            reason: Reason for pausing
        """
        self.training_paused = True
        self.pause_reason = reason
        print(f"Training paused: {reason}")
    
    def resume_training(self):
        """Resume training"""
        if self.quota_exhausted:
            print("Cannot resume training - quota still exhausted")
            return False
        
        self.training_paused = False
        self.pause_reason = None
        print("Training resumed")
        return True
    
    def start_session(self) -> str:
        """
        Start a new API usage session
        
        Returns:
            Session ID
        """
        session_id = f"session_{len(self.active_sessions)}_{int(time.time())}"
        
        session = {
            "session_id": session_id,
            "start_time": time.time(),
            "usage": 0
        }
        
        self.active_sessions.append(session)
        self.session_start_time = time.time()
        self.session_usage = 0
        
        print(f"API session started: {session_id}")
        return session_id
    
    def end_session(self, session_id: str) -> Dict:
        """
        End an API usage session
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Session summary
        """
        session = None
        for s in self.active_sessions:
            if s["session_id"] == session_id:
                session = s
                break
        
        if not session:
            return {"error": "Session not found"}
        
        session_end_time = time.time()
        session_duration = session_end_time - session["start_time"]
        
        session_summary = {
            "session_id": session_id,
            "start_time": session["start_time"],
            "end_time": session_end_time,
            "duration": session_duration,
            "usage": session["usage"]
        }
        
        self.active_sessions.remove(session)
        print(f"API session ended: {session_id}")
        
        return session_summary
    
    def get_usage_history(self, limit: int = 50) -> List[Dict]:
        """
        Get recent usage history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Recent usage records
        """
        return self.usage_history[-limit:] if self.usage_history else []
    
    def get_usage_statistics(self) -> Dict:
        """
        Get usage statistics
        
        Returns:
            Usage statistics
        """
        if not self.usage_history:
            return {
                "total_calls": 0,
                "total_cost": 0,
                "average_cost": 0.0,
                "calls_by_type": self.usage_by_type
            }
        
        total_calls = len(self.usage_history)
        total_cost = sum(record["cost"] for record in self.usage_history)
        average_cost = total_cost / total_calls if total_calls > 0 else 0.0
        
        return {
            "total_calls": total_calls,
            "total_cost": total_cost,
            "average_cost": average_cost,
            "calls_by_type": self.usage_by_type,
            "quota_utilization": (self.current_usage / self.daily_quota) * 100 if self.daily_quota > 0 else 0.0
        }
    
    def set_quota(self, new_quota: int):
        """
        Set a new daily quota
        
        Args:
            new_quota: New daily quota limit
        """
        self.daily_quota = new_quota
        print(f"Daily quota updated to: {new_quota}")
    
    def set_auto_resume(self, enabled: bool):
        """
        Set whether training should auto-resume when quota renews
        
        Args:
            enabled: Whether auto-resume is enabled
        """
        self.auto_resume = enabled
        print(f"Auto-resume set to: {enabled}")
    
    def save_usage_data(self, filepath: str):
        """
        Save usage data to file
        
        Args:
            filepath: Path to save file
        """
        data = {
            "current_usage": self.current_usage,
            "daily_quota": self.daily_quota,
            "quota_exhausted": self.quota_exhausted,
            "usage_by_type": self.usage_by_type,
            "usage_history": self.usage_history[-200:]  # Save last 200 records
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Usage data saved to {filepath}")
    
    def load_usage_data(self, filepath: str):
        """
        Load usage data from file
        
        Args:
            filepath: Path to load file
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.current_usage = data.get("current_usage", 0)
            self.daily_quota = data.get("daily_quota", self.daily_quota)
            self.quota_exhausted = data.get("quota_exhausted", False)
            self.usage_by_type = data.get("usage_by_type", self.usage_by_type)
            self.usage_history = data.get("usage_history", [])
            
            print(f"Usage data loaded from {filepath}")
            
        except FileNotFoundError:
            print(f"No usage data file found at {filepath}")
        except Exception as e:
            print(f"Error loading usage data: {e}")
    
    def reset_all(self):
        """Reset all usage data"""
        self.current_usage = 0
        self.quota_exhausted = False
        self.usage_by_type = {key: 0 for key in self.usage_by_type}
        self.usage_history = []
        self.session_usage = 0
        self.training_paused = False
        self.pause_reason = None
        
        print("API usage manager reset")


if __name__ == "__main__":
    # Test the API usage manager
    print("Testing API Usage Manager...")
    
    api_manager = APIUsageManager(daily_quota=100)
    
    # Test API call recording
    print("\nTesting API call recording...")
    result = api_manager.record_api_call("instruction", cost=5)
    print(f"API call result: {result}")
    
    result = api_manager.record_api_call("evaluation", cost=3)
    print(f"API call result: {result}")
    
    # Test usage status
    print("\nTesting usage status...")
    status = api_manager.get_usage_status()
    print(f"Usage status: {status}")
    
    # Test can make API call
    print("\nTesting can make API call...")
    can_call = api_manager.can_make_api_call(cost=10)
    print(f"Can make API call: {can_call}")
    
    # Test quota exhaustion
    print("\nTesting quota exhaustion...")
    api_manager.record_api_call("instruction", cost=95)  # Exhaust quota
    status = api_manager.get_usage_status()
    print(f"Status after exhaustion: {status}")
    
    # Test quota reset
    print("\nTesting quota reset...")
    api_manager.reset_quota()
    status = api_manager.get_usage_status()
    print(f"Status after reset: {status}")
    
    # Test training pause/resume
    print("\nTesting training pause/resume...")
    api_manager.pause_training("Manual test")
    api_manager.resume_training()
    
    # Test usage statistics
    print("\nTesting usage statistics...")
    stats = api_manager.get_usage_statistics()
    print(f"Usage statistics: {stats}")
    
    print("API usage manager test completed!")