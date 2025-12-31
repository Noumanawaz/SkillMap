from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StrategicGoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    time_horizon_year: Optional[int] = None
    business_unit: Optional[str] = None
    priority: Optional[int] = None
    owner_employee_id: Optional[str] = None


class StrategicGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_horizon_year: Optional[int] = None
    business_unit: Optional[str] = None
    priority: Optional[int] = None
    owner_employee_id: Optional[str] = None


class StrategicGoalOut(BaseModel):
    goal_id: str
    title: str
    description: Optional[str] = None
    time_horizon_year: Optional[int] = None
    business_unit: Optional[str] = None
    priority: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
