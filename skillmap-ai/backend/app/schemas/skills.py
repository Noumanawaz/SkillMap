from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel


class SkillCreate(BaseModel):
  name: str
  category: Optional[str] = None
  domain: Optional[str] = None
  description: Optional[str] = None
  parent_skill_id: Optional[str] = None
  prerequisites: Optional[List[str]] = None
  is_future_skill: bool = False
  ontology_version: str
  effective_from: Optional[date] = None
  effective_to: Optional[date] = None


class SkillOut(BaseModel):
  skill_id: str
  name: str
  category: Optional[str] = None
  domain: Optional[str] = None
  description: Optional[str] = None
  is_future_skill: bool
  ontology_version: str
  created_at: datetime

  class Config:
    from_attributes = True


class SkillMatchRequest(BaseModel):
  phrase: str
  top_k: int = 5


class SkillMatchResult(BaseModel):
  skill: SkillOut
  score: float


