from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GeneratePathRequest(BaseModel):
    employee_id: str
    goal_id: str
    max_hours: float = 40.0


class PathItem(BaseModel):
    skill_id: str
    module_id: str
    title: str
    description: Optional[str] = None
    order: int
    expected_gain: float
    duration_minutes: Optional[int] = None
    is_generated: bool = False


class GeneratePathResponse(BaseModel):
    employee_id: str
    goal_id: str
    items: List[PathItem]
    total_hours: float
    meta: Dict[str, Any]


