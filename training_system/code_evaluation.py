"""
Code Evaluation Engine
Evaluates code correctness and quality across multiple programming languages
"""

import ast
import re
import json
from typing import Dict, List, Tuple, Optional
import subprocess
import tempfile
import os

class CodeEvaluationEngine:
    """
    Evaluates code correctness and quality across multiple programming languages
    """
    
    def __init__(self):
        """Initialize the code evaluation engine"""
        # Language-specific evaluators
        self.evaluators = {
            "python": self._evaluate_python,
            "typescript": self._evaluate_typescript,
            "javascript": self._evaluate_javascript,
            "css": self._evaluate_css,
            "html": self._evaluate_html,
            "json": self._evaluate_json,
            "graphql": self._evaluate_graphql,
            "toml": self._evaluate_toml,
            "yaml": self._evaluate_yaml,
            "ini": self._evaluate_ini,
            "xml_rpc": self._evaluate_xml_rpc,
            "soap": self._evaluate_soap,
            # Additional advanced languages
            "rust": self._evaluate_rust,
            "c++": self._evaluate_cpp,
            "c#": self._evaluate_csharp,
            "go": self._evaluate_go,
            "java": self._evaluate_java,
            "swift": self._evaluate_swift,
            "kotlin": self._evaluate_kotlin,
            "php": self._evaluate_php,
            "ruby": self._evaluate_ruby,
            "sql": self._evaluate_sql,
            # Additional format languages
            "protobuf": self._evaluate_protobuf,
            "avro": self._evaluate_avro,
            "msgpack": self._evaluate_msgpack,
            "cbor": self._evaluate_cbor,
            "bson": self._evaluate_bson
        }
        
        print(f"Code evaluation engine initialized for {len(self.evaluators)} languages")
    
    def evaluate_code(self, code: str, language: str, test_cases: List = None) -> Dict:
        """
        Evaluate code for a specific language
        
        Args:
            code: Code to evaluate
            language: Programming language
            test_cases: List of test cases to run
            
        Returns:
            Evaluation results
        """
        language = language.lower()
        
        if language not in self.evaluators:
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": f"Unsupported language: {language}",
                "errors": ["Language not supported"]
            }
        
        try:
            # Run language-specific evaluation
            evaluation = self.evaluators[language](code, test_cases)
            
            # Add overall assessment
            evaluation["language"] = language
            evaluation["code_length"] = len(code)
            evaluation["line_count"] = len(code.split('\n'))
            
            return evaluation
            
        except Exception as e:
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": f"Evaluation error: {str(e)}",
                "errors": [str(e)]
            }
    
    def _evaluate_python(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Python code"""
        errors = []
        warnings = []
        
        # Syntax check
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": "Syntax error in code",
                "errors": errors
            }
        
        # Check for common patterns
        if "def " not in code and "class " not in code:
            warnings.append("No functions or classes defined")
        
        # Check for return statements in functions
        if "def " in code and "return " not in code:
            warnings.append("Functions may not return values")
        
        # Calculate quality score
        quality = 1.0
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Python code: {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_typescript(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate TypeScript code"""
        errors = []
        warnings = []
        
        # Basic syntax checks
        if "interface " not in code and "class " not in code and "function " not in code:
            warnings.append("No type definitions or functions found")
        
        # Check for type annotations
        if "function " in code and ":" not in code:
            warnings.append("Functions may lack type annotations")
        
        # Check for semicolons (should not be used in TS)
        if code.count(";") > 0:
            warnings.append("TypeScript generally uses no semicolons")
        
        quality = 1.0
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"TypeScript code: {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_javascript(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate JavaScript code"""
        errors = []
        warnings = []
        
        # Basic syntax checks
        if "function " not in code and "const " not in code and "let " not in code:
            warnings.append("No functions or variable declarations found")
        
        # Check for var usage (should use const/let)
        if "var " in code:
            warnings.append("Consider using const/let instead of var")
        
        # Check for semicolons
        if code.count(";") == 0 and code.count("\n") > 1:
            warnings.append("JavaScript statements typically end with semicolons")
        
        quality = 1.0
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"JavaScript code: {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_css(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate CSS code"""
        errors = []
        warnings = []
        
        # Check for selector patterns
        if "." not in code and "#" not in code and code.strip().startswith(" "):
            warnings.append("No class or ID selectors found")
        
        # Check for property patterns
        if ":" not in code:
            errors.append("No CSS properties found")
        
        # Check for common CSS patterns
        if code.count("{") != code.count("}"):
            errors.append("Mismatched braces")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"CSS code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_html(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate HTML code"""
        errors = []
        warnings = []
        
        # Check for HTML tags
        tag_pattern = r'<[^>]+>'
        tags = re.findall(tag_pattern, code)
        
        if not tags:
            errors.append("No HTML tags found")
        
        # Check for closing tags
        open_tags = [tag for tag in tags if not tag.startswith("</")]
        close_tags = [tag for tag in tags if tag.startswith("</")]
        
        for tag in open_tags:
            tag_name = tag.strip('<>').split()[0]
            if tag_name not in ['img', 'br', 'hr', 'input', 'meta', 'link']:  # Self-closing tags
                if f"</{tag_name}>" not in code:
                    warnings.append(f"Unclosed tag: {tag_name}")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"HTML code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_json(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate JSON code"""
        errors = []
        warnings = []
        
        # Try to parse JSON
        try:
            parsed = json.loads(code)
            
            # Check if it's a dictionary or list
            if not isinstance(parsed, (dict, list)):
                warnings.append("JSON should be an object or array")
            
            return {
                "correct": True,
                "quality": 1.0,
                "feedback": "Valid JSON structure",
                "errors": errors,
                "warnings": warnings
            }
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            return {
                "correct": False,
                "quality": 0.0,
                "feedback": f"Invalid JSON: {e}",
                "errors": errors,
                "warnings": warnings
            }
    
    def _evaluate_graphql(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate GraphQL code"""
        errors = []
        warnings = []
        
        # Check for GraphQL patterns
        if "query" not in code.lower() and "mutation" not in code.lower():
            warnings.append("No query or mutation found")
        
        # Check for braces
        if code.count("{") != code.count("}"):
            errors.append("Mismatched braces")
        
        # Check for basic GraphQL structure
        if "type " not in code and "schema" not in code:
            warnings.append("No type definitions or schema found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"GraphQL code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_toml(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate TOML code"""
        errors = []
        warnings = []
        
        # Check for key-value patterns
        if "=" not in code:
            errors.append("No key-value pairs found")
        
        # Check for section headers
        if "[" not in code:
            warnings.append("No section headers found")
        
        # Check for basic TOML structure
        lines = code.split('\n')
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                if not key.strip():
                    errors.append("Empty key found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"TOML code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_yaml(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate YAML code"""
        errors = []
        warnings = []
        
        # Check for YAML patterns
        if ":" not in code:
            errors.append("No key-value pairs found")
        
        # Check for indentation (YAML uses indentation)
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and ':' in line:
                # Check that the line has proper indentation
                if not line.startswith(' ') and i > 0:
                    # Only first line can be at column 0
                    pass  # Allow top-level to be at column 0
        
        # Check for lists
        if "-" not in code:
            warnings.append("No list items found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"YAML code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_ini(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate INI code"""
        errors = []
        warnings = []
        
        # Check for INI patterns
        if "=" not in code:
            errors.append("No key-value pairs found")
        
        # Check for section headers
        if "[" not in code:
            warnings.append("No section headers found")
        
        # Check for comments
        if ";" not in code and "#" not in code:
            warnings.append("No comments found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"INI code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_xml_rpc(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate XML-RPC code"""
        errors = []
        warnings = []
        
        # Check for XML-RPC specific elements
        if "methodCall" not in code and "methodResponse" not in code:
            errors.append("No methodCall or methodResponse found")
        
        # Check for methodName
        if "methodName" not in code:
            errors.append("No methodName found")
        
        # Check for params
        if "params" not in code and "param" not in code:
            warnings.append("No parameters found")
        
        # Check for basic XML structure
        if code.count("<") != code.count(">"):
            errors.append("Mismatched angle brackets")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"XML-RPC code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_soap(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate SOAP code"""
        errors = []
        warnings = []
        
        # Check for SOAP specific elements
        if "Envelope" not in code or "soap:" not in code:
            errors.append("No SOAP Envelope or namespace found")
        
        # Check for Body
        if "Body" not in code:
            errors.append("No SOAP Body found")
        
        # Check for Header
        if "Header" not in code:
            warnings.append("No SOAP Header found")
        
        # Check for basic XML structure
        if code.count("<") != code.count(">"):
            errors.append("Mismatched angle brackets")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"SOAP code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_rust(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Rust code"""
        errors = []
        warnings = []
        
        # Check for Rust-specific patterns
        if "fn " not in code:
            errors.append("No function definitions found")
        
        # Check for ownership patterns
        if "fn " in code and ("&" not in code and "mut" not in code):
            warnings.append("Consider ownership and borrowing patterns")
        
        # Check for main function
        if "fn main" not in code:
            warnings.append("No main function found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Rust code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_cpp(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate C++ code"""
        errors = []
        warnings = []
        
        # Check for C++ patterns
        if "#include" not in code:
            warnings.append("No include statements found")
        
        # Check for main function
        if "int main" not in code:
            errors.append("No main function found")
        
        # Check for memory management
        if "new " in code and "delete" not in code:
            warnings.append("Memory leak potential - missing delete")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"C++ code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_csharp(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate C# code"""
        errors = []
        warnings = []
        
        # Check for C# patterns
        if "class " not in code and "namespace " not in code:
            warnings.append("No class or namespace definitions found")
        
        # Check for using statements
        if "using " not in code:
            warnings.append("No using statements found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"C# code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_go(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Go code"""
        errors = []
        warnings = []
        
        # Check for Go patterns
        if "package " not in code:
            errors.append("No package declaration found")
        
        # Check for main function
        if "func main" not in code:
            warnings.append("No main function found")
        
        # Check for goroutines
        if "go " not in code:
            warnings.append("No goroutines found (Go is known for concurrency)")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Go code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_java(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Java code"""
        errors = []
        warnings = []
        
        # Check for Java patterns
        if "class " not in code:
            errors.append("No class definition found")
        
        # Check for main method
        if "public static void main" not in code:
            warnings.append("No main method found")
        
        # Check for package
        if "package " not in code:
            warnings.append("No package declaration found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Java code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_swift(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Swift code"""
        errors = []
        warnings = []
        
        # Check for Swift patterns
        if "func " not in code:
            errors.append("No function definitions found")
        
        # Check for optionals
        if "?" not in code and "!" not in code:
            warnings.append("No optional handling found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Swift code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_kotlin(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Kotlin code"""
        errors = []
        warnings = []
        
        # Check for Kotlin patterns
        if "fun " not in code:
            errors.append("No function definitions found")
        
        # Check for null safety
        if "?" not in code:
            warnings.append("No null safety operators found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Kotlin code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_php(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate PHP code"""
        errors = []
        warnings = []
        
        # Check for PHP patterns
        if "<?php" not in code:
            warnings.append("No PHP opening tag found")
        
        # Check for functions
        if "function " not in code:
            warnings.append("No function definitions found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"PHP code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_ruby(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Ruby code"""
        errors = []
        warnings = []
        
        # Check for Ruby patterns
        if "def " not in code:
            errors.append("No method definitions found")
        
        # Check for blocks
        if "{" not in code and "do" not in code:
            warnings.append("No blocks found (Ruby is known for blocks)")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Ruby code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_sql(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate SQL code"""
        errors = []
        warnings = []
        
        # Check for SQL patterns
        if "SELECT" not in code.upper() and "INSERT" not in code.upper():
            errors.append("No SQL statements found")
        
        # Check for FROM clause in SELECT
        if "SELECT" in code.upper() and "FROM" not in code.upper():
            errors.append("SELECT statement missing FROM clause")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"SQL code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_protobuf(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Protocol Buffers code"""
        errors = []
        warnings = []
        
        # Check for protobuf patterns
        if "message " not in code:
            errors.append("No message definitions found")
        
        # Check for package
        if "package " not in code:
            warnings.append("No package declaration found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Protobuf code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_avro(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate Avro code"""
        errors = []
        warnings = []
        
        # Check for Avro patterns
        if "type" not in code and "name" not in code:
            errors.append("No type definitions found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"Avro code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_msgpack(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate MessagePack code"""
        errors = []
        warnings = []
        
        # MessagePack is binary format, check for related patterns
        if "msgpack" not in code.lower():
            warnings.append("No msgpack references found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"MessagePack code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_cbor(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate CBOR code"""
        errors = []
        warnings = []
        
        # CBOR is binary format, check for related patterns
        if "cbor" not in code.lower():
            warnings.append("No cbor references found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"CBOR code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def _evaluate_bson(self, code: str, test_cases: List = None) -> Dict:
        """Evaluate BSON code"""
        errors = []
        warnings = []
        
        # BSON is binary format, check for related patterns
        if "bson" not in code.lower():
            warnings.append("No bson references found")
        
        quality = 1.0
        if errors:
            quality -= 0.3 * len(errors)
        if warnings:
            quality -= 0.1 * len(warnings)
        quality = max(0.0, quality)
        
        return {
            "correct": len(errors) == 0,
            "quality": quality,
            "feedback": f"BSON code: {len(errors)} errors, {len(warnings)} warnings",
            "errors": errors,
            "warnings": warnings
        }
    
    def run_test_cases(self, code: str, language: str, test_cases: List) -> Dict:
        """
        Run test cases for the code
        
        Args:
            code: Code to test
            language: Programming language
            test_cases: List of test cases
            
        Returns:
            Test results
        """
        results = {
            "total_tests": len(test_cases) if test_cases else 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        
        if not test_cases:
            return results
        
        for test_case in test_cases:
            # Simplified test evaluation
            # In a real implementation, this would actually execute the code
            test_result = self._run_single_test(code, language, test_case)
            
            if test_result["passed"]:
                results["passed_tests"] += 1
            else:
                results["failed_tests"] += 1
            
            results["test_details"].append(test_result)
        
        return results
    
    def _run_single_test(self, code: str, language: str, test_case) -> Dict:
        """Run a single test case"""
        # Simplified test - in real implementation would execute code
        # For now, we'll do basic string matching tests
        
        if isinstance(test_case, tuple):
            test_description, expected_output = test_case
        else:
            test_description = test_case
            expected_output = None
        
        # Check if test case passes
        passed = True
        output = "N/A"
        
        if expected_output is not None:
            # Check if expected output is in code
            if isinstance(expected_output, str):
                passed = expected_output in code
            elif isinstance(expected_output, list):
                passed = all(item in code for item in expected_output)
        
        return {
            "test": test_description,
            "expected": expected_output,
            "actual": output,
            "passed": passed
        }
    
    def get_evaluation_summary(self, evaluations: List[Dict]) -> Dict:
        """
        Get summary of multiple evaluations
        
        Args:
            evaluations: List of evaluation results
            
        Returns:
            Summary statistics
        """
        if not evaluations:
            return {}
        
        total_evaluations = len(evaluations)
        correct_count = sum(1 for eval in evaluations if eval.get("correct", False))
        avg_quality = sum(eval.get("quality", 0.0) for eval in evaluations) / total_evaluations
        
        languages_evaluated = set()
        for eval in evaluations:
            if "language" in eval:
                languages_evaluated.add(eval["language"])
        
        return {
            "total_evaluations": total_evaluations,
            "correct_count": correct_count,
            "success_rate": correct_count / total_evaluations if total_evaluations > 0 else 0.0,
            "average_quality": avg_quality,
            "languages_evaluated": list(languages_evaluated),
            "total_errors": sum(len(eval.get("errors", [])) for eval in evaluations),
            "total_warnings": sum(len(eval.get("warnings", [])) for eval in evaluations)
        }


if __name__ == "__main__":
    # Test the code evaluation engine
    print("Testing Code Evaluation Engine...")
    
    evaluator = CodeEvaluationEngine()
    
    # Test Python evaluation
    print("\nTesting Python evaluation...")
    python_code = "def add_numbers(a, b):\n    return a + b"
    python_eval = evaluator.evaluate_code(python_code, "python")
    print(f"Python evaluation: {python_eval}")
    
    # Test JSON evaluation
    print("\nTesting JSON evaluation...")
    json_code = '{"name": "John", "age": 30}'
    json_eval = evaluator.evaluate_code(json_code, "json")
    print(f"JSON evaluation: {json_eval}")
    
    # Test HTML evaluation
    print("\nTesting HTML evaluation...")
    html_code = '<p>Hello World</p>'
    html_eval = evaluator.evaluate_code(html_code, "html")
    print(f"HTML evaluation: {html_eval}")
    
    # Test evaluation summary
    print("\nTesting evaluation summary...")
    evaluations = [python_eval, json_eval, html_eval]
    summary = evaluator.get_evaluation_summary(evaluations)
    print(f"Evaluation summary: {summary}")
    
    print("Code evaluation engine test completed!")