"""
Service to extract and store skills from employee descriptions.
"""
from typing import Dict
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
        if not description or not description.strip():
            return {"extracted_skills": 0, "message": "No description provided"}

        if not self.llm:
            return {
                "extracted_skills": 0,
                "message": "OpenAI API key not configured",
            }

        try:
            existing_skills = self.db.query(Skill).limit(100).all()
            skills_context = [
                {"name": s.name, "description": s.description or ""}
                for s in existing_skills
            ]

            extracted_skills = self.llm.extract_skills_from_description(
                description, skills_context
            )

            if not extracted_skills:
                return {
                    "extracted_skills": 0,
                    "message": "No skills extracted from description",
                }

            emp = self.db.get(EmployeeProfile, UUID(employee_id))
            if not emp:
                raise ValueError("Employee not found")

            profile = emp.cognitive_profile or {}
            matched_count = 0

            for skill_data in extracted_skills:
                try:
                    matched_skill = self._match_or_create_skill(skill_data)
                    if not matched_skill:
                        continue

                    skill_id = str(matched_skill.skill_id)
                    proficiency = int(skill_data.get("proficiency_level", 3))

                    if skill_id not in profile:
                        profile[skill_id] = {
                            "theta": (proficiency - 3) * 0.5,
                            "alpha": 1.0,
                            "level": proficiency,
                        }
                    else:
                        if proficiency > profile[skill_id]["level"]:
                            profile[skill_id]["level"] = proficiency
                            profile[skill_id]["theta"] = (proficiency - 3) * 0.5

                    matched_count += 1

                except Exception as e:
                    print(f"Skill processing failed: {e}")
                    continue

            if matched_count > 0:
                emp.cognitive_profile = profile
                self.db.add(emp)
                self.db.commit()
                self.db.refresh(emp)

            return {
                "extracted_skills": matched_count,
                "message": f"Stored {matched_count} skills",
            }

        except Exception as e:
            return {
                "extracted_skills": 0,
                "message": f"Failed to extract skills: {str(e)}",
            }

    def _match_or_create_skill(self, skill_data: dict) -> Skill:
        from app.schemas.skills import SkillMatchRequest, SkillCreate

        match_req = SkillMatchRequest(
            phrase=f"{skill_data['name']} {skill_data.get('description', '')}",
            top_k=1,
        )

        matches = self.ontology.match_skill(match_req)

        if matches and matches[0].score > 0.75:
            return self.db.get(Skill, UUID(matches[0].skill.skill_id))

        create_req = SkillCreate(
            name=skill_data["name"],
            description=skill_data.get("description", ""),
            category=skill_data.get("category", "technical"),
            domain=skill_data.get("domain", ""),
            ontology_version="1.0.0",
            is_future_skill=False,
        )

        created = self.ontology.create_skill(create_req)
        return self.db.get(Skill, UUID(created.skill_id))
