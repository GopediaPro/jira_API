from utils.connect_handler import JiraConnectHandler
from utils.get_handler import JiraGetHandler
from utils.create_handler import JiraCreateHandler
from utils.error_handler import JiraError
import os
import sys
import logging
from typing import Dict, Any

class JiraManager:
    def __init__(self):
        """Initialize Jira Manager with all handlers"""
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        try:
            self.connect_handler = JiraConnectHandler()
            self.get_handler = JiraGetHandler()
            self.create_handler = JiraCreateHandler()
        except JiraError as e:
            self.logger.error(f"Initialization error: {str(e)}")
            sys.exit(1)

    def test_connection(self) -> Dict[str, Any]:
        """Test Jira connection and return detailed results"""
        try:
            is_connected = self.connect_handler.test_connection()
            project_key = os.getenv("PROJECT_KEY", "Not set")
            
            results = {
                "connection": "✓ Connected" if is_connected else "✗ Failed",
                "project_key": project_key,
                "jira_url": self.connect_handler.base_url,
                "username": self.connect_handler.username
            }
            
            if is_connected:
                # Try to get project details
                project_details = self.connect_handler.get_project(project_key)
                if project_details:
                    results["project_name"] = project_details.get("name", "Unknown")
                    results["project_type"] = project_details.get("projectTypeKey", "Unknown")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {"connection": "✗ Failed", "error": str(e)}

    def fetch_jira_data(self, data_types: list = None) -> Dict[str, Any]:
        """Fetch specific or all Jira data"""
        try:
            if not data_types:
                data_types = ["fields", "issue_types", "components", "versions", "work_items"]
            
            results = {}
            for data_type in data_types:
                self.logger.info(f"Fetching {data_type}...")
                if hasattr(self.get_handler, f"get_{data_type}"):
                    results[data_type] = getattr(self.get_handler, f"get_{data_type}")()
                else:
                    self.logger.warning(f"Unknown data type: {data_type}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            return {"error": str(e)}

    def create_jira_issues(self, yaml_file: str) -> Dict[str, Any]:
        """Create Jira issues from YAML file"""
        try:
            self.logger.info(f"Creating issues from {yaml_file}...")
            return self.create_handler.upload_roadmap(yaml_file)
            
        except Exception as e:
            self.logger.error(f"Error creating issues: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

def print_results(results: Dict[str, Any], section: str = None) -> None:
    """Print results in a formatted way"""
    if section == "connection":
        print("\n=== Connection Test Results ===")
        for key, value in results.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    elif section == "data":
        print("\n=== Data Fetch Results ===")
        for data_type, data in results.items():
            if isinstance(data, list):
                print(f"\n{data_type.replace('_', ' ').title()}: {len(data)} items")
            elif isinstance(data, dict):
                print(f"\n{data_type.replace('_', ' ').title()}: {len(data.keys())} items")
            else:
                print(f"\n{data_type.replace('_', ' ').title()}: {'Success' if data else 'Failed'}")
    
    elif section == "creation":
        print("\n=== Issue Creation Results ===")
        print(f"Success: {'✓' if results.get('success') else '✗'}")
        print(f"Project: {results.get('project', 'Unknown')}")
        
        if results.get('success'):
            created = results.get('created_issues', {})
            print(f"Created Epics: {len(created.get('epics', {}))}")
            print(f"Created Tasks: {len(created.get('tasks', {}))}")
            print(f"Created Subtasks: {len(created.get('subtasks', {}))}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")

def display_menu() -> None:
    """Display the main menu"""
    print("\n=== Jira Manager Menu ===")
    print("1. Test Connection")
    print("2. Fetch Jira Data")
    print("3. Create Issues from YAML")
    print("4. Full Sync (Fetch & Create)")
    print("5. Exit")

def main():
    """Main function with improved menu and error handling"""
    try:
        jira_manager = JiraManager()
        
        while True:
            display_menu()
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == "1":
                results = jira_manager.test_connection()
                print_results(results, "connection")
                
            elif choice == "2":
                print("\nSelect data types to fetch (comma-separated):")
                print("Available: fields, issue_types, components, versions, work_items")
                print("Press Enter for all")
                
                data_types = input("\nEnter data types: ").strip()
                data_types = [t.strip() for t in data_types.split(",")] if data_types else None
                
                results = jira_manager.fetch_jira_data(data_types)
                print_results(results, "data")
                
            elif choice == "3":
                yaml_file = input("\nEnter path to YAML file (default: data/tasks.yaml): ").strip()
                yaml_file = yaml_file or "data/tasks.yaml"
                
                results = jira_manager.create_jira_issues(yaml_file)
                print_results(results, "creation")
                
            elif choice == "4":
                # Fetch data first
                print("\nFetching Jira data...")
                fetch_results = jira_manager.fetch_jira_data()
                print_results(fetch_results, "data")
                
                # Then create issues
                yaml_file = input("\nEnter path to YAML file (default: data/tasks.yaml): ").strip()
                yaml_file = yaml_file or "data/tasks.yaml"
                
                create_results = jira_manager.create_jira_issues(yaml_file)
                print_results(create_results, "creation")
                
            elif choice == "5":
                print("\nExiting Jira Manager. Goodbye!")
                break
                
            else:
                print("\nInvalid choice. Please enter a number between 1 and 5.")
                
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user. Exiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 