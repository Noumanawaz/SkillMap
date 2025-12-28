from typing import Dict, List, Optional, Union
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator


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

    @field_validator('hire_date', 'role_id', 'manager_id', mode='before')
    @classmethod
    def parse_optional_fields(cls, v):
        """Convert empty string to None for optional fields."""
        if v == "" or v is None:
            return None
        return v


class EmployeeUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    description: Optional[str] = None  # Employee description/bio for skill extraction
    role_id: Optional[str] = None
    manager_id: Optional[str] = None
    hire_date: Optional[date] = None
    location: Optional[str] = None

    @field_validator('hire_date', 'role_id', 'manager_id', mode='before')
    @classmethod
    def parse_optional_fields(cls, v):
        """Convert empty string to None for optional fields."""
        if v == "" or v is None:
            return None
        return v


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
