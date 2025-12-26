from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.learning import GeneratePathRequest, GeneratePathResponse, PathItem
from app.services.recommender import RecommenderService


router = APIRouter()


@router.post("/learning-path", response_model=GeneratePathResponse)
def create_learning_path(
    payload: GeneratePathRequest,
    db: Session = Depends(get_db),
):
    service = RecommenderService(db)
    try:
        result = service.generate_learning_path(
            employee_id=payload.employee_id,
            goal_id=payload.goal_id,
            max_hours=payload.max_hours,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    items = [PathItem(**i) for i in result["items"]]
    return GeneratePathResponse(
        employee_id=result["employee_id"],
        goal_id=result["goal_id"],
        items=items,
        total_hours=result["total_hours"],
        meta=result["meta"],
    )


