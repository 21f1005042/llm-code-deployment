"""
LLM Code Deployment Application

A FastAPI application that automatically generates, deploys, and updates web applications
using Hugging Face LLMs and GitHub Pages.
"""

__version__ = "1.0.0"
__author__ = "LLM Code Deployment Team"
__description__ = "Automated web application deployment using AI"

# Import main components for easier access
from .main import app
from .models import BuildRequest, RevisionRequest, EvaluationResponse
from .llm_client import LLMClient
from .github_client import GitHubClient
from .evaluation_client import EvaluationClient

__all__ = [
    'app',
    'BuildRequest', 
    'RevisionRequest',
    'EvaluationResponse',
    'LLMClient',
    'GitHubClient',
    'EvaluationClient'
]