import os
import base64
import uuid
import tempfile
from typing import List, Dict, Any
from .models import Attachment
import logging

logger = logging.getLogger(__name__)

# In production, use a proper database
SECRET_STORE = {}

def verify_secret(email: str, secret: str) -> bool:
    """Verify student secret (simplified - use proper auth in production)"""
    # In production, this should check against a database
    expected_secret = SECRET_STORE.get(email)
    if expected_secret is None:
        # Store the first secret received
        SECRET_STORE[email] = secret
        return True
    return expected_secret == secret

def save_attachments(attachments: List[Attachment]) -> List[str]:
    """Save attachments to temporary files and return file paths"""
    saved_paths = []
    
    for attachment in attachments:
        try:
            # Parse data URL
            if attachment.url.startswith('data:'):
                header, data = attachment.url.split(',', 1)
                mime_type = header.split(';')[0].split(':')[1]
                
                # Decode base64 data
                file_data = base64.b64decode(data)
                
                # Save to temporary file
                file_ext = mime_type.split('/')[-1]
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=f'.{file_ext}',
                    prefix=attachment.name
                )
                temp_file.write(file_data)
                temp_file.close()
                
                saved_paths.append(temp_file.name)
                logger.info(f"Saved attachment: {attachment.name}")
                
        except Exception as e:
            logger.error(f"Error saving attachment {attachment.name}: {str(e)}")
    
    return saved_paths

def generate_task_id(brief: str) -> str:
    """Generate a unique task ID based on brief"""
    brief_hash = str(hash(brief))[:8]
    return f"task-{brief_hash}-{uuid.uuid4().hex[:4]}"