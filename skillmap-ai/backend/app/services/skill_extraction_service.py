"""
Service to automatically extract skills from strategic goals using LLM.
"""
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Skill, StrategicGoal, StrategicGoalRequiredSkill
from app.services.llm_service import LLMService
from app.services.ontology_service import OntologyService


class SkillExtractionService:
    """Extract and map skills from strategic goals."""

    def __init__(self, db: Session):
        self.db = db
        try:
            self.llm = LLMService()
        except ValueError:
            self.llm = None
        self.ontology = OntologyService(db)

    def extract_skills_for_goal(self, goal_id: str) -> List[dict]:
        """
        Extract required skills from a strategic goal and create StrategicGoalRequiredSkill records.
        Returns list of created skill mappings.
        """
        goal = self.db.get(StrategicGoal, UUID(goal_id))
        if not goal:
            raise ValueError("Goal not found")

        # Check if already extracted
        existing = (
            self.db.query(StrategicGoalRequiredSkill)
            .filter(StrategicGoalRequiredSkill.goal_id == UUID(goal_id))
            .all()
        )
        if existing:
            return [
                {
                    "skill_id": str(rs.skill_id),
                    "skill_name": rs.skill.name if rs.skill else "Unknown",
                    "target_level": rs.target_level,
                    "importance_weight": float(rs.importance_weight or 1.0),
                }
                for rs in existing
            ]

        if not self.llm:
            raise ValueError("LLM service not available (OPENAI_API_KEY not set)")

        # Get existing skills for context
        existing_skills = self.db.query(Skill).limit(100).all()
        skills_context = [
            {"name": s.name, "description": s.description or ""} for s in existing_skills
        ]

        # Extract skills using LLM
        extracted = self.llm.extract_skills_from_goal(
            goal.title, goal.description or "", skills_context
        )

        created_mappings = []
        for skill_data in extracted:
            # Try to match to existing skill via ontology
            matched_skill = self._match_or_create_skill(skill_data)
            
            # Create StrategicGoalRequiredSkill
            mapping = StrategicGoalRequiredSkill(
                goal_id=UUID(goal_id),
                skill_id=matched_skill.skill_id,
                target_level=skill_data["target_level"],
                importance_weight=skill_data["importance_weight"],
                required_by_year=goal.time_horizon_year,
            )
            self.db.add(mapping)
            created_mappings.append({
                "skill_id": str(matched_skill.skill_id),
                "skill_name": matched_skill.name,
                "target_level": skill_data["target_level"],
                "importance_weight": skill_data["importance_weight"],
            })

        self.db.commit()
        return created_mappings

    def _match_or_create_skill(self, skill_data: dict) -> Skill:
        """Match extracted skill to ontology or create new skill."""
        # Try to match via embedding similarity
        from app.schemas.skills import SkillMatchRequest
        
        match_req = SkillMatchRequest(
            phrase=f"{skill_data['name']} {skill_data.get('description', '')}",
            top_k=1,
        )
        matches = self.ontology.match_skill(match_req)
        
        # If good match (similarity > 0.7), use existing
        if matches and matches[0].score > 0.7:
            skill_id_str = matches[0].skill.skill_id  # Already a string from SkillOut
            return self.db.get(Skill, UUID(skill_id_str))
        
        # Otherwise create new skill
        from app.schemas.skills import SkillCreate
        
        create_req = SkillCreate(
            name=skill_data["name"],
            description=skill_data.get("description", ""),
            category=skill_data.get("category", "technical"),
            domain=skill_data.get("domain", ""),
            ontology_version="1.0.0",
            is_future_skill=True,
        )
        created = self.ontology.create_skill(create_req)
        return self.db.get(Skill, UUID(created.skill_id))

