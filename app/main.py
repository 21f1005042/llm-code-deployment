from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import os
from typing import List, Optional, Dict, Any
import uuid
import logging

from .models import BuildRequest, EvaluationResponse, RevisionRequest
from .llm_client import LLMClient
from .github_client import GitHubClient
from .evaluation_client import EvaluationClient
from .utils import verify_secret, save_attachments

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Code Deployment", version="1.0.0")

# Initialize clients
llm_client = LLMClient()
github_client = GitHubClient()
evaluation_client = EvaluationClient()

# In-memory storage (replace with Redis in production)
task_store = {}

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/")
async def root():
    return {"message": "LLM Code Deployment API"}

@app.get("/health")
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")

@app.post("/api/deploy")
async def deploy_app(request: BuildRequest, background_tasks: BackgroundTasks):
    """Handle initial app deployment request"""
    try:
        # Verify secret
        if not verify_secret(request.email, request.secret):
            raise HTTPException(status_code=401, detail="Invalid secret")
        
        # Store task in memory
        task_id = f"{request.task}-{request.round}"
        task_store[task_id] = {
            "request": request.dict(),
            "status": "processing"
        }
        
        # Process in background
        background_tasks.add_task(process_build_request, request)
        
        return JSONResponse(
            status_code=200,
            content={"status": "accepted", "task_id": task_id}
        )
        
    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/revise")
async def revise_app(request: RevisionRequest, background_tasks: BackgroundTasks):
    """Handle app revision request"""
    try:
        # Verify secret
        if not verify_secret(request.email, request.secret):
            raise HTTPException(status_code=401, detail="Invalid secret")
        
        # Check if round 1 exists
        round1_task_id = f"{request.task}-1"
        if round1_task_id not in task_store:
            raise HTTPException(status_code=404, detail="Original task not found")
        
        # Store revision task
        task_id = f"{request.task}-{request.round}"
        task_store[task_id] = {
            "request": request.dict(),
            "status": "processing"
        }
        
        # Process in background
        background_tasks.add_task(process_revision_request, request)
        
        return JSONResponse(
            status_code=200,
            content={"status": "accepted", "task_id": task_id}
        )
        
    except Exception as e:
        logger.error(f"Revision error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_build_request(request: BuildRequest):
    """Process build request asynchronously"""
    try:
        # Save attachments
        attachment_paths = save_attachments(request.attachments)
        
        # Generate code using LLM
        logger.info(f"Generating code for task: {request.task}")
        generated_code = await llm_client.generate_app_code(
            brief=request.brief,
            checks=request.checks,
            attachments=attachment_paths
        )
        
        # Create GitHub repository
        repo_name = f"{request.task}-{uuid.uuid4().hex[:8]}"
        repo_url, pages_url = await github_client.create_repository(
            name=repo_name,
            code=generated_code,
            description=f"Generated app for: {request.brief[:100]}..."
        )
        
        # Get commit SHA
        commit_sha = await github_client.get_latest_commit(repo_name)
        
        # Notify evaluation service
        eval_response = EvaluationResponse(
            email=request.email,
            task=request.task,
            round=request.round,
            nonce=request.nonce,
            repo_url=repo_url,
            commit_sha=commit_sha,
            pages_url=pages_url
        )
        
        success = await evaluation_client.submit_evaluation(
            eval_response, request.evaluation_url
        )
        
        if success:
            task_store[f"{request.task}-{request.round}"]["status"] = "completed"
            logger.info(f"Successfully processed task: {request.task}")
        else:
            task_store[f"{request.task}-{request.round}"]["status"] = "evaluation_failed"
            logger.error(f"Evaluation submission failed for task: {request.task}")
            
    except Exception as e:
        task_store[f"{request.task}-{request.round}"]["status"] = "failed"
        logger.error(f"Process build error: {str(e)}")

async def process_revision_request(request: RevisionRequest):
    """Process revision request asynchronously"""
    try:
        # Get original repo info
        round1_task_id = f"{request.task}-1"
        original_request = task_store[round1_task_id]["request"]
        repo_name = original_request.get("repo_name")
        
        if not repo_name:
            raise Exception("Original repository not found")
        
        # Generate updated code using LLM
        logger.info(f"Generating revision code for task: {request.task}")
        updated_code = await llm_client.generate_app_code(
            brief=request.brief,
            checks=request.checks,
            attachments=save_attachments(request.attachments),
            existing_repo=repo_name
        )
        
        # Update GitHub repository
        repo_url, pages_url = await github_client.update_repository(
            name=repo_name,
            code=updated_code
        )
        
        # Get commit SHA
        commit_sha = await github_client.get_latest_commit(repo_name)
        
        # Notify evaluation service
        eval_response = EvaluationResponse(
            email=request.email,
            task=request.task,
            round=request.round,
            nonce=request.nonce,
            repo_url=repo_url,
            commit_sha=commit_sha,
            pages_url=pages_url
        )
        
        success = await evaluation_client.submit_evaluation(
            eval_response, request.evaluation_url
        )
        
        if success:
            task_store[f"{request.task}-{request.round}"]["status"] = "completed"
            logger.info(f"Successfully processed revision: {request.task}")
        else:
            task_store[f"{request.task}-{request.round}"]["status"] = "evaluation_failed"
            
    except Exception as e:
        task_store[f"{request.task}-{request.round}"]["status"] = "failed"
        logger.error(f"Process revision error: {str(e)}")

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a task"""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task_store[task_id]["status"],
        "request": task_store[task_id].get("request", {})
    }