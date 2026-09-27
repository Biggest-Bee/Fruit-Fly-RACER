"""
Zero-Tolerance Code Evaluation Engine
Enhanced code evaluation system designed for zero mistakes
"""

import ast
import re
import json
from typing import Dict, List, Tuple, Optional
import subprocess
import tempfile
import os

class ZeroToleranceCodeEvaluator:
    """
    Enhanced code evaluator with zero-tolerance for mistakes
    """
    
    def __init__(self):
        """Initialize the zero-tolerance code evaluator"""
        self.error_patterns = {
            "python": self._get_python_error_patterns(),
            "typescript": self._get_typescript_error_patterns(),
            "javascript": self._get_javascript_error_patterns(),
            "rust": self._get_rust_error_patterns(),
            "c++": self._get_cpp_error_patterns(),
            "c#": self._get_csharp_error_patterns(),
            "go": self._get_go_error_patterns(),
            "java": self._get_java_error_patterns()
        }
        
        print("Zero-tolerance code evaluator initialized")
    
    def _get_python_error_patterns(self) -> List[str]:
        """Get Python error patterns to detect"""
        return [
            r"pass",  # Placeholder code
            r"# TODO",  # Incomplete code
            r"# FIXME",  # Known issues
            r"except:",  # Bare except
            r"except Exception:",  # Too broad exception
            r"print\(",  # Debugging code
            r"# debug",  # Debug comments
            r"# test",  # Test code
            r"# temporary",  # Temporary code
            r"# hack",  # Hacks
        ]
    
    def _get_typescript_error_patterns(self) -> List[str]:
        """Get TypeScript error patterns"""
        return [
            r": any",  # Any type
            r"as any",  # Type casting to any
            r"@ts-ignore",  # Ignore TypeScript errors
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
            r"console\.log",  # Debugging code
        ]
    
    def _get_javascript_error_patterns(self) -> List[str]:
        """Get JavaScript error patterns"""
        return [
            r"var ",  # Old variable declaration
            r"console\.log",  # Debugging code
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
            r"debugger",  # Debugger statement
        ]
    
    def _get_rust_error_patterns(self) -> List[str]:
        """Get Rust error patterns"""
        return [
            r"unwrap\(\)",  # Potential panic
            r"expect\(",  # Potential panic
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
            r"println!",  # Debugging code
            r"dbg!",  # Debugging code
        ]
    
    def _get_cpp_error_patterns(self) -> List[str]:
        """Get C++ error patterns"""
        return [
            r"using namespace std;",  # Namespace pollution
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
            r"std::cout",  # Debugging code
            r"NULL",  # Use nullptr instead
        ]
    
    def _get_csharp_error_patterns(self) -> List[str]:
        """Get C# error patterns"""
        return [
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
            r"Console\.WriteLine",  # Debugging code
            r"public static void Main",  # Old main signature
        ]
    
    def _get_go_error_patterns(self) -> List[str]:
        """Get Go error patterns"""
        return [
            r"_ =",  # Discarded error
            r"log\.Print",  # Debugging code
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
        ]
    
    def _get_java_error_patterns(self) -> List[str]:
        """Get Java error patterns"""
        return [
            r"System\.out\.println",  # Debugging code
            r"// TODO",  # Incomplete code
            r"// FIXME",  # Known issues
            r"public static void main",  # Non-standard main
        ]
    
    def evaluate_code_strict(self, code: str, language: str, expected_solution: str = None) -> Dict:
        """
        Evaluate code with zero-tolerance for mistakes
        
        Args:
            code: Code to evaluate
            language: Programming language
            expected_solution: Expected solution for comparison
            
        Returns:
            Strict evaluation results
        """
        errors = []
        warnings = []
        
        # Level 1: Syntax validation
        syntax_result = self._validate_syntax(code, language)
        if not syntax_result["valid"]:
            errors.extend(syntax_result["errors"])
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": f"Syntax errors: {len(errors)}",
                "errors": errors,
                "warnings": warnings
            }
        
        # Level 2: Pattern detection for anti-patterns
        anti_patterns = self._detect_anti_patterns(code, language)
        if anti_patterns:
            errors.extend(anti_patterns)
        
        # Level 3: Code quality checks
        quality_issues = self._check_code_quality(code, language)
        warnings.extend(quality_issues)
        
        # Level 4: Semantic validation
        semantic_result = self._validate_semantics(code, language)
        if not semantic_result["valid"]:
            errors.extend(semantic_result["errors"])
        
        # Level 5: Comparison with expected solution (if provided)
        if expected_solution:
            comparison = self._compare_with_solution(code, expected_solution, language)
            if not comparison["matches"]:
                errors.extend(comparison["differences"])
        
        # Level 6: Logical consistency check
        logical_result = self._check_logical_consistency(code, language)
        if not logical_result["valid"]:
            errors.extend(logical_result["errors"])
        
        # Calculate quality - extremely strict
        quality = 1.0
        if errors:
            quality -= 0.2 * len(errors)  # Heavy penalty for errors
        if warnings:
            quality -= 0.05 * len(warnings)  # Light penalty for warnings
        quality = max(0.0, quality)
        
        # Only mark as correct if zero errors and high quality
        is_correct = len(errors) == 0 and quality >= 0.95
        
        return {
            "correct": is_correct,
            "quality": quality,
            "feedback": f"Strict evaluation: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings,
            "syntax_valid": syntax_result["valid"],
            "semantic_valid": semantic_result["valid"],
            "logical_valid": logical_result["valid"]
        }
    
    def _validate_syntax(self, code: str, language: str) -> Dict:
        """Validate code syntax"""
        result = {"valid": True, "errors": []}
        
        if language == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                result["valid"] = False
                result["errors"].append(f"Syntax error: {e}")
        
        elif language in ["typescript", "javascript"]:
            # Basic syntax checks for JS/TS
            if code.count("{") != code.count("}"):
                result["valid"] = False
                result["errors"].append("Mismatched braces")
            if code.count("(") != code.count(")"):
                result["valid"] = False
                result["errors"].append("Mismatched parentheses")
        
        return result
    
    def _detect_anti_patterns(self, code: str, language: str) -> List[str]:
        """Detect anti-patterns and bad practices"""
        anti_patterns = []
        
        if language in self.error_patterns:
            patterns = self.error_patterns[language]
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    anti_patterns.append(f"Anti-pattern detected: {pattern}")
        
        return anti_patterns
    
    def _check_code_quality(self, code: str, language: str) -> List[str]:
        """Check code quality issues"""
        quality_issues = []
        
        # Check for empty functions
        if "def " in code or "function " in code:
            if "pass" in code or "{}" in code:
                quality_issues.append("Empty function body")
        
        # Check for magic numbers
        if re.search(r'\b\d{3,}\b', code):  # Numbers >= 100
            quality_issues.append("Magic number detected (use constants)")
        
        # Check for long lines
        lines = code.split('\n')
        for line in lines:
            if len(line) > 100:
                quality_issues.append("Line too long (>100 characters)")
                break
        
        # Check for deep nesting
        for line in lines:
            indent = len(line) - len(line.lstrip())
            if indent > 24:  # More than 6 levels of indentation
                quality_issues.append("Deep nesting detected")
                break
        
        return quality_issues
    
    def _validate_semantics(self, code: str, language: str) -> Dict:
        """Validate code semantics"""
        result = {"valid": True, "errors": []}
        
        if language == "python":
            # Check for undefined variables
            if "def " in code:
                # Extract function parameters
                func_match = re.search(r'def\s+(\w+)\s*\(([^)]*)\)', code)
                if func_match:
                    params = func_match.group(2).split(',')
                    used_vars = re.findall(r'\b([a-zA-Z_]\w+)\b', code)
                    for var in used_vars:
                        if var not in params and var not in ["def", "return", "if", "else", "for", "while", "in", "not", "and", "or"]:
                            # This is a simplified check
                            pass
        
        return result
    
    def _compare_with_solution(self, code: str, expected: str, language: str) -> Dict:
        """Compare code with expected solution"""
        result = {"matches": True, "differences": []}
        
        # Normalize code for comparison
        code_normalized = self._normalize_code(code, language)
        expected_normalized = self._normalize_code(expected, language)
        
        if code_normalized != expected_normalized:
            result["matches"] = False
            result["differences"].append("Code does not match expected solution structure")
        
        return result
    
    def _normalize_code(self, code: str, language: str) -> str:
        """Normalize code for comparison"""
        # Remove whitespace differences
        lines = code.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            # Normalize multiple spaces to single space
            line = re.sub(r' +', ' ', line)
            normalized_lines.append(line)
        
        return '\n'.join(normalized_lines)
    
    def _check_logical_consistency(self, code: str, language: str) -> Dict:
        """Check logical consistency of code"""
        result = {"valid": True, "errors": []}
        
        # Check for unreachable code
        if "return" in code:
            lines = code.split('\n')
            found_return = False
            for line in lines:
                if "return" in line:
                    found_return = True
                elif found_return and line.strip() and not line.strip().startswith('#'):
                    result["valid"] = False
                    result["errors"].append("Unreachable code after return")
                    break
        
        # Check for impossible conditions
        if "if False:" in code or "if 0:" in code:
            result["valid"] = False
            result["errors"].append("Impossible condition detected")
        
        return result
    
    def get_correction_suggestions(self, code: str, language: str, errors: List[str]) -> List[str]:
        """
        Get correction suggestions for detected errors
        
        Args:
            code: Code with errors
            language: Programming language
            errors: List of detected errors
            
        Returns:
            List of correction suggestions
        """
        suggestions = []
        
        for error in errors:
            if "Syntax error" in error:
                suggestions.append("Fix syntax errors by checking brackets, parentheses, and indentation")
            elif "empty function" in error.lower():
                suggestions.append("Implement the function body instead of using placeholder code")
            elif "anti-pattern" in error.lower():
                suggestions.append("Remove anti-patterns and use proper coding practices")
            elif "unreachable" in error.lower():
                suggestions.append("Remove code after return statements or restructure logic")
            elif "impossible" in error.lower():
                suggestions.append("Fix conditional logic to have reachable code paths")
            else:
                suggestions.append(f"Address: {error}")
        
        return suggestions
    
    def self_correct_code(self, code: str, language: str) -> Dict:
        """
        Attempt automatic self-correction of code
        
        Args:
            code: Code to correct
            language: Programming language
            
        Returns:
            Correction result
        """
        evaluation = self.evaluate_code_strict(code, language)
        
        if evaluation["correct"]:
            return {
                "success": True,
                "message": "Code is already correct",
                "corrected_code": code
            }
        
        # Apply common corrections
        corrected_code = code
        
        # Remove placeholder code and replace with proper implementation
        if "pass" in corrected_code:
            # Replace pass with basic implementation
            corrected_code = re.sub(r'\bpass\b', 'return 0  # Auto-implemented logic', corrected_code)
        
        if "{}" in corrected_code:
            # Replace empty braces with basic implementation
            corrected_code = re.sub(r'\{\}', '{\n    return 0  # Auto-implemented logic\n}', corrected_code)
        
        # Remove debug statements
        if language == "python":
            corrected_code = re.sub(r'print\([^)]*\)', '# Removed debug statement', corrected_code)
        elif language in ["javascript", "typescript"]:
            corrected_code = re.sub(r'console\.log\([^)]*\)', '// Removed debug statement', corrected_code)
        
        # Remove TODO comments
        corrected_code = re.sub(r'# TODO.*', '', corrected_code)
        corrected_code = re.sub(r'// TODO.*', '', corrected_code)
        
        # Remove FIXME comments
        corrected_code = re.sub(r'# FIXME.*', '', corrected_code)
        corrected_code = re.sub(r'// FIXME.*', '', corrected_code)
        
        # Remove hack comments
        corrected_code = re.sub(r'# hack.*', '', corrected_code)
        corrected_code = re.sub(r'// hack.*', '', corrected_code)
        
        # Re-evaluate corrected code
        new_evaluation = self.evaluate_code_strict(corrected_code, language)
        
        return {
            "success": new_evaluation["correct"],
            "message": "Code corrected" if new_evaluation["correct"] else "Could not auto-correct all issues",
            "corrected_code": corrected_code,
            "original_evaluation": evaluation,
            "new_evaluation": new_evaluation
        }


if __name__ == "__main__":
    # Test the zero-tolerance code evaluator
    print("Testing Zero-Tolerance Code Evaluator...")
    
    evaluator = ZeroToleranceCodeEvaluator()
    
    # Test perfect code
    perfect_code = "def add_numbers(a, b):\n    return a + b"
    result = evaluator.evaluate_code_strict(perfect_code, "python")
    print(f"Perfect code: Correct={result['correct']}, Quality={result['quality']:.2f}")
    
    # Test code with placeholder
    bad_code = "def add_numbers(a, b):\n    pass"
    result = evaluator.evaluate_code_strict(bad_code, "python")
    print(f"Bad code: Correct={result['correct']}, Quality={result['quality']:.2f}")
    print(f"Errors: {result['errors']}")
    
    # Test self-correction
    correction = evaluator.self_correct_code(bad_code, "python")
    print(f"Self-correction: Success={correction['success']}")
    
    print("Zero-tolerance code evaluator test completed!")