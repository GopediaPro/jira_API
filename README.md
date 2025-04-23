# JIRA API Integration Project
JIRA API와 연동하여 JIRA 이슈를 관리하는 프로젝트입니다.
This project integrates with JIRA API to manage JIRA issues.

## Custom Field 확인 방법 / How to Check Custom Fields
```bash
curl -s -u 'your-email@example.com:your-api-token' \
  -X GET 'https://exam.atlassian.net/rest/api/3/field' \
  -H 'Accept: application/json' | jq
```

## 개발 환경 설정 / Development Environment Setup

### Python 가상환경 설정 / Python Virtual Environment Setup

1. Python 가상환경 생성 / Create Python virtual environment
```bash
python3 -m venv venv
```

2. 가상환경 활성화 / Activate virtual environment

MacOS/Linux:
```bash
source venv/bin/activate
```

3. 필요한 패키지 설치 / Install required packages
```bash
pip install -r requirements.txt
```

## Run the script
```bash
python src/main.py 
```

## 프로젝트 구조 / Project Structure
```
jira_API/
├── data/                          
│   ├── jira_fields.json
│   ├── issue_types.json
│   ├── work_items.json
│   └── all_jira_data.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── utils/
│       ├── __init__.py
│       ├── auth_handler.py
│       ├── connect_handler.py
│       ├── get_handler.py
│       └── json_handler.py
├── .env
└── requirements.txt
```

## 환경 변수 설정 / Environment Variables
프로젝트 실행을 위해 다음 환경 변수를 설정해야 합니다:
The following environment variables need to be set to run the project:

- `JIRA_EMAIL`: Your JIRA account email
- `JIRA_API_TOKEN`: Your JIRA API token
- `JIRA_DOMAIN`: Your JIRA domain (e.g., your-company.atlassian.net)