from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import StrategicGoal
from app.db.session import get_db
from app.schemas.strategy import (
    StrategicGoalOut,
    StrategicGoalCreate,
    StrategicGoalUpdate,
)

router = APIRouter()


@router.get("/goals", response_model=List[StrategicGoalOut])
def list_goals(db: Session = Depends(get_db)):
    """List all strategic goals."""
    rows = db.query(StrategicGoal).all()
    return [
        StrategicGoalOut(
            goal_id=str(r.goal_id),
            title=r.title,
            description=r.description,
            time_horizon_year=r.time_horizon_year,
            business_unit=r.business_unit,
            priority=r.priority,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/goals", response_model=StrategicGoalOut)
def create_goal(payload: StrategicGoalCreate, db: Session = Depends(get_db)):
    """Create a new strategic goal."""
    goal = StrategicGoal(
        title=payload.title,
        description=payload.description,
        time_horizon_year=payload.time_horizon_year,
        business_unit=payload.business_unit,
        priority=payload.priority,
        owner_employee_id=UUID(payload.owner_employee_id)
        if payload.owner_employee_id
        else None,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return StrategicGoalOut(
        goal_id=str(goal.goal_id),
        title=goal.title,
        description=goal.description,
        time_horizon_year=goal.time_horizon_year,
        business_unit=goal.business_unit,
        priority=goal.priority,
        created_at=goal.created_at,
    )


@router.put("/goals/{goal_id}", response_model=StrategicGoalOut)
def update_goal(
    goal_id: str, payload: StrategicGoalUpdate, db: Session = Depends(get_db)
):
    """Update a strategic goal."""
    try:
        goal = db.get(StrategicGoal, UUID(goal_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID")

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if payload.title is not None:
        goal.title = payload.title
    if payload.description is not None:
        goal.description = payload.description
    if payload.time_horizon_year is not None:
        goal.time_horizon_year = payload.time_horizon_year
    if payload.business_unit is not None:
        goal.business_unit = payload.business_unit
    if payload.priority is not None:
        goal.priority = payload.priority
    if payload.owner_employee_id is not None:
        goal.owner_employee_id = (
            UUID(payload.owner_employee_id) if payload.owner_employee_id else None
        )

    db.commit()
    db.refresh(goal)

    return StrategicGoalOut(
        goal_id=str(goal.goal_id),
        title=goal.title,
        description=goal.description,
        time_horizon_year=goal.time_horizon_year,
        business_unit=goal.business_unit,
        priority=goal.priority,
        created_at=goal.created_at,
    )


@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    """Delete a strategic goal."""
    try:
        goal = db.get(StrategicGoal, UUID(goal_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID")

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted successfully"}


