import json
import os
from pathlib import Path

class JsonHandler:
    def __init__(self, base_dir="data"):
        """Initialize JsonHandler with base directory for JSON files"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_json(self, data, filename):
        """Save data to a JSON file"""
        file_path = self.base_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return file_path
    
    def load_json(self, filename):
        """Load data from a JSON file"""
        file_path = self.base_dir / filename
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def append_json(self, data, filename):
        """Append data to an existing JSON file or create new one"""
        existing_data = self.load_json(filename) or []
        if isinstance(existing_data, list):
            existing_data.append(data)
        else:
            existing_data = [existing_data, data]
        return self.save_json(existing_data, filename)
