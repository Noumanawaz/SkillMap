from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile, LearningModule, Skill, StrategicGoal
from app.services.gap_engine import GapEngine
from app.services.llm_service import LLMService


class RecommenderService:
    """
    Personalized learning path generator with on-demand LLM content generation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.gap_engine = GapEngine(db)
        try:
            self.llm = LLMService()
        except ValueError:
            self.llm = None

    def generate_learning_path(
        self, employee_id: str, goal_id: str, max_hours: float = 40.0
    ) -> Dict[str, Any]:
        emp = self.db.get(EmployeeProfile, UUID(employee_id))
        if not emp:
            raise ValueError("Employee not found")
        goal = self.db.get(StrategicGoal, UUID(goal_id))
        if not goal:
            raise ValueError("Goal not found")

        # Access goal attributes before any operations that might cause rollback
        goal_time_horizon = goal.time_horizon_year
        current_year = datetime.utcnow().year
        years_left = max(0.5, (goal_time_horizon or current_year + 3) - current_year) if goal_time_horizon else None

        gaps = self.gap_engine.gaps_for_employee(employee_id, goal_id)
        scalar_gaps = gaps.get("scalar_gaps", {})
        
        # If no skills extracted, return empty path with message
        if not scalar_gaps:
            error_message = gaps.get("message", "No skills extracted for this goal. Please extract skills first.")
            return {
                "employee_id": employee_id,
                "goal_id": goal_id,
                "items": [],
                "total_hours": 0.0,
                "meta": {
                    "similarity": gaps.get("similarity", 0.0),
                    "gap_index": gaps.get("gap_index", 0.0),
                    "message": error_message,
                    "years_left": years_left,
                },
            }

        skills_sorted = sorted(
            scalar_gaps.items(), key=lambda kv: kv[1], reverse=True
        )  # highest gap first

        total_minutes = 0
        path_items: List[Dict[str, Any]] = []
        added_module_ids = set()  # Track which modules have been added to prevent duplicates

        profile = emp.cognitive_profile or {}

        # Continue adding modules until max_hours is reached or all gaps are closed
        max_hours_minutes = max_hours * 60
        iterations_without_progress = 0
        max_iterations = len(skills_sorted) * 10  # Safety limit to prevent infinite loops
        
        # Track generated modules per skill to prevent repetition
        skill_module_counts = {}
        for skill_id, gap in scalar_gaps.items():
            # Estimate total modules needed (gap / 0.5)
            skill_module_counts[skill_id] = {
                "current": 0,
                "total": max(1, int(gap / 0.5))
            }

        iteration = 0
        while total_minutes < max_hours_minutes and iteration < max_iterations:
            iteration += 1
            
            # Re-sort skills by remaining gap to prioritize skills with larger gaps
            skills_sorted = sorted(
                [(sid, gap) for sid, gap in skills_sorted if gap > 0],
                key=lambda kv: kv[1], reverse=True
            )
            
            if not skills_sorted:
                break  # No more gaps to fill
            
            skill_id, gap_val = skills_sorted[0]
            
            # Skip skills with no gap
            if gap_val <= 0:
                skills_sorted = skills_sorted[1:]
                continue
            
            state = profile.get(skill_id, {})
            theta = float(state.get("theta", 0.0))
            current_level = float(state.get("level", theta))
            target_level = min(5, max(1, int(current_level + gap_val)))

            # Try to find existing modules (excluding already added ones)
            all_modules = self.db.query(LearningModule).all()
            modules = [
                m for m in all_modules
                if str(m.module_id) not in added_module_ids
                and m.skills 
                and (skill_id in [str(s) for s in m.skills] if isinstance(m.skills, list) else str(skill_id) in str(m.skills))
            ]
            modules.sort(key=lambda m: m.difficulty_level or 999)
            
            # If no modules exist, generate one on-demand
            if not modules and self.llm:
                skill = self.db.get(Skill, UUID(skill_id))
                if skill:
                    # Increment current module index for this skill
                    counts = skill_module_counts.get(skill_id, {"current": 0, "total": 1})
                    counts["current"] += 1
                    
                    module = self._generate_module_for_skill(
                        skill, 
                        target_level, 
                        theta, 
                        profile, 
                        employee_id,
                        module_index=counts["current"],
                        total_modules=counts["total"]
                    )
                    if module and str(module.module_id) not in added_module_ids:
                        modules = [module]

            # If still no modules, try module_metadata fallback
            if not modules:
                # Query all modules and filter in Python (cross-database compatible)
                all_fallback_modules = self.db.query(LearningModule).all()
                fallback_modules = [
                    m for m in all_fallback_modules
                    if m.module_metadata
                    and m.module_metadata.get("skill_id") == skill_id
                    and str(m.module_id) not in added_module_ids
                ]
                modules = fallback_modules

            # Try to add modules for this skill
            module_added = False
            for m in modules:
                # Skip if already added
                if str(m.module_id) in added_module_ids:
                    continue
                
                # Calculate real duration
                module_duration = self._calculate_module_duration(m, target_level, gap_val)
                
                # Check if adding this module would exceed max_hours
                remaining_minutes = max_hours_minutes - total_minutes
                if module_duration > remaining_minutes:
                    # Try to fit a partial module if there's enough time
                    if remaining_minutes >= 15:  # Minimum viable module duration
                        module_duration = remaining_minutes
                    else:
                        # Not enough time, move to next skill
                        break
                
                path_items.append(
                    {
                        "skill_id": skill_id,
                        "module_id": str(m.module_id),
                        "title": m.title,
                        "description": m.description,
                        "order": len(path_items) + 1,
                        "expected_gain": min(gap_val, 0.5),
                        "duration_minutes": int(module_duration),
                        "is_generated": m.is_generated,
                    }
                )
                added_module_ids.add(str(m.module_id))
                total_minutes += module_duration
                gap_val -= 0.5
                module_added = True
                
                # Update the gap value in the sorted list
                skills_sorted[0] = (skill_id, gap_val)
                
                # Stop if we've reached max hours
                if total_minutes >= max_hours_minutes:
                    break
                
                # If gap is closed, move to next skill
                if gap_val <= 0:
                    skills_sorted = skills_sorted[1:]
                    break
            
            # If no module was added for this skill, remove it from consideration
            if not module_added:
                skills_sorted = skills_sorted[1:]
                iterations_without_progress += 1
                if iterations_without_progress > len(skills_sorted):
                    break  # No progress made, exit
            else:
                iterations_without_progress = 0

        # If no items were generated, provide a clear reason in meta
        meta_message: Optional[str] = None
        if not path_items:
            # Check if there are still gaps according to the gap engine
            has_gaps = any(gap > 0 for gap in scalar_gaps.values())
            if has_gaps:
                meta_message = (
                    "AI identified skill gaps for this employee, but no learning modules could be "
                    "matched or generated. Please add or tag learning modules for the required skills "
                    "or ensure your OpenAI key is configured so SkillMap AI can generate modules on-demand."
                )
            else:
                meta_message = (
                    "AI analysis indicates the employee already meets the required skill levels "
                    "for this goal. No learning items are needed."
                )

        return {
            "employee_id": employee_id,
            "goal_id": goal_id,
            "items": path_items,
            "total_hours": round(total_minutes / 60.0, 2),  # Round to 2 decimal places
            "meta": {
                "similarity": gaps["similarity"],
                "gap_index": gaps["gap_index"],
                "years_left": years_left,
                "max_hours_requested": max_hours,
                "utilization_percent": round((total_minutes / (max_hours * 60)) * 100, 1) if max_hours > 0 else 0,
                "message": meta_message,
            },
        }

    def _generate_module_for_skill(
        self, 
        skill: Skill, 
        target_level: int, 
        theta: float, 
        profile: Dict, 
        employee_id: Optional[str] = None,
        module_index: int = 1,
        total_modules: int = 1
    ) -> Optional[LearningModule]:
        """Generate a learning module on-demand using LLM."""
        if not self.llm:
            return None

        try:
            # Get employee email for demo mode
            user_email = None
            if employee_id:
                try:
                    emp = self.db.get(EmployeeProfile, UUID(employee_id))
                    user_email = emp.email if emp else None
                except:
                    pass
            
            # Determine learning style from profile (simple heuristic)
            learning_style = profile.get("learning_style", "balanced")
            
            # Generate content
            content = self.llm.generate_learning_content(
                skill.name,
                skill.description or "",
                target_level,
                theta,
                learning_style,
                module_index=module_index,
                total_modules=total_modules,
                user_email=user_email
            )

            # Calculate realistic duration based on content, exercises, and target level
            content_text = content.get("content", "")
            content_length = len(content_text)
            exercises_count = len(content.get("exercises", []))
            assessment_count = len(content.get("assessment", []))
            
            # Base duration: reading time (average 200 words per minute, ~5 chars per word)
            # For technical content, reading is slower - use 150 wpm
            word_count = content_length / 5
            reading_time = word_count / 150  # minutes at 150 wpm for technical content
            
            # Exercise time: scales with target level
            # Level 1-2: 5-8 min, Level 3: 10-12 min, Level 4-5: 15-20 min per exercise
            exercise_time_per_item = 5 + (target_level * 2.5)
            exercise_time = exercises_count * exercise_time_per_item
            
            # Assessment time: 3-7 minutes per question depending on level
            assessment_time_per_item = 3 + (target_level * 0.8)
            assessment_time = assessment_count * assessment_time_per_item
            
            # Add buffer for comprehension, note-taking, and practice
            # Higher levels need more time for deep understanding
            comprehension_buffer = reading_time * (0.2 + target_level * 0.1)  # 20-70% buffer
            
            # Total duration with realistic estimates
            duration = reading_time + exercise_time + assessment_time + comprehension_buffer
            
            # Clamp to reasonable bounds based on target level
            # Level 1: 20-45 min, Level 2: 30-60 min, Level 3: 45-90 min, Level 4: 60-120 min, Level 5: 90-180 min
            min_duration = 15 + (target_level * 10)
            max_duration = 45 + (target_level * 30)
            duration = max(min_duration, min(max_duration, int(duration)))

            # Create module
            module = LearningModule(
                title=content["title"],
                description=content.get("description", ""),
                provider="SkillMap AI (Generated)",
                format="micro_lesson",
                duration_minutes=duration,
                difficulty_level=target_level,
                skills=[str(skill.skill_id)],  # JSON stores as strings
                module_metadata={
                    "content": content.get("content", ""),
                    "exercises": content.get("exercises", []),
                    "assessment": content.get("assessment", []),
                    "skill_id": str(skill.skill_id),
                    "generated_for_theta": theta,
                },
                is_generated=True,
            )
            self.db.add(module)
            self.db.commit()
            self.db.refresh(module)
            return module
        except Exception as e:
            print(f"Failed to generate module: {e}")
            return None

    def _calculate_module_duration(
        self, module: LearningModule, target_level: int, gap_val: float
    ) -> float:
        """
        Calculate realistic duration for a learning module.
        Uses actual duration if available, otherwise estimates based on content.
        """
        # If module has explicit duration, use it
        if module.duration_minutes:
            return float(module.duration_minutes)
        
        # For generated modules, check metadata for content
        if module.module_metadata:
            content = module.module_metadata.get("content", "")
            exercises = module.module_metadata.get("exercises", [])
            assessment = module.module_metadata.get("assessment", [])
            
            if content:
                # Calculate based on content length (same logic as generation)
                content_length = len(content)
                word_count = content_length / 5
                reading_time = word_count / 150  # 150 wpm for technical content
                
                exercise_time_per_item = 5 + (target_level * 2.5)
                exercise_time = len(exercises) * exercise_time_per_item
                
                assessment_time_per_item = 3 + (target_level * 0.8)
                assessment_time = len(assessment) * assessment_time_per_item
                
                comprehension_buffer = reading_time * (0.2 + target_level * 0.1)
                
                duration = reading_time + exercise_time + assessment_time + comprehension_buffer
                min_duration = 15 + (target_level * 10)
                max_duration = 45 + (target_level * 30)
                return max(min_duration, min(max_duration, duration))
        
        # Fallback: estimate based on difficulty level and gap
        # Higher difficulty and larger gaps need more time
        base_duration = 20 + (target_level * 10)  # 30-70 minutes base
        gap_multiplier = 1.0 + (gap_val * 0.2)  # Up to 20% more for larger gaps
        estimated = base_duration * gap_multiplier
        # Clamp to reasonable bounds
        min_duration = 15 + (target_level * 10)
        max_duration = 45 + (target_level * 30)
        return max(min_duration, min(max_duration, estimated))


