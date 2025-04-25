from typing import Dict, List, Set, Protocol
from .validate_handler import JiraValidateHandler
from .error_handler import error_handler, JiraError
from .connect_handler import JiraConnectHandler

class CreateHandlerProtocol(Protocol):
    """Protocol defining the required methods from CreateHandler"""
    project_key: str
    def create_component(self, data: Dict) -> Dict: ...
    def create_version(self, data: Dict) -> Dict: ...
    # def create_version_field(self) -> Dict: ...
    def create_components_field(self) -> Dict: ...

class JiraCombiHandler:
    def __init__(self, connect_handler: JiraConnectHandler, create_handler: CreateHandlerProtocol):
        self.connect = connect_handler
        self.validate_handler = JiraValidateHandler(connect_handler=self.connect)
        self.create_handler = create_handler

    def _validate_and_create_fields(self) -> None:
        """Validate required fields exist and create them if missing"""
        print("\nValidating required fields...")
        
        # # Check if fixVersions field exists
        # if not self.validate_handler.validate_field("fixVersions"):
        #     print("Creating missing fixVersions field...")
        #     try:
        #         self.create_handler.create_version_field()
        #         print("✓ Created fixVersions field")
        #     except Exception as e:
        #         print(f"✗ Failed to create fixVersions field: {str(e)}")
        
        # Check if components field exists
        if not self.validate_handler.validate_field("components"):
            print("Creating missing components field...")
            try:
                self.create_handler.create_components_field()
                print("✓ Created components field")
            except Exception as e:
                print(f"✗ Failed to create components field: {str(e)}")

    @error_handler
    def validate_and_prepare_project(self, data: Dict) -> None:
        """Validate and prepare project configuration before creating issues"""
        print("\nValidating project configuration...")
        project_key = self.create_handler.project_key
        
        # Validate and create required fields
        self._validate_and_create_fields()
        
        # Collect all components and versions from the data
        all_components: Set[str] = set()
        all_versions: Set[str] = set()
        
        # Check epics
        for epic in data.get("epics", []):
            all_components.update(epic.get("components", []))
            all_versions.update(epic.get("fixVersions", []))
            
            # Validate epic fields
            missing_fields = self.validate_handler.validate_task_fields({
                "fields": {
                    "summary": epic.get("summary"),
                    "description": epic.get("description"),
                    "issuetype": "Epic"
                }
            })
            if missing_fields:
                raise JiraError(
                    f"Missing required fields in epic: {', '.join(missing_fields)}",
                    "MISSING_FIELDS",
                    {"fields": missing_fields},
                    {"file": "epic_data"}
                )
        
        # Check tasks
        for task in data.get("tasks", []):
            all_components.update(task.get("components", []))
            all_versions.update(task.get("fixVersions", []))
            
            # Validate task fields
            missing_fields = self.validate_handler.validate_task_fields({
                "fields": {
                    "summary": task.get("summary"),
                    "description": task.get("description"),
                    "issuetype": "Task"
                }
            })
            if missing_fields:
                raise JiraError(
                    f"Missing required fields in task: {', '.join(missing_fields)}",
                    "MISSING_FIELDS",
                    {"fields": missing_fields},
                    {"file": "task_data"}
                )
            
            # Validate subtasks
            for subtask in task.get("subtasks", []):
                missing_fields = self.validate_handler.validate_subtask_fields({
                    "fields": {
                        "summary": subtask.get("summary"),
                        "description": subtask.get("description"),
                        "parent": task.get("summary")
                    }
                })
                if missing_fields:
                    raise JiraError(
                        f"Missing required fields in subtask: {', '.join(missing_fields)}",
                        "MISSING_FIELDS",
                        {"fields": missing_fields},
                        {"file": "subtask_data"}
                    )
        
        # Validate project exists
        if not self.validate_handler.validate_project(project_key):
            raise JiraError(
                f"Project {project_key} does not exist",
                "INVALID_PROJECT",
                {"project_key": project_key},
                {"file": "project_config"}
            )
        
        # Validate issue types
        required_types = ["Epic", "Task", "Sub-task"]
        for issue_type in required_types:
            if not self.validate_handler.validate_issue_type(project_key, issue_type):
                raise JiraError(
                    f"Required issue type '{issue_type}' not found in project",
                    "INVALID_ISSUE_TYPE",
                    {"issue_type": issue_type},
                    {"file": "project_config"}
                )
        
        # Check components
        if all_components:
            print("\nChecking components...")
            for component in all_components:
                if not self.validate_handler.validate_component(project_key, component):
                    print(f"Creating missing component: {component}")
                    self.create_handler.create_component({"name": component})
        
        # Check versions
        if all_versions:
            print("\nChecking versions...")
            for version in all_versions:
                if not self.validate_handler.validate_version(project_key, version):
                    print(f"Creating missing version: {version}")
                    self.create_handler.create_version({"name": version})
        
        print("Project configuration validated successfully")
