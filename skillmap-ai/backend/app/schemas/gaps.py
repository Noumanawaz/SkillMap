from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EmployeeGapResponse(BaseModel):
    employee_id: str
    goal_id: str
    scalar_gaps: Dict[str, float]
    skill_names: Optional[Dict[str, str]] = None  # Mapping of skill_id to skill_name
    similarity: float
    gap_index: float
    message: Optional[str] = None
    ai_insights: Optional[Dict[str, Any]] = None  # AI-powered gap analysis insights
    processing_info: Optional[Dict[str, Any]] = None  # Processing metadata


class TeamGapMember(BaseModel):
    employee_id: str
    goal_id: str
    scalar_gaps: Dict[str, float]
    similarity: float
    gap_index: float


class TeamGapResponse(BaseModel):
    team_size: int
    members: List[TeamGapMember]
    avg_gap_index: float


