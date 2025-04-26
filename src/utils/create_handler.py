import os
import yaml
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import pandas as pd

from .auth_handler import JiraAuthHandler
from .connect_handler import JiraConnectHandler
from .error_handler import error_handler, JiraError, JiraDataError, JiraAPIError
from .get_handler import JiraGetHandler
from .validate_handler import JiraValidateHandler


class JiraCreateHandler:
    """Handler class for creating Jira issues from YAML files"""
    
    def __init__(self):
        """Initialize the handler with authentication and connection handlers"""
        self.auth_handler = JiraAuthHandler()
        self.connect_handler = JiraConnectHandler()
        self.get_handler = JiraGetHandler()
        self.validate_handler = JiraValidateHandler(self.connect_handler)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Validate credentials
        self.auth_handler.validate_credentials()
        
        # Project key from environment or will be loaded from YAML
        self.project_key = os.getenv("PROJECT_KEY")
        
        # Dictionary to store created epics/tasks for reference
        self.created_issues = {
            "epics": {},  # Mapping epic summary to epic key
            "tasks": {},   # Mapping task summary to task key
            "subtasks": {} # Mapping subtask summary to subtask key
        }

    def load_yaml_file(self, filepath: str) -> Dict[str, Any]:
        """Load and parse a YAML file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            if not data:
                raise JiraDataError("YAML file is empty", "EMPTY_FILE", 
                                    {"file": filepath}, 
                                    {"file": "yaml_parser"})
                
            # Set project key from YAML if not set in environment
            if "project" in data and not self.project_key:
                self.project_key = data["project"]
                
            # Validate the structure
            self.validate_handler._validate_yaml_structure(data)
                
            return data
        except yaml.YAMLError as e:
            raise JiraDataError(f"YAML parsing error: {str(e)}", "YAML_PARSE_ERROR", 
                                {"error": str(e)}, 
                                {"file": filepath})
        except Exception as e:
            self.logger.error(f"Error loading YAML file: {str(e)}")
            raise
            
    def _process_issue_response(self, response: Any, summary: str, hierarchy_level: int, is_cleaned: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """Process the issue creation response and store the results
        
        Args:
            response: Response from Jira API
            summary: Issue summary
            hierarchy_level: Hierarchy level of the issue
            is_cleaned: Whether this was created with cleaned fields
            
        Returns:
            Tuple of (issue_id, issue_key) or (None, None) if processing fails
        """
        if response.status_code == 201:
            data = response.json()
            issue_id = data.get("id")
            issue_key = data.get("key")
            
            status_msg = "with cleaned fields" if is_cleaned else ""
            self.logger.info(f"Task created successfully {status_msg}: {issue_key} (ID: {issue_id})")
            
            # Store reference based on hierarchy
            if hierarchy_level == 1:
                self.created_issues["epics"][summary] = issue_key
            elif hierarchy_level == 0:
                self.created_issues["tasks"][summary] = issue_key
            elif hierarchy_level == -1:
                self.created_issues["subtasks"][summary] = issue_key
                
            return issue_id, issue_key
            
        return None, None

    def _prepare_issue_fields(self, summary: str, description: str, issue_type_id: str, 
                            task_data: Dict[str, Any], parent_key: Optional[str] = None, 
                            hierarchy_level: int = 0) -> Dict[str, Any]:
        """Prepare fields for issue creation
        Args:
            summary: Issue summary
            description: Issue description
            issue_type_id: Issue type ID
            task_data: Original task data
            parent_key: Optional parent issue key
            hierarchy_level: Hierarchy level
        Returns:
            Dictionary of prepared fields
        """
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"text": description, "type": "text"}]}]
            },
            "issuetype": {"id": issue_type_id}
        }
        
        # Set parent for tasks and subtasks
        if parent_key and hierarchy_level <= 0:
            fields["parent"] = {"key": parent_key}
            
        # Process standard fields
        for key, value in task_data.items():
            if key in ["summary", "description", "project", "issuetype", "subtasks"]:
                continue
                
            if key == "priority":
                fields["priority"] = {"name": value}
            elif key == "labels":
                fields["labels"] = value if isinstance(value, list) else [value]
            elif key == "assignee":
                fields["assignee"] = {"accountId": value} if '@' in value else {"name": value}
            elif key == "duedate":
                fields["duedate"] = value
            elif key.startswith("customfield_"):
                fields[key] = value
            elif key == "components":
                fields["customfield_10040"] = value if isinstance(value, list) else [value]
            
        return fields

    def _retry_with_cleaned_fields(self, fields: Dict[str, Any], summary: str, hierarchy_level: int) -> Tuple[Optional[str], Optional[str]]:
        """Retry issue creation with cleaned fields after initial failure
        Args:
            fields: Original fields that failed
            summary: Issue summary
            hierarchy_level: Hierarchy level of the issue
        Returns:
            Tuple of (issue_id, issue_key) or (None, None) if retry fails
        """
        try:
            # Validate and clean fields
            cleaned_fields = self.validate_handler.validate_and_clean_fields(fields)
            payload = {"fields": cleaned_fields}
            
            # Retry with cleaned fields
            response = self.connect_handler._make_request("POST", "issue", json=payload)
            if response.status_code != 201:
                self.logger.error(f"Failed to create issue with cleaned fields: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None, None
            else:
                return self._process_issue_response(response, summary, hierarchy_level, is_cleaned=True)
            
        except Exception as retry_error:
            self.logger.error(f"Error during retry attempt: {str(retry_error)}")
            return None, None

    @error_handler
    def create_hierarchical_task(self, task_data: Dict[str, Any], parent_key: Optional[str] = None, 
                               hierarchy_level: int = 0) -> Tuple[Optional[str], Optional[str]]:
        """Create a task with proper hierarchy level
        
        Args:
            task_data: Dictionary containing task details
            parent_key: Optional parent task key
            hierarchy_level: Hierarchy level (1 for Epic, 0 for Task, -1 for Sub-task)
            
        Returns:
            Tuple of (task_id, task_key) or (None, None) if creation fails
        """
        summary = task_data.get("summary")
        description = task_data.get("description", "")
        
        if not summary:
            self.logger.error("Task must have a summary")
            return None, None
            
        # Get issue type ID based on hierarchy level
        issue_type_id = self.get_handler.get_issue_type_by_hierarchy(hierarchy_level)
        if not issue_type_id:
            self.logger.error(f"Could not find issue type for hierarchy level {hierarchy_level}")
            return None, None
            
        # Prepare initial fields
        fields = self._prepare_issue_fields(summary, description, issue_type_id, task_data, parent_key, hierarchy_level)
        payload = {"fields": fields}
        
        try:
            # First attempt with original fields
            response = self.connect_handler._make_request("POST", "issue", json=payload)
            result = self._process_issue_response(response, summary, hierarchy_level)
            if result[0]:
                return result
                
        except JiraAPIError as e:
            self.logger.warning(f"Initial creation attempt failed: {str(e)}")
            return self._retry_with_cleaned_fields(fields, summary, hierarchy_level)
            
        return None, None

    @error_handler
    def process_yaml_file(self, yaml_file: str) -> None:
        """Process a YAML file and create Jira issues with hierarchy"""
        self.logger.info(f"Processing YAML file: {yaml_file}")
        
        data = self.load_yaml_file(yaml_file)
        self.project_key = data.get("project", self.project_key)
        
        if not self.project_key:
            raise JiraDataError(
                "Project key not found in YAML or environment",
                "MISSING_PROJECT_KEY",
                {},
                {"file": yaml_file}
            )
            
        self.logger.info(f"Creating issues for project: {self.project_key}")
        
        # Create epics (hierarchy level 1)
        if "epics" in data:
            for epic_data in data["epics"]:
                epic_id, epic_key = self.create_hierarchical_task(epic_data, hierarchy_level=1)
                if not epic_key:
                    self.logger.warning(f"Failed to create epic: {epic_data.get('summary')}")
                    continue
                    
                # Create tasks under epic
                if "tasks" in epic_data:
                    for task_data in epic_data["tasks"]:
                        task_id, task_key = self.create_hierarchical_task(task_data, epic_key, hierarchy_level=0)
                        if not task_key:
                            self.logger.warning(f"Failed to create task: {task_data.get('summary')}")
                            continue
                            
                        # Create subtasks
                        if "subtasks" in task_data:
                            for subtask_data in task_data["subtasks"]:
                                subtask_id, subtask_key = self.create_hierarchical_task(subtask_data, task_key, hierarchy_level=-1)
                                if not subtask_key:
                                    self.logger.warning(f"Failed to create subtask: {subtask_data.get('summary')}")
                                    
        # Create standalone tasks (hierarchy level 0)
        if "tasks" in data:
            for task_data in data["tasks"]:
                task_id, task_key = self.create_hierarchical_task(task_data, hierarchy_level=0)
                if not task_key:
                    self.logger.warning(f"Failed to create task: {task_data.get('summary')}")
                    continue
                    
                # Create subtasks
                if "subtasks" in task_data:
                    for subtask_data in task_data["subtasks"]:
                        subtask_id, subtask_key = self.create_hierarchical_task(subtask_data, task_key, hierarchy_level=-1)
                        if not subtask_key:
                            self.logger.warning(f"Failed to create subtask: {subtask_data.get('summary')}")

    def upload_roadmap(self, yaml_file: str) -> Dict[str, Any]:
        """Upload a roadmap from a YAML file to Jira
        
        Args:
            yaml_file: Path to the YAML file containing the roadmap
            
        Returns:
            Dictionary with summary of created issues
        """
        try:
            # Check if connection to Jira works
            if not self.connect_handler.test_connection():
                raise JiraError(
                    "Failed to connect to Jira instance",
                    "CONNECTION_ERROR",
                    {"jira_instance": self.auth_handler.get_jira_instance()},
                    {"file": "create_handler"}
                )
                
            # Process the YAML file
            self.process_yaml_file(yaml_file)
            
            # Return summary
            return {
                "success": True,
                "project": self.project_key,
                "created_issues": {
                    "epics": self.created_issues["epics"],
                    "tasks": self.created_issues["tasks"],
                    "subtasks": self.created_issues["subtasks"]
                }
            }
        except Exception as e:
            self.logger.error(f"Error uploading roadmap: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "project": self.project_key,
                "created_issues": self.created_issues
            }

if __name__ == "__main__":
    # Example usage
    create_handler = JiraCreateHandler()
    result = create_handler.upload_roadmap("data/tasks.yaml")
    
    print("\nRoadmap Upload Results:")
    print(f"Success: {result['success']}")
    print(f"Project: {result['project']}")
    
    if result['success']:
        print(f"Created Epics: {len(result['created_issues']['epics'])}")
        print(f"Created Tasks: {len(result['created_issues']['tasks'])}")
        print(f"Created Subtasks: {len(result['created_issues']['subtasks'])}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
