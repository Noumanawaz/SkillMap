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
    """List all employees."""
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
    """Create a new employee and extract skills from description if provided."""
    # Check if email already exists
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
    db.flush()  # Flush to get employee_id
    
    # Extract skills from description if provided
    if payload.description and payload.description.strip():
        try:
            skill_service = EmployeeSkillService(db)
            skill_service.extract_and_store_skills(str(emp.employee_id), payload.description)
        except Exception as e:
            # Log error but don't fail employee creation
            print(f"Failed to extract skills for employee {emp.employee_id}: {e}")
    
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
    """Get employee by ID."""
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


@router.put("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: str, payload: EmployeeUpdate, db: Session = Depends(get_db)
):
    """Update an employee."""
    try:
        emp = db.get(EmployeeProfile, UUID(employee_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if payload.email and payload.email != emp.email:
        # Check if new email already exists
        existing = db.query(EmployeeProfile).filter(EmployeeProfile.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Employee with this email already exists")
        emp.email = payload.email
    
    if payload.name:
        emp.name = payload.name
    if payload.description is not None:
        old_description = emp.description
        emp.description = payload.description
        # Extract skills if description changed or is new
        if payload.description and payload.description.strip():
            if payload.description != old_description:  # Only extract if changed
                try:
                    skill_service = EmployeeSkillService(db)
                    result = skill_service.extract_and_store_skills(str(emp.employee_id), payload.description)
                    # Log result for debugging
                    if result.get("extracted_skills", 0) == 0:
                        print(f"Skill extraction result for {emp.employee_id}: {result.get('message', 'Unknown error')}")
                    else:
                        print(f"Successfully extracted {result.get('extracted_skills')} skills for {emp.employee_id}")
                except Exception as e:
                    print(f"Failed to extract skills for employee {emp.employee_id}: {e}")
                    import traceback
                    traceback.print_exc()
    if payload.role_id is not None:
        emp.role_id = UUID(payload.role_id) if payload.role_id else None
    if payload.manager_id is not None:
        emp.manager_id = UUID(payload.manager_id) if payload.manager_id else None
    if payload.hire_date is not None:
        emp.hire_date = payload.hire_date
    if payload.location is not None:
        emp.location = payload.location
    
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
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    """Delete an employee."""
    try:
        emp = db.get(EmployeeProfile, UUID(employee_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted successfully"}


@router.post("/{employee_id}/cognitive-update", response_model=CognitiveSummaryResponse)
def update_cognitive_profile(
    employee_id: str, payload: CognitiveUpdateRequest, db: Session = Depends(get_db)
):
    service = CognitiveService(db)
    profile = service.update_profile(employee_id, [a.dict() for a in payload.assessments])
    return CognitiveSummaryResponse(employee_id=employee_id, profile=profile)


@router.get("/{employee_id}/cognitive-summary", response_model=CognitiveSummaryResponse)
def cognitive_summary(employee_id: str, db: Session = Depends(get_db)):
    service = CognitiveService(db)
    try:
        profile = service.get_cognitive_summary(employee_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Employee not found")
    return CognitiveSummaryResponse(employee_id=employee_id, profile=profile)


@router.get("/{employee_id}/skills")
def get_employee_skills(employee_id: str, db: Session = Depends(get_db)):
    """Get employee skills with details from cognitive profile."""
    from app.db.models import Skill
    
    try:
        emp = db.get(EmployeeProfile, UUID(employee_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid employee ID")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    profile = emp.cognitive_profile or {}
    skills_list = []
    missing_skills = []  # Track skills in profile but not in Skill table
    
    for skill_id, skill_data in profile.items():
        try:
            # Validate skill_id is a valid UUID
            skill_uuid = UUID(skill_id)
            skill = db.get(Skill, skill_uuid)
            
            level = skill_data.get("level", 0.0)
            # Convert theta to level if needed
            if level == 0.0 and "theta" in skill_data:
                theta = skill_data.get("theta", 0.0)
                level = max(1, min(5, int((theta + 3) * 5 / 6) + 1))
            
            if skill:
                # Skill exists in database
                skills_list.append({
                    "skill_id": skill_id,
                    "name": skill.name,
                    "category": skill.category,
                    "domain": skill.domain,
                    "proficiency_level": float(level),
                    "theta": skill_data.get("theta", 0.0),
                    "alpha": skill_data.get("alpha", 1.0),
                })
            else:
                # Skill ID exists in cognitive profile but not in Skill table
                missing_skills.append({
                    "skill_id": skill_id,
                    "name": f"Unknown Skill ({skill_id[:8]}...)",
                    "category": "unknown",
                    "domain": "unknown",
                    "proficiency_level": float(level),
                    "theta": skill_data.get("theta", 0.0),
                    "alpha": skill_data.get("alpha", 1.0),
                    "status": "missing_from_ontology"
                })
        except (ValueError, TypeError) as e:
            # Invalid skill_id format - skip it
            continue
    
    # Sort by proficiency level (highest first)
    skills_list.sort(key=lambda x: x["proficiency_level"], reverse=True)
    missing_skills.sort(key=lambda x: x["proficiency_level"], reverse=True)
    
    # Combine both lists - existing skills first, then missing ones
    all_skills = skills_list + missing_skills
    
    return {
        "employee_id": employee_id,
        "employee_name": emp.name,
        "skills": all_skills,
        "total_skills": len(all_skills),
        "skills_in_ontology": len(skills_list),
        "skills_missing_from_ontology": len(missing_skills),
    }


