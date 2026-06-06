"""AST analysis for code structure."""
import ast
from typing import List, Dict, Any
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ASTAnalyzer:
    """Analyze code using Abstract Syntax Tree."""
    
    def analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Python file structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code, filename=file_path)
            
            return {
                "functions": self._extract_functions(tree),
                "classes": self._extract_classes(tree),
                "imports": self._extract_imports(tree),
                "calls": self._extract_function_calls(tree),
            }
        except Exception as e:
            logger.error(f"AST analysis error for {file_path}: {e}")
            return {"error": str(e)}
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions."""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                })
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [base.id for base in node.bases if isinstance(base, ast.Name)],
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                })
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                imports.extend([f"{module}.{alias.name}" for alias in node.names])
        return imports
    
    def _extract_function_calls(self, tree: ast.AST) -> List[str]:
        """Extract function calls."""
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        return list(set(calls))