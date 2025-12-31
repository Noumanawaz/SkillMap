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
    def __init__(self, db: Session):
        self.db = db
        try:
            self.llm = LLMService()
        except ValueError:
            self.llm = None
        self.ontology = OntologyService(db)

    def extract_skills_for_goal(self, goal_id: str) -> List[dict]:
        goal = self.db.get(StrategicGoal, UUID(goal_id))
        if not goal:
            raise ValueError("Goal not found")

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
            raise ValueError("LLM service not available")

        existing_skills = self.db.query(Skill).limit(100).all()
        skills_context = [
            {"name": s.name, "description": s.description or ""}
            for s in existing_skills
        ]

        try:
            extracted = self.llm.extract_skills_from_goal(
                goal.title,
                goal.description or "",
                skills_context,
            )
        except Exception as e:
            raise ValueError(f"Skill extraction failed: {str(e)}")

        created = []

        for skill_data in extracted:
            try:
                matched_skill = self._match_or_create_skill(skill_data)

                # Check if mapping already exists
                existing_mapping = (
                    self.db.query(StrategicGoalRequiredSkill)
                    .filter(
                        StrategicGoalRequiredSkill.goal_id == UUID(goal_id),
                        StrategicGoalRequiredSkill.skill_id == matched_skill.skill_id
                    )
                    .first()
                )

                if existing_mapping:
                    # Update existing mapping if needed
                    existing_mapping.target_level = skill_data["target_level"]
                    existing_mapping.importance_weight = skill_data["importance_weight"]
                    if goal.time_horizon_year:
                        existing_mapping.required_by_year = goal.time_horizon_year
                    
                    created.append({
                        "skill_id": str(matched_skill.skill_id),
                        "skill_name": matched_skill.name,
                        "target_level": skill_data["target_level"],
                        "importance_weight": skill_data["importance_weight"],
                    })
                else:
                    # Create new mapping
                    mapping = StrategicGoalRequiredSkill(
                        goal_id=UUID(goal_id),
                        skill_id=matched_skill.skill_id,
                        target_level=skill_data["target_level"],
                        importance_weight=skill_data["importance_weight"],
                        required_by_year=goal.time_horizon_year,
                    )

                    self.db.add(mapping)

                    created.append({
                        "skill_id": str(matched_skill.skill_id),
                        "skill_name": matched_skill.name,
                        "target_level": skill_data["target_level"],
                        "importance_weight": skill_data["importance_weight"],
                    })
            except Exception as e:
                # Rollback on error and continue with next skill
                self.db.rollback()
                print(f"⚠️ Failed to process skill {skill_data.get('name', 'unknown')}: {e}")
                continue

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to save skill mappings: {str(e)}")
        
        return created

    def _match_or_create_skill(self, skill_data: dict) -> Skill:
        from app.schemas.skills import SkillMatchRequest, SkillCreate

        match_req = SkillMatchRequest(
            phrase=f"{skill_data['name']} {skill_data.get('description', '')}",
            top_k=1,
        )

        matches = self.ontology.match_skill(match_req)

        if matches and matches[0].score > 0.7:
            return self.db.get(Skill, UUID(matches[0].skill.skill_id))

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
