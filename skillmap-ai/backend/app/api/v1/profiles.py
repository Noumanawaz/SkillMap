from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile, SkillAssessment, StrategicGoal
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
    db.flush()  # Flush to get employee_id, but don't commit yet

    if payload.description and payload.description.strip():
        try:
            skill_service = EmployeeSkillService(db)
            result = skill_service.extract_and_store_skills(str(emp.employee_id), payload.description)
            if result.get("extracted_skills", 0) == 0:
                print(f"⚠️ No skills extracted for employee {emp.employee_id}: {result.get('message', 'Unknown error')}")
            else:
                print(f"✅ Extracted {result.get('extracted_skills', 0)} skills for employee {emp.employee_id}")
        except Exception as e:
            import traceback
            print(f"❌ Skill extraction failed for employee {emp.employee_id}: {e}")
            traceback.print_exc()

    db.commit()  # Commit everything together (employee + cognitive_profile)
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


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_profile(employee_id: str, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    try:
        emp = db.get(EmployeeProfile, UUID(employee_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = payload.model_dump(exclude_unset=True)
    
    # Handle UUID conversions for optional fields
    for field in ["role_id", "manager_id"]:
        if field in update_data and update_data[field]:
            update_data[field] = UUID(update_data[field])

    for field, value in update_data.items():
        setattr(emp, field, value)

    db.add(emp)
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


@router.delete("/{employee_id}")
def delete_profile(employee_id: str, db: Session = Depends(get_db)):
    try:
        emp_uuid = UUID(employee_id)
        emp = db.get(EmployeeProfile, emp_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    try:
        # 1. Handle subordinates: reassign or set manager_id to None
        subordinates = db.query(EmployeeProfile).filter(EmployeeProfile.manager_id == emp_uuid).all()
        for sub in subordinates:
            sub.manager_id = None
            db.add(sub)

        # 2. Delete skill assessments associated with this employee
        db.query(SkillAssessment).filter(SkillAssessment.employee_id == emp_uuid).delete()

        # 3. Handle owned strategic goals: set owner_employee_id to None
        owned_goals = db.query(StrategicGoal).filter(StrategicGoal.owner_employee_id == emp_uuid).all()
        for goal in owned_goals:
            goal.owner_employee_id = None
            db.add(goal)

        # 4. Finally delete the employee profile
        db.delete(emp)
        db.commit()
        
        return {"status": "success", "message": f"Employee {employee_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error during employee deletion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete employee: {str(e)}")
