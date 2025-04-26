from typing import Dict, List, Optional, Any
from .error_handler import error_handler, JiraError, JiraDataError
from .connect_handler import JiraConnectHandler
from .json_handler import JsonHandler
import pandas as pd

class JiraValidateHandler:
    def __init__(self, connect_handler: JiraConnectHandler):
        self.connect = connect_handler
        self.json_handler = JsonHandler()

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
        
    def _validate_yaml_structure(self, data: Dict[str, Any]) -> None:
        """Validate the YAML structure has required fields"""
        required_keys = ["project"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            raise JiraDataError(
                f"Missing required keys in YAML: {', '.join(missing_keys)}",
                "INVALID_YAML_STRUCTURE",
                {"missing_keys": missing_keys},
                {"file": "yaml_validation"}
            )
        
        # Validate at least one of epics or tasks exists
        if "epics" not in data and "tasks" not in data:
            raise JiraDataError(
                "YAML must contain either 'epics' or 'tasks' key",
                "INVALID_YAML_STRUCTURE",
                {"error": "No epics or tasks found"},
                {"file": "yaml_validation"}
            )

    def validate_and_clean_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate fields against field_map.json and remove invalid fields
        
        Args:
            fields (Dict[str, Any]): Fields to validate
            
        Returns:
            Dict[str, Any]: Cleaned fields dictionary
        """
        try:
            # Load field_map from JSON
            field_map_df = pd.DataFrame.from_dict(self.json_handler.load_json("field_map.json"), orient='index')
            
            # Create DataFrame from input fields
            fields_df = pd.DataFrame(list(fields.keys()), columns=['field_name'])
            
            # Get valid fields by comparing with field_map
            valid_fields = fields_df[fields_df['field_name'].isin(field_map_df.index)]
            
            # Create cleaned fields dictionary
            cleaned_fields = {field: fields[field] for field in valid_fields['field_name']}
            
            # Log removed fields
            removed_fields = set(fields.keys()) - set(cleaned_fields.keys())
            if removed_fields:
                print(f"Warning: Removed invalid fields: {removed_fields}")
            
            return cleaned_fields
            
        except Exception as e:
            print(f"Error during field validation: {str(e)}")
            # Return original fields if validation fails
            return fields
