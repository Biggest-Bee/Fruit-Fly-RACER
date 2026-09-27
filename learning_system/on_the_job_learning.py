"""
On-the-Job Learning System
Local memory management for continuous learning from user's computer environment
No external databases - all local file-based storage
"""

import json
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import pickle
import hashlib
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .memory_integrity import MemoryIntegrity, TruthVerifier
except ImportError:
    from memory_integrity import MemoryIntegrity, TruthVerifier

class OnTheJobLearningSystem:
    """
    On-the-job learning system with local memory management
    All storage is local file-based, no external databases
    """
    
    def __init__(self, memory_dir: str = "fly_memory"):
        """
        Initialize the on-the-job learning system
        
        Args:
            memory_dir: Directory for local memory storage
        """
        self.memory_dir = memory_dir
        self.short_term_memory = {}  # Volatile memory for current session
        self.long_term_memory = {}  # Persistent memory across sessions
        self.context_memory = {}  # Context-aware memory
        self.learning_cache = {}  # Cached learning results
        
        # Memory management
        self.max_short_term_size = 1000  # Max items in short-term memory
        self.max_long_term_size = 10000  # Max items in long-term memory
        self.memory_retention_time = 7 * 24 * 3600  # 7 days in seconds
        
        # Memory integrity: older memories are protected from conflicting claims,
        # and user statements are verified before they are believed.
        self.integrity = MemoryIntegrity()
        self.truth_verifier = TruthVerifier(self.integrity)
        self.conflict_log: List[Dict] = []
        
        # Create memory directory
        os.makedirs(memory_dir, exist_ok=True)
        
        # Initialize memory files
        self._init_memory_files()
        
        # Load existing long-term memory
        self._load_long_term_memory()
        
        print(f"On-the-job learning system initialized with local memory at {memory_dir}")
    
    def _init_memory_files(self):
        """Initialize local memory files"""
        self.short_term_file = os.path.join(self.memory_dir, "short_term_memory.json")
        self.long_term_file = os.path.join(self.memory_dir, "long_term_memory.json")
        self.context_file = os.path.join(self.memory_dir, "context_memory.json")
        self.learning_cache_file = os.path.join(self.memory_dir, "learning_cache.json")
        self.user_preferences_file = os.path.join(self.memory_dir, "user_preferences.json")
        self.interaction_history_file = os.path.join(self.memory_dir, "interaction_history.json")
    
    def _load_long_term_memory(self):
        """Load long-term memory from local file"""
        try:
            if os.path.exists(self.long_term_file):
                with open(self.long_term_file, 'r') as f:
                    self.long_term_memory = json.load(f)
                print(f"Loaded {len(self.long_term_memory)} items from long-term memory")
        except Exception as e:
            print(f"Could not load long-term memory: {e}")
            self.long_term_memory = {}
    
    def _save_long_term_memory(self):
        """Save long-term memory to local file"""
        try:
            with open(self.long_term_file, 'w') as f:
                json.dump(self.long_term_memory, f, indent=2)
        except Exception as e:
            print(f"Could not save long-term memory: {e}")
    
    def store_short_term(self, key: str, value: Any, category: str = "general"):
        """
        Store information in short-term memory
        
        Args:
            key: Memory key
            value: Value to store
            category: Memory category
        """
        if category not in self.short_term_memory:
            self.short_term_memory[category] = {}
        
        self.short_term_memory[category][key] = {
            "value": value,
            "timestamp": time.time(),
            "access_count": 0
        }
        
        # Enforce size limit
        if len(self.short_term_memory[category]) > self.max_short_term_size:
            # Remove oldest items
            sorted_items = sorted(
                self.short_term_memory[category].items(),
                key=lambda x: x[1]["timestamp"]
            )
            self.short_term_memory[category] = dict(sorted_items[-self.max_short_term_size:])
    
    def retrieve_short_term(self, key: str, category: str = "general") -> Optional[Any]:
        """
        Retrieve information from short-term memory
        
        Args:
            key: Memory key
            category: Memory category
            
        Returns:
            Stored value or None
        """
        if category in self.short_term_memory and key in self.short_term_memory[category]:
            item = self.short_term_memory[category][key]
            item["access_count"] += 1
            return item["value"]
        return None
    
    def store_long_term(self, key: str, value: Any, category: str = "knowledge",
                        importance: float = 0.5, source: str = "observation",
                        evidence: Optional[str] = None) -> Dict:
        """
        Store information in long-term memory without losing what came before
        
        A value that conflicts with an established memory does not overwrite it.
        The older memory is kept and the new claim is recorded as disputed until
        it is backed by evidence or repeated corroboration.
        
        Args:
            key: Memory key
            value: Value to store
            category: Memory category
            importance: Importance score (0-1) for retention
            source: Where the information came from (observation, system, user, ...)
            evidence: Optional description of the evidence behind the value
            
        Returns:
            Outcome dict describing what happened to the memory
        """
        if category not in self.long_term_memory:
            self.long_term_memory[category] = {}
        
        existing = self.long_term_memory[category].get(key)
        if existing is None:
            record = self.integrity.new_record(value, source=source, importance=importance)
            if evidence:
                record["evidence"] = evidence
            outcome = {
                "action": "stored",
                "accepted": True,
                "kept_value": value,
                "reason": "nothing was remembered under this key yet",
            }
        else:
            record, outcome = self.integrity.resolve(
                existing, value, source=source, importance=importance,
                evidence=evidence
            )
        
        self.long_term_memory[category][key] = record
        
        if outcome["action"] in ("kept_older", "replaced"):
            self.conflict_log.append({
                "category": category,
                "key": key,
                "timestamp": time.time(),
                **outcome,
            })
        
        # Save to file
        self._save_long_term_memory()
        return outcome
    
    def learn_from_user_statement(self, statement: str, key: str, value: Any,
                                  category: str = "knowledge",
                                  importance: float = 0.5) -> Dict:
        """
        Take in something the user said, after checking whether it is true
        
        The statement is verified against the fly's own observations and its
        existing memories first. A contradicted statement is never stored as
        fact, which is what stops the fly from being talked out of what it knows.
        
        Args:
            statement: What the user said
            key: Memory key the statement is about
            value: The value the statement asserts
            category: Memory category
            importance: Importance score (0-1)
            
        Returns:
            Dict with the verification verdict, what was done, and a reply
        """
        known = self.long_term_memory.get(category, {}).get(key)
        verdict = self.truth_verifier.verify(
            statement, key=key, value=value, known_memory=known, source="user"
        )
        
        if verdict["believe"]:
            outcome = self.store_long_term(
                key, value, category=category, importance=importance,
                source="user", evidence=statement if not verdict["pressure_detected"] else None
            )
        else:
            # Still record the disagreement so repeated, evidenced claims can
            # eventually win, but do not change what the fly believes now.
            if known is not None:
                record, outcome = self.integrity.resolve(
                    known, value, source="user", importance=importance,
                    confidence=verdict["confidence"],
                    evidence=None,
                )
                self.long_term_memory[category][key] = record
                self._save_long_term_memory()
            else:
                outcome = {
                    "action": "rejected",
                    "accepted": False,
                    "reason": "statement could not be verified",
                }
            self.conflict_log.append({
                "category": category,
                "key": key,
                "timestamp": time.time(),
                **outcome,
            })
        
        return {
            "verdict": verdict,
            "outcome": outcome,
            "reply": self.truth_verifier.explain(verdict),
        }
    
    def record_observation(self, key: str, value: Any, category: str = "knowledge",
                           importance: float = 0.8) -> Dict:
        """
        Record something the fly established first hand
        
        First-hand observations are the strongest evidence the fly has, so they
        take precedence over anything it has merely been told.
        """
        self.truth_verifier.record_observation(key, value)
        return self.store_long_term(key, value, category=category,
                                    importance=importance, source="observation")
    
    def get_conflicts(self, category: Optional[str] = None) -> List[Dict]:
        """Get the memory conflicts the fly has run into"""
        if category is None:
            return list(self.conflict_log)
        return [c for c in self.conflict_log if c["category"] == category]
    
    def retrieve_long_term(self, key: str, category: str = "knowledge") -> Optional[Any]:
        """
        Retrieve information from long-term memory
        
        Args:
            key: Memory key
            category: Memory category
            
        Returns:
            Stored value or None
        """
        if category in self.long_term_memory and key in self.long_term_memory[category]:
            item = self.long_term_memory[category][key]
            item["access_count"] += 1
            item["last_accessed"] = time.time()
            self._save_long_term_memory()
            return item["value"]
        return None
    
    def learn_from_interaction(self, interaction: Dict):
        """
        Learn from user interaction
        
        Args:
            interaction: Interaction data including context, code, feedback
        """
        # Store in short-term memory
        interaction_key = f"interaction_{int(time.time())}"
        self.store_short_term(interaction_key, interaction, "interactions")
        
        # Extract learning patterns
        if "code" in interaction and "language" in interaction:
            language = interaction["language"]
            code = interaction["code"]
            
            # Learn code patterns
            code_pattern = self._extract_code_pattern(code, language)
            pattern_key = f"{language}_pattern_{hash(code_pattern)}"
            
            # Check if pattern is already known
            existing = self.retrieve_long_term(pattern_key, "code_patterns")
            if existing:
                # Reinforce existing pattern
                existing["frequency"] = existing.get("frequency", 0) + 1
                self.store_long_term(pattern_key, existing, "code_patterns", importance=0.7)
            else:
                # Learn new pattern
                self.store_long_term(pattern_key, {
                    "pattern": code_pattern,
                    "language": language,
                    "frequency": 1,
                    "success_rate": interaction.get("success", 0.0)
                }, "code_patterns", importance=0.7)
        
        # Store interaction history
        self._add_to_interaction_history(interaction)
    
    def _extract_code_pattern(self, code: str, language: str) -> str:
        """Extract simplified code pattern"""
        # Normalize code for pattern extraction
        normalized = code.strip().lower()
        
        # Remove comments and extra whitespace
        lines = normalized.split('\n')
        pattern_lines = []
        
        for line in lines:
            if line and not line.startswith('#') and not line.startswith('//'):
                # Remove extra spaces
                pattern_line = ' '.join(line.split())
                pattern_lines.append(pattern_line)
        
        return '\n'.join(pattern_lines)
    
    def _add_to_interaction_history(self, interaction: Dict):
        """Add interaction to history"""
        history = []
        if os.path.exists(self.interaction_history_file):
            try:
                with open(self.interaction_history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append({
            "timestamp": time.time(),
            "interaction": interaction
        })
        
        # Keep only last 1000 interactions
        if len(history) > 1000:
            history = history[-1000:]
        
        try:
            with open(self.interaction_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Could not save interaction history: {e}")
    
    def learn_from_file(self, file_path: str, content: str, language: str):
        """
        Learn from file created or accessed by the fly
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
        """
        file_key = f"file_{hashlib.md5(file_path.encode()).hexdigest()}"
        
        # Learn file structure
        file_structure = {
            "path": file_path,
            "language": language,
            "size": len(content),
            "lines": len(content.split('\n')),
            "complexity": self._calculate_complexity(content, language),
            "last_modified": time.time()
        }
        
        self.store_long_term(file_key, file_structure, "files", importance=0.8)
        
        # Learn from code patterns in file
        if language in ["python", "javascript", "typescript", "rust", "c++", "c#", "go", "java"]:
            patterns = self._extract_all_patterns(content, language)
            for pattern in patterns:
                pattern_key = f"{language}_pattern_{hash(pattern)}"
                existing = self.retrieve_long_term(pattern_key, "code_patterns")
                if existing:
                    existing["frequency"] = existing.get("frequency", 0) + 1
                    self.store_long_term(pattern_key, existing, "code_patterns", importance=0.6)
                else:
                    self.store_long_term(pattern_key, {
                        "pattern": pattern,
                        "language": language,
                        "frequency": 1,
                        "source_file": file_path
                    }, "code_patterns", importance=0.6)
    
    def _calculate_complexity(self, content: str, language: str) -> float:
        """Calculate code complexity score"""
        complexity = 0.0
        
        # Lines of code
        lines = content.split('\n')
        complexity += len(lines) * 0.1
        
        # Indentation depth
        for line in lines:
            indent = len(line) - len(line.lstrip())
            complexity += indent * 0.05
        
        # Special characters
        complexity += content.count('{') * 0.2
        complexity += content.count('(') * 0.1
        complexity += content.count('[') * 0.1
        
        return min(1.0, complexity / 100.0)
    
    def _extract_all_patterns(self, content: str, language: str) -> List[str]:
        """Extract all code patterns from content"""
        patterns = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                # Extract structure patterns
                if "def " in line or "function " in line:
                    patterns.append(f"function_definition:{line[:50]}")
                elif "class " in line:
                    patterns.append(f"class_definition:{line[:50]}")
                elif "if " in line:
                    patterns.append(f"conditional:{line[:50]}")
                elif "for " in line or "while " in line:
                    patterns.append(f"loop:{line[:50]}")
                elif "import " in line or "from " in line:
                    patterns.append(f"import:{line[:50]}")
        
        return patterns
    
    def get_learning_context(self, current_context: Dict) -> Dict:
        """
        Get relevant learning context based on current situation
        
        Args:
            current_context: Current context (language, task, etc.)
            
        Returns:
            Relevant learning context
        """
        context_key = f"context_{hash(str(current_context))}"
        
        # Check if context is cached
        cached = self.retrieve_short_term(context_key, "context_cache")
        if cached:
            return cached
        
        # Build context from memory
        relevant_context = {
            "current_language": current_context.get("language", "python"),
            "recent_patterns": self._get_recent_patterns(current_context.get("language", "python")),
            "user_preferences": self._get_user_preferences(),
            "learning_progress": self._get_learning_progress(current_context.get("language", "python")),
            "common_mistakes": self._get_common_mistakes(current_context.get("language", "python"))
        }
        
        # Cache context
        self.store_short_term(context_key, relevant_context, "context_cache")
        
        return relevant_context
    
    def _get_recent_patterns(self, language: str) -> List[str]:
        """Get recent code patterns for a language"""
        patterns = []
        
        # Get patterns from long-term memory
        if "code_patterns" in self.long_term_memory:
            for key, pattern_data in self.long_term_memory["code_patterns"].items():
                if pattern_data.get("language") == language:
                    patterns.append(pattern_data.get("pattern", ""))
        
        return patterns[:10]  # Return top 10 most recent
    
    def _get_user_preferences(self) -> Dict:
        """Get learned user preferences"""
        # Load from file
        if os.path.exists(self.user_preferences_file):
            try:
                with open(self.user_preferences_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "preferred_languages": ["python"],
            "preferred_complexity": "intermediate",
            "learning_style": "incremental"
        }
    
    def _get_learning_progress(self, language: str) -> Dict:
        """Get learning progress for a language"""
        progress = {
            "patterns_learned": 0,
            "files_processed": 0,
            "total_interactions": 0
        }
        
        if "code_patterns" in self.long_term_memory:
            for key, pattern_data in self.long_term_memory["code_patterns"].items():
                if pattern_data.get("language") == language:
                    progress["patterns_learned"] += 1
        
        if "files" in self.long_term_memory:
            for key, file_data in self.long_term_memory["files"].items():
                if file_data.get("language") == language:
                    progress["files_processed"] += 1
        
        # Count interactions
        if "interactions" in self.short_term_memory:
            progress["total_interactions"] = len(self.short_term_memory["interactions"])
        
        return progress
    
    def _get_common_mistakes(self, language: str) -> List[str]:
        """Get common mistakes to avoid"""
        mistakes = []
        
        # Analyze interaction history for mistakes
        if os.path.exists(self.interaction_history_file):
            try:
                with open(self.interaction_history_file, 'r') as f:
                    history = json.load(f)
                
                for item in history[-50:]:  # Last 50 interactions
                    interaction = item.get("interaction", {})
                    if not interaction.get("success", True):
                        if "code" in interaction:
                            mistake_pattern = self._extract_code_pattern(
                                interaction["code"],
                                interaction.get("language", language)
                            )
                            mistakes.append(mistake_pattern)
            except:
                pass
        
        return list(set(mistakes))  # Remove duplicates
    
    def adapt_to_environment(self, environment_info: Dict):
        """
        Adapt learning system to user's computer environment
        
        Args:
            environment_info: Information about the user's environment
        """
        # Store environment context
        env_key = f"environment_{hash(str(environment_info))}"
        self.store_long_term(env_key, environment_info, "environment", importance=0.9)
        
        # Learn optimal learning times
        current_hour = datetime.now().hour
        self.store_short_term("learning_time", current_hour, "environment")
        
        # Learn from file system structure
        if "file_structure" in environment_info:
            for path, info in environment_info["file_structure"].items():
                self.learn_from_file(path, info.get("content", ""), info.get("language", "text"))
    
    def get_memory_statistics(self) -> Dict:
        """Get memory system statistics"""
        short_term_size = sum(len(category) for category in self.short_term_memory.values())
        long_term_size = sum(len(category) for category in self.long_term_memory.values())
        
        return {
            "memory_dir": self.memory_dir,
            "short_term_memory_size": short_term_size,
            "long_term_memory_size": long_term_size,
            "max_short_term_size": self.max_short_term_size,
            "max_long_term_size": self.max_long_term_size,
            "categories": {
                "short_term": list(self.short_term_memory.keys()),
                "long_term": list(self.long_term_memory.keys())
            },
            "storage_size_mb": self._get_storage_size()
        }
    
    def _get_storage_size(self) -> float:
        """Get total storage size in MB"""
        total_size = 0
        
        for filename in os.listdir(self.memory_dir):
            file_path = os.path.join(self.memory_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def clean_old_memory(self):
        """Clean old memory items based on retention time"""
        current_time = time.time()
        
        # Clean long-term memory
        for category in self.long_term_memory:
            keys_to_remove = []
            
            for key, item in self.long_term_memory[category].items():
                age = current_time - item.get("timestamp", current_time)
                
                # Remove if older than retention time and low importance
                if age > self.memory_retention_time and item.get("importance", 0.5) < 0.3:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.long_term_memory[category][key]
        
        if keys_to_remove:
            self._save_long_term_memory()
            print(f"Cleaned {len(keys_to_remove)} old memory items")
    
    def export_memory(self, export_path: str):
        """
        Export memory to file for backup
        
        Args:
            export_path: Path to export memory
        """
        try:
            memory_data = {
                "short_term_memory": self.short_term_memory,
                "long_term_memory": self.long_term_memory,
                "context_memory": self.context_memory,
                "export_timestamp": time.time()
            }
            
            with open(export_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            print(f"Memory exported to {export_path}")
            return True
            
        except Exception as e:
            print(f"Failed to export memory: {e}")
            return False
    
    def import_memory(self, import_path: str):
        """
        Import memory from file
        
        Args:
            import_path: Path to import memory from
        """
        try:
            with open(import_path, 'r') as f:
                memory_data = json.load(f)
            
            self.short_term_memory = memory_data.get("short_term_memory", {})
            self.long_term_memory = memory_data.get("long_term_memory", {})
            self.context_memory = memory_data.get("context_memory", {})
            
            print(f"Memory imported from {import_path}")
            return True
            
        except Exception as e:
            print(f"Failed to import memory: {e}")
            return False


if __name__ == "__main__":
    # Test the on-the-job learning system
    print("Testing On-the-Job Learning System...")
    
    learning_system = OnTheJobLearningSystem()
    
    # Test short-term memory
    print("\nTesting short-term memory...")
    learning_system.store_short_term("test_key", "test_value", "general")
    retrieved = learning_system.retrieve_short_term("test_key", "general")
    print(f"Short-term memory: Retrieved = {retrieved}")
    
    # Test long-term memory
    print("\nTesting long-term memory...")
    learning_system.store_long_term("python_basics", {"status": "learned"}, "knowledge", importance=0.8)
    retrieved = learning_system.retrieve_long_term("python_basics", "knowledge")
    print(f"Long-term memory: Retrieved = {retrieved}")
    
    # Test learning from interaction
    print("\nTesting learning from interaction...")
    interaction = {
        "code": "def test(): return 42",
        "language": "python",
        "success": True
    }
    learning_system.learn_from_interaction(interaction)
    print("Interaction learned")
    
    # Test learning from file
    print("\nTesting learning from file...")
    learning_system.learn_from_file("test.py", "def test():\n    return 42", "python")
    print("File learned")
    
    # Test memory statistics
    print("\nTesting memory statistics...")
    stats = learning_system.get_memory_statistics()
    print(f"Memory statistics: {stats}")
    
    # Test context retrieval
    print("\nTesting context retrieval...")
    context = learning_system.get_learning_context({"language": "python"})
    print(f"Context retrieved: {len(context)} components")
    
    print("On-the-job learning system test completed!")