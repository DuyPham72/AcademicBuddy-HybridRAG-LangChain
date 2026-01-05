import requests
import os
import json
from typing import Generator, List, Dict, Any

class APIClient:
    def __init__(self):
        # Allow overriding URL via env var, default to docker service name
        self.base_url = os.getenv("BACKEND_URL", "http://backend:8000")
        self.headers = {"accept": "application/json"}

    def get_files(self) -> List[str]:
        """Fetch list of available files from backend."""
        try:
            response = requests.get(
                f"{self.base_url}/documents/", 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("files", [])
        except requests.RequestException as e:
            print(f"Error fetching files: {e}")
            return []

    def upload_files(self, files: List[Any]) -> bool:
        """Uploads a list of Streamlit file objects."""
        if not files:
            return False
        
        # Prepare files for multipart/form-data
        files_payload = [
            ('files', (f.name, f.getvalue(), f.type)) for f in files
        ]
        
        try:
            response = requests.post(f"{self.base_url}/documents/upload", files=files_payload)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error uploading files: {e}")
            return False

    def delete_file(self, filename: str) -> bool:
        """Deletes a file by name."""
        try:
            response = requests.delete(f"{self.base_url}/documents/{filename}")
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error deleting file: {e}")
            return False

    def chat_stream(self, message: str, history: List[Dict[str, str]], selected_files=None) -> Generator[Dict, None, None]:
        """
        Yields structured data chunks (JSON) from the backend.
        """
        url = f"{self.base_url}/chat/"

        payload = {
            "message": message, 
            "history": history,
            "selected_files": selected_files if selected_files else [] 
        }
        
        try:
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            yield data
                        except json.JSONDecodeError:
                            continue
        except requests.RequestException as e:
            yield {"type": "error", "data": f"Connection error: {e}"}