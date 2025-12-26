from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.assessments import (
    SkillAssessmentGenerateRequest,
    SkillAssessmentGenerateResponse,
    SkillAssessmentSubmitRequest,
    SkillAssessmentResult,
    SkillAssessmentHistory,
)
from app.services.assessment_service import AssessmentService

router = APIRouter()


@router.post("/generate", response_model=SkillAssessmentGenerateResponse)
def generate_assessment(
    request: SkillAssessmentGenerateRequest,
    employee_id: str,  # TODO: Get from auth token
    db: Session = Depends(get_db),
):
    """Generate a dynamic MCQ test for a skill."""
    try:
        service = AssessmentService(db)
        result = service.generate_assessment(
            employee_id=employee_id,
            skill_id=request.skill_id,
            skill_name=request.skill_name,
            skill_description=request.skill_description,
            readiness_score=request.readiness_score,
            num_questions=request.num_questions,
        )
        return SkillAssessmentGenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate assessment: {str(e)}")


@router.post("/submit", response_model=SkillAssessmentResult)
def submit_assessment(
    request: SkillAssessmentSubmitRequest,
    employee_id: str,  # TODO: Get from auth token
    db: Session = Depends(get_db),
):
    """Submit assessment answers and get results."""
    try:
        service = AssessmentService(db)
        result = service.submit_assessment(
            assessment_id=request.assessment_id,
            employee_id=employee_id,
            answers=request.answers,
        )
        return SkillAssessmentResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit assessment: {str(e)}")


@router.get("/{assessment_id}", response_model=SkillAssessmentGenerateResponse)
def get_assessment(
    assessment_id: str,
    employee_id: str,  # TODO: Get from auth token
    db: Session = Depends(get_db),
):
    """Get assessment details."""
    try:
        service = AssessmentService(db)
        result = service.get_assessment(assessment_id, employee_id)
        return SkillAssessmentGenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assessment: {str(e)}")


@router.get("/history/{employee_id}", response_model=List[SkillAssessmentHistory])
def get_assessment_history(
    employee_id: str,
    skill_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get assessment history for an employee."""
    try:
        service = AssessmentService(db)
        results = service.get_assessment_history(employee_id, skill_id)
        return [SkillAssessmentHistory(**r) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assessment history: {str(e)}")

