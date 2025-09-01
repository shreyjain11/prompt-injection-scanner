"""
AST-based analysis for better pattern detection and context understanding.
"""

import ast
import re
from typing import List, Dict, Any, Optional, Set
from pathlib import Path


class ASTAnalyzer:
    """AST-based analyzer for Python code."""
    
    def __init__(self):
        self.api_calls = set()
        self.user_variables = set()
        self.prompt_variables = set()
        self.dangerous_functions = set()
    
    def analyze_python_file(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file using AST."""
        try:
            tree = ast.parse(content)
            return self._analyze_ast_tree(tree, content)
        except SyntaxError:
            # If AST parsing fails, fall back to regex
            return self._fallback_analysis(content)
    
    def _analyze_ast_tree(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze the AST tree."""
        analyzer = PythonASTVisitor()
        analyzer.visit(tree)
        
        return {
            'api_calls': analyzer.api_calls,
            'user_variables': analyzer.user_variables,
            'prompt_variables': analyzer.prompt_variables,
            'dangerous_functions': analyzer.dangerous_functions,
            'imports': analyzer.imports,
            'function_calls': analyzer.function_calls,
            'assignments': analyzer.assignments,
        }
    
    def _fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback analysis using regex when AST fails."""
        return {
            'api_calls': self._find_api_calls_regex(content),
            'user_variables': set(),
            'prompt_variables': set(),
            'dangerous_functions': set(),
            'imports': set(),
            'function_calls': set(),
            'assignments': set(),
        }
    
    def _find_api_calls_regex(self, content: str) -> Set[str]:
        """Find API calls using regex."""
        api_patterns = [
            r'openai\.[a-zA-Z]+\.[a-zA-Z]+',
            r'langchain\.[a-zA-Z]+',
            r'anthropic\.[a-zA-Z]+',
            r'cohere\.[a-zA-Z]+',
        ]
        
        api_calls = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            api_calls.update(matches)
        
        return api_calls


class PythonASTVisitor(ast.NodeVisitor):
    """AST visitor for Python code analysis."""
    
    def __init__(self):
        self.api_calls = set()
        self.user_variables = set()
        self.prompt_variables = set()
        self.dangerous_functions = set()
        self.imports = set()
        self.function_calls = set()
        self.assignments = set()
        
        # API patterns
        self.api_patterns = [
            'openai',
            'langchain',
            'anthropic',
            'cohere',
            'huggingface',
        ]
        
        # User input indicators
        self.user_input_patterns = [
            'user_input',
            'userInput',
            'input',
            'query',
            'prompt',
            'user_message',
            'userMessage',
            'request',
            'data',
            'content',
            'text',
            'string',
            'value',
            'param',
            'arg',
            'variable',
        ]
        
        # Dangerous functions
        self.dangerous_function_patterns = [
            'eval',
            'exec',
            '__import__',
            'compile',
        ]
    
    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import statements."""
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls."""
        if isinstance(node.func, ast.Attribute):
            # Method calls like openai.ChatCompletion.create
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
                self.function_calls.add(func_name)
                
                # Check for API calls
                for pattern in self.api_patterns:
                    if pattern in func_name.lower():
                        self.api_calls.add(func_name)
            
            # Check for dangerous functions
            if node.func.attr in self.dangerous_function_patterns:
                self.dangerous_functions.add(node.func.attr)
        
        elif isinstance(node.func, ast.Name):
            # Direct function calls
            self.function_calls.add(node.func.id)
            
            # Check for dangerous functions
            if node.func.id in self.dangerous_function_patterns:
                self.dangerous_functions.add(node.func.id)
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment statements."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                self.assignments.add(var_name)
                
                # Check if it's a user input variable
                for pattern in self.user_input_patterns:
                    if pattern.lower() in var_name.lower():
                        self.user_variables.add(var_name)
                
                # Check if it's a prompt variable
                if 'prompt' in var_name.lower():
                    self.prompt_variables.add(var_name)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Visit annotated assignment statements."""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            self.assignments.add(var_name)
            
            # Check if it's a user input variable
            for pattern in self.user_input_patterns:
                if pattern.lower() in var_name.lower():
                    self.user_variables.add(var_name)
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        # Check function parameters for user input
        for arg in node.args.args:
            arg_name = arg.arg
            for pattern in self.user_input_patterns:
                if pattern.lower() in arg_name.lower():
                    self.user_variables.add(arg_name)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        # Check function parameters for user input
        for arg in node.args.args:
            arg_name = arg.arg
            for pattern in self.user_input_patterns:
                if pattern.lower() in arg_name.lower():
                    self.user_variables.add(arg_name)
        
        self.generic_visit(node)





