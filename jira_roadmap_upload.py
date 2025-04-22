import requests
import json
from datetime import datetime, timedelta
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Jira 연결 설정
JIRA_INSTANCE = os.getenv("JIRA_INSTANCE")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")
PROJECT_KEY = os.getenv("PROJECT_KEY")
EPIC_NAME = os.getenv("EPIC_NAME")

# 이슈 타입 ID 설정
ISSUE_TYPE_IDS = {
    "TASK": "10001",    # Task for NEUN project
    "SUB_TASK": "10002", # Sub-task for NEUN project
    "EPIC": "10010"     # Epic for NEUN project
}

# 환경 변수 검증
def validate_env_vars():
    required_vars = {
        "JIRA_INSTANCE": JIRA_INSTANCE,
        "EMAIL": EMAIL,
        "API_TOKEN": API_TOKEN,
        "PROJECT_KEY": PROJECT_KEY,
        "EPIC_NAME": EPIC_NAME
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    # JIRA_INSTANCE URL 형식 검증
    if not JIRA_INSTANCE.startswith(("http://", "https://")):
        raise ValueError("JIRA_INSTANCE must start with http:// or https://")

# 인증 헤더 생성
def get_auth_header():
    auth_str = f"{EMAIL}:{API_TOKEN}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
    return {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}

# 프로젝트의 사용 가능한 이슈 타입 확인 및 필드 정보 가져오기
def get_project_issue_types():
    url = f"{JIRA_INSTANCE}/rest/api/3/project/{PROJECT_KEY}"
    response = requests.get(url, headers=get_auth_header())
    
    if response.status_code == 200:
        project_data = response.json()
        issue_types = project_data.get('issueTypes', [])
        
        # 디버깅을 위해 이슈 타입 정보 출력
        print("\n사용 가능한 이슈 타입:")
        for issue_type in issue_types:
            print(f"- {issue_type.get('name')} (ID: {issue_type.get('id')})")
        
        # 이슈 타입 정보 반환
        return issue_types
    else:
        print(f"프로젝트 정보 조회 실패: {response.status_code}")
        print(response.text)
        return []

# JIRA에서 필드 정보 가져오기
def get_available_fields():
    url = f"{JIRA_INSTANCE}/rest/api/3/field"
    response = requests.get(url, headers=get_auth_header())
    
    if response.status_code == 200:
        fields = response.json()
        # 필드 ID를 키로 하는 딕셔너리 생성
        field_dict = {field['id']: field for field in fields}
        return field_dict
    else:
        print(f"필드 정보 조회 실패: {response.status_code}")
        print(response.text)
        return {}

# Epic 생성 함수
def create_epic(summary, description, is_real_epic=True):
    url = f"{JIRA_INSTANCE}/rest/api/3/issue"
    
    # 이슈 타입 ID 확인
    issue_types = get_project_issue_types()
    epic_id = None
    task_id = None
    
    # 프로젝트에서 사용 가능한 이슈 타입 ID 찾기
    for issue_type in issue_types:
        name = issue_type.get('name', '').lower()
        id = issue_type.get('id')
        if name == 'epic':
            epic_id = id
        elif name == 'task':
            task_id = id
    
    # 이슈 타입 ID 설정
    if is_real_epic and epic_id:
        issue_type_id = epic_id
        print(f"Epic 타입 사용 (ID: {issue_type_id})")
    else:
        issue_type_id = task_id or ISSUE_TYPE_IDS["TASK"]
        print(f"Task 타입을 Epic 대용으로 사용 (ID: {issue_type_id})")
    
    # 기본 필드 설정
    fields = {
        "project": {"key": PROJECT_KEY},
        "summary": summary,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"text": description, "type": "text"}]}]
        },
        "issuetype": {"id": issue_type_id}
    }
    
    # Task를 Epic 대용으로 사용하는 경우 레이블 추가
    if not is_real_epic or not epic_id:
        fields["labels"] = ["epic"]
    
    # payload 생성
    payload = {"fields": fields}
    
    # 생성 요청 전송
    response = requests.post(url, headers=get_auth_header(), data=json.dumps(payload))
    if response.status_code == 201:
        epic_id = response.json()["id"]
        epic_key = response.json()["key"]
        print(f"Epic 생성 성공: {epic_key} (ID: {epic_id})")
        return epic_id, epic_key
    else:
        print(f"Epic 생성 실패: {response.status_code}")
        print(f"요청 데이터: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        print(f"응답: {response.text}")
        
        # 오류 응답 분석
        try:
            error_data = response.json()
            errors = error_data.get("errors", {})
            
            # 필드 오류가 있으면 해당 필드를 제거하고 다시 시도
            if errors:
                print("필드 오류가 발견되어 다시 시도합니다.")
                for field in errors.keys():
                    if field in fields:
                        print(f"'{field}' 필드를 제거합니다.")
                        del fields[field]
                
                # 다시 시도
                retry_payload = {"fields": fields}
                retry_response = requests.post(url, headers=get_auth_header(), data=json.dumps(retry_payload))
                if retry_response.status_code == 201:
                    epic_id = retry_response.json()["id"]
                    epic_key = retry_response.json()["key"]
                    print(f"Epic 생성 성공 (다시 시도): {epic_key} (ID: {epic_id})")
                    return epic_id, epic_key
                else:
                    print(f"Epic 생성 실패 (다시 시도): {retry_response.status_code}")
                    print(f"응답: {retry_response.text}")
        except Exception as e:
            print(f"오류 응답 처리 중 예외 발생: {str(e)}")
        
        return None, None

# Task/Sub-task 생성 함수
def create_task(summary, description, epic_key=None, parent_key=None, issue_type="Task", 
                priority="Medium", story_points=None, start_date=None, due_date=None, 
                category=None, labels=None):
    url = f"{JIRA_INSTANCE}/rest/api/3/issue"
    
    # 이슈 타입 ID 확인
    issue_types = get_project_issue_types()
    task_id = None
    subtask_id = None
    
    # 프로젝트에서 사용 가능한 이슈 타입 ID 찾기
    for issue_type_info in issue_types:
        name = issue_type_info.get('name', '').lower()
        id = issue_type_info.get('id')
        if name == 'task':
            task_id = id
        elif name == 'sub-task':
            subtask_id = id
    
    # Sub-task인 경우와 일반 Task인 경우 구분
    is_subtask = issue_type.lower() == "sub-task" or issue_type.lower() == "subtask"
    
    # Sub-task인데 parent_key가 없으면 일반 Task로 생성
    if is_subtask and not parent_key:
        is_subtask = False
        print("경고: Sub-task에 부모 이슈 키가 지정되지 않아 일반 Task로 생성합니다.")
    
    # 적절한 이슈 타입 ID 설정
    if is_subtask and subtask_id:
        issue_type_id = subtask_id
    else:
        issue_type_id = task_id or ISSUE_TYPE_IDS["TASK"]
    
    print(f"이슈 타입 '{issue_type}' 사용 (ID: {issue_type_id})")
    
    # 기본 필드 설정
    fields = {
        "project": {"key": PROJECT_KEY},
        "summary": summary,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"text": description, "type": "text"}]}]
        },
        "issuetype": {"id": issue_type_id}
    }
    
    # Sub-task인 경우 부모 이슈 연결 (필수 필드)
    if is_subtask and parent_key:
        fields["parent"] = {"key": parent_key}
    
    # 사용 가능한 필드 정보 가져오기
    available_fields = get_available_fields()
    
    # Add category if available and valid
    if category:
        # 유효한 카테고리 값 목록 가져오기 (실제로는 API 호출이 필요할 수 있음)
        valid_categories = ["Infrastructure", "Core Services", "Security", "Frontend", 
                           "Integration", "Automation", "AI", "Database", "Knowledge",
                           "Dashboard", "Monitoring", "ERP", "Search", "Performance",
                           "UX", "Localization", "Testing", "Stability", "Analytics", 
                           "Architecture", "Data", "Reliability", "Network"]
        
        # 유효한 카테고리인 경우에만 추가
        if category in valid_categories and "customfield_10031" in available_fields:
            fields["customfield_10031"] = {"value": category}
    
    # Add labels if available
    labels_list = labels or []
    
    # Epic 관련 태스크임을 표시
    if epic_key and not is_subtask:
        labels_list.append("epic-task")  # Epic에 속한 태스크임을 표시
        
        # Epic Link 필드 사용 (customfield_10014가 일반적인 Epic Link 필드 ID)
        if "customfield_10014" in available_fields:
            print(f"Epic Link 필드 사용하여 {epic_key}에 연결")
            fields["customfield_10014"] = epic_key
        # 또는 다른 Epic Link 필드 ID를 찾아서 사용 (프로젝트마다 다를 수 있음)
        else:
            # Epic Link 필드 ID 찾기
            epic_link_field = next((field_id for field_id, field_info in available_fields.items() 
                                  if field_info.get('name') == 'Epic Link'), None)
            if epic_link_field:
                print(f"Epic Link 필드({epic_link_field}) 사용하여 {epic_key}에 연결")
                fields[epic_link_field] = epic_key
            else:
                print("Epic Link 필드 없음. Epic 연결 불가.")
    
    # 레이블이 있으면 추가
    if labels_list:
        fields["labels"] = labels_list
    
    # Priority가 사용 가능한 경우 추가
    if "priority" in available_fields:
        fields["priority"] = {"name": str(priority)}
    
    # Story Points 필드 추가
    if story_points and "customfield_10016" in available_fields:
        fields["customfield_10016"] = float(story_points)
    
    # 시작 날짜 필드 추가
    if start_date and "customfield_10015" in available_fields:
        fields["customfield_10015"] = start_date.strftime("%Y-%m-%d")
    
    # 마감일 필드 추가
    if due_date and "duedate" in available_fields:
        fields["duedate"] = due_date.strftime("%Y-%m-%d")
    
    # 최종 payload 생성
    payload = {"fields": fields}
    print(f"이슈 생성 요청: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    # API 요청 전송
    response = requests.post(url, headers=get_auth_header(), data=json.dumps(payload))
    if response.status_code == 201:
        task_id = response.json()["id"]
        task_key = response.json()["key"]
        status_text = "Sub-task" if is_subtask else "Task"
        print(f"{status_text} 업로드 성공: {task_key} (ID: {task_id})")
        return task_id, task_key
    else:
        status_text = "Sub-task" if is_subtask else "Task"
        print(f"{status_text} 생성 실패: {response.status_code}")
        print(f"요청 데이터: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        print(f"응답: {response.text}")
        
        # 오류 응답 분석 및 재시도
        try:
            error_data = response.json()
            errors = error_data.get("errors", {})
            
            # 필드 오류가 있으면 해당 필드를 제거하고 다시 시도
            if errors:
                print(f"필드 오류가 발견되어 {status_text} 생성을 다시 시도합니다.")
                for field in errors.keys():
                    if field in fields:
                        print(f"'{field}' 필드를 제거합니다.")
                        del fields[field]
                
                # 다시 시도
                retry_payload = {"fields": fields}
                retry_response = requests.post(url, headers=get_auth_header(), data=json.dumps(retry_payload))
                if retry_response.status_code == 201:
                    task_id = retry_response.json()["id"]
                    task_key = retry_response.json()["key"]
                    print(f"{status_text} 업로드 성공 (다시 시도): {task_key} (ID: {task_id})")
                    return task_id, task_key
                else:
                    print(f"{status_text} 생성 실패 (다시 시도): {retry_response.status_code}")
                    print(f"응답: {retry_response.text}")
        except Exception as e:
            print(f"오류 응답 처리 중 예외 발생: {str(e)}")
        
        return None, None

# 로드맵에 따른 태스크 생성
def create_roadmap_tasks():
    # 프로젝트 이슈 타입 가져오기
    available_issue_types = get_project_issue_types()
    issue_type_names = [it.get('name', '').lower() for it in available_issue_types] if available_issue_types else []
    
    # Epic 이슈 타입이 있는지 확인
    has_epic_type = 'epic' in issue_type_names
    
    # Load tasks from JSON file
    with open('test_tasks.json', 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    # 스테이지(단계)별 그룹화
    stages = {}
    for task in tasks:
        stage = task['stage']
        if stage not in stages:
            stages[stage] = []
        stages[stage].append(task)
    
    # 메인 Epic 생성
    main_epic_id, main_epic_key = create_epic(
        "통합 기업용 웹 서비스 구축",
        "온프레미스 환경에서 시작하여 하이브리드로 확장하는 기업용 웹 서비스 구축 프로젝트",
        is_real_epic=has_epic_type
    )
    
    if not main_epic_key:
        print("메인 Epic 생성 실패, 프로세스 중단")
        return
    
    # 각 스테이지별로 Epic과 Task 생성
    stage_epics = {}
    
    # 진행 상황을 추적할 변수
    total_tasks = len(tasks)
    completed_tasks = 0
    
    for stage_name, stage_tasks in stages.items():
        # 스테이지별 Epic 생성
        stage_epic_id, stage_epic_key = create_epic(
            stage_name,
            f"{stage_name} 단계 작업",
            is_real_epic=has_epic_type
        )
        
        # Epic 키 저장
        stage_epics[stage_name] = stage_epic_key
        
        # 카테고리별 그룹화 (Sub-task 생성을 위해)
        categories = {}
        for task in stage_tasks:
            if 'category' in task:
                category = task['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(task)
        
        # 카테고리별 Task 생성 및 Sub-task 할당
        for category, category_tasks in categories.items():
            if len(category_tasks) > 1:  # 카테고리에 여러 태스크가 있으면 상위 Task 생성
                category_task_id, category_task_key = create_task(
                    f"{stage_name} - {category}",
                    f"{category} 관련 작업",
                    epic_key=stage_epic_key,
                    issue_type="Task",
                    priority="High",
                    category=category,
                    labels=["category-group"]
                )
                
                # 각 태스크를 Sub-task로 생성
                for task in category_tasks:
                    create_task(
                        summary=task['summary'],
                        description=task['description'],
                        epic_key=stage_epic_key,
                        parent_key=category_task_key,  # 부모 Task 키
                        issue_type="Sub-task",  # Sub-task로 지정
                        priority=task['priority'],
                        story_points=task.get('story_points'),
                        start_date=datetime.strptime(task['start_date'], "%Y-%m-%d"),
                        due_date=datetime.strptime(task['due_date'], "%Y-%m-%d"),
                        category=task.get('category'),
                        labels=task.get('labels', [])
                    )
                    
                    completed_tasks += 1
                    print(f"진행 상황: {completed_tasks}/{total_tasks} 태스크 처리됨 ({completed_tasks/total_tasks*100:.1f}%)")
            else:  # 카테고리에 하나만 있으면 일반 Task로 생성
                for task in category_tasks:
                    create_task(
                        summary=task['summary'],
                        description=task['description'],
                        epic_key=stage_epic_key,
                        issue_type="Task",
                        priority=task['priority'],
                        story_points=task.get('story_points'),
                        start_date=datetime.strptime(task['start_date'], "%Y-%m-%d"),
                        due_date=datetime.strptime(task['due_date'], "%Y-%m-%d"),
                        category=task.get('category'),
                        labels=task.get('labels', [])
                    )
                    
                    completed_tasks += 1
                    print(f"진행 상황: {completed_tasks}/{total_tasks} 태스크 처리됨 ({completed_tasks/total_tasks*100:.1f}%)")
    
    print("Jira에 로드맵 태스크 업로드 완료")

if __name__ == "__main__":
    validate_env_vars()
    create_roadmap_tasks()