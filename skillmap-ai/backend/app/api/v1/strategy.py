from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import StrategicGoal
from app.db.session import get_db
from app.schemas.strategy import (
    StrategyIngestRequest,
    StrategicGoalOut,
    StrategicGoalCreate,
    StrategicGoalUpdate,
)
from app.services.nlp_service import StrategyNLPService


router = APIRouter()


@router.post("/ingest", response_model=List[StrategicGoalOut])
def ingest_strategy_document(
    payload: StrategyIngestRequest,
    db: Session = Depends(get_db),
    auto_extract_skills: bool = False,
):
    """
    Ingest raw strategy text, extract strategic goals using NLP/LLM,
    and persist them.
    If auto_extract_skills is True, automatically extract skills for each goal.
    """
    service = StrategyNLPService(db=db)
    goals = service.ingest_and_extract(payload)
    
    # Auto-extract skills if requested and LLM is available
    if auto_extract_skills:
        try:
            from app.services.skill_extraction_service import SkillExtractionService
            extraction_service = SkillExtractionService(db=db)
            for goal in goals:
                try:
                    extraction_service.extract_skills_for_goal(goal.goal_id)
                except Exception as e:
                    print(f"Failed to extract skills for goal {goal.goal_id}: {e}")
        except Exception as e:
            print(f"Skill extraction service unavailable: {e}")
    
    return goals


@router.get("/goals", response_model=List[StrategicGoalOut])
def list_goals(db: Session = Depends(get_db)):
    """List all strategic goals."""
    from app.db.models import StrategicGoalRequiredSkill
    
    rows = db.query(StrategicGoal).all()
    goals_out = []
    for r in rows:
        goals_out.append(
            StrategicGoalOut(
                goal_id=str(r.goal_id),
                title=r.title,
                description=r.description,
                time_horizon_year=r.time_horizon_year,
                business_unit=r.business_unit,
                priority=r.priority,
                created_at=r.created_at,
            )
        )
    return goals_out

@router.get("/goals/{goal_id}/skills-count")
def get_goal_skills_count(goal_id: str, db: Session = Depends(get_db)):
    """Get the number of skills extracted for a goal."""
    from app.db.models import StrategicGoalRequiredSkill
    from uuid import UUID
    
    try:
        count = (
            db.query(StrategicGoalRequiredSkill)
            .filter(StrategicGoalRequiredSkill.goal_id == UUID(goal_id))
            .count()
        )
        return {"goal_id": goal_id, "skills_count": count}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid goal ID")


@router.post("/goals", response_model=StrategicGoalOut)
def create_goal(payload: StrategicGoalCreate, db: Session = Depends(get_db)):
    """Create a new strategic goal."""
    goal = StrategicGoal(
        title=payload.title,
        description=payload.description,
        time_horizon_year=payload.time_horizon_year,
        business_unit=payload.business_unit,
        priority=payload.priority,
        owner_employee_id=UUID(payload.owner_employee_id) if payload.owner_employee_id else None,
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
    
    if payload.title:
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
        goal.owner_employee_id = UUID(payload.owner_employee_id) if payload.owner_employee_id else None
    
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


@router.post("/goals/{goal_id}/extract-skills")
def extract_skills_for_goal(goal_id: str, db: Session = Depends(get_db)):
    """
    Automatically extract required skills from a strategic goal using LLM.
    """
    from app.services.skill_extraction_service import SkillExtractionService
    from fastapi import HTTPException
    
    try:
        service = SkillExtractionService(db=db)
        mappings = service.extract_skills_for_goal(goal_id)
        return {
            "goal_id": goal_id,
            "skills_extracted": len(mappings),
            "mappings": mappings,
            "message": f"Successfully extracted {len(mappings)} skills using AI"
        }
    except ValueError as e:
        if "not available" in str(e) or "OPENAI_API_KEY" in str(e):
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file."
            )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract skills: {str(e)}")


