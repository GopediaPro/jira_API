import requests
import os
import sys
from pathlib import Path

# Add parent directory to Python path for direct script execution
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from .auth_handler import JiraAuthHandler  # For package import
except ImportError:
    from src.utils.auth_handler import JiraAuthHandler  # For direct script execution

class JiraConnectHandler:
    def __init__(self):
        self.auth_handler = JiraAuthHandler()
        self.headers = self.auth_handler.get_auth_header()
        self.base_url = self.auth_handler.get_jira_instance()
        
    def _make_request(self, method, endpoint, data=None, params=None):
        """Generic method to make HTTP requests to Jira API"""
        url = f"{self.base_url}/rest/api/3/{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=data,
            params=params
        )
        return response

    def test_connection(self):
        """Test Jira API connection and authentication"""
        results = {
            "auth_test": self._test_authentication(),
            "project_access": self._test_project_access(),
            "projects_list": self._list_accessible_projects()
        }
        return results

    def _test_authentication(self):
        """Test authentication with Jira API"""
        response = self._make_request("GET", "myself")
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }

    def _test_project_access(self):
        """Test access to specific project"""
        project_key = os.getenv("PROJECT_KEY")
        response = self._make_request("GET", f"project/{project_key}")
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }

    def _list_accessible_projects(self):
        """List all accessible projects"""
        response = self._make_request("GET", "project")
        if response.status_code == 200:
            projects = response.json()
            return {
                "status_code": response.status_code,
                "projects": [
                    {"key": proj.get("key"), "name": proj.get("name")}
                    for proj in projects
                ]
            }
        return {
            "status_code": response.status_code,
            "response": response.text
        }

    def get_project_details(self, project_key):
        """Get detailed information about a specific project"""
        response = self._make_request("GET", f"project/{project_key}")
        return response.json() if response.status_code == 200 else None

    def create_issue(self, project_key, summary, description, issue_type="Task"):
        """Create a new issue in Jira"""
        data = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type}
            }
        }
        response = self._make_request("POST", "issue", data=data)
        return response.json() if response.status_code == 201 else None

if __name__ == "__main__":
    # Example usage
    jira_connect = JiraConnectHandler()
    connection_test = jira_connect.test_connection()
    print("\nConnection Test Results:")
    for test_name, result in connection_test.items():
        print(f"\n{test_name.upper()}:")
        print(result) 