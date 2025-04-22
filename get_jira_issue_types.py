import requests
import json
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

def get_auth_header():
    email = os.getenv("EMAIL")
    api_token = os.getenv("API_TOKEN")
    auth_str = f"{email}:{api_token}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    return {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}

def get_all_fields():
    """JIRA의 모든 필드 정보를 조회합니다."""
    jira_instance = os.getenv("JIRA_INSTANCE")
    fields_url = f"{jira_instance}/rest/api/3/field"
    
    response = requests.get(fields_url, headers=get_auth_header())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"필드 조회 실패: {response.status_code}")
        print(response.text)
        return None

def get_issue_types():
    jira_instance = os.getenv("JIRA_INSTANCE")
    project_key = os.getenv("PROJECT_KEY")
    
    # 1. Get all fields
    print("\n1. 모든 필드 정보 조회:")
    fields = get_all_fields()
    if fields:
        field_info = {
            "custom_fields": [],
            "system_fields": []
        }
        
        for field in fields:
            field_data = {
                "id": field.get("id"),
                "name": field.get("name"),
                "custom": field.get("custom", False),
                "schema": field.get("schema", {})
            }
            
            if field.get("custom"):
                field_info["custom_fields"].append(field_data)
            else:
                field_info["system_fields"].append(field_data)
        
        # Save fields information
        with open("jira_fields.json", "w", encoding="utf-8") as f:
            json.dump(field_info, f, indent=2, ensure_ascii=False)
        print("필드 정보가 'jira_fields.json'에 저장되었습니다.")
        
        # Print summary of custom fields
        print("\n커스텀 필드 요약:")
        for field in field_info["custom_fields"]:
            print(f"- {field['name']}")
            print(f"  ID: {field['id']}")
            print(f"  Schema: {field['schema']}")
            print()
    
    # 2. Get all issue types
    issue_types_url = f"{jira_instance}/rest/api/3/issuetype"
    response = requests.get(issue_types_url, headers=get_auth_header())
    print("\n2. 이슈 타입 정보:")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        all_issue_types = response.json()
        
        # 3. Get project-specific information
        project_url = f"{jira_instance}/rest/api/3/project/{project_key}"
        project_response = requests.get(project_url, headers=get_auth_header())
        
        result = {
            "all_issue_types": all_issue_types,
            "project_info": project_response.json() if project_response.status_code == 200 else None,
            "project_key": project_key
        }
        
        # 4. Get createmeta for more detailed information
        meta_url = f"{jira_instance}/rest/api/3/issue/createmeta?projectKeys={project_key}&expand=projects.issuetypes.fields"
        meta_response = requests.get(meta_url, headers=get_auth_header())
        if meta_response.status_code == 200:
            result["create_meta"] = meta_response.json()
            
            # Extract available fields for each issue type
            print("\n각 이슈 타입별 사용 가능한 필드:")
            for project in result["create_meta"]["projects"]:
                for issuetype in project["issuetypes"]:
                    print(f"\n[{issuetype['name']}] 사용 가능한 필드:")
                    for field_id, field_info in issuetype["fields"].items():
                        print(f"- {field_info['name']}")
                        print(f"  ID: {field_id}")
                        print(f"  Required: {field_info.get('required', False)}")
                        if field_info.get('allowedValues'):
                            print(f"  Allowed Values: {[v.get('name') for v in field_info['allowedValues']]}")
        
        # Save to JSON file
        with open("jira_issue_types.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n이슈 타입 정보가 'jira_issue_types.json'에 저장되었습니다.")
        
        # Print summary
        print("\n사용 가능한 이슈 타입 요약:")
        for issue_type in all_issue_types:
            print(f"- {issue_type['name']} (ID: {issue_type['id']})")
            print(f"  Description: {issue_type.get('description', 'No description')}")
            print(f"  Subtask: {issue_type.get('subtask', False)}")
            if issue_type.get('scope'):
                print(f"  Scope: Project {issue_type['scope'].get('project', {}).get('id')}")
            print()
            
    else:
        print(f"이슈 타입 조회 실패: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_issue_types() 