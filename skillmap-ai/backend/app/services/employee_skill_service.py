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
            error_msg = "OpenAI API key not configured. Skills cannot be extracted automatically."
            print(f"❌ {error_msg}")
            return {
                "extracted_skills": 0,
                "message": error_msg,
            }

        try:
            print(f"🔍 Starting skill extraction for employee {employee_id}...")
            print(f"   Description length: {len(description)} characters")
            # Get existing skills for context
            existing_skills = self.db.query(Skill).limit(100).all()
            skills_context = [
                {"name": s.name, "description": s.description or ""} for s in existing_skills
            ]

            # Extract skills using LLM
            print(f"   Calling LLM to extract skills...")
            extracted_skills_data = self.llm.extract_skills_from_description(
                description, skills_context
            )
            print(f"   LLM returned {len(extracted_skills_data) if extracted_skills_data else 0} skills")

            if not extracted_skills_data:
                error_msg = "No skills could be extracted from the description. The LLM did not return any skills."
                print(f"⚠️  {error_msg}")
                return {
                    "extracted_skills": 0,
                    "message": error_msg,
                }

            # Get employee
            emp = self.db.get(EmployeeProfile, UUID(employee_id))
            if not emp:
                raise ValueError("Employee not found")

            # Get or initialize cognitive profile
            profile = emp.cognitive_profile or {}

            # Match or create skills and add to profile
            matched_count = 0
            for idx, skill_data in enumerate(extracted_skills_data, 1):
                try:
                    skill_name = skill_data.get("name", "Unknown")
                    print(f"   Processing skill {idx}/{len(extracted_skills_data)}: {skill_name}")
                    
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
                            print(f"      ✅ Added skill: {matched_skill.name} (level {proficiency})")
                        else:
                            # Update level if higher
                            current_level = profile[skill_id].get("level", 0)
                            if proficiency > current_level:
                                profile[skill_id]["level"] = float(proficiency)
                                profile[skill_id]["theta"] = float(proficiency - 3) * 0.5
                                print(f"      ✅ Updated skill: {matched_skill.name} (level {proficiency})")
                            else:
                                print(f"      ℹ️  Skill already exists: {matched_skill.name} (current level {current_level})")
                        matched_count += 1
                    else:
                        print(f"      ⚠️  Failed to match or create skill: {skill_name}")
                except Exception as skill_error:
                    print(f"      ❌ Error processing skill {skill_name}: {skill_error}")
                    import traceback
                    traceback.print_exc()
                    continue

            # Update employee profile
            if matched_count > 0:
                emp.cognitive_profile = profile
                self.db.add(emp)
                self.db.commit()
                self.db.refresh(emp)
                print(f"✅ Successfully stored {matched_count} skill(s) in cognitive profile")
            else:
                print(f"⚠️  No skills were stored (matched_count: {matched_count})")

            return {
                "extracted_skills": matched_count,
                "message": f"Successfully extracted and stored {matched_count} skill(s) from description.",
            }

        except Exception as e:
            error_msg = f"Failed to extract skills: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "extracted_skills": 0,
                "message": error_msg,
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

