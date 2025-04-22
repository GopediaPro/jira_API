import requests
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_auth_header():
    email = os.getenv("EMAIL")
    api_token = os.getenv("API_TOKEN")
    auth_str = f"{email}:{api_token}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    return {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}

def test_jira_connection():
    jira_instance = os.getenv("JIRA_INSTANCE")
    
    # 1. Test basic authentication
    auth_url = f"{jira_instance}/rest/api/3/myself"
    auth_response = requests.get(auth_url, headers=get_auth_header())
    print("\n1. Authentication Test:")
    print(f"Status Code: {auth_response.status_code}")
    print(f"Response: {auth_response.text}")
    
    # 2. Test project access
    project_key = os.getenv("PROJECT_KEY")
    project_url = f"{jira_instance}/rest/api/3/project/{project_key}"
    project_response = requests.get(project_url, headers=get_auth_header())
    print("\n2. Project Access Test:")
    print(f"Status Code: {project_response.status_code}")
    print(f"Response: {project_response.text}")
    
    # 3. List all accessible projects
    projects_url = f"{jira_instance}/rest/api/3/project"
    projects_response = requests.get(projects_url, headers=get_auth_header())
    print("\n3. All Accessible Projects:")
    print(f"Status Code: {projects_response.status_code}")
    if projects_response.status_code == 200:
        projects = projects_response.json()
        for project in projects:
            print(f"Project Key: {project.get('key')}, Name: {project.get('name')}")

if __name__ == "__main__":
    test_jira_connection() 