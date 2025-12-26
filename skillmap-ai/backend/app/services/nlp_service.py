from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import StrategicGoal
from app.schemas.strategy import StrategyIngestRequest, StrategicGoalOut
from app.services.llm_service import LLMService


class StrategyNLPService:
    """
    Real LLM-based strategy ingestion and goal extraction using OpenAI GPT-3.5.
    """

    def __init__(self, db: Session):
        self.db = db
        try:
            self.llm = LLMService()
        except ValueError:
            # If API key not set, will use fallback
            self.llm = None

    def ingest_and_extract(self, payload: StrategyIngestRequest) -> List[StrategicGoalOut]:
        """Extract strategic goals using LLM."""
        if self.llm:
            goals_data = self.llm.extract_strategic_goals(
                payload.raw_text, payload.business_unit
            )
        else:
            # Fallback if LLM not available
            goals_data = self._heuristic_extract(payload.raw_text, payload.business_unit)
        
        out: List[StrategicGoalOut] = []
        for g in goals_data:
            row = StrategicGoal(
                title=g["title"],
                description=g.get("description", g["title"]),
                time_horizon_year=g.get("time_horizon_year"),
                business_unit=payload.business_unit,
                priority=g.get("priority", 3),
                created_at=datetime.utcnow(),
            )
            self.db.add(row)
            self.db.flush()
            out.append(
                StrategicGoalOut(
                    goal_id=str(row.goal_id),
                    title=row.title,
                    description=row.description,
                    time_horizon_year=row.time_horizon_year,
                    business_unit=row.business_unit,
                    priority=row.priority,
                    created_at=row.created_at,
                )
            )
        self.db.commit()
        return out

    def _heuristic_extract(self, text: str, business_unit: Optional[str]):
        """Fallback heuristic if LLM unavailable."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        goals = []
        current_year = datetime.utcnow().year
        for ln in lines:
            if ln and (ln[0].isdigit() or ln.startswith(("-", "*"))):
                title = ln.lstrip("0123456789.-* ").strip()
                goals.append(
                    {
                        "title": title[:200],
                        "description": title,
                        "time_horizon_year": current_year + 3,
                        "priority": 3,
                    }
                )
        if not goals:
            goals.append(
                {
                    "title": "Strategic Transformation",
                    "description": text[:500],
                    "time_horizon_year": current_year + 3,
                    "priority": 3,
                }
            )
        return goals


