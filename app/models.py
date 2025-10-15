from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Attachment(BaseModel):
    name: str
    url: str

class BuildRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int = Field(ge=1, le=2)
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: str
    attachments: List[Attachment] = []

class RevisionRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int = Field(ge=2, le=2)
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: str
    attachments: List[Attachment] = []

class EvaluationResponse(BaseModel):
    email: str
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str