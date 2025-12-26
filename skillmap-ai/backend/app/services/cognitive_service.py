from collections import defaultdict
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile


class CognitiveService:
    """
    Simple 2-PL IRT-based cognitive profile management.
    Stores per-skill theta and alpha in EmployeeProfile.cognitive_profile JSON.
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _irt_probability(theta: float, alpha: float, beta: float) -> float:
        import math

        z = alpha * (theta - beta)
        return 1.0 / (1.0 + math.exp(-z))

    def _update_theta(self, theta: float, responses, lr: float = 0.01, steps: int = 15) -> float:
        t = theta
        for _ in range(steps):
            grad = 0.0
            for alpha, beta, correct in responses:
                p = self._irt_probability(t, alpha, beta)
                grad += (correct - p) * alpha
            t += lr * grad
        return t

    def update_profile(
        self,
        employee_id: str,
        assessments: List[Dict],
    ) -> Dict:
        """
        assessments: [{skill_id, difficulty, correct}]
        """
        try:
            emp = self.db.get(EmployeeProfile, UUID(employee_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid employee ID")
        if not emp:
            raise ValueError("Employee not found")

        profile = emp.cognitive_profile or {}
        grouped = defaultdict(list)
        for a in assessments:
            grouped[a["skill_id"]].append(a)

        for skill_id, items in grouped.items():
            state = profile.get(skill_id, {"theta": 0.0, "alpha": 1.0, "level": 0.0})
            responses = [(state["alpha"], i["difficulty"], i["correct"]) for i in items]
            state["theta"] = self._update_theta(state["theta"], responses)
            # Convert theta to proficiency level (0-5 scale)
            # theta range: -3 to +3, map to 0-5
            state["level"] = max(0.0, min(5.0, ((state["theta"] + 3) / 6) * 5))
            profile[skill_id] = state

        emp.cognitive_profile = profile
        self.db.add(emp)
        self.db.commit()
        self.db.refresh(emp)
        return profile

    def get_cognitive_summary(self, employee_id: str) -> Dict:
        try:
            emp = self.db.get(EmployeeProfile, UUID(employee_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid employee ID")
        if not emp:
            raise ValueError("Employee not found")
        return emp.cognitive_profile or {}


