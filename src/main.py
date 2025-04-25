from utils.connect_handler import JiraConnectHandler
from utils.get_handler import JiraGetHandler
from utils.create_handler import JiraCreateHandler

def test_connection():
    """Test Jira connection"""
    jira_connect = JiraConnectHandler()
    connection_test = jira_connect.test_connection()
    
    print("\nConnection Test Results:")
    for test_name, result in connection_test.items():
        print(f"\n{test_name.upper()}:")
        print(result)

def fetch_jira_data():
    """Fetch and save Jira data"""
    getter = JiraGetHandler()
    print("\nFetching Jira data...")
    results = getter.fetch_all_data()
    
    print("\nResults saved to JSON files in the 'data' directory:")
    for data_type, data in results.items():
        if data:
            print(f"✓ {data_type} saved successfully")
        else:
            print(f"✗ Failed to fetch {data_type}")

def create_jira_issues():
    """Create Jira issues from tasks.json"""
    creator = JiraCreateHandler()
    print("\nCreating Jira issues from tasks.json...")
    try:
        results = creator.process_tasks_json()
        
        print("\nCreated issues:")
        print("\nEpics:")
        for epic in results["epics"]:
            print(f"✓ {epic['key']}: {epic['summary']}")
            
        print("\nTasks:")
        for task in results["tasks"]:
            print(f"✓ {task['key']}: {task['summary']}")
            
        print("\nSubtasks:")
        for subtask in results["subtasks"]:
            print(f"✓ {subtask['key']}: {subtask['summary']} (Parent: {subtask['parent_key']})")
            
        print("\nResults saved to data/created_issues.json")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")

def main():
    # Test connection first
    test_connection()
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Fetch Jira data")
    print("2. Create issues from tasks.json")
    print("3. Both")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        fetch_jira_data()
    elif choice == "2":
        create_jira_issues()
    elif choice == "3":
        fetch_jira_data()
        create_jira_issues()
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main() 