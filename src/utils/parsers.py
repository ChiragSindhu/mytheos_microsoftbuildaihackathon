"""Error log and stack trace parsers."""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ParsedError:
    """Parsed error information."""
    error_type: str
    error_message: str
    file_path: Optional[str]
    line_number: Optional[int]
    function_name: Optional[str]
    stack_trace: List[Dict[str, Any]]
    language: str

def parse_error_log(error_log: str) -> ParsedError:
    """Parse error log to extract structured information."""
    
    # Detect language
    language = detect_language(error_log)
    
    if language == "python":
        return parse_python_error(error_log)
    elif language == "javascript":
        return parse_javascript_error(error_log)
    elif language == "java":
        return parse_java_error(error_log)
    else:
        return parse_generic_error(error_log)

def detect_language(error_log: str) -> str:
    """Detect programming language from error log."""
    if "Traceback (most recent call last)" in error_log:
        return "python"
    elif "Error:" in error_log and ".js:" in error_log:
        return "javascript"
    elif "Exception in thread" in error_log:
        return "java"
    return "unknown"

def parse_python_error(error_log: str) -> ParsedError:
    """Parse Python error/traceback."""
    lines = error_log.split('\n')
    
    # Extract error type and message (last non-empty line)
    error_line = ""
    for line in reversed(lines):
        if line.strip():
            error_line = line.strip()
            break
    
    # Parse error type and message
    error_match = re.match(r'(\w+(?:Error|Exception)):\s*(.+)', error_line)
    if error_match:
        error_type = error_match.group(1)
        error_message = error_match.group(2)
    else:
        error_type = "UnknownError"
        error_message = error_line
    
    # Extract stack trace
    stack_trace = []
    file_pattern = re.compile(r'File "(.+)", line (\d+)(?:, in (.+))?')
    
    for i, line in enumerate(lines):
        match = file_pattern.search(line)
        if match:
            file_path = match.group(1)
            line_number = int(match.group(2))
            function_name = match.group(3) if match.group(3) else None
            
            # Get the code line (next line)
            code_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            
            stack_trace.append({
                'file': file_path,
                'line': line_number,
                'function': function_name,
                'code': code_line
            })
    
    # Get the most recent frame
    file_path = stack_trace[-1]['file'] if stack_trace else None
    line_number = stack_trace[-1]['line'] if stack_trace else None
    function_name = stack_trace[-1]['function'] if stack_trace else None
    
    return ParsedError(
        error_type=error_type,
        error_message=error_message,
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        stack_trace=stack_trace,
        language="python"
    )

def parse_javascript_error(error_log: str) -> ParsedError:
    """Parse JavaScript error."""
    lines = error_log.split('\n')
    
    # Extract error (first line usually)
    error_line = lines[0].strip() if lines else ""
    error_parts = error_line.split(':', 1)
    error_type = error_parts[0].strip() if error_parts else "Error"
    error_message = error_parts[1].strip() if len(error_parts) > 1 else error_line
    
    # Extract stack trace
    stack_trace = []
    stack_pattern = re.compile(r'at (?:(.+) \()?(.+):(\d+):(\d+)\)?')
    
    for line in lines[1:]:
        match = stack_pattern.search(line)
        if match:
            function_name = match.group(1)
            file_path = match.group(2)
            line_number = int(match.group(3))
            
            stack_trace.append({
                'file': file_path,
                'line': line_number,
                'function': function_name,
                'code': ''
            })
    
    file_path = stack_trace[0]['file'] if stack_trace else None
    line_number = stack_trace[0]['line'] if stack_trace else None
    function_name = stack_trace[0]['function'] if stack_trace else None
    
    return ParsedError(
        error_type=error_type,
        error_message=error_message,
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        stack_trace=stack_trace,
        language="javascript"
    )

def parse_java_error(error_log: str) -> ParsedError:
    """Parse Java exception."""
    lines = error_log.split('\n')
    
    # First line has exception
    error_line = lines[0].strip() if lines else ""
    error_parts = error_line.split(':', 1)
    error_type = error_parts[0].replace("Exception in thread", "").strip().strip('"')
    error_message = error_parts[1].strip() if len(error_parts) > 1 else ""
    
    # Extract stack trace
    stack_trace = []
    stack_pattern = re.compile(r'at (.+)\((.+):(\d+)\)')
    
    for line in lines[1:]:
        match = stack_pattern.search(line)
        if match:
            function_name = match.group(1)
            file_path = match.group(2)
            line_number = int(match.group(3))
            
            stack_trace.append({
                'file': file_path,
                'line': line_number,
                'function': function_name,
                'code': ''
            })
    
    file_path = stack_trace[0]['file'] if stack_trace else None
    line_number = stack_trace[0]['line'] if stack_trace else None
    function_name = stack_trace[0]['function'] if stack_trace else None
    
    return ParsedError(
        error_type=error_type,
        error_message=error_message,
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        stack_trace=stack_trace,
        language="java"
    )

def parse_generic_error(error_log: str) -> ParsedError:
    """Parse generic error log."""
    return ParsedError(
        error_type="GenericError",
        error_message=error_log[:200],
        file_path=None,
        line_number=None,
        function_name=None,
        stack_trace=[],
        language="unknown"
    )

def extract_stack_trace(error_log: str) -> List[str]:
    """Extract just the stack trace lines."""
    parsed = parse_error_log(error_log)
    return [f"{frame['file']}:{frame['line']} in {frame['function']}" 
            for frame in parsed.stack_trace]