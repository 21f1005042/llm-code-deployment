import os
import base64
import logging
from github import Github, GithubException
import tempfile
import shutil
import subprocess
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        self.github = Github(self.token)
        self.user = self.github.get_user()
    
    async def create_repository(self, name: str, code: dict, description: str = "") -> Tuple[str, str]:
        """Create a new repository with generated code"""
        try:
            # Create repository
            repo = self.user.create_repo(
                name=name,
                description=description,
                auto_init=False,
                private=False
            )
            
            # Create files
            for filename, content in code.items():
                repo.create_file(
                    filename,
                    f"Add {filename}",
                    content,
                    branch="main"
                )
            
            # Enable GitHub Pages
            repo.edit(has_pages=True)
            repo.create_pages_site(branch="main", path="/")
            
            repo_url = repo.html_url
            pages_url = f"https://{self.user.login}.github.io/{name}"
            
            logger.info(f"Created repository: {repo_url}")
            logger.info(f"Pages URL: {pages_url}")
            
            return repo_url, pages_url
            
        except GithubException as e:
            logger.error(f"GitHub error: {str(e)}")
            raise
    
    async def update_repository(self, name: str, code: dict) -> Tuple[str, str]:
        """Update existing repository with new code"""
        try:
            repo = self.github.get_repo(f"{self.user.login}/{name}")
            
            # Update files
            for filename, content in code.items():
                try:
                    # Try to get existing file to update
                    file_contents = repo.get_contents(filename, ref="main")
                    repo.update_file(
                        filename,
                        f"Update {filename}",
                        content,
                        file_contents.sha,
                        branch="main"
                    )
                except:
                    # File doesn't exist, create it
                    repo.create_file(
                        filename,
                        f"Add {filename}",
                        content,
                        branch="main"
                    )
            
            repo_url = repo.html_url
            pages_url = f"https://{self.user.login}.github.io/{name}"
            
            logger.info(f"Updated repository: {repo_url}")
            
            return repo_url, pages_url
            
        except GithubException as e:
            logger.error(f"GitHub update error: {str(e)}")
            raise
    
    async def get_latest_commit(self, repo_name: str) -> str:
        """Get the latest commit SHA for a repository"""
        try:
            repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
            branch = repo.get_branch("main")
            return branch.commit.sha
        except GithubException as e:
            logger.error(f"Error getting commit SHA: {str(e)}")
            return "unknown"