# JIRA API Integration Project

JIRA API와 연동하여 JIRA 이슈를 관리하는 프로젝트입니다.
This project integrates with JIRA API to manage JIRA issues.

## 주요 기능 / Key Features

1. **연결 테스트 / Connection Test**
   - JIRA 서버 연결 상태 확인
   - 프로젝트 정보 검증
   - 인증 상태 확인

2. **데이터 조회 / Data Retrieval**
   - Fields 정보 조회
   - Issue Types 조회
   - Components 조회
   - Versions 조회
   - Work Items 조회

3. **이슈 생성 / Issue Creation**
   - Epic 생성
   - Task 생성
   - Subtask 생성
   - YAML 파일을 통한 일괄 생성

## 시작하기 / Getting Started

### 사전 요구사항 / Prerequisites

- Python 3.8 이상 / Python 3.8 or higher
- JIRA 계정 및 API 토큰 / JIRA account and API token
- 프로젝트 접근 권한 / Project access permissions

### 환경 변수 설정 / Environment Variables

프로젝트 실행을 위해 다음 환경 변수를 `.env` 파일에 설정하세요:
Set the following environment variables in `.env` file:

```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_USER=your-email@example.com
JIRA_TOKEN=your-api-token
PROJECT_KEY=YOUR_PROJECT_KEY
```

또는 다음 변수명도 사용 가능합니다:
Or you can use these alternative variable names:

```bash
JIRA_INSTANCE=https://your-domain.atlassian.net
EMAIL=your-email@example.com
API_TOKEN=your-api-token
```

### 설치 방법 / Installation

1. 저장소 클론 / Clone the repository
```bash
git clone https://github.com/your-username/jira_API.git
cd jira_API
```

2. Python 가상환경 생성 / Create Python virtual environment
```bash
python3 -m venv venv
```

3. 가상환경 활성화 / Activate virtual environment

MacOS/Linux:
```bash
source venv/bin/activate
```

Windows:
```bash
.\venv\Scripts\activate
```

4. 필요한 패키지 설치 / Install required packages
```bash
pip install -r requirements.txt
```

## 사용 방법 / Usage

1. 프로그램 실행 / Run the program
```bash
python src/main.py
```

2. 메뉴 선택 / Select Menu Option
```
=== Jira Manager Menu ===
1. Test Connection
2. Fetch Jira Data
3. Create Issues from YAML
4. Full Sync (Fetch & Create)
5. Exit
```

### YAML 파일 구조 / YAML File Structure

이슈 생성을 위한 YAML 파일 구조 예시:
Example YAML file structure for issue creation:

```yaml
project: YOUR_PROJECT_KEY
epics:
  - summary: Epic 1
    description: Epic 1 description
    tasks:
      - summary: Task 1
        description: Task 1 description
        subtasks:
          - summary: Subtask 1
            description: Subtask 1 description

tasks:
  - summary: Standalone Task
    description: Task without epic
    components: [Backend]
    labels: [important]
```

### Custom Field 확인 / Check Custom Fields

JIRA Custom Field IDs 확인 방법:
How to check JIRA Custom Field IDs:

```bash
curl -s -u 'your-email@example.com:your-api-token' \
  -X GET 'https://your-domain.atlassian.net/rest/api/3/field' \
  -H 'Accept: application/json' | jq
```

## 프로젝트 구조 / Project Structure
```
jira_API/
├── data/                          # 데이터 저장소 / Data storage
│   ├── jira_fields.json          # JIRA 필드 정보 / JIRA fields info
│   ├── issue_types.json         # 이슈 타입 정보 / Issue types info
│   ├── field_map.json          # 필드 매핑 정보 / Field mapping info
│   ├── work_items.json        # 작업 항목 정보 / Work items info
│   └── all_jira_data.json    # 전체 데이터 / All JIRA data
├── src/
│   ├── __init__.py
│   ├── main.py               # 메인 실행 파일 / Main execution file
│   └── utils/               # 유틸리티 모듈 / Utility modules
│       ├── __init__.py
│       ├── auth_handler.py      # 인증 처리 / Authentication handler
│       ├── connect_handler.py   # 연결 처리 / Connection handler
│       ├── create_handler.py    # 이슈 생성 처리 / Issue creation handler
│       ├── get_handler.py       # 데이터 조회 처리 / Data retrieval handler
│       ├── error_handler.py     # 에러 처리 / Error handler
│       └── json_handler.py      # JSON 파일 처리 / JSON file handler
├── .env                     # 환경 변수 파일 / Environment variables file
├── requirements.txt         # 의존성 패키지 목록 / Package dependencies
└── README.md               # 프로젝트 문서 / Project documentation
```

## 에러 처리 / Error Handling

주요 에러 코드 및 해결 방법:
Common error codes and solutions:

- `ENV_ERROR`: 환경 변수 설정 확인 / Check environment variables
- `CONNECTION_ERROR`: JIRA 서버 연결 확인 / Check JIRA server connection
- `API_ERROR`: API 요청 오류 확인 / Check API request errors
- `INVALID_YAML_STRUCTURE`: YAML 파일 구조 확인 / Check YAML file structure

## 라이선스 / License

This project is licensed under the MIT License - see the LICENSE file for details.