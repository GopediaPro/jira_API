from .connect_handler import JiraConnectHandler
from .json_handler import JsonHandler
from .error_handler import error_handler, JiraError, JiraAPIError
from typing import Dict, List, Optional, Any
import os

class JiraGetHandler:
    def __init__(self):
        self.jira = JiraConnectHandler()
        self.json_handler = JsonHandler()
        self.project_key = os.getenv("PROJECT_KEY", "NEUN")
        
        # Cache for frequently accessed data
        self._cache = {
            'fields': None,
            'issue_types': None,
            'components': None,
            'versions': None,
            'work_items': None,
            'field_map': None,
            'issue_type_map': None
        }

    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """Clear specific or all cache entries"""
        if cache_key:
            if cache_key in self._cache:
                self._cache[cache_key] = None
        else:
            for key in self._cache:
                self._cache[key] = None

    @error_handler
    def get_fields(self) -> List[Dict]:
        """Get all fields from Jira"""
        if self._cache['fields'] is None:
            response = self.jira._make_request("GET", "field")
            if response.status_code == 200:
                self._cache['fields'] = response.json()
                self.json_handler.save_json(self._cache['fields'], "jira_fields.json")
                # Build field map
                self._build_field_map()
            else:
                raise JiraAPIError(f"Failed to get fields: {response.status_code}")
        return self._cache['fields']

    def _build_field_map(self) -> None:
        """Build a map of field names to their IDs and schemas"""
        if self._cache['fields']:
            self._cache['field_map'] = {}
            for field in self._cache['fields']:
                self._cache['field_map'][field['name']] = {
                    'id': field['id'],
                    'key': field['key'],
                    'schema': field.get('schema', {}),
                    'custom': field.get('custom', False)
                }
            # Save field map for reference
            self.json_handler.save_json(self._cache['field_map'], "field_map.json")

    @error_handler
    def get_issue_types(self) -> List[Dict]:
        """Get all issue types"""
        if self._cache['issue_types'] is None:
            try:
                response = self.jira._make_request("GET", "issuetype")
                if response.status_code == 200:
                    self._cache['issue_types'] = response.json()
                    print("\nDebug - Issue Types Retrieved:")
                    for issue_type in self._cache['issue_types']:
                        print(f"  - {issue_type.get('name', 'Unknown')}: {issue_type.get('id', 'No ID')}")
                    
                    self.json_handler.save_json(self._cache['issue_types'], "issue_types.json")
                    # Build issue type map
                    self._build_issue_type_map()
                else:
                    error_msg = f"Failed to get issue types: {response.status_code}"
                    try:
                        error_details = response.json()
                        error_msg += f"\nResponse: {error_details}"
                    except:
                        error_msg += f"\nResponse Text: {response.text}"
                    raise JiraAPIError(
                        error_msg,
                        "API_ERROR",
                        {"status_code": response.status_code, "response": response.text},
                        {"file": "jira_api", "operation": "get_issue_types"}
                    )
            except Exception as e:
                print(f"\nDebug - Error getting issue types: {str(e)}")
                raise
        return self._cache['issue_types']

    def _build_issue_type_map(self) -> None:
        """Build a map of issue type names to their IDs and metadata"""
        if self._cache['issue_types']:
            try:
                self._cache['issue_type_map'] = {}
                print("\nDebug - Building Issue Type Map:")
                for issue_type in self._cache['issue_types']:
                    name = issue_type.get('name')
                    id = issue_type.get('id')
                    if name and id:
                        self._cache['issue_type_map'][name] = {
                            'id': id,
                            'hierarchyLevel': issue_type.get('hierarchyLevel', 0),
                            'subtask': issue_type.get('subtask', False),
                            'description': issue_type.get('description', '')
                        }
                        print(f"  - Mapped {name} -> {id}")
                    else:
                        print(f"  - Warning: Skipping issue type with missing name or id: {issue_type}")
                
                # Save issue type map for reference
                self.json_handler.save_json(self._cache['issue_type_map'], "issue_type_map.json")
                print(f"  Total mapped issue types: {len(self._cache['issue_type_map'])}")
            except Exception as e:
                print(f"\nDebug - Error building issue type map: {str(e)}")
                raise

    def get_field_id(self, field_name: str) -> Optional[str]:
        """Get field ID by name"""
        if self._cache['field_map'] is None:
            self.get_fields()
        return self._cache['field_map'].get(field_name, {}).get('id')

    def get_issue_type_id(self, issue_type_name: str) -> Optional[str]:
        """Get issue type ID by name"""
        if self._cache['issue_type_map'] is None:
            self.get_issue_types()
        
        if issue_type_name not in self._cache['issue_type_map']:
            print(f"\nDebug - Issue Type Not Found: {issue_type_name}")
            print("Available Issue Types:")
            for name, data in self._cache['issue_type_map'].items():
                print(f"  - {name}: {data['id']}")
            raise JiraError(
                f"Issue type not found: {issue_type_name}",
                "INVALID_ISSUE_TYPE",
                {"issue_type": issue_type_name},
                {"available_types": list(self._cache['issue_type_map'].keys())}
            )
        
        return self._cache['issue_type_map'][issue_type_name]['id']

    @error_handler
    def get_components(self) -> List[Dict]:
        """Get all project components"""
        if self._cache['components'] is None:
            response = self.jira._make_request("GET", f"project/{self.project_key}/components")
            if response.status_code == 200:
                self._cache['components'] = response.json()
                self.json_handler.save_json(self._cache['components'], "components.json")
            else:
                raise JiraAPIError(f"Failed to get components: {response.status_code}")
        return self._cache['components']

    @error_handler
    def get_versions(self) -> List[Dict]:
        """Get all project versions"""
        if self._cache['versions'] is None:
            response = self.jira._make_request("GET", f"project/{self.project_key}/versions")
            if response.status_code == 200:
                self._cache['versions'] = response.json()
                self.json_handler.save_json(self._cache['versions'], "versions.json")
            else:
                raise JiraAPIError(f"Failed to get versions: {response.status_code}")
        return self._cache['versions']

    @error_handler
    def get_work_items(self, jql: Optional[str] = None, fields: Optional[List[str]] = None) -> Dict:
        """Get work items based on JQL"""
        if not jql:
            jql = f'project = {self.project_key} ORDER BY created DESC'
        
        if not fields:
            fields = [
                "summary",
                "description",
                "issuetype",
                "priority",
                "status",
                "assignee",
                "reporter",
                "labels",
                "components",
                "fixVersions",
                "duedate",
                "customfield_10001"  # Epic Name field
            ]
        
        params = {
            "jql": jql,
            "maxResults": 100,
            "fields": ",".join(fields)
        }
        
        response = self.jira._make_request("GET", "search", params=params)
        if response.status_code == 200:
            work_items = response.json()
            self.json_handler.save_json(work_items, "work_items.json")
            self._cache['work_items'] = work_items
            return work_items
        else:
            raise JiraAPIError(f"Failed to get work items: {response.status_code}")

    @error_handler
    def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch and save all data types"""
        results = {
            "fields": self.get_fields(),
            "issue_types": self.get_issue_types(),
            "components": self.get_components(),
            "versions": self.get_versions(),
            "work_items": self.get_work_items(),
            "field_map": self._cache.get('field_map'),
            "issue_type_map": self._cache.get('issue_type_map')
        }
        
        # Save combined results
        self.json_handler.save_json(results, "all_jira_data.json")
        return results

def main():
    """Main function to demonstrate usage"""
    getter = JiraGetHandler()
    
    print("\nFetching all Jira data...")
    try:
        results = getter.fetch_all_data()
        
        print("\nResults saved to JSON files in the 'data' directory:")
        for data_type, data in results.items():
            if data:
                print(f"✓ {data_type} saved successfully")
            else:
                print(f"✗ Failed to fetch {data_type}")
                
    except JiraError as e:
        print(f"\n✗ Error: {str(e)}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
