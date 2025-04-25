import os
import base64
import yaml
from dotenv import load_dotenv

class JiraAuthHandler:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv("EMAIL")
        self.api_token = os.getenv("API_TOKEN")
        self.jira_instance = os.getenv("JIRA_INSTANCE")
        
    def get_auth_header(self):
        """Generate authentication header for Jira API requests"""
        auth_str = f"{self.email}:{self.api_token}"
        auth_bytes = auth_str.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }
    
    def get_jira_instance(self):
        """Get Jira instance URL"""
        return self.jira_instance
    
    def validate_credentials(self):
        """Validate if all required credentials are present"""
        required_env_vars = ["EMAIL", "API_TOKEN", "JIRA_INSTANCE"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        return True
        
    def load_credentials_from_yaml(self, yaml_file):
        """Load credentials from YAML file if not set in environment"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            # Only set values that aren't already set
            if not self.email and 'email' in config:
                self.email = config['email']
                
            if not self.api_token and 'api_token' in config:
                self.api_token = config['api_token']
                
            if not self.jira_instance and 'jira_instance' in config:
                self.jira_instance = config['jira_instance']
                
            return True
        except Exception as e:
            print(f"Error loading credentials from YAML: {str(e)}")
            return False
