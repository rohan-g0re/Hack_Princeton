from fastapi import APIRouter, HTTPException
from app.models.comparison import ComparisonResponse
from app.services.comparison_parser import parse_knot_api_jsons

router = APIRouter(prefix="/comparison", tags=["comparison"])


@router.get("/{job_id}", response_model=ComparisonResponse)
async def get_comparison(job_id: str):
    """
    Get platform comparison results after driver completes
    """
    platforms = parse_knot_api_jsons()
    
    if not platforms:
        raise HTTPException(
            status_code=404,
            detail="No comparison data available yet. Driver may still be running."
        )
    
    return ComparisonResponse(job_id=job_id, platforms=platforms)

