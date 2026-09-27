"""
Skill Tracking System
Tracks skill development and progress across programming languages
"""

import json
import time
from typing import Dict, List, Optional
from datetime import datetime

class SkillTrackingSystem:
    """
    Tracks skill development and progress across programming languages
    """
    
    def __init__(self):
        """Initialize the skill tracking system"""
        # Define supported languages and their skills
        self.language_skills = {
            "python": ["basic_syntax", "data_structures", "functions", "classes", "xml_processing"],
            "typescript": ["basic_syntax", "types", "interfaces", "classes", "xml_handling"],
            "javascript": ["basic_syntax", "dom_manipulation", "ajax", "xml_processing"],
            "css": ["selectors", "properties", "layouts", "xml_in_css"],
            "html": ["elements", "attributes", "structure", "xml_html"],
            "json": ["parsing", "serialization", "xml_conversion"],
            "graphql": ["schema", "queries", "mutations", "xml_alternatives"],
            "toml": ["parsing", "serialization", "configuration"],
            "yaml": ["parsing", "serialization", "configuration"],
            "ini": ["parsing", "configuration", "basic_structure"],
            "xml_rpc": ["protocols", "serialization", "remote_calls"],
            "soap": ["protocols", "wsdl", "envelopes", "xml_messaging"],
            # Additional advanced languages
            "rust": ["basic_syntax", "memory_safety", "ownership", "lifetimes", "concurrency"],
            "c++": ["basic_syntax", "memory_management", "pointers", "templates", "stl"],
            "c#": ["basic_syntax", "dotnet", "linq", "async", "generics"],
            "go": ["basic_syntax", "concurrency", "interfaces", "goroutines", "channels"],
            "java": ["basic_syntax", "oop", "streams", "generics", "spring"],
            "swift": ["basic_syntax", "optionals", "closures", "protocols", "ios_development"],
            "kotlin": ["basic_syntax", "null_safety", "coroutines", "android", "interoperability"],
            "php": ["basic_syntax", "web_development", "frameworks", "databases", "security"],
            "ruby": ["basic_syntax", "metaprogramming", "rails", "blocks", "gems"],
            "sql": ["basic_syntax", "queries", "joins", "aggregation", "optimization"],
            # Additional format languages
            "protobuf": ["schema_definition", "serialization", "deserialization", "grpc"],
            "avro": ["schema_definition", "serialization", "evolution", "compression"],
            "msgpack": ["serialization", "binary_format", "efficiency", "compatibility"],
            "cbor": ["serialization", "binary_format", "conciseness", "extensibility"],
            "bson": ["serialization", "binary_format", "document_model", "mongodb"]
        }
        
        # Skill levels (0.0 to 1.0)
        self.skill_levels = {lang: {skill: 0.0 for skill in skills} 
                            for lang, skills in self.language_skills.items()}
        
        # Practice history
        self.practice_history = []
        self.language_mastery = {lang: 0.0 for lang in self.language_skills}
        
        # Achievement tracking
        self.achievements = {
            "first_lesson": False,
            "skill_mastered": False,
            "language_mastered": False,
            "streak_5": False,
            "streak_10": False,
            "multi_linguist": False
        }
        
        # Current streak
        self.current_streak = 0
        self.best_streak = 0
        
        print(f"Skill tracking system initialized for {len(self.language_skills)} languages")
    
    def update_skill(self, language: str, skill: str, improvement: float) -> Dict:
        """
        Update skill level for a specific language and skill
        
        Args:
            language: Programming language
            skill: Specific skill
            improvement: Improvement amount (0-1)
            
        Returns:
            Updated skill information
        """
        if language not in self.skill_levels:
            return {"error": f"Unknown language: {language}"}
        
        if skill not in self.skill_levels[language]:
            return {"error": f"Unknown skill for {language}: {skill}"}
        
        # Update skill level
        current_level = self.skill_levels[language][skill]
        new_level = min(1.0, current_level + improvement)
        self.skill_levels[language][skill] = new_level
        
        # Update language mastery
        self._update_language_mastery(language)
        
        # Record practice
        practice_record = {
            "timestamp": time.time(),
            "language": language,
            "skill": skill,
            "previous_level": current_level,
            "new_level": new_level,
            "improvement": improvement
        }
        self.practice_history.append(practice_record)
        
        # Check achievements
        self._check_achievements()
        
        return {
            "language": language,
            "skill": skill,
            "previous_level": current_level,
            "new_level": new_level,
            "improvement": improvement,
            "language_mastery": self.language_mastery[language]
        }
    
    def _update_language_mastery(self, language: str):
        """Update overall mastery level for a language"""
        skills = self.skill_levels[language]
        if skills:
            avg_skill = sum(skills.values()) / len(skills)
            self.language_mastery[language] = avg_skill
    
    def get_skill_level(self, language: str, skill: str) -> float:
        """
        Get current skill level
        
        Args:
            language: Programming language
            skill: Specific skill
            
        Returns:
            Skill level (0.0 to 1.0)
        """
        if language in self.skill_levels and skill in self.skill_levels[language]:
            return self.skill_levels[language][skill]
        return 0.0
    
    def get_language_progress(self, language: str) -> Dict:
        """
        Get detailed progress for a specific language
        
        Args:
            language: Programming language
            
        Returns:
            Language progress information
        """
        if language not in self.skill_levels:
            return {"error": f"Unknown language: {language}"}
        
        skills = self.skill_levels[language]
        mastery = self.language_mastery[language]
        
        # Count mastered skills (>= 0.9)
        mastered_skills = sum(1 for level in skills.values() if level >= 0.9)
        
        # Count skills in progress (>= 0.5)
        in_progress = sum(1 for level in skills.values() if 0.5 <= level < 0.9)
        
        return {
            "language": language,
            "mastery": mastery,
            "skills": skills,
            "total_skills": len(skills),
            "mastered_skills": mastered_skills,
            "in_progress": in_progress,
            "not_started": len(skills) - mastered_skills - in_progress
        }
    
    def get_overall_progress(self) -> Dict:
        """Get overall progress across all languages"""
        total_languages = len(self.language_skills)
        total_skills = sum(len(skills) for skills in self.language_skills.values())
        
        # Calculate total mastery
        total_mastery = sum(self.language_mastery.values()) / total_languages if total_languages > 0 else 0.0
        
        # Count mastered languages (>= 0.8 average)
        mastered_languages = sum(1 for mastery in self.language_mastery.values() if mastery >= 0.8)
        
        # Count languages with any progress
        languages_in_progress = sum(1 for mastery in self.language_mastery.values() if mastery > 0.0)
        
        return {
            "total_languages": total_languages,
            "total_skills": total_skills,
            "overall_mastery": total_mastery,
            "mastered_languages": mastered_languages,
            "languages_in_progress": languages_in_progress,
            "language_mastery": self.language_mastery,
            "achievements": self.achievements,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak
        }
    
    def record_success(self, language: str):
        """
        Record a successful lesson completion
        
        Args:
            language: Programming language
        """
        self.current_streak += 1
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        
        # Mark first lesson achievement
        if not self.achievements["first_lesson"]:
            self.achievements["first_lesson"] = True
        
        # Check streak achievements
        if self.current_streak >= 5:
            self.achievements["streak_5"] = True
        if self.current_streak >= 10:
            self.achievements["streak_10"] = True
        
        self._check_achievements()
    
    def record_failure(self):
        """Record a failed lesson"""
        self.current_streak = 0
    
    def _check_achievements(self):
        """Check and update achievements"""
        # Check for skill mastery
        for lang_skills in self.skill_levels.values():
            for skill_level in lang_skills.values():
                if skill_level >= 0.9:
                    self.achievements["skill_mastered"] = True
                    break
        
        # Check for language mastery
        for mastery in self.language_mastery.values():
            if mastery >= 0.8:
                self.achievements["language_mastered"] = True
                break
        
        # Check for multi-linguist (3+ languages with progress)
        languages_with_progress = sum(1 for mastery in self.language_mastery.values() if mastery > 0.0)
        if languages_with_progress >= 3:
            self.achievements["multi_linguist"] = True
    
    def get_achievements(self) -> Dict:
        """Get current achievements"""
        return {
            "achievements": self.achievements,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "total_practice_sessions": len(self.practice_history)
        }
    
    def get_recommended_lesson(self) -> Dict:
        """
        Get recommended next lesson based on current progress
        
        Returns:
            Recommended lesson information
        """
        # Find language with lowest mastery
        lowest_mastery_lang = min(self.language_mastery.items(), key=lambda x: x[1])[0]
        
        # Find lowest skill in that language
        skills = self.skill_levels[lowest_mastery_lang]
        lowest_skill = min(skills.items(), key=lambda x: x[1])[0]
        
        return {
            "language": lowest_mastery_lang,
            "skill": lowest_skill,
            "current_level": skills[lowest_skill],
            "reason": f"Focus on {lowest_mastery_lang} {lowest_skill} to improve overall mastery"
        }
    
    def get_practice_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent practice history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Recent practice records
        """
        return self.practice_history[-limit:] if self.practice_history else []
    
    def save_progress(self, filepath: str):
        """
        Save progress to file
        
        Args:
            filepath: Path to save file
        """
        data = {
            "skill_levels": self.skill_levels,
            "language_mastery": self.language_mastery,
            "achievements": self.achievements,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "practice_history": self.practice_history[-100:]  # Save last 100 records
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Progress saved to {filepath}")
    
    def load_progress(self, filepath: str):
        """
        Load progress from file
        
        Args:
            filepath: Path to load file
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.skill_levels = data.get("skill_levels", self.skill_levels)
            self.language_mastery = data.get("language_mastery", self.language_mastery)
            self.achievements = data.get("achievements", self.achievements)
            self.current_streak = data.get("current_streak", 0)
            self.best_streak = data.get("best_streak", 0)
            self.practice_history = data.get("practice_history", [])
            
            print(f"Progress loaded from {filepath}")
            
        except FileNotFoundError:
            print(f"No progress file found at {filepath}")
        except Exception as e:
            print(f"Error loading progress: {e}")
    
    def reset_progress(self):
        """Reset all progress"""
        self.skill_levels = {lang: {skill: 0.0 for skill in skills} 
                            for lang, skills in self.language_skills.items()}
        self.language_mastery = {lang: 0.0 for lang in self.language_skills}
        self.practice_history = []
        self.achievements = {
            "first_lesson": False,
            "skill_mastered": False,
            "language_mastered": False,
            "streak_5": False,
            "streak_10": False,
            "multi_linguist": False
        }
        self.current_streak = 0
        self.best_streak = 0
        
        print("Skill tracking progress reset")


