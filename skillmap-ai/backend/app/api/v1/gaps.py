from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.gaps import EmployeeGapResponse, TeamGapResponse, TeamGapMember
from app.services.gap_engine import GapEngine


router = APIRouter()


@router.get("/by-goal/{goal_id}/employee/{employee_id}", response_model=EmployeeGapResponse)
def gaps_for_employee(goal_id: str, employee_id: str, db: Session = Depends(get_db)):
    engine = GapEngine(db)
    try:
        result = engine.gaps_for_employee(employee_id, goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return EmployeeGapResponse(**result)


@router.get("/by-goal/{goal_id}/team/{manager_id}", response_model=TeamGapResponse)
def gaps_for_team(goal_id: str, manager_id: str, db: Session = Depends(get_db)):
    engine = GapEngine(db)
    result = engine.gaps_for_team(manager_id, goal_id)
    members = [TeamGapMember(**m) for m in result.get("members", [])]
    return TeamGapResponse(
        team_size=result.get("team_size", 0),
        members=members,
        avg_gap_index=result.get("avg_gap_index", 0.0),
    )


