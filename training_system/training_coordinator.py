"""
Training Coordinator
Main training system that coordinates all Phase 4 components
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from training_system.coding_curriculum import CodingCurriculum
from training_system.ai_training_interface import AITrainingInterface
from training_system.code_evaluation import CodeEvaluationEngine
from training_system.reward_system import RewardSystem
from training_system.skill_tracking import SkillTrackingSystem
from training_system.api_usage_manager import APIUsageManager
from training_system.hunger_mechanics import HungerMechanics
from training_system.zero_tolerance_evaluator import ZeroToleranceCodeEvaluator

try:
    from learning_system.on_the_job_learning import OnTheJobLearningSystem
except ImportError:
    OnTheJobLearningSystem = None

class TrainingCoordinator:
    """
    Main training coordinator that integrates all Phase 4 components
    """
    
    def __init__(self):
        """Initialize the training coordinator"""
        # Initialize all components
        self.curriculum = CodingCurriculum()
        self.ai_trainer = AITrainingInterface()
        self.code_evaluator = CodeEvaluationEngine()
        self.zero_tolerance_evaluator = ZeroToleranceCodeEvaluator()
        self.reward_system = RewardSystem()
        self.skill_tracker = SkillTrackingSystem()
        self.api_manager = APIUsageManager(daily_quota=1000)
        
        # Initialize on-the-job learning system
        if OnTheJobLearningSystem:
            self.learning_system = OnTheJobLearningSystem()
        else:
            self.learning_system = None
        
        # Training state
        self.training_active = False
        self.current_language = "python"
        self.current_level = "beginner"
        self.current_lesson = None
        self.attempts = 0
        self.max_attempts = 3
        
        # User control
        self.user_stop_requested = False
        
        print("Training coordinator initialized with all Phase 4 components")
    
    def start_training(self, language: str = "python", level: str = "beginner") -> Dict:
        """
        Start a training session
        
        Args:
            language: Programming language to train
            level: Difficulty level
            
        Returns:
            Training session information
        """
        # Check API quota
        can_start = self.api_manager.can_make_api_call(cost=10)
        if not can_start["can_call"]:
            return {
                "success": False,
                "reason": f"Cannot start training: {can_start['reason']}"
            }
        
        # Check hunger status
        hunger_check = self.reward_system.check_hunger_can_train()
        if not hunger_check["can_train"]:
            return {
                "success": False,
                "reason": f"Cannot start training: {hunger_check['reason']}"
            }
        
        # Set training parameters
        self.current_language = language
        self.current_level = level
        self.training_active = True
        self.user_stop_requested = False
        
        # Start AI training session
        ai_session = self.ai_trainer.start_training_session(self.curriculum)
        
        # Start API session
        self.api_manager.start_session()
        
        # Enable training mode in reward system
        self.reward_system.set_training_mode(True, reward_only=True)
        
        # Get first lesson
        self.current_lesson = self.curriculum.get_lesson_for_language(language, level)
        self.attempts = 0
        
        return {
            "success": True,
            "language": language,
            "level": level,
            "lesson": self.current_lesson["task"],
            "ai_session": ai_session,
            "hunger_status": hunger_check
        }
    
    def get_lesson_instruction(self) -> str:
        """
        Get AI instruction for current lesson
        
        Returns:
            Instruction text
        """
        if not self.current_lesson:
            return "No active lesson"
        
        # Record API call
        api_result = self.api_manager.record_api_call("instruction", cost=5)
        if not api_result["success"]:
            return "API quota exhausted - cannot get instruction"
        
        # Get instruction from AI
        instruction = self.ai_trainer.get_lesson_instruction(self.current_lesson)
        
        return instruction
    
    def submit_code(self, user_code: str) -> Dict:
        """
        Submit code for evaluation
        
        Args:
            user_code: Code written by the fly
            
        Returns:
            Evaluation results and reward information
        """
        if not self.training_active:
            return {
                "success": False,
                "reason": "Training not active"
            }
        
        if self.user_stop_requested:
            return {
                "success": False,
                "reason": "Training stopped by user"
            }
        
        self.attempts += 1
        
        # Evaluate code locally with zero-tolerance
        local_eval = self.code_evaluator.evaluate_code(
            user_code, 
            self.current_language,
            self.current_lesson.get("test_cases", [])
        )
        
        # Apply zero-tolerance evaluation
        zero_tolerance_eval = self.zero_tolerance_evaluator.evaluate_code_strict(
            user_code,
            self.current_language,
            self.current_lesson.get("expected_solution", "")
        )
        
        # Use zero-tolerance evaluation as the primary check
        final_eval = zero_tolerance_eval if zero_tolerance_eval["correct"] else local_eval
        
        # Record API call for AI evaluation
        api_result = self.api_manager.record_api_call("evaluation", cost=10)
        
        # Get AI evaluation if quota available
        if api_result["success"]:
            ai_eval = self.ai_trainer.evaluate_code(user_code, self.current_lesson)
            # Combine evaluations (prefer zero-tolerance if available)
            if zero_tolerance_eval["correct"]:
                final_eval = zero_tolerance_eval
            else:
                final_eval = ai_eval if ai_eval.get("correct", False) else local_eval
        else:
            final_eval = zero_tolerance_eval if zero_tolerance_eval["correct"] else local_eval
        
        # Calculate reward
        reward = self.reward_system.calculate_reward(final_eval, self.current_language)
        
        # Only grant reward if code is truly correct (zero mistakes)
        if not final_eval.get("correct", False):
            reward["fed"] = False
            reward["reward"] = 0.0
            reward["reason"] = "Code contains errors - zero tolerance mode"
        
        # Grant reward if earned
        if reward["fed"]:
            self.reward_system.grant_reward(reward)
        
        # Update skill tracking
        if final_eval.get("correct", False):
            # Determine which skill was practiced
            skill = self._determine_skill_from_lesson()
            improvement = reward["quality"] * 0.2  # Scale quality to improvement
            self.skill_tracker.update_skill(self.current_language, skill, improvement)
            self.skill_tracker.record_success(self.current_language)
            
            # Learn from successful interaction
            if self.learning_system:
                self.learning_system.learn_from_interaction({
                    "code": user_code,
                    "language": self.current_language,
                    "success": True,
                    "quality": final_eval.get("quality", 0.0)
                })
        else:
            self.skill_tracker.record_failure()
            
            # Learn from mistake
            if self.learning_system:
                self.learning_system.learn_from_interaction({
                    "code": user_code,
                    "language": self.current_language,
                    "success": False,
                    "errors": final_eval.get("errors", [])
                })
        
        # Record lesson result in AI trainer
        self.ai_trainer.record_lesson_result(self.current_language, final_eval.get("correct", False))
        
        # Check if lesson is complete
        lesson_complete = final_eval.get("correct", False) or self.attempts >= self.max_attempts
        
        if lesson_complete:
            # Move to next lesson
            self.current_lesson = self.curriculum.get_lesson_for_language(
                self.current_language, 
                self.current_level
            )
            self.attempts = 0
        
        return {
            "success": True,
            "evaluation": final_eval,
            "reward": reward,
            "lesson_complete": lesson_complete,
            "attempts": self.attempts,
            "skill_progress": self.skill_tracker.get_language_progress(self.current_language),
            "hunger_status": self.reward_system.get_hunger_status()
        }
    
    def _determine_skill_from_lesson(self) -> str:
        """Determine which skill is being practiced based on current lesson"""
        # Simplified skill determination
        task = self.current_lesson.get("task", "").lower()
        
        if "function" in task or "def" in task:
            return "functions"
        elif "class" in task:
            return "classes"
        elif "interface" in task:
            return "interfaces"
        elif "type" in task:
            return "types"
        elif "data" in task or "list" in task or "dict" in task:
            return "data_structures"
        else:
            return "basic_syntax"
    
    def get_hint(self) -> str:
        """
        Get a hint for the current lesson
        
        Returns:
            Hint text
        """
        if not self.current_lesson:
            return "No active lesson"
        
        # Record API call
        api_result = self.api_manager.record_api_call("hint", cost=3)
        if not api_result["success"]:
            return "API quota exhausted - cannot get hint"
        
        # Get hint from AI
        hint = self.ai_trainer.provide_hint(
            self.current_lesson,
            "",  # Current code (would be tracked in real implementation)
            self.attempts
        )
        
        return hint
    
    def stop_training(self, reason: str = "User stopped") -> Dict:
        """
        Stop the training session
        
        Args:
            reason: Reason for stopping
            
        Returns:
            Training session summary
        """
        if not self.training_active:
            return {"success": False, "reason": "Training not active"}
        
        self.training_active = False
        self.user_stop_requested = True
        
        # End AI training session
        ai_summary = self.ai_trainer.end_training_session()
        
        # End API session
        api_summary = self.api_manager.end_session("current")
        
        # Disable training mode in reward system
        self.reward_system.set_training_mode(False)
        
        # Get final statistics
        final_stats = self.get_training_statistics()
        
        return {
            "success": True,
            "reason": reason,
            "ai_summary": ai_summary,
            "api_summary": api_summary,
            "final_statistics": final_stats
        }
    
    def get_training_statistics(self) -> Dict:
        """
        Get comprehensive training statistics
        
        Returns:
            Training statistics
        """
        return {
            "training_active": self.training_active,
            "current_language": self.current_language,
            "current_level": self.current_level,
            "api_usage": self.api_manager.get_usage_status(),
            "skill_progress": self.skill_tracker.get_overall_progress(),
            "reward_performance": self.reward_system.get_performance_stats(),
            "hunger_status": self.reward_system.get_hunger_status(),
            "ai_training_progress": self.ai_trainer.get_training_progress(),
            "zero_mistake_mode": True,
            "learning_active": self.learning_system is not None
        }
    
    def change_language(self, new_language: str) -> Dict:
        """
        Change the current training language
        
        Args:
            new_language: New programming language
            
        Returns:
            Change result
        """
        if new_language not in self.curriculum.languages:
            return {
                "success": False,
                "reason": f"Unknown language: {new_language}"
            }
        
        self.current_language = new_language
        self.current_lesson = self.curriculum.get_lesson_for_language(new_language, self.current_level)
        self.attempts = 0
        
        return {
            "success": True,
            "language": new_language,
            "lesson": self.current_lesson["task"]
        }
    
    def change_level(self, new_level: str) -> Dict:
        """
        Change the current training level
        
        Args:
            new_level: New difficulty level
            
        Returns:
            Change result
        """
        if new_level not in ["beginner", "intermediate", "advanced"]:
            return {
                "success": False,
                "reason": f"Unknown level: {new_level}"
            }
        
        self.current_level = new_level
        self.current_lesson = self.curriculum.get_lesson_for_language(self.current_language, new_level)
        self.attempts = 0
        
        return {
            "success": True,
            "level": new_level,
            "lesson": self.current_lesson["task"]
        }
    
    def take_break(self, duration: float = 60.0) -> Dict:
        """
        Take a break from training
        
        Args:
            duration: Break duration in seconds
            
        Returns:
            Break information
        """
        # Simulate hunger during break
        self.reward_system.hunger_system.update_hunger(duration, activity_level=0.1)
        
        return {
            "success": True,
            "duration": duration,
            "new_energy": self.reward_system.hunger_system.energy,
            "new_hunger_drive": self.reward_system.hunger_system.hunger_drive
        }
    
    def can_train(self) -> Dict:
        """
        Check if training can continue
        
        Returns:
            Whether training can continue and reasons
        """
        checks = {
            "api_quota": self.api_manager.can_make_api_call(cost=10),
            "hunger_status": self.reward_system.check_hunger_can_train(),
            "user_stop": not self.user_stop_requested
        }
        
        can_train = all([
            checks["api_quota"]["can_call"],
            checks["hunger_status"]["can_train"],
            checks["user_stop"]
        ])
        
        return {
            "can_train": can_train,
            "checks": checks,
            "reason": "All checks passed" if can_train else "Training cannot continue"
        }


if __name__ == "__main__":
    # Test the training coordinator
    print("Testing Training Coordinator...")
    
    coordinator = TrainingCoordinator()
    
    # Test starting training
    print("\nTesting starting training...")
    # Simulate some hunger first
    coordinator.reward_system.hunger_system.update_hunger(50.0, activity_level=0.5)
    start_result = coordinator.start_training("python", "beginner")
    print(f"Start result: {start_result}")
    
    # Test getting lesson instruction
    print("\nTesting getting lesson instruction...")
    instruction = coordinator.get_lesson_instruction()
    print(f"Instruction length: {len(instruction)} chars")
    
    # Test submitting code
    print("\nTesting submitting code...")
    submit_result = coordinator.submit_code("def add_numbers(a, b):\n    return a + b")
    print(f"Submit result: {submit_result}")
    
    # Test getting training statistics
    print("\nTesting getting training statistics...")
    stats = coordinator.get_training_statistics()
    print(f"Training statistics available: {len(stats)} components")
    
    # Test stopping training
    print("\nTesting stopping training...")
    stop_result = coordinator.stop_training("Test complete")
    print(f"Stop result: {stop_result}")
    
    print("Training coordinator test completed!")