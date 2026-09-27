"""
Coding Curriculum
Multi-language coding curriculum for training the fly
"""

from typing import Dict, List, Tuple
import json

class CodingCurriculum:
    """
    Manages the coding curriculum across multiple programming languages
    """
    
    def __init__(self):
        """Initialize the coding curriculum"""
        # Define target languages as per project plan + additional advanced languages
        self.languages = {
            "python": {
                "name": "Python",
                "xml_versions": ["lxml", "ElementTree"],
                "difficulty": 1.0,
                "skills": ["basic_syntax", "data_structures", "functions", "classes", "xml_processing"]
            },
            "typescript": {
                "name": "TypeScript",
                "xml_versions": ["ts-xml-parser"],
                "difficulty": 1.2,
                "skills": ["basic_syntax", "types", "interfaces", "classes", "xml_handling"]
            },
            "javascript": {
                "name": "JavaScript",
                "xml_versions": ["DOMParser", "XMLHttpRequest"],
                "difficulty": 1.1,
                "skills": ["basic_syntax", "dom_manipulation", "ajax", "xml_processing"]
            },
            "css": {
                "name": "CSS",
                "xml_versions": ["data-uri", "content_property"],
                "difficulty": 0.8,
                "skills": ["selectors", "properties", "layouts", "xml_in_css"]
            },
            "html": {
                "name": "HTML",
                "xml_versions": ["XHTML", "SVG"],
                "difficulty": 0.7,
                "skills": ["elements", "attributes", "structure", "xml_html"]
            },
            "json": {
                "name": "JSON",
                "xml_versions": ["json_to_xml"],
                "difficulty": 0.6,
                "skills": ["parsing", "serialization", "xml_conversion"]
            },
            "graphql": {
                "name": "GraphQL",
                "xml_versions": ["graphql_over_xml"],
                "difficulty": 1.3,
                "skills": ["schema", "queries", "mutations", "xml_alternatives"]
            },
            "toml": {
                "name": "TOML",
                "xml_versions": ["xml_alternative"],
                "difficulty": 0.5,
                "skills": ["parsing", "serialization", "configuration"]
            },
            "yaml": {
                "name": "YAML",
                "xml_versions": ["xml_alternative"],
                "difficulty": 0.6,
                "skills": ["parsing", "serialization", "configuration"]
            },
            "ini": {
                "name": "INI",
                "xml_versions": ["xml_alternative"],
                "difficulty": 0.4,
                "skills": ["parsing", "configuration", "basic_structure"]
            },
            "xml_rpc": {
                "name": "XML-RPC",
                "xml_versions": ["xml_protocol"],
                "difficulty": 1.4,
                "skills": ["protocols", "serialization", "remote_calls"]
            },
            "soap": {
                "name": "SOAP",
                "xml_versions": ["xml_protocol"],
                "difficulty": 1.5,
                "skills": ["protocols", "wsdl", "envelopes", "xml_messaging"]
            },
            # Additional advanced languages
            "rust": {
                "name": "Rust",
                "xml_versions": ["serde_xml"],
                "difficulty": 1.8,
                "skills": ["basic_syntax", "memory_safety", "ownership", "lifetimes", "concurrency"]
            },
            "c++": {
                "name": "C++",
                "xml_versions": ["rapidxml"],
                "difficulty": 1.7,
                "skills": ["basic_syntax", "memory_management", "pointers", "templates", "stl"]
            },
            "c#": {
                "name": "C#",
                "xml_versions": ["system_xml"],
                "difficulty": 1.5,
                "skills": ["basic_syntax", "dotnet", "linq", "async", "generics"]
            },
            "go": {
                "name": "Go",
                "xml_versions": ["encoding_xml"],
                "difficulty": 1.4,
                "skills": ["basic_syntax", "concurrency", "interfaces", "goroutines", "channels"]
            },
            "java": {
                "name": "Java",
                "xml_versions": ["jaxb", "dom4j"],
                "difficulty": 1.3,
                "skills": ["basic_syntax", "oop", "streams", "generics", "spring"]
            },
            "swift": {
                "name": "Swift",
                "xml_versions": ["foundation_xml"],
                "difficulty": 1.4,
                "skills": ["basic_syntax", "optionals", "closures", "protocols", "ios_development"]
            },
            "kotlin": {
                "name": "Kotlin",
                "xml_versions": ["kotlin_xml"],
                "difficulty": 1.3,
                "skills": ["basic_syntax", "null_safety", "coroutines", "android", "interoperability"]
            },
            "php": {
                "name": "PHP",
                "xml_versions": ["simplexml", "dom"],
                "difficulty": 1.1,
                "skills": ["basic_syntax", "web_development", "frameworks", "databases", "security"]
            },
            "ruby": {
                "name": "Ruby",
                "xml_versions": ["nokogiri"],
                "difficulty": 1.0,
                "skills": ["basic_syntax", "metaprogramming", "rails", "blocks", "gems"]
            },
            "sql": {
                "name": "SQL",
                "xml_versions": ["sql_xml"],
                "difficulty": 0.9,
                "skills": ["basic_syntax", "queries", "joins", "aggregation", "optimization"]
            },
            # Additional format languages
            "protobuf": {
                "name": "Protocol Buffers",
                "xml_versions": ["protobuf_xml"],
                "difficulty": 0.7,
                "skills": ["schema_definition", "serialization", "deserialization", "grpc"]
            },
            "avro": {
                "name": "Apache Avro",
                "xml_versions": ["avro_xml"],
                "difficulty": 0.8,
                "skills": ["schema_definition", "serialization", "evolution", "compression"]
            },
            "msgpack": {
                "name": "MessagePack",
                "xml_versions": ["msgpack_xml"],
                "difficulty": 0.6,
                "skills": ["serialization", "binary_format", "efficiency", "compatibility"]
            },
            "cbor": {
                "name": "CBOR",
                "xml_versions": ["cbor_xml"],
                "difficulty": 0.6,
                "skills": ["serialization", "binary_format", "conciseness", "extensibility"]
            },
            "bson": {
                "name": "BSON",
                "xml_versions": ["bson_xml"],
                "difficulty": 0.5,
                "skills": ["serialization", "binary_format", "document_model", "mongodb"]
            }
        }
        
        # Curriculum levels
        self.levels = {
            "beginner": {
                "description": "Basic syntax and simple programs",
                "difficulty_range": (0.0, 0.5),
                "skills_required": 1
            },
            "intermediate": {
                "description": "Complex programs and libraries",
                "difficulty_range": (0.5, 1.0),
                "skills_required": 3
            },
            "advanced": {
                "description": "Expert-level code and optimization",
                "difficulty_range": (1.0, 1.5),
                "skills_required": 5
            }
        }
        
        # Progress tracking
        self.skill_levels = {lang: {skill: 0.0 for skill in data["skills"]} 
                            for lang, data in self.languages.items()}
        self.completed_lessons = []
        self.current_level = "beginner"
        
        print(f"Coding curriculum initialized with {len(self.languages)} languages")
    
    def get_lesson_for_language(self, language: str, level: str = None) -> Dict:
        """
        Get a lesson for a specific language and level
        
        Args:
            language: Programming language
            level: Difficulty level (beginner, intermediate, advanced)
            
        Returns:
            Lesson dictionary with exercise and solution
        """
        if language not in self.languages:
            raise ValueError(f"Unknown language: {language}")
        
        if level is None:
            level = self.current_level
        
        # Generate lesson based on language and level
        lesson = self._generate_lesson(language, level)
        return lesson
    
    def _generate_lesson(self, language: str, level: str) -> Dict:
        """Generate a lesson for the given language and level"""
        lang_data = self.languages[language]
        
        if level == "beginner":
            return self._beginner_lesson(language, lang_data)
        elif level == "intermediate":
            return self._intermediate_lesson(language, lang_data)
        else:
            return self._advanced_lesson(language, lang_data)
    
    def _beginner_lesson(self, language: str, lang_data: Dict, level: str = "beginner") -> Dict:
        """Generate a beginner-level lesson"""
        lessons = {
            "python": {
                "task": "Write a function that adds two numbers",
                "starter_code": "def add_numbers(a, b):\n    # Your code here\n    pass",
                "expected_solution": "def add_numbers(a, b):\n    return a + b",
                "test_cases": [("add_numbers(2, 3)", 5), ("add_numbers(-1, 1)", 0)]
            },
            "typescript": {
                "task": "Create a simple interface for a user",
                "starter_code": "interface User {\n    // Your code here\n}",
                "expected_solution": "interface User {\n    name: string;\n    age: number;\n}",
                "test_cases": ["interface definition", "property definitions"]
            },
            "javascript": {
                "task": "Write a function that returns the length of a string",
                "starter_code": "function getStringLength(str) {\n    // Your code here\n}",
                "expected_solution": "function getStringLength(str) {\n    return str.length;\n}",
                "test_cases": [("getStringLength('hello')", 5), ("getStringLength('')", 0)]
            },
            "css": {
                "task": "Create a class that sets text color to blue",
                "starter_code": ".blue-text {\n    /* Your code here */\n}",
                "expected_solution": ".blue-text {\n    color: blue;\n}",
                "test_cases": ["color property", "selector syntax"]
            },
            "html": {
                "task": "Create a paragraph element with some text",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<p>This is a paragraph</p>",
                "test_cases": ["paragraph element", "text content"]
            },
            "json": {
                "task": "Create a JSON object with name and age",
                "starter_code": "{\n  // Your code here\n}",
                "expected_solution": "{\n  \"name\": \"John\",\n  \"age\": 30\n}",
                "test_cases": ["valid JSON", "name property", "age property"]
            },
            "graphql": {
                "task": "Create a simple GraphQL query for a user",
                "starter_code": "query {\n  # Your code here\n}",
                "expected_solution": "query {\n  user {\n    name\n    age\n  }\n}",
                "test_cases": ["query structure", "field selection"]
            },
            "toml": {
                "task": "Create a TOML configuration with a title",
                "starter_code": "# Your code here",
                "expected_solution": "title = \"My Config\"",
                "test_cases": ["key-value pair", "string value"]
            },
            "yaml": {
                "task": "Create a YAML document with a list",
                "starter_code": "# Your code here",
                "expected_solution": "items:\n  - item1\n  - item2",
                "test_cases": ["list structure", "item format"]
            },
            "ini": {
                "task": "Create an INI file with a section",
                "starter_code": "# Your code here",
                "expected_solution": "[section]\nkey = value",
                "test_cases": ["section header", "key-value pair"]
            },
            "xml_rpc": {
                "task": "Create a simple XML-RPC method call",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<methodCall>\n  <methodName>example</methodName>\n</methodCall>",
                "test_cases": ["methodCall element", "methodName"]
            },
            "soap": {
                "task": "Create a basic SOAP envelope",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<soap:Envelope>\n  <soap:Body>\n    <m:Example/>\n  </soap:Body>\n</soap:Envelope>",
                "test_cases": ["Envelope element", "Body element"]
            }
        }
        
        return lessons.get(language, self._generic_lesson(language, "beginner"))
    
    def _intermediate_lesson(self, language: str, lang_data: Dict, level: str = "intermediate") -> Dict:
        """Generate an intermediate-level lesson"""
        lessons = {
            "python": {
                "task": "Write a function that processes a list of dictionaries",
                "starter_code": "def process_data(data):\n    # Your code here\n    pass",
                "expected_solution": "def process_data(data):\n    return [item['value'] for item in data if 'value' in item]",
                "test_cases": [("process_data([{'value': 1}, {'value': 2}])", [1, 2])]
            },
            "typescript": {
                "task": "Create a generic class that can store any type",
                "starter_code": "class Container<T> {\n    // Your code here\n}",
                "expected_solution": "class Container<T> {\n    private value: T;\n    constructor(value: T) {\n        this.value = value;\n    }\n}",
                "test_cases": ["generic syntax", "constructor"]
            },
            "javascript": {
                "task": "Write a function that filters an array based on a condition",
                "starter_code": "function filterArray(arr, condition) {\n    // Your code here\n}",
                "expected_solution": "function filterArray(arr, condition) {\n    return arr.filter(condition);\n}",
                "test_cases": [("filterArray([1,2,3,4], x => x % 2 === 0)", [2, 4])]
            },
            "css": {
                "task": "Create a responsive layout using flexbox",
                "starter_code": ".container {\n    /* Your code here */\n}",
                "expected_solution": ".container {\n    display: flex;\n    flex-wrap: wrap;\n}",
                "test_cases": ["flexbox display", "wrap property"]
            },
            "html": {
                "task": "Create a form with input fields and validation",
                "starter_code": "<form>\n  <!-- Your code here -->\n</form>",
                "expected_solution": "<form>\n  <input type=\"text\" required>\n  <button type=\"submit\">Submit</button>\n</form>",
                "test_cases": ["form element", "required attribute"]
            },
            "json": {
                "task": "Create a nested JSON structure representing a user profile",
                "starter_code": "{\n  /* Your code here */\n}",
                "expected_solution": "{\n  \"user\": {\n    \"name\": \"John\",\n    \"profile\": {\n      \"age\": 30\n    }\n  }\n}",
                "test_cases": ["nested structure", "valid JSON"]
            },
            "graphql": {
                "task": "Create a GraphQL mutation to update user data",
                "starter_code": "mutation {\n  # Your code here\n}",
                "expected_solution": "mutation {\n  updateUser(id: 1, name: \"New Name\") {\n    name\n  }\n}",
                "test_cases": ["mutation structure", "arguments"]
            },
            "toml": {
                "task": "Create a TOML table with multiple key-value pairs",
                "starter_code": "[server]\n# Your code here",
                "expected_solution": "[server]\nhost = \"localhost\"\nport = 8080",
                "test_cases": ["table syntax", "multiple keys"]
            },
            "yaml": {
                "task": "Create a YAML document with nested mappings",
                "starter_code": "# Your code here",
                "expected_solution": "config:\n  database:\n    host: localhost\n    port: 5432",
                "test_cases": ["nested structure", "mapping syntax"]
            },
            "ini": {
                "task": "Create an INI file with multiple sections",
                "starter_code": "# Your code here",
                "expected_solution": "[section1]\nkey1 = value1\n[section2]\nkey2 = value2",
                "test_cases": ["multiple sections", "key-value pairs"]
            },
            "xml_rpc": {
                "task": "Create an XML-RPC request with parameters",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<methodCall>\n  <methodName>process</methodName>\n  <params>\n    <param><value>42</value></param>\n  </params>\n</methodCall>",
                "test_cases": ["parameters element", "value structure"]
            },
            "soap": {
                "task": "Create a SOAP request with headers",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<soap:Envelope>\n  <soap:Header>\n    <auth:Token>xyz</auth:Token>\n  </soap:Header>\n  <soap:Body>\n    <m:Request/>\n  </soap:Body>\n</soap:Envelope>",
                "test_cases": ["Header element", "authentication"]
            }
        }
        
        return lessons.get(language, self._generic_lesson(language, "beginner"))
    
    def _advanced_lesson(self, language: str, lang_data: Dict) -> Dict:
        """Generate an advanced-level lesson"""
        lessons = {
            "python": {
                "task": "Implement a class with method overriding and decorators",
                "starter_code": "class Base:\n    def method(self):\n        pass\n\nclass Derived(Base):\n    # Your code here",
                "expected_solution": "class Derived(Base):\n    @property\n    def method(self):\n        return super().method()",
                "test_cases": ["inheritance", "decorators", "property"]
            },
            "typescript": {
                "task": "Create a complex type with union types and conditional types",
                "starter_code": "type ComplexType = /* Your code here */",
                "expected_solution": "type ComplexType = string | number | { [key: string]: any }",
                "test_cases": ["union types", "conditional types"]
            },
            "javascript": {
                "task": "Implement a class with async methods and error handling",
                "starter_code": "class AsyncClass {\n    async process() {\n        // Your code here\n    }\n}",
                "expected_solution": "class AsyncClass {\n    async process() {\n        try {\n            await this.getData();\n        } catch (error) {\n            console.error(error);\n        }\n    }\n}",
                "test_cases": ["async syntax", "error handling"]
            },
            "css": {
                "task": "Create a complex animation with keyframes and transforms",
                "starter_code": "@keyframes animate {\n  /* Your code here */\n}",
                "expected_solution": "@keyframes animate {\n  0% { transform: translateX(0); }\n  100% { transform: translateX(100px); }\n}",
                "test_cases": ["keyframes", "transforms", "timing"]
            },
            "html": {
                "task": "Create a semantic HTML structure with accessibility features",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<main role=\"main\">\n  <article aria-labelledby=\"title\">\n    <h1 id=\"title\">Title</h1>\n  </article>\n</main>",
                "test_cases": ["semantic elements", "ARIA attributes"]
            },
            "json": {
                "task": "Create a complex JSON schema with validation rules",
                "starter_code": "{\n  \"$schema\": \"http://json-schema.org/draft-07/schema#\",\n  /* Your code here */\n}",
                "expected_solution": "{\n  \"$schema\": \"http://json-schema.org/draft-07/schema#\",\n  \"type\": \"object\",\n  \"properties\": {\n    \"name\": {\"type\": \"string\"}\n  },\n  \"required\": [\"name\"]\n}",
                "test_cases": ["schema structure", "validation rules"]
            },
            "graphql": {
                "task": "Create a GraphQL schema with interfaces and unions",
                "starter_code": "# Your code here",
                "expected_solution": "interface Node {\n  id: ID!\n}\n\ntype Query {\n  node(id: ID!): Node\n}",
                "test_cases": ["interface definition", "union types"]
            },
            "toml": {
                "task": "Create a complex TOML configuration with nested tables",
                "starter_code": "# Your code here",
                "expected_solution": "[database]\nhost = \"localhost\"\n[database.credentials]\nusername = \"user\"\npassword = \"pass\"",
                "test_cases": ["nested tables", "dotted keys"]
            },
            "yaml": {
                "task": "Create a YAML document with anchors and aliases",
                "starter_code": "# Your code here",
                "expected_solution": "defaults: &defaults\n  verbose: true\n\ndevelopment:\n  <<: *defaults\n  debug: true",
                "test_cases": ["anchors", "aliases", "merging"]
            },
            "ini": {
                "task": "Create an INI file with comments and complex values",
                "starter_code": "# Your code here",
                "expected_solution": "# Configuration file\n[section]\nkey = \"complex_value\"\nanother_key = 123",
                "test_cases": ["comments", "quoted values", "numbers"]
            },
            "xml_rpc": {
                "task": "Create an XML-RPC response with fault handling",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<methodResponse>\n  <fault>\n    <value><struct>\n      <member><name>faultCode</name></member>\n    </struct></value>\n  </fault>\n</methodResponse>",
                "test_cases": ["fault structure", "error handling"]
            },
            "soap": {
                "task": "Create a SOAP message with attachments and headers",
                "starter_code": "<!-- Your code here -->",
                "expected_solution": "<soap:Envelope>\n  <soap:Header>\n    <Attachment>file.txt</Attachment>\n  </soap:Header>\n  <soap:Body>\n    <m:Data/>\n  </soap:Body>\n</soap:Envelope>",
                "test_cases": ["attachments", "complex headers"]
            }
        }
        
        return lessons.get(language, self._generic_lesson(language, "beginner"))
    
    def _generic_lesson(self, language: str, level: str) -> Dict:
        """Generate a generic lesson if specific one not available"""
        return {
            "task": f"Write a {level} level {language} program",
            "starter_code": f"# {language} {level} lesson\n# Your code here",
            "expected_solution": f"# {language} solution\n# Basic implementation",
            "test_cases": ["basic syntax", "correct structure"]
        }
    
    def update_skill_level(self, language: str, skill: str, improvement: float):
        """
        Update skill level for a specific language and skill
        
        Args:
            language: Programming language
            skill: Specific skill
            improvement: Improvement amount (0-1)
        """
        if language in self.skill_levels and skill in self.skill_levels[language]:
            current_level = self.skill_levels[language][skill]
            new_level = min(1.0, current_level + improvement)
            self.skill_levels[language][skill] = new_level
    
    def get_skill_progress(self, language: str) -> Dict:
        """
        Get skill progress for a specific language
        
        Args:
            language: Programming language
            
        Returns:
            Dictionary with skill levels
        """
        if language not in self.skill_levels:
            return {}
        
        skills = self.skill_levels[language]
        avg_skill = sum(skills.values()) / len(skills) if skills else 0.0
        
        return {
            "language": language,
            "skills": skills,
            "average_skill": avg_skill,
            "total_skills": len(skills),
            "mastered_skills": sum(1 for level in skills.values() if level >= 0.9)
        }
    
    def get_overall_progress(self) -> Dict:
        """Get overall progress across all languages"""
        total_skills = 0
        mastered_skills = 0
        language_progress = {}
        
        for language in self.languages:
            progress = self.get_skill_progress(language)
            language_progress[language] = progress
            total_skills += progress["total_skills"]
            mastered_skills += progress["mastered_skills"]
        
        return {
            "total_languages": len(self.languages),
            "language_progress": language_progress,
            "total_skills": total_skills,
            "mastered_skills": mastered_skills,
            "overall_mastery": mastered_skills / total_skills if total_skills > 0 else 0.0
        }
    
    def advance_level(self):
        """Advance to the next difficulty level"""
        levels = ["beginner", "intermediate", "advanced"]
        current_index = levels.index(self.current_level)
        
        if current_index < len(levels) - 1:
            self.current_level = levels[current_index + 1]
            print(f"Advanced to {self.current_level} level")
        else:
            print("Already at advanced level")
    
    def reset_progress(self):
        """Reset all skill progress"""
        self.skill_levels = {lang: {skill: 0.0 for skill in data["skills"]} 
                            for lang, data in self.languages.items()}
        self.completed_lessons = []
        self.current_level = "beginner"
        print("Curriculum progress reset")


if __name__ == "__main__":
    # Test the coding curriculum
    print("Testing Coding Curriculum...")
    
    curriculum = CodingCurriculum()
    
    # Test lesson generation
    print("\nTesting lesson generation...")
    lesson = curriculum.get_lesson_for_language("python", "beginner")
    print(f"Python beginner lesson: {lesson['task']}")
    
    lesson = curriculum.get_lesson_for_language("typescript", "intermediate")
    print(f"TypeScript intermediate lesson: {lesson['task']}")
    
    # Test skill progress
    print("\nTesting skill progress...")
    curriculum.update_skill_level("python", "basic_syntax", 0.3)
    curriculum.update_skill_level("python", "functions", 0.5)
    progress = curriculum.get_skill_progress("python")
    print(f"Python progress: {progress}")
    
    # Test overall progress
    print("\nTesting overall progress...")
    overall = curriculum.get_overall_progress()
    print(f"Overall progress: {overall['total_languages']} languages, {overall['mastered_skills']} mastered skills")
    
    print("Coding curriculum test completed!")