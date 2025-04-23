import requests
import json
import base64
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JIRA_INSTANCE = os.getenv("JIRA_INSTANCE")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")
PROJECT_KEY = os.getenv("PROJECT_KEY")

def get_auth_header():
    auth_str = f"{EMAIL}:{API_TOKEN}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    return {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}

def get_work_items(start_at=0, max_results=50):
    """
    JIRA의 워크 아이템을 가져오는 함수
    :param start_at: 시작 인덱스
    :param max_results: 한 번에 가져올 최대 결과 수
    :return: 워크 아이템 목록
    """
    url = f"{JIRA_INSTANCE}/rest/api/3/search"
    
    # JQL 쿼리 구성
    jql = f"project = {PROJECT_KEY} ORDER BY created DESC"
    
    # API 요청 페이로드 (빈 fields 리스트로 모든 필드 가져오기)
    payload = {
        "jql": jql,
        "startAt": start_at,
        "maxResults": max_results,
        "fields": []  # 빈 리스트로 설정하면 모든 필드를 가져옴
    }
    
    response = requests.post(url, headers=get_auth_header(), json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching work items: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def format_date(date_str):
    """날짜 문자열을 보기 좋게 포맷팅"""
    if not date_str:
        return "Not set"
    try:
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        return date.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str

def format_field_value(value):
    """필드 값을 보기 좋게 포맷팅"""
    if value is None:
        return "None"
    elif isinstance(value, dict):
        if 'displayName' in value:
            return value['displayName']
        elif 'name' in value:
            return value['name']
        elif 'summary' in value:
            return value['summary']
        else:
            # content 형식의 description 처리
            if 'content' in value:
                text_parts = []
                for content in value['content']:
                    if content['type'] == 'paragraph':
                        for text in content.get('content', []):
                            if text['type'] == 'text':
                                text_parts.append(text.get('text', ''))
                return ' '.join(text_parts)
            return json.dumps(value, ensure_ascii=False, indent=2)
    elif isinstance(value, list):
        if not value:
            return "[]"
        if isinstance(value[0], dict):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return ', '.join(map(str, value))
    return str(value)

def display_work_item(item):
    """워크 아이템 정보를 보기 좋게 출력"""
    print("\n" + "="*80)
    print(f"Issue Key: {item['key']}")
    print("="*80)
    
    # 모든 필드 출력
    fields = item["fields"]
    for field_name, field_value in sorted(fields.items()):
        if field_value is not None:  # None이 아닌 값만 출력
            # 필드 이름에서 'customfield_' 접두사 처리
            display_name = field_name
            if field_name.startswith('customfield_'):
                # 여기에 알려진 커스텀 필드 매핑 추가
                custom_field_mapping = {
                    'customfield_10014': 'Epic Link',
                    'customfield_10016': 'Story Points',
                    'customfield_10015': 'Start date',
                    'customfield_10031': 'Category'
                }
                display_name = custom_field_mapping.get(field_name, field_name)
            
            formatted_value = format_field_value(field_value)
            print(f"\n{display_name}:")
            print(f"{formatted_value}")
    
    print("="*80)

def main():
    """메인 함수"""
    if not all([JIRA_INSTANCE, EMAIL, API_TOKEN, PROJECT_KEY]):
        print("Error: Missing required environment variables")
        return
    
    start_at = 0
    max_results = 50
    total_fetched = 0
    
    print(f"\nFetching work items from project {PROJECT_KEY}...\n")
    
    while True:
        result = get_work_items(start_at, max_results)
        if not result:
            break
        print("jira work itemsresult :", result)
        total = result['total']
        issues = result['issues']
        
        for issue in issues:
            display_work_item(issue)
            total_fetched += 1
        
        if total_fetched >= total:
            break
        
        start_at += max_results
        
        # 진행 상황 표시
        print(f"\nFetched {total_fetched} of {total} items...")
        
        # 사용자에게 계속할지 물어보기
        if total_fetched < total:
            response = input("\nFetch more items? (y/n): ")
            if response.lower() != 'y':
                break
    
    print(f"\nTotal work items fetched: {total_fetched}")

if __name__ == "__main__":
    main() 