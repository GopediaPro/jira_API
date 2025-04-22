import os
from dotenv import load_dotenv
from jira import JIRA

# Load environment variables
load_dotenv()

def connect_jira():
    """
    JIRA 연결 설정
    Setup JIRA connection
    """
    email = os.getenv('EMAIL')
    api_token = os.getenv('API_TOKEN')
    domain = os.getenv('JIRA_INSTANCE')
    
    if not all([email, api_token, domain]):
        raise ValueError("환경 변수가 올바르게 설정되지 않았습니다. / Environment variables are not properly set.")
    
    return JIRA(
        server=f"https://{domain}",
        basic_auth=(email, api_token)
    )

def main():
    try:
        jira = connect_jira()
        print("JIRA 연결 성공! / JIRA connection successful!")
    except Exception as e:
        print(f"JIRA 연결 실패 / JIRA connection failed: {str(e)}")

if __name__ == "__main__":
    main() 