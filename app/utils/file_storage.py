# app/utils/file_storage.py

import os
from typing import Optional
from fastapi import UploadFile
import uuid
import shutil

class FileStorage:
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = base_upload_dir
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """Ensure base upload directory exists"""
        if not os.path.exists(self.base_upload_dir):
            os.makedirs(self.base_upload_dir, exist_ok=True)
    
    def get_opinion_request_dir(self, request_id: int) -> str:
        """Get directory for opinion request files"""
        request_dir = os.path.join(self.base_upload_dir, 'opinion_requests', str(request_id))
        os.makedirs(request_dir, exist_ok=True)
        return request_dir
    
    async def save_file(
        self,
        file: UploadFile,
        request_id: int,
        max_size_mb: int = 10
    ) -> tuple[str, str, int]:
        """
        Save uploaded file and return path, filename and size
        """
        if not file.filename:
            return None, None, 0
            
        # Get save directory
        save_dir = self.get_opinion_request_dir(request_id)
        
        # Generate safe filename
        safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(save_dir, safe_filename)
        
        # Read and validate file
        contents = await file.read()
        file_size = len(contents)
        
        # Check file size
        if file_size > max_size_mb * 1024 * 1024:
            raise ValueError(f"File size exceeds {max_size_mb}MB limit")
            
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
            
        return file_path, safe_filename, file_size
    
    def remove_file(self, file_path: str) -> bool:
        """Remove file if it exists"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            return False
        return False

# Initialize file storage
file_storage = FileStorage()