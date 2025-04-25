from typing import Dict, List, Optional, Any
from .error_handler import error_handler, JiraError
from .connect_handler import JiraConnectHandler

class JiraValidateHandler:
    def __init__(self, connect_handler: JiraConnectHandler):
        self.connect = connect_handler

    @error_handler
    def validate_project(self, project_key: str) -> bool:
        """Validate if a project exists"""
        project = self.connect.get_project(project_key)
        return project is not None

    @error_handler
    def validate_component(self, project_key: str, component_name: str) -> bool:
        """Validate if a component exists in the project"""
        response = self.connect._make_request("GET", f"project/{project_key}/components")
        components = response.json()
        return any(comp["name"] == component_name for comp in components)

    @error_handler
    def validate_version(self, project_key: str, version_name: str) -> bool:
        """Validate if a version exists in the project"""
        response = self.connect._make_request("GET", f"project/{project_key}/versions")
        versions = response.json()
        return any(ver["name"] == version_name for ver in versions)

    @error_handler
    def validate_issue_type(self, project_key: str, issue_type: str) -> bool:
        """Validate if an issue type is available for the project"""
        response = self.connect._make_request("GET", f"project/{project_key}")
        project_data = response.json()
        issue_types = project_data.get("issueTypes", [])
        return any(it["name"] == issue_type for it in issue_types)

    @error_handler
    def validate_epic(self, epic_key: str) -> bool:
        """Validate if an epic exists"""
        try:
            response = self.connect._make_request("GET", f"issue/{epic_key}")
            issue = response.json()
            return issue.get("fields", {}).get("issuetype", {}).get("name") == "Epic"
        except JiraError:
            return False

    @error_handler
    def validate_task_fields(self, task_data: Dict[str, Any]) -> List[str]:
        """Validate required fields for a task"""
        missing_fields = []
        required_fields = ["summary", "description", "issuetype"]
        
        for field in required_fields:
            if field not in task_data.get("fields", {}):
                missing_fields.append(field)
        
        return missing_fields

    @error_handler
    def validate_subtask_fields(self, subtask_data: Dict[str, Any]) -> List[str]:
        """Validate required fields for a subtask"""
        missing_fields = []
        required_fields = ["summary", "description", "parent"]
        
        for field in required_fields:
            if field not in subtask_data.get("fields", {}):
                missing_fields.append(field)
        
        return missing_fields

    @error_handler
    def get_available_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all available issue types for a project"""
        response = self.connect._make_request("GET", f"project/{project_key}")
        project_data = response.json()
        return project_data.get("issueTypes", [])

    @error_handler
    def validate_field(self, field_name: str) -> bool:
        """Validate if a field exists in Jira
        
        Args:
            field_name (str): Name of the field to validate
            
        Returns:
            bool: True if field exists, False otherwise
        """
        try:
            response = self.connect._make_request("GET", "field")
            if response.status_code == 200:
                fields = response.json()
                return any(field["name"].lower() == field_name.lower() for field in fields)
            return False
        except Exception as e:
            print(f"Error validating field {field_name}: {str(e)}")
            return False
