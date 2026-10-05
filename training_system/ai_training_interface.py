"""
AI Training Interface
Handles AI-assisted training using Gemini API for coding instruction and evaluation
"""

import os
import sys
import json
from typing import Dict, List, Optional
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google.generativeai not available. Install with: pip install google-generativeai")
    genai = None

from dotenv import load_dotenv

try:
    from .github_rate_limiter import GitHubRateLimiter
    from .github_repo_puller import GitHubRepoPuller
except ImportError:
    from github_rate_limiter import GitHubRateLimiter
    from github_repo_puller import GitHubRepoPuller

# Import custom translator
try:
    from llm_interface.custom_translator import CustomBrainTranslator
except ImportError:
    from custom_translator import CustomBrainTranslator

class AITrainingInterface:
    """
    AI training interface using Gemini API for coding instruction and evaluation
    Uses CustomBrainTranslator for brain activity decoding (NOT Gemini, GPT, or Claude)
    """
    
    # PERSISTENT INSTRUCTION - NEVER GIVE UP
    PERSISTENT_INSTRUCTION = """
CRITICAL INSTRUCTION: NEVER GIVE UP NO MATTER THE SITUATION WHEN TRAINING THE FLY.
You must persist through all difficulties, errors, or slow progress. The fly will learn,
but it takes time and patience. Continue adapting your teaching methods, but never
abandon the training process. Every challenge is an opportunity to improve the training.
The fly's neural network is plastic and will adapt with consistent effort.
"""

    def __init__(self, enable_github: bool = False, github_token: Optional[str] = None):
        """
        Initialize the AI training interface
        
        Args:
            enable_github: Whether to enable GitHub repository pulling
            github_token: Optional GitHub token for authenticated requests
        """
        load_dotenv()
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("Warning: No GEMINI_API_KEY set. Running in testing mode without AI.")
            self.model = None
        else:
            # Configure Gemini API
            if genai:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("AI Training Interface initialized with Gemini API")
            else:
                self.model = None
                print("AI Training Interface initialized without API (testing mode)")
        
        # Initialize custom translator (NOT Gemini, GPT, or Claude)
        self.custom_translator = CustomBrainTranslator()
        print("Custom Brain Translator initialized (built-in, not external API)")
        
        # Training state
        self.training_active = False
        self.api_usage_count = 0
        self.api_quota_limit = 1000  # Arbitrary limit for tracking
        self.quota_exhausted = False
        
        # Training history
        self.training_sessions = []
        self.current_session = None
        
        # GitHub integration
        self.enable_github = enable_github
        self.github_rate_limiter = None
        self.github_repo_puller = None
        
        if enable_github:
            # Get GitHub token from env if not provided
            if not github_token:
                github_token = os.getenv("GITHUB_TOKEN")
            
            authenticated = bool(github_token)
            self.github_rate_limiter = GitHubRateLimiter(
                authenticated=authenticated,
                github_token=github_token
            )
            self.github_repo_puller = GitHubRepoPuller(
                self.github_rate_limiter,
                workspace_dir="github_repos"
            )
            print("GitHub integration enabled for training")
    
    def start_training_session(self, curriculum) -> Dict:
        """
        Start a new training session
        
        Args:
            curriculum: Coding curriculum object
            
        Returns:
            Session information
        """
        if self.quota_exhausted:
            return {
                "success": False,
                "reason": "API quota exhausted",
                "message": "Training cannot continue - API quota exhausted"
            }
        
        session_id = len(self.training_sessions)
        self.current_session = {
            "session_id": session_id,
            "start_time": time.time(),
            "lessons_completed": 0,
            "lessons_failed": 0,
            "total_lessons": 0,
            "languages_practiced": set(),
            "curriculum": curriculum
        }
        
        self.training_active = True
        print(f"Training session {session_id} started")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Training session started successfully"
        }
    
    def get_lesson_instruction(self, lesson: Dict) -> str:
        """
        Get AI instruction for a specific lesson
        
        Args:
            lesson: Lesson dictionary from curriculum
            
        Returns:
            Instruction text from AI
        """
        if not self.model:
            return f"Practice this task: {lesson['task']}\n\nStarter code:\n{lesson['starter_code']}"
        
        prompt = f"""
        You are a coding instructor. Provide clear, concise instruction for this programming task:
        
        Task: {lesson['task']}
        Language: {lesson.get('language', 'Unknown')}
        Level: {lesson.get('level', 'Beginner')}
        
        Starter code:
        {lesson['starter_code']}
        
        {self.PERSISTENT_INSTRUCTION}
        
        Provide:
        1. A brief explanation of the concept
        2. Step-by-step guidance
        3. Any important syntax or patterns to remember
        4. Keep it concise and actionable
        
        Format your response as plain text without markdown.
        """
        
        try:
            response = self.model.generate_content(prompt)
            self.api_usage_count += 1
            self._check_quota()
            
            instruction = response.text.strip()
            return instruction
            
        except Exception as e:
            print(f"Error getting instruction: {e}")
            return f"Practice this task: {lesson['task']}\n\nStarter code:\n{lesson['starter_code']}"
    
    def evaluate_code(self, user_code: str, lesson: Dict) -> Dict:
        """
        Evaluate user's code against the expected solution
        
        Args:
            user_code: Code written by the fly
            lesson: Lesson dictionary with expected solution
            
        Returns:
            Evaluation results
        """
        if not self.model:
            return self._basic_evaluation(user_code, lesson)
        
        prompt = f"""
        You are a code evaluator. Evaluate this code against the expected solution:
        
        Task: {lesson['task']}
        
        User's code:
        {user_code}
        
        Expected solution:
        {lesson['expected_solution']}
        
        Test cases to consider:
        {', '.join(lesson['test_cases'])}
        
        Evaluate:
        1. Does the code accomplish the task?
        2. Is the syntax correct?
        3. Are there any obvious bugs?
        4. Rate the quality from 0.0 to 1.0
        
        Return your response in this exact JSON format:
        {{
            "correct": true/false,
            "quality": 0.0-1.0,
            "feedback": "brief feedback message",
            "suggestions": ["suggestion1", "suggestion2"]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            self.api_usage_count += 1
            self._check_quota()
            
            # Try to parse JSON response
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    evaluation = json.loads(json_str)
                    return evaluation
                except json.JSONDecodeError:
                    pass
            
            # Fallback if JSON parsing fails
            return self._basic_evaluation(user_code, lesson)
            
        except Exception as e:
            print(f"Error evaluating code: {e}")
            return self._basic_evaluation(user_code, lesson)
    
    def _basic_evaluation(self, user_code: str, lesson: Dict) -> Dict:
        """Basic evaluation without AI"""
        # Simple heuristic evaluation
        expected = lesson['expected_solution']
        
        # Check if user code is not empty
        if not user_code.strip() or user_code.strip() == "# Your code here":
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": "No code provided",
                "suggestions": ["Write some code to solve the task"]
            }
        
        # Check if user code is just a placeholder
        if "pass" in user_code and len(user_code.strip()) < 20:
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": "Code is incomplete (only placeholder)",
                "suggestions": ["Implement the actual logic"]
            }
        
        # Check if user code contains some keywords from expected solution
        keyword_match = 0
        expected_keywords = ['def', 'class', 'function', 'interface', 'return', 'import', 'from']
        for keyword in expected_keywords:
            if keyword in expected and keyword in user_code:
                keyword_match += 1
        
        # For beginner lessons, require at least a return statement
        if "def " in user_code and "return " not in user_code:
            return {
                "correct": False,
                "quality": 0.2,
                "feedback": "Function missing return statement",
                "suggestions": ["Add a return statement to complete the function"]
            }
        
        quality = min(1.0, keyword_match / 3.0)
        
        # If no significant keywords matched, mark as incorrect
        if keyword_match == 0:
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": "Code does not match expected solution structure",
                "suggestions": ["Review the expected solution and implement the required logic"]
            }
        
        return {
            "correct": quality > 0.5,
            "quality": quality,
            "feedback": f"Code provided. Quality: {quality:.2f}",
            "suggestions": ["Try to match the expected solution structure"]
        }
    
    def provide_hint(self, lesson: Dict, user_code: str, previous_attempts: int) -> str:
        """
        Provide a hint to help the fly solve the problem
        
        Args:
            lesson: Lesson dictionary
            user_code: Current user code
            previous_attempts: Number of previous attempts
            
        Returns:
            Hint text
        """
        if not self.model:
            return f"Hint: Focus on the task: {lesson['task']}"
        
        prompt = f"""
        The student has attempted this problem {previous_attempts} times.
        
        Task: {lesson['task']}
        
        Current code:
        {user_code}
        
        Expected solution:
        {lesson['expected_solution']}
        
        Provide a helpful hint that guides them toward the solution without giving it away completely.
        Keep it concise and encouraging.
        """
        
        try:
            response = self.model.generate_content(prompt)
            self.api_usage_count += 1
            self._check_quota()
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Error providing hint: {e}")
            return f"Hint: Review the task: {lesson['task']}"
    
    def _check_quota(self):
        """Check if API quota has been exhausted"""
        if self.api_usage_count >= self.api_quota_limit:
            self.quota_exhausted = True
            self.training_active = False
            print("API quota exhausted - training paused")
    
    def get_training_progress(self) -> Dict:
        """Get current training progress"""
        if not self.current_session:
            return {
                "training_active": False,
                "api_usage_count": self.api_usage_count,
                "quota_exhausted": self.quota_exhausted
            }
        
        session = self.current_session
        total_lessons = session["lessons_completed"] + session["lessons_failed"]
        success_rate = session["lessons_completed"] / total_lessons if total_lessons > 0 else 0.0
        
        return {
            "training_active": self.training_active,
            "session_id": session["session_id"],
            "lessons_completed": session["lessons_completed"],
            "lessons_failed": session["lessons_failed"],
            "total_lessons": total_lessons,
            "success_rate": success_rate,
            "languages_practiced": list(session["languages_practiced"]),
            "api_usage_count": self.api_usage_count,
            "quota_remaining": self.api_quota_limit - self.api_usage_count,
            "quota_exhausted": self.quota_exhausted
        }
    
    def record_lesson_result(self, language: str, success: bool):
        """
        Record the result of a lesson
        
        Args:
            language: Programming language practiced
            success: Whether the lesson was completed successfully
        """
        if self.current_session:
            if success:
                self.current_session["lessons_completed"] += 1
            else:
                self.current_session["lessons_failed"] += 1
            
            self.current_session["languages_practiced"].add(language)
            self.current_session["total_lessons"] += 1
    
    def end_training_session(self) -> Dict:
        """End the current training session"""
        if not self.current_session:
            return {"success": False, "reason": "No active session"}
        
        session_end_time = time.time()
        session_duration = session_end_time - self.current_session["start_time"]
        
        session_summary = {
            "session_id": self.current_session["session_id"],
            "duration": session_duration,
            "lessons_completed": self.current_session["lessons_completed"],
            "lessons_failed": self.current_session["lessons_failed"],
            "total_lessons": self.current_session["total_lessons"],
            "languages_practiced": list(self.current_session["languages_practiced"]),
            "api_usage": self.api_usage_count
        }
        
        self.training_sessions.append(session_summary)
        self.current_session = None
        self.training_active = False
        
        print(f"Training session ended: {session_summary}")
        
        return {
            "success": True,
            "session_summary": session_summary
        }
    
    def reset_quota(self):
        """Reset API quota (for testing or when quota renews)"""
        self.api_usage_count = 0
        self.quota_exhausted = False
        print("API quota reset")
    
    # ---------------------------------------------------------------- GitHub integration
    def pull_github_repository(self, repo_url: str, branch: Optional[str] = None,
                              depth: Optional[int] = None) -> Dict:
        """
        Pull a GitHub repository for the fly to study.
        
        Args:
            repo_url: GitHub repository URL
            branch: Optional branch to clone
            depth: Optional clone depth for shallow clone
            
        Returns:
            Result dictionary with success status and information
        """
        if not self.enable_github or not self.github_repo_puller:
            return {
                "success": False,
                "reason": "GitHub integration not enabled"
            }
        
        success, message, local_path = self.github_repo_puller.clone_repository(
            repo_url, branch, depth
        )
        
        return {
            "success": success,
            "message": message,
            "local_path": local_path,
            "repo_url": repo_url
        }
    
    def get_github_file(self, repo_url: str, file_path: str) -> Dict:
        """
        Get a file from a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            file_path: Path to file within repository
            
        Returns:
            Result dictionary with file content
        """
        if not self.enable_github or not self.github_repo_puller:
            return {
                "success": False,
                "reason": "GitHub integration not enabled"
            }
        
        success, content, message = self.github_repo_puller.get_file_contents(
            repo_url, file_path
        )
        
        return {
            "success": success,
            "content": content,
            "message": message,
            "repo_url": repo_url,
            "file_path": file_path
        }
    
    def list_github_files(self, repo_url: str, path: str = "") -> Dict:
        """
        List files in a GitHub repository directory.
        
        Args:
            repo_url: GitHub repository URL
            path: Path within repository (empty for root)
            
        Returns:
            Result dictionary with list of files
        """
        if not self.enable_github or not self.github_repo_puller:
            return {
                "success": False,
                "reason": "GitHub integration not enabled"
            }
        
        success, files, message = self.github_repo_puller.list_repository_files(
            repo_url, path
        )
        
        return {
            "success": success,
            "files": files,
            "message": message,
            "repo_url": repo_url,
            "path": path
        }
    
    def get_github_commits(self, repo_url: str, max_count: int = 10) -> Dict:
        """
        Get commit history from a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            max_count: Maximum number of commits to retrieve
            
        Returns:
            Result dictionary with commit history
        """
        if not self.enable_github or not self.github_repo_puller:
            return {
                "success": False,
                "reason": "GitHub integration not enabled"
            }
        
        success, commits, message = self.github_repo_puller.get_commit_history(
            repo_url, max_count
        )
        
        return {
            "success": success,
            "commits": commits,
            "message": message,
            "repo_url": repo_url
        }
    
    def get_github_status(self) -> Dict:
        """Get current GitHub integration status."""
        if not self.enable_github:
            return {
                "enabled": False,
                "reason": "GitHub integration not enabled"
            }
        
        return {
            "enabled": True,
            "rate_limiter": self.github_rate_limiter.get_status(),
            "repo_puller": self.github_repo_puller.get_status()
        }
    
    def cleanup_github_repo(self, repo_url: str) -> Dict:
        """
        Clean up a cloned GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Result dictionary
        """
        if not self.enable_github or not self.github_repo_puller:
            return {
                "success": False,
                "reason": "GitHub integration not enabled"
            }
        
        success = self.github_repo_puller.cleanup_repository(repo_url)
        
        return {
            "success": success,
            "repo_url": repo_url
        }


if __name__ == "__main__":
    # Test the AI training interface
    print("Testing AI Training Interface...")
    
    try:
        ai_trainer = AITrainingInterface()
        
        # Test instruction generation
        print("\nTesting instruction generation...")
        test_lesson = {
            "task": "Write a function that adds two numbers",
            "starter_code": "def add_numbers(a, b):\n    pass",
            "expected_solution": "def add_numbers(a, b):\n    return a + b",
            "test_cases": ["syntax", "correctness"]
        }
        
        instruction = ai_trainer.get_lesson_instruction(test_lesson)
        print(f"Instruction received (length: {len(instruction)} chars)")
        
        # Test code evaluation
        print("\nTesting code evaluation...")
        user_code = "def add_numbers(a, b):\n    return a + b"
        evaluation = ai_trainer.evaluate_code(user_code, test_lesson)
        print(f"Evaluation: {evaluation}")
        
        # Test quota management
        print("\nTesting quota management...")
        progress = ai_trainer.get_training_progress()
        print(f"API usage: {progress['api_usage_count']}")
        
        print("AI Training Interface test completed!")
        
    except Exception as e:
        print(f"Error during AI Training Interface test: {e}")
        print("Make sure to set your GEMINI_API_KEY in the .env file")