from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Optional, List
from datetime import datetime
import uuid
import asyncio
from enum import Enum

from agent.agent import graph

# Initialize FastAPI app
app = FastAPI(
    title="Web Scraping Agent API",
    description="API for scraping and formatting web content using LangGraph agent",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job status enum
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# In-memory job storage (use Redis/DB in production)
jobs_store: Dict[str, Dict] = {}

# Request/Response Models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com"
            }
        }

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    created_at: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    url: str
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None

class ScrapedDataItem(BaseModel):
    url: str
    response: Dict[str, str]

class ScrapeResultResponse(BaseModel):
    source_url: str
    data: List[ScrapedDataItem]

# Background task to run the scraping agent
async def run_scraping_job(job_id: str, url: str):
    """
    Run the scraping agent in the background
    """
    try:
        jobs_store[job_id]["status"] = JobStatus.RUNNING
        
        # Run the graph synchronously (LangGraph doesn't support async yet)
        # We use asyncio.to_thread to run it in a separate thread
        result = await asyncio.to_thread(
            graph.invoke,
            {"url": url}
        )
        
        # Update job status
        jobs_store[job_id]["status"] = JobStatus.COMPLETED
        jobs_store[job_id]["completed_at"] = datetime.utcnow().isoformat()
        jobs_store[job_id]["result"] = result.get("result", {})
        
    except Exception as e:
        jobs_store[job_id]["status"] = JobStatus.FAILED
        jobs_store[job_id]["completed_at"] = datetime.utcnow().isoformat()
        jobs_store[job_id]["error"] = str(e)
        print(f"Error in job {job_id}: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "Web Scraping Agent API",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/scrape", response_model=JobResponse, status_code=202)
async def create_scrape_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new scraping job (async)
    
    - **url**: The URL to scrape
    
    Returns a job_id that can be used to check the status
    """
    job_id = str(uuid.uuid4())
    url_str = str(request.url)
    
    # Initialize job in store
    jobs_store[job_id] = {
        "job_id": job_id,
        "url": url_str,
        "status": JobStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(run_scraping_job, job_id, url_str)
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Scraping job created successfully",
        created_at=jobs_store[job_id]["created_at"]
    )

@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a scraping job
    
    - **job_id**: The ID of the job to check
    """
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_store[job_id]
    return JobStatusResponse(**job)

@app.get("/jobs/{job_id}/result", response_model=ScrapeResultResponse)
async def get_job_result(job_id: str):
    """
    Get the result of a completed scraping job
    
    - **job_id**: The ID of the job to get results for
    """
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_store[job_id]
    
    if job["status"] == JobStatus.PENDING or job["status"] == JobStatus.RUNNING:
        raise HTTPException(
            status_code=425,
            detail=f"Job is still {job['status']}. Please wait for completion."
        )
    
    if job["status"] == JobStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'Unknown error')}"
        )
    
    if not job.get("result"):
        raise HTTPException(status_code=404, detail="No result found for this job")
    
    return ScrapeResultResponse(**job["result"])

@app.post("/scrape/sync", response_model=ScrapeResultResponse)
async def scrape_sync(request: ScrapeRequest):
    """
    Scrape a URL synchronously (waits for completion)
    
    - **url**: The URL to scrape
    
    Note: This endpoint may take a while to respond depending on the URL
    """
    url_str = str(request.url)
    
    try:
        # Run the graph synchronously
        result = await asyncio.to_thread(
            graph.invoke,
            {"url": url_str}
        )
        
        if not result.get("result"):
            raise HTTPException(
                status_code=500,
                detail="Scraping completed but no data was returned"
            )
        
        return ScrapeResultResponse(**result["result"])
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )

@app.get("/jobs")
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    List all jobs (optionally filtered by status)
    
    - **status**: Filter by job status (pending, running, completed, failed)
    - **limit**: Maximum number of jobs to return (1-100)
    """
    jobs = list(jobs_store.values())
    
    # Filter by status if provided
    if status:
        jobs = [job for job in jobs if job["status"] == status]
    
    # Sort by created_at (most recent first)
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Limit results
    jobs = jobs[:limit]
    
    return {
        "total": len(jobs),
        "jobs": jobs
    }

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from the store
    
    - **job_id**: The ID of the job to delete
    """
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs_store[job_id]
    
    return {"message": "Job deleted successfully", "job_id": job_id}

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {
        "error": "Internal server error",
        "detail": str(exc)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)