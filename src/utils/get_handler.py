from .connect_handler import JiraConnectHandler
from .json_handler import JsonHandler
import os

class JiraGetHandler:
    def __init__(self):
        self.jira = JiraConnectHandler()
        self.json_handler = JsonHandler()
        self.project_key = os.getenv("PROJECT_KEY")

    def get_and_save_fields(self):
        """Get all fields from Jira and save to JSON"""
        response = self.jira._make_request("GET", "field")
        if response.status_code == 200:
            fields = response.json()
            self.json_handler.save_json(fields, "jira_fields.json")
            return fields
        return None

    def get_and_save_issue_types(self):
        """Get all issue types for the project and save to JSON"""
        response = self.jira._make_request("GET", "search")
        if response.status_code == 200:
            issue_types = response.json()
            self.json_handler.save_json(issue_types, "issue_types.json")
            return issue_types
        return None

    def get_and_save_work_items(self, jql=None):
        """Get work items based on JQL and save to JSON"""
        if not jql:
            jql = f'project = {self.project_key} ORDER BY created DESC'
        
        # Using enhanced_jql for cloud compatibility
        params = {
            "jql": jql,
            "maxResults": 100,  # Adjust as needed
            "fields": "summary,description,issuetype,priority,status,assignee,reporter,labels,components,fixVersions,duedate,customfield_10001"
        }
        
        response = self.jira._make_request("GET", "search", params=params)
        if response.status_code == 200:
            work_items = response.json()
            self.json_handler.save_json(work_items, "work_items.json")
            return work_items
        return None

    def fetch_all_data(self):
        """Fetch and save all data types"""
        results = {
            "fields": self.get_and_save_fields(),
            "issue_types": self.get_and_save_issue_types(),
            "work_items": self.get_and_save_work_items()
        }
        
        # Save combined results
        self.json_handler.save_json(results, "all_jira_data.json")
        return results

def main():
    """Main function to demonstrate usage"""
    getter = JiraGetHandler()
    
    print("\nFetching all Jira data...")
    results = getter.fetch_all_data()
    
    print("\nResults saved to JSON files in the 'data' directory:")
    for data_type, data in results.items():
        if data:
            print(f"✓ {data_type} saved successfully")
        else:
            print(f"✗ Failed to fetch {data_type}")

if __name__ == "__main__":
    main()
