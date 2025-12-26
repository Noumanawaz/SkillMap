from typing import Dict, List, Optional
from datetime import date

from pydantic import BaseModel, EmailStr


class AssessmentEvent(BaseModel):
    skill_id: str
    difficulty: float
    correct: bool


class CognitiveUpdateRequest(BaseModel):
    assessments: List[AssessmentEvent]


class CognitiveSummaryResponse(BaseModel):
    employee_id: str
    profile: Dict[str, Dict]


class EmployeeCreate(BaseModel):
    email: EmailStr
    name: str
    description: Optional[str] = None  # Employee description/bio for skill extraction
    role_id: Optional[str] = None
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None
    location: Optional[str] = None


class EmployeeUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    description: Optional[str] = None  # Employee description/bio for skill extraction
    role_id: Optional[str] = None
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None
    location: Optional[str] = None


class EmployeeOut(BaseModel):
    employee_id: str
    email: str
    name: str
    description: Optional[str] = None
    role_id: Optional[str] = None
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None
    location: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
