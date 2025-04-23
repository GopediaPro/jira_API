from utils.connect_handler import JiraConnectHandler
from utils.get_handler import JiraGetHandler

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

def main():
    # Test connection first
    test_connection()
    
    # If connection is successful, fetch data
    fetch_jira_data()

if __name__ == "__main__":
    main() 