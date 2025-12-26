"""
Service to extract and store skills from employee descriptions.
"""
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile, Skill
from app.services.llm_service import LLMService
from app.services.ontology_service import OntologyService


class EmployeeSkillService:
    """Extract skills from employee descriptions and store in cognitive profile."""

    def __init__(self, db: Session):
        self.db = db
        try:
            self.llm = LLMService()
        except ValueError:
            self.llm = None
        self.ontology = OntologyService(db)

    def extract_and_store_skills(self, employee_id: str, description: str) -> Dict:
        """
        Extract skills from employee description and store them in cognitive_profile.
        Returns dict with extracted_skills count and message.
        """
        if not description or not description.strip():
            return {"extracted_skills": 0, "message": "No description provided"}

        if not self.llm:
            return {
                "extracted_skills": 0,
                "message": "OpenAI API key not configured. Skills cannot be extracted automatically.",
            }

        try:
            # Get existing skills for context
            existing_skills = self.db.query(Skill).limit(100).all()
            skills_context = [
                {"name": s.name, "description": s.description or ""} for s in existing_skills
            ]

            # Extract skills using LLM
            extracted_skills_data = self.llm.extract_skills_from_description(
                description, skills_context
            )

            if not extracted_skills_data:
                return {
                    "extracted_skills": 0,
                    "message": "No skills could be extracted from the description.",
                }

            # Get employee
            emp = self.db.get(EmployeeProfile, UUID(employee_id))
            if not emp:
                raise ValueError("Employee not found")

            # Get or initialize cognitive profile
            profile = emp.cognitive_profile or {}

            # Match or create skills and add to profile
            matched_count = 0
            for skill_data in extracted_skills_data:
                # Try to match to existing skill
                matched_skill = self._match_or_create_skill(skill_data)
                if matched_skill:
                    skill_id = str(matched_skill.skill_id)
                    proficiency = skill_data.get("proficiency_level", 3)
                    
                    # Initialize skill in cognitive profile if not present
                    if skill_id not in profile:
                        profile[skill_id] = {
                            "theta": float(proficiency - 3) * 0.5,  # Convert 1-5 to approximate theta
                            "alpha": 1.0,
                            "level": float(proficiency),
                        }
                    else:
                        # Update level if higher
                        current_level = profile[skill_id].get("level", 0)
                        if proficiency > current_level:
                            profile[skill_id]["level"] = float(proficiency)
                            profile[skill_id]["theta"] = float(proficiency - 3) * 0.5
                    matched_count += 1

            # Update employee profile
            emp.cognitive_profile = profile
            self.db.add(emp)
            self.db.commit()
            self.db.refresh(emp)

            return {
                "extracted_skills": matched_count,
                "message": f"Successfully extracted and stored {matched_count} skill(s) from description.",
            }

        except Exception as e:
            return {
                "extracted_skills": 0,
                "message": f"Failed to extract skills: {str(e)}",
            }

    def _match_or_create_skill(self, skill_data: dict) -> Skill:
        """Match extracted skill to ontology or create new skill."""
        # Try to match via embedding similarity
        from app.schemas.skills import SkillMatchRequest
        
        match_req = SkillMatchRequest(
            phrase=f"{skill_data['name']} {skill_data.get('description', '')}",
            top_k=1,
        )
        matches = self.ontology.match_skill(match_req)

        # If good match (similarity > 0.75), use existing
        if matches and matches[0].score > 0.75:
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
            is_future_skill=False,
        )
        created = self.ontology.create_skill(create_req)
        # created.skill_id is already a string from SkillOut
        return self.db.get(Skill, UUID(created.skill_id))

