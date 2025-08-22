"""
REST API for AutoTasker AI
Provides HTTP endpoints for external integrations and webhooks
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import uvicorn
import logging
from datetime import datetime
import json
import os

from backend.langgraph_runner import AutoTaskerRunner
from backend.scheduler import TaskScheduler
from backend.utils import load_config, create_task_id

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AutoTasker AI API",
    description="REST API for AutoTasker AI - Smart Multi-Agent Task Automator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global config and instances
config = None
runner = None
scheduler = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token authentication - enhance for production"""
    expected_token = os.environ.get("API_TOKEN", "autotasker-api-key")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return {"user": "api_user"}

# Pydantic models
class TaskRequest(BaseModel):
    prompt: str = Field(..., description="Natural language task description")
    priority: str = Field(default="medium", description="Task priority")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class ScheduleTaskRequest(BaseModel):
    prompt: str = Field(..., description="Natural language task description")
    schedule_type: str = Field(..., description="Schedule type: daily, weekly, monthly, interval, cron")
    schedule_value: str = Field(..., description="Schedule value")
    task_name: Optional[str] = Field(default=None, description="Task name")
    use_cloud: bool = Field(default=False, description="Use cloud scheduling (EventBridge)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class WebhookRequest(BaseModel):
    event_type: str = Field(..., description="Type of webhook event")
    payload: Dict[str, Any] = Field(..., description="Webhook payload")
    source: str = Field(..., description="Source of the webhook")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

class JobResponse(BaseModel):
    job_id: str
    name: str
    next_run: Optional[str]
    trigger: str
    status: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global config, runner, scheduler
    
    try:
        config = load_config("config/config.yaml")
        runner = AutoTaskerRunner(config)
        scheduler = TaskScheduler(config)
        scheduler.start()
        logger.info("AutoTasker AI API started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scheduler
    if scheduler:
        scheduler.stop()
    logger.info("AutoTasker AI API shutdown complete")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "runner": runner is not None,
            "scheduler": scheduler is not None and scheduler.is_running
        }
    }

