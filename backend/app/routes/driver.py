from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.job import DriverJobResponse, DriverStatusResponse
from app.services.driver_runner import driver_runner
from app.services.agent_orchestrator import agent_orchestrator
from app.services.artifact_scanner import get_artifact_counts
import psutil
import logging

router = APIRouter(prefix="/run-driver", tags=["driver"])
logger = logging.getLogger(__name__)


def execute_agents_task(job_id: str):
    """Background task to execute agents directly"""
    logger.info(f"[DRIVER] Starting background task for job_id: {job_id}")
    try:
        # Update status to running
        driver_runner.update_status(job_id, "running")
        logger.info(f"[DRIVER] Job {job_id} status updated to 'running'")
        
        # Execute the full pipeline (agents + knot generation)
        platforms = ["instacart", "ubereats"]  # Could be made configurable
        logger.info(f"[DRIVER] Executing full pipeline for platforms: {platforms}")
        result = agent_orchestrator.execute_full_pipeline(platforms)
        
        if result.get("success"):
            knot_count = result.get("knot_results", {}).get("generated_count", 0)
            logger.info(f"[DRIVER] Pipeline succeeded. Generated {knot_count} knot files")
            if knot_count > 0:
                driver_runner.update_status(job_id, "success")
                logger.info(f"[DRIVER] Job {job_id} completed successfully")
            else:
                driver_runner.update_status(job_id, "error", "No output files generated")
                logger.error(f"[DRIVER] Job {job_id} failed: No output files generated")
        else:
            error_msg = result.get("error", "Pipeline execution failed")
            driver_runner.update_status(job_id, "error", error_msg)
            logger.error(f"[DRIVER] Job {job_id} failed: {error_msg}")
            
    except Exception as e:
        driver_runner.update_status(job_id, "error", str(e))
        logger.exception(f"[DRIVER] Job {job_id} failed with exception: {str(e)}")


@router.post("", response_model=DriverJobResponse)
async def start_driver(background_tasks: BackgroundTasks):
    """
    Start background execution of agent pipeline
    Returns job_id for tracking
    """
    logger.info("[DRIVER] Received request to start driver")
    try:
        job_id = driver_runner.create_job()  # Create job without starting subprocess
        logger.info(f"[DRIVER] Created job with ID: {job_id}")
        background_tasks.add_task(execute_agents_task, job_id)
        logger.info(f"[DRIVER] Added background task for job: {job_id}")
        return DriverJobResponse(job_id=job_id)
    except Exception as e:
        logger.exception(f"[DRIVER] Failed to start driver: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start driver: {e}")


@router.get("/status", response_model=DriverStatusResponse)
async def get_driver_status(job_id: str):
    """
    Get current status of a driver job
    """
    logger.debug(f"[DRIVER] Checking status for job_id: {job_id}")
    state = driver_runner.get_status(job_id)
    
    if not state:
        logger.warning(f"[DRIVER] Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    counts = get_artifact_counts()
    
    message = None
    if state.status == "error":
        message = state.error_message
        logger.error(f"[DRIVER] Job {job_id} in error state: {message}")
    elif state.status == "success":
        message = f"Completed successfully. Generated {counts['knot_api_count']} platform summaries."
        logger.info(f"[DRIVER] Job {job_id} completed successfully")
    
    return DriverStatusResponse(
        job_id=job_id,
        status=state.status,
        cart_count=counts["cart_count"],
        knot_api_count=counts["knot_api_count"],
        message=message
    )

