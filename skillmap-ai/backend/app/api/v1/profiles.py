from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile
from app.db.session import get_db
from app.schemas.profiles import (
    CognitiveUpdateRequest,
    CognitiveSummaryResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeOut,
)
from app.services.cognitive_service import CognitiveService
from app.services.employee_skill_service import EmployeeSkillService

router = APIRouter()


@router.get("", response_model=List[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeProfile).all()
    return [
        EmployeeOut(
            employee_id=str(emp.employee_id),
            email=emp.email,
            name=emp.name,
            description=emp.description,
            role_id=str(emp.role_id) if emp.role_id else None,
            manager_id=str(emp.manager_id) if emp.manager_id else None,
            hire_date=emp.hire_date,
            location=emp.location,
            created_at=emp.created_at.isoformat() if emp.created_at else None,
        )
        for emp in employees
    ]


@router.post("", response_model=EmployeeOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(EmployeeProfile).filter(EmployeeProfile.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")

    emp = EmployeeProfile(
        email=payload.email,
        name=payload.name,
        description=payload.description,
        role_id=UUID(payload.role_id) if payload.role_id else None,
        manager_id=UUID(payload.manager_id) if payload.manager_id else None,
        hire_date=payload.hire_date,
        location=payload.location,
    )
    db.add(emp)
    db.flush()

    if payload.description and payload.description.strip():
        try:
            skill_service = EmployeeSkillService(db)
            skill_service.extract_and_store_skills(str(emp.employee_id), payload.description)
        except Exception as e:
            print(f"⚠️ Skill extraction failed for employee {emp.employee_id}: {e}")

    db.commit()
    db.refresh(emp)

    return EmployeeOut(
        employee_id=str(emp.employee_id),
        email=emp.email,
        name=emp.name,
        description=emp.description,
        role_id=str(emp.role_id) if emp.role_id else None,
        manager_id=str(emp.manager_id) if emp.manager_id else None,
        hire_date=emp.hire_date,
        location=emp.location,
        created_at=emp.created_at.isoformat() if emp.created_at else None,
    )


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_profile(employee_id: str, db: Session = Depends(get_db)):
    try:
        emp = db.get(EmployeeProfile, UUID(employee_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    return EmployeeOut(
        employee_id=str(emp.employee_id),
        email=emp.email,
        name=emp.name,
        description=emp.description,
        role_id=str(emp.role_id) if emp.role_id else None,
        manager_id=str(emp.manager_id) if emp.manager_id else None,
        hire_date=emp.hire_date,
        location=emp.location,
        created_at=emp.created_at.isoformat() if emp.created_at else None,
    )


@router.get("/{employee_id}/skills")
def get_employee_skills(employee_id: str, db: Session = Depends(get_db)):
    from app.db.models import Skill

    try:
        emp = db.get(EmployeeProfile, UUID(employee_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    profile = emp.cognitive_profile or {}
    skills_list = []
    missing_skills = []

    for skill_id, skill_data in profile.items():
        try:
            skill_uuid = UUID(skill_id)
            skill = db.get(Skill, skill_uuid)

            level = skill_data.get("level", 0.0)

            # Convert theta → level if level missing
            if level == 0.0 and "theta" in skill_data:
                theta = skill_data.get("theta", 0.0)
                level = max(1, min(5, int((theta + 3) * 5 / 6) + 1))

            skill_payload = {
                "skill_id": skill_id,
                "proficiency_level": float(level),
                "theta": skill_data.get("theta", 0.0),
                "alpha": skill_data.get("alpha", 1.0),
            }

            if skill:
                skill_payload.update({
                    "name": skill.name,
                    "category": skill.category,
                    "domain": skill.domain,
                })
                skills_list.append(skill_payload)
            else:
                skill_payload.update({
                    "name": f"Unknown Skill ({skill_id[:8]}...)",
                    "category": "unknown",
                    "domain": "unknown",
                    "status": "missing_from_ontology",
                })
                missing_skills.append(skill_payload)

        except (ValueError, TypeError):
            continue

    skills_list.sort(key=lambda x: x["proficiency_level"], reverse=True)
    missing_skills.sort(key=lambda x: x["proficiency_level"], reverse=True)

    all_skills = skills_list + missing_skills

    return {
        "employee_id": employee_id,
        "employee_name": emp.name,
        "skills": all_skills,
        "total_skills": len(all_skills),
        "skills_in_ontology": len(skills_list),
        "skills_missing_from_ontology": len(missing_skills),
    }