if __name__ == "__main__":
    # Test the skill tracking system
    print("Testing Skill Tracking System...")
    
    skill_tracker = SkillTrackingSystem()
    
    # Test skill updates
    print("\nTesting skill updates...")
    result = skill_tracker.update_skill("python", "basic_syntax", 0.3)
    print(f"Skill update result: {result}")
    
    result = skill_tracker.update_skill("python", "functions", 0.5)
    print(f"Skill update result: {result}")
    
    # Test language progress
    print("\nTesting language progress...")
    progress = skill_tracker.get_language_progress("python")
    print(f"Python progress: {progress}")
    
    # Test overall progress
    print("\nTesting overall progress...")
    overall = skill_tracker.get_overall_progress()
    print(f"Overall progress: {overall}")
    
    # Test success/failure recording
    print("\nTesting success/failure recording...")
    skill_tracker.record_success("python")
    skill_tracker.record_success("python")
    skill_tracker.record_success("typescript")
    achievements = skill_tracker.get_achievements()
    print(f"Achievements: {achievements}")
    
    # Test recommended lesson
    print("\nTesting recommended lesson...")
    recommendation = skill_tracker.get_recommended_lesson()
    print(f"Recommended lesson: {recommendation}")
    
    # Test practice history
    print("\nTesting practice history...")
    history = skill_tracker.get_practice_history(5)
    print(f"Practice history: {history}")
    
    print("Skill tracking system test completed!")