import json
import logging
from typing import Optional, Dict, Any
from functools import wraps
import traceback
import os

class JiraError(Exception):
    """Base exception class for Jira API errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None, location: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.location = location or {}
        super().__init__(self.message)

class JiraAPIError(JiraError):
    """Exception for API-related errors"""
    pass

class JiraDataError(JiraError):
    """Exception for data validation/processing errors"""
    pass

class JiraFileError(JiraError):
    """Exception for file operation errors"""
    pass

class ErrorHandler:
    def __init__(self, log_file: str = "jira_errors.log"):
        """Initialize error handler with logging configuration"""
        self.logger = logging.getLogger("jira_api")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def handle_api_error(self, response) -> None:
        """Handle API response errors"""
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            error_data = {"error": response.text}
        
        error_message = error_data.get("errorMessages", ["Unknown API error"])[0]
        error_code = str(response.status_code)
        
        self.logger.error(f"API Error {error_code}: {error_message}")
        raise JiraAPIError(error_message, error_code, error_data)

    def handle_json_error(self, error: json.JSONDecodeError, file_path: str) -> None:
        """Handle JSON parsing errors"""
        # Get the problematic line from the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                error_line = lines[error.lineno - 1] if error.lineno <= len(lines) else "<<line not found>>"
        except Exception:
            error_line = "<<unable to read file>>"

        # Create error location info
        location = {
            "file": os.path.basename(file_path),
            "full_path": file_path,
            "line_number": error.lineno,
            "column": error.colno,
            "position": error.pos,
            "error_line": error_line.strip(),
            "error_indicator": "^".rjust(error.colno, " ")  # Visual indicator of error position
        }

        error_message = (
            f"JSON parsing error in {location['file']}:\n"
            f"Line {location['line_number']}, Column {location['column']}:\n"
            f"{location['error_line']}\n"
            f"{location['error_indicator']}\n"
            f"Error: {str(error)}"
        )

        self.logger.error(error_message)
        raise JiraDataError(error_message, "JSON_PARSE_ERROR", {
            "error_type": "json_parse",
            "error_details": str(error)
        }, location)

    def handle_file_error(self, error: Exception, file_path: str) -> None:
        """Handle file operation errors"""
        location = {
            "file": os.path.basename(file_path),
            "full_path": file_path,
            "operation": error.__class__.__name__
        }

        error_message = f"File operation error with {location['file']}: {str(error)}"
        self.logger.error(error_message)
        raise JiraFileError(error_message, "FILE_ERROR", {
            "error_type": type(error).__name__
        }, location)

def error_handler(func):
    """Decorator for handling errors in Jira operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JiraError:
            # Re-raise Jira-specific errors
            raise
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            file_path = kwargs.get('json_file', 'unknown_file')
            if not os.path.isabs(file_path):
                # If it's a relative path, try to resolve it relative to data directory
                data_dir = os.path.join(os.getcwd(), 'data')
                possible_path = os.path.join(data_dir, file_path)
                if os.path.exists(possible_path):
                    file_path = possible_path
            ErrorHandler().handle_json_error(e, file_path)
        except Exception as e:
            # Get the source file and line number where the error occurred
            tb = traceback.extract_tb(e.__traceback__)[-1]
            location = {
                "file": os.path.basename(tb.filename),
                "full_path": tb.filename,
                "line_number": tb.lineno,
                "function": tb.name,
                "line": tb.line
            }

            error_message = (
                f"Error in {location['file']} at line {location['line_number']}:\n"
                f"Function: {location['function']}\n"
                f"Code: {location['line']}\n"
                f"Error: {str(e)}"
            )

            ErrorHandler().logger.error(f"{error_message}\n{traceback.format_exc()}")
            raise JiraError(error_message, "UNEXPECTED_ERROR", {
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }, location)
    return wrapper
