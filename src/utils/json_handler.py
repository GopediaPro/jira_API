import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from .error_handler import error_handler, JiraError

class JsonHandler:
    def __init__(self, base_dir="data"):
        """Initialize JsonHandler with base directory for JSON files"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    @error_handler
    def save_json(self, data: Any, filename: str) -> Path:
        """Save data to a JSON file"""
        file_path = self.base_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    
    @error_handler
    def load_json(self, filename: str) -> Optional[Any]:
        """Load data from a JSON file"""
        file_path = self.base_dir / filename
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @error_handler
    def append_json(self, data: Any, filename: str) -> Path:
        """Append data to an existing JSON file or create new one"""
        existing_data = self.load_json(filename) or []
        if isinstance(existing_data, list):
            existing_data.append(data)
        else:
            existing_data = [existing_data, data]
        return self.save_json(existing_data, filename)

    @error_handler
    def process_jira_tasks(self, filename: str = "tasks.json") -> Dict:
        """Process tasks.json file and prepare data for Jira issue creation"""
        tasks_data = self.load_json(filename)
        if not tasks_data:
            raise JiraError(f"Could not load {filename} or file is empty")

        results = {
            "epics": [],
            "tasks": [],
            "subtasks": [],
            "errors": []
        }

        # Process and validate work items
        for item in tasks_data.get("work_items", []):
            try:
                self._validate_work_item(item)
                if item["issue_type"] == "Epic":
                    results["epics"].append(item)
                elif item["issue_type"] == "Task":
                    results["tasks"].append(item)
                    # Process subtasks if they exist
                    for subtask in item.get("subtasks", []):
                        try:
                            self._validate_subtask(subtask)
                            results["subtasks"].append({
                                "parent_summary": item["summary"],
                                **subtask
                            })
                        except Exception as e:
                            results["errors"].append({
                                "type": "subtask_validation",
                                "parent_summary": item["summary"],
                                "subtask_summary": subtask.get("summary", "Unknown"),
                                "error": str(e)
                            })
            except Exception as e:
                results["errors"].append({
                    "type": "item_validation",
                    "summary": item.get("summary", "Unknown"),
                    "error": str(e)
                })

        return results

    def _validate_work_item(self, item: Dict) -> None:
        """Validate required fields in a work item"""
        required_fields = [
            "project_key", "issue_type", "summary", "description",
            "priority", "labels", "components", "fix_versions"
        ]
        
        missing_fields = [field for field in required_fields if field not in item]
        if missing_fields:
            raise JiraError(f"Missing required fields in work item: {', '.join(missing_fields)}")

    def _validate_subtask(self, subtask: Dict) -> None:
        """Validate required fields in a subtask"""
        required_fields = ["summary", "description", "issue_type"]
        
        missing_fields = [field for field in required_fields if field not in subtask]
        if missing_fields:
            raise JiraError(f"Missing required fields in subtask: {', '.join(missing_fields)}")

    @error_handler
    def save_creation_results(self, results: Dict, filename: str = "created_issues.json") -> Path:
        """Save issue creation results to JSON file"""
        return self.save_json(results, filename)

    @error_handler
    def load_creation_results(self, filename: str = "created_issues.json") -> Optional[Dict]:
        """Load previously created issues results"""
        return self.load_json(filename)