# Task execution endpoints
@app.post("/api/v1/tasks/execute", response_model=TaskResponse, tags=["Tasks"])
async def execute_task(
    task_request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Execute a task immediately"""
    try:
        task_id = create_task_id()
        
        # Execute task in background
        background_tasks.add_task(
            _execute_task_background,
            task_id,
            task_request.prompt,
            task_request.metadata or {}
        )
        
        return TaskResponse(
            task_id=task_id,
            status="accepted",
            message="Task accepted for execution",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/schedule", response_model=JobResponse, tags=["Tasks"])
async def schedule_task(
    schedule_request: ScheduleTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Schedule a recurring task"""
    try:
        # Create appropriate scheduler
        task_scheduler = scheduler
        if schedule_request.use_cloud:
            task_scheduler = TaskScheduler(config, use_cloud=True)
        
        job_id = task_scheduler.schedule_task(
            prompt=schedule_request.prompt,
            schedule_type=schedule_request.schedule_type,
            schedule_value=schedule_request.schedule_value,
            task_name=schedule_request.task_name,
            metadata=schedule_request.metadata
        )
        
        return JobResponse(
            job_id=job_id,
            name=schedule_request.task_name or f"Task-{job_id}",
            next_run="Scheduled",
            trigger=f"{schedule_request.schedule_type}: {schedule_request.schedule_value}",
            status="scheduled"
        )
        
    except Exception as e:
        logger.error(f"Failed to schedule task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks/scheduled", response_model=List[JobResponse], tags=["Tasks"])
async def list_scheduled_tasks(current_user: dict = Depends(get_current_user)):
    """List all scheduled tasks"""
    try:
        jobs = scheduler.list_jobs()
        return [
            JobResponse(
                job_id=job["id"],
                name=job["name"],
                next_run=job["next_run"],
                trigger=job["trigger"],
                status="active"
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Failed to list scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/tasks/scheduled/{job_id}", tags=["Tasks"])
async def delete_scheduled_task(job_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scheduled task"""
    try:
        success = scheduler.remove_job(job_id)
        if success:
            return {"message": f"Task {job_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except Exception as e:
        logger.error(f"Failed to delete task {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/scheduled/{job_id}/pause", tags=["Tasks"])
async def pause_scheduled_task(job_id: str, current_user: dict = Depends(get_current_user)):
    """Pause a scheduled task"""
    try:
        success = scheduler.pause_job(job_id)
        if success:
            return {"message": f"Task {job_id} paused successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except Exception as e:
        logger.error(f"Failed to pause task {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/scheduled/{job_id}/resume", tags=["Tasks"])
async def resume_scheduled_task(job_id: str, current_user: dict = Depends(get_current_user)):
    """Resume a paused task"""
    try:
        success = scheduler.resume_job(job_id)
        if success:
            return {"message": f"Task {job_id} resumed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Task not found")
            
    except Exception as e:
        logger.error(f"Failed to resume task {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoints
@app.post("/api/v1/webhooks/github", tags=["Webhooks"])
async def github_webhook(
    webhook_request: WebhookRequest,
    background_tasks: BackgroundTasks
):
    """Handle GitHub webhooks"""
    try:
        # Process GitHub webhook
        if webhook_request.event_type == "push":
            prompt = f"Summarize recent GitHub commits and send via email"
            task_id = create_task_id()
            
            background_tasks.add_task(
                _execute_task_background,
                task_id,
                prompt,
                {"source": "github_webhook", "event": webhook_request.payload}
            )
            
            return {"message": "GitHub webhook processed", "task_id": task_id}
        
        return {"message": "Webhook received but not processed"}
        
    except Exception as e:
        logger.error(f"Failed to process GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/webhooks/slack", tags=["Webhooks"])
async def slack_webhook(
    webhook_request: WebhookRequest,
    background_tasks: BackgroundTasks
):
    """Handle Slack webhooks"""
    try:
        # Process Slack webhook
        if webhook_request.event_type == "app_mention":
            # Extract text from Slack message
            text = webhook_request.payload.get("event", {}).get("text", "")
            
            if text:
                task_id = create_task_id()
                background_tasks.add_task(
                    _execute_task_background,
                    task_id,
                    text,
                    {"source": "slack_webhook", "event": webhook_request.payload}
                )
                
                return {"message": "Slack command processed", "task_id": task_id}
        
        return {"message": "Webhook received but not processed"}
        
    except Exception as e:
        logger.error(f"Failed to process Slack webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/api/v1/analytics/stats", tags=["Analytics"])
async def get_analytics_stats(current_user: dict = Depends(get_current_user)):
    """Get system analytics and statistics"""
    try:
        # Read execution logs
        log_file = "data/logs/scheduled_tasks.log"
        stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "scheduled_tasks": len(scheduler.list_jobs()),
            "last_execution": None
        }
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        stats["total_executions"] += 1
                        
                        if log_entry.get("success"):
                            stats["successful_executions"] += 1
                        else:
                            stats["failed_executions"] += 1
                        
                        if not stats["last_execution"] or log_entry.get("executed_at") > stats["last_execution"]:
                            stats["last_execution"] = log_entry.get("executed_at")
                            
                    except json.JSONDecodeError:
                        continue
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task execution
async def _execute_task_background(task_id: str, prompt: str, metadata: Dict[str, Any]):
    """Execute task in background"""
    try:
        logger.info(f"Executing background task {task_id}: {prompt}")
        
        # Add task metadata
        metadata.update({
            "task_id": task_id,
            "execution_time": datetime.now().isoformat(),
            "api_request": True
        })
        
        # Execute the workflow
        result = runner.run_workflow(prompt)
        
        # Log execution
        execution_log = {
            "task_id": task_id,
            "prompt": prompt,
            "executed_at": datetime.now().isoformat(),
            "success": result.get("success", True),
            "error": result.get("error"),
            "metadata": metadata
        }
        
        # Save to log file
        log_file = "data/logs/api_executions.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(execution_log) + '\n')
        
        logger.info(f"Background task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Background task {task_id} failed: {e}")

# Configuration endpoints
@app.get("/api/v1/config", tags=["Configuration"])
async def get_configuration(current_user: dict = Depends(get_current_user)):
    """Get current configuration (sanitized)"""
    try:
        # Return sanitized config (remove sensitive data)
        sanitized_config = {
            "app": config.get("app", {}),
            "agents": {k: {**v, "api_key": "***" if "api_key" in v else v} for k, v in config.get("agents", {}).items()},
            "aws": {k: v for k, v in config.get("aws", {}).items() if not k.endswith("_key")},
            "logging": config.get("logging", {})
        }
        
        return sanitized_config
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
