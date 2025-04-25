import os
import requests
from typing import Optional, Dict, Any, List
import logging

from .error_handler import JiraError

class JiraConnectHandler:
    def __init__(self):
        self.base_url = os.getenv('JIRA_URL', '') or os.getenv('JIRA_INSTANCE', '')
        if self.base_url:
            self.base_url = self.base_url.rstrip('/')
        
        self.username = os.getenv('JIRA_USER') or os.getenv('EMAIL')
        self.token = os.getenv('JIRA_TOKEN') or os.getenv('API_TOKEN')
        
        if not all([self.base_url, self.username, self.token]):
            raise JiraError(
                "Missing required environment variables",
                "ENV_ERROR",
                {"missing": [var for var in ['JIRA_URL/JIRA_INSTANCE', 'JIRA_USER/EMAIL', 'JIRA_TOKEN/API_TOKEN'] 
                             if not os.getenv(var.split('/')[0]) and not os.getenv(var.split('/')[1])]},
                {"file": "environment"}
            )
        
        # Initialize REST client
        self.session = requests.Session()
        self.session.auth = (self.username, self.token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a request to the Jira REST API v3"""
        # Ensure endpoint doesn't start with slash
        endpoint = endpoint.lstrip('/')
        url = f"{self.base_url}/rest/api/3/{endpoint}"
        
        # Log request details
        self.logger.debug(f"Making {method} request to: {url}")
        if 'json' in kwargs:
            self.logger.debug(f"Request payload: {kwargs['json']}")
            
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Log response details
            self.logger.debug(f"Response status: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            self.logger.debug(f"Response content: {response.text}")
            
            if response.status_code == 400:
                error_details = response.json() if response.text else {}
                raise JiraError(
                    f"Invalid request: {error_details.get('errorMessages', ['Unknown error'])[0]}",
                    "INVALID_REQUEST",
                    {"error": error_details},
                    {"file": "jira_api", "endpoint": endpoint}
                )
            
            return response
            
        except requests.exceptions.RequestException as e:
            error_message = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_message += f"\nResponse: {e.response.text}"
            
            self.logger.error(error_message)
            raise JiraError(
                error_message,
                "API_ERROR",
                {"error": str(e), "status_code": getattr(e.response, 'status_code', None)},
                {"file": "jira_api", "endpoint": endpoint}
            )

    def test_connection(self) -> bool:
        """Test the connection to Jira"""
        try:
            response = self._make_request("GET", "myself")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get project information"""
        try:
            response = self._make_request("GET", f"project/{project_key}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self.logger.error(f"Failed to get project {project_key}: {str(e)}")
            return None

    def get_project_details(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific project"""
        try:
            response = self._make_request("GET", f"project/{project_key}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self.logger.error(f"Failed to get project details for {project_key}: {str(e)}")
            return None

    def get_create_meta(self, project_key: str, issue_type_name: str) -> Optional[Dict[str, Any]]:
        """Get create metadata for a specific project and issue type"""
        try:
            params = {
                "projectKeys": project_key,
                "issuetypeNames": issue_type_name,
                "expand": "projects.issuetypes.fields"
            }
            response = self._make_request("GET", "issue/createmeta", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.debug(f"Create meta response: {data}")
                return data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get create metadata: {str(e)}")
            return None

    def get_field_configurations(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get field configurations for a project"""
        try:
            response = self._make_request("GET", f"fieldconfiguration/project/{project_key}")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.debug(f"Field configurations: {data}")
                return data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get field configurations: {str(e)}")
            return None

    def get_screens(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get screens associated with a project"""
        try:
            response = self._make_request("GET", f"screens/addToDefault/available")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.debug(f"Available screens: {data}")
                return data
            return None
        except Exception as e:
            self.logger.error(f"Failed to get screens: {str(e)}")
            return None

    def debug_issue_creation(self, project_key: str, issue_type: str) -> None:
        """Debug issue creation metadata and configurations"""
        self.logger.info(f"\nDebugging issue creation for project {project_key} and type {issue_type}")
        
        # Get create metadata
        create_meta = self.get_create_meta(project_key, issue_type)
        if create_meta:
            projects = create_meta.get("projects", [])
            if projects:
                project = projects[0]
                issue_types = project.get("issuetypes", [])
                if issue_types:
                    issue_type_meta = issue_types[0]
                    self.logger.info("\nAvailable fields for issue creation:")
                    for field_id, field_meta in issue_type_meta.get("fields", {}).items():
                        self.logger.info(f"- {field_id}: {field_meta.get('name')} (Required: {field_meta.get('required', False)})")
        
        # Get field configurations
        field_configs = self.get_field_configurations(project_key)
        if field_configs:
            self.logger.info("\nField configurations:")
            self.logger.info(f"{field_configs}")
        
        # Get screens
        screens = self.get_screens(project_key)
        if screens:
            self.logger.info("\nAvailable screens:")
            self.logger.info(f"{screens}")

    def create_issue(self, project_key: str, summary: str, description: str, issue_type: str = "Task", 
                     fields: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Create a new issue in Jira"""
        try:
            # Prepare request data
            data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": description
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": issue_type}
                }
            }
            
            # Add any additional fields
            if fields:
                data["fields"].update(fields)
            
            response = self._make_request("POST", "issue", json=data)
            
            if response.status_code == 201:
                return response.json()
            else:
                self.logger.error(f"Failed to create issue. Status: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create issue: {str(e)}")
            return None
            
    def get_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all issue types available for a project"""
        try:
            project_data = self.get_project(project_key)
            if project_data and "issueTypes" in project_data:
                return project_data["issueTypes"]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get issue types: {str(e)}")
            return []
            
    def find_epic_link_field(self, project_key: str) -> Optional[str]:
        """Find the custom field ID used for epic links"""
        # Get fields metadata 
        try:
            response = self._make_request("GET", "field")
            if response.status_code == 200:
                fields = response.json()
                # Look for Epic Link field
                for field in fields:
                    if field.get("name") == "Epic Link":
                        return field["id"]
                    
                # Common fallback if name matching fails
                return "customfield_10014"  # Common default in many Jira instances
            return None
        except Exception as e:
            self.logger.error(f"Failed to find Epic Link field: {str(e)}")
            return "customfield_10014"  # Fallback to common default

if __name__ == "__main__":
    # Example usage
    jira_connect = JiraConnectHandler()
    connection_test = jira_connect.test_connection()
    print("\nConnection Test Results:")
    print(f"Connection Test: {'Passed' if connection_test else 'Failed'}")
