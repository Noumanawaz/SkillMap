from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile, Skill, StrategicGoal, StrategicGoalRequiredSkill
from app.vector.base import get_vector_store


class GapEngine:
    """
    Computes scalar gaps and vector-based gap index.
    """

    def __init__(self, db: Session):
        self.db = db
        self.vectors = get_vector_store()
        self.llm = None

        try:
            from app.services.llm_service import LLMService
            from app.core.config import get_settings
            import os

            settings = get_settings()
            api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

            if api_key and api_key.startswith("sk-"):
                self.llm = LLMService()
                print("✅ LLM initialized")
            else:
                print("⚠️ OpenAI API key missing or invalid")

        except Exception as e:
            print(f"❌ LLM init failed: {e}")
            self.llm = None

    def _required_skills(self, goal_id: str) -> List[StrategicGoalRequiredSkill]:
        return (
            self.db.query(StrategicGoalRequiredSkill)
            .filter(StrategicGoalRequiredSkill.goal_id == UUID(goal_id))
            .all()
        )

    def _bundle_embedding(self, skill_ids: List[str], weights: List[float]) -> List[float]:
        import numpy as np

        vecs = []
        for sid, w in zip(skill_ids, weights):
            v = self.vectors.fetch(sid)
            if v:
                vecs.append(w * np.array(v, dtype=float))

        if not vecs:
            return []

        summed = sum(vecs)
        return (summed / (sum(weights) + 1e-8)).tolist()

    def _similarity(self, a: List[float], b: List[float]) -> float:
        import numpy as np

        if not a or not b:
            return 0.0

        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb)) + 1e-8
        return float((va @ vb) / denom)

    def gaps_for_employee(self, employee_id: str, goal_id: str) -> Dict:
        emp = self.db.get(EmployeeProfile, UUID(employee_id))
        goal = self.db.get(StrategicGoal, UUID(goal_id))

        if not emp or not goal:
            raise ValueError("Employee or Goal not found")

        req_skills = self._required_skills(goal_id)
        skills_extracted = False

        if not req_skills:
            from app.services.skill_extraction_service import SkillExtractionService

            extractor = SkillExtractionService(self.db)
            if not extractor.llm:
                return {
                    "employee_id": employee_id,
                    "goal_id": goal_id,
                    "message": "AI required but not configured",
                }

            try:
                extractor.extract_skills_for_goal(goal_id)
                # Refresh the session to ensure we get the latest data
                self.db.commit()
                req_skills = self._required_skills(goal_id)
                skills_extracted = bool(req_skills)
            except Exception as e:
                # Rollback any partial changes
                self.db.rollback()
                return {
                    "employee_id": employee_id,
                    "goal_id": goal_id,
                    "message": f"Skill extraction failed: {e}",
                }

        if not req_skills:
            return {
                "employee_id": employee_id,
                "goal_id": goal_id,
                "message": "No skills found for goal",
            }

        profile = emp.cognitive_profile or {}

        employee_skills_for_ai = []
        for sid, data in profile.items():
            try:
                skill = self.db.get(Skill, UUID(sid))
                if skill:
                    level = float(data.get("level", 0.0))
                    employee_skills_for_ai.append({
                        "name": skill.name,
                        "proficiency_level": level,
                        "domain": skill.domain or "",
                        "category": skill.category or "",
                    })
            except Exception:
                continue

        required_skills_for_ai = []
        required_levels = {}
        weights = []
        skill_ids = []

        for rs in req_skills:
            skill = self.db.get(Skill, rs.skill_id)
            if skill:
                sid = str(rs.skill_id)
                skill_ids.append(sid)
                required_levels[sid] = float(rs.target_level)
                weights.append(float(rs.importance_weight or 1.0))

                required_skills_for_ai.append({
                    "name": skill.name,
                    "target_level": float(rs.target_level),
                    "domain": skill.domain or "",
                    "category": skill.category or "",
                    "importance_weight": float(rs.importance_weight or 1.0),
                })

        if not self.llm:
            return {
                "employee_id": employee_id,
                "goal_id": goal_id,
                "message": "AI gap analysis required but unavailable",
            }

        try:
            ai_gap_analysis = self.llm.analyze_skill_gaps(
                employee_skills_for_ai,
                required_skills_for_ai,
                goal.title,
                goal.description or "",
                emp.name,
                emp.description or "",
            )
        except Exception as e:
            return {
                "employee_id": employee_id,
                "goal_id": goal_id,
                "message": f"AI gap analysis failed: {e}",
            }

        current_levels = {sid: 0.0 for sid in skill_ids}
        scalar_gaps = {}

        for match in ai_gap_analysis.get("skill_matches", []):
            for rs in req_skills:
                skill = self.db.get(Skill, rs.skill_id)
                if skill and skill.name == match.get("required_skill"):
                    sid = str(rs.skill_id)
                    gap = float(match.get("gap_value", 0.0))
                    scalar_gaps[sid] = max(0.0, gap)
                    current_levels[sid] = max(0.0, required_levels[sid] - gap)

        for missing in ai_gap_analysis.get("missing_skills", []):
            for rs in req_skills:
                skill = self.db.get(Skill, rs.skill_id)
                if skill and skill.name == missing.get("required_skill"):
                    sid = str(rs.skill_id)
                    scalar_gaps[sid] = float(missing.get("gap_value", required_levels[sid]))

        emp_vec = self._bundle_embedding(skill_ids, [current_levels[sid] for sid in skill_ids])
        req_vec = self._bundle_embedding(skill_ids, weights)
        similarity = self._similarity(emp_vec, req_vec)

        avg_gap = sum(scalar_gaps.values()) / (len(scalar_gaps) + 1e-8)
        gap_index = (1.0 - similarity) + avg_gap

        skill_names = {
            sid: (self.db.get(Skill, UUID(sid)).name if self.db.get(Skill, UUID(sid)) else "Unknown")
            for sid in skill_ids
        }

        return {
            "employee_id": employee_id,
            "goal_id": goal_id,
            "scalar_gaps": scalar_gaps,
            "skill_names": skill_names,
            "similarity": similarity,
            "gap_index": gap_index,
            "skills_extracted": skills_extracted,
        }

    def gaps_for_team(self, manager_id: str, goal_id: str) -> Dict:
        members = self.db.query(EmployeeProfile).filter(
            EmployeeProfile.manager_id == UUID(manager_id)
        ).all()

        results = [self.gaps_for_employee(str(m.employee_id), goal_id) for m in members]
        if not results:
            return {"team_size": 0, "members": [], "avg_gap_index": 0.0}

        avg_gap = sum(r["gap_index"] for r in results) / len(results)
        return {"team_size": len(results), "members": results, "avg_gap_index": avg_gap}
