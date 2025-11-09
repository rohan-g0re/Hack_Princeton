from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.job import DriverJobResponse, DriverStatusResponse
from app.services.driver_runner import driver_runner
from app.services.artifact_scanner import get_artifact_counts
import psutil

router = APIRouter(prefix="/run-driver", tags=["driver"])


def monitor_job(job_id: str):
    """Background task to monitor job completion"""
    import time
    from app.config import settings
    
    max_runtime = settings.max_job_runtime_seconds
    poll_interval = settings.poll_interval_seconds
    elapsed = 0
    
    while elapsed < max_runtime:
        time.sleep(poll_interval)
        elapsed += poll_interval
        
        state = driver_runner.get_status(job_id)
        if not state:
            break
        
        # Check if process still running
        if state.pid:
            try:
                process = psutil.Process(state.pid)
                if not process.is_running():
                    # Process finished
                    counts = get_artifact_counts()
                    if counts["knot_api_count"] > 0:
                        driver_runner.update_status(job_id, "success")
                    else:
                        driver_runner.update_status(job_id, "error", "No output files generated")
                    break
            except psutil.NoSuchProcess:
                # Process ended
                counts = get_artifact_counts()
                if counts["knot_api_count"] > 0:
                    driver_runner.update_status(job_id, "success")
                else:
                    driver_runner.update_status(job_id, "error", "Process ended without output")
                break
    
    # Timeout
    if elapsed >= max_runtime:
        driver_runner.update_status(job_id, "error", "Job timed out")


@router.post("", response_model=DriverJobResponse)
async def start_driver(background_tasks: BackgroundTasks):
    """
    Start background execution of current_code/main.py
    Returns job_id for tracking
    """
    try:
        job_id = driver_runner.start_job()
        background_tasks.add_task(monitor_job, job_id)
        return DriverJobResponse(job_id=job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start driver: {e}")


@router.get("/status", response_model=DriverStatusResponse)
async def get_driver_status(job_id: str):
    """
    Get current status of a driver job
    """
    state = driver_runner.get_status(job_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")
    
    counts = get_artifact_counts()
    
    message = None
    if state.status == "error":
        message = state.error_message
    elif state.status == "success":
        message = f"Completed successfully. Generated {counts['knot_api_count']} platform summaries."
    
    return DriverStatusResponse(
        job_id=job_id,
        status=state.status,
        cart_count=counts["cart_count"],
        knot_api_count=counts["knot_api_count"],
        message=message
    )

