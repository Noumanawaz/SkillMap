"""
Service for generating and evaluating dynamic skill assessment tests.
"""
import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import SkillAssessment, EmployeeProfile, Skill
from app.services.llm_service import LLMService
from app.services.cognitive_service import CognitiveService


class AssessmentService:
    """Service for generating and managing skill assessment tests."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = None
        try:
            self.llm = LLMService()
        except Exception as e:
            print(f"⚠️  LLM Service not available for assessments: {e}")
        self.cognitive_service = CognitiveService(db)

    def generate_assessment(
        self,
        employee_id: str,
        skill_id: str,
        skill_name: Optional[str] = None,
        skill_description: Optional[str] = None,
        readiness_score: Optional[float] = None,
        num_questions: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate a dynamic MCQ test for a skill.
        Difficulty is based on readiness_score (0-1) or defaults to moderate.
        """
        if not self.llm:
            raise ValueError("LLM service is required for dynamic test generation")

        # Get skill info if not provided
        if not skill_name or not skill_description:
            skill = self.db.get(Skill, UUID(skill_id))
            if not skill:
                raise ValueError(f"Skill {skill_id} not found")
            skill_name = skill.name
            skill_description = skill.description or ""

        # Determine difficulty based on readiness score
        # readiness_score 0-1 maps to difficulty 1-5
        if readiness_score is None:
            # Check employee's current proficiency
            emp = self.db.get(EmployeeProfile, UUID(employee_id))
            if not emp:
                raise ValueError(f"Employee {employee_id} not found")
            
            cognitive_profile = emp.cognitive_profile or {}
            skill_data = cognitive_profile.get(skill_id, {})
            current_theta = skill_data.get("theta", 0.0)
            # Convert theta (-3 to +3) to readiness (0 to 1)
            readiness_score = max(0.0, min(1.0, (current_theta + 3) / 6))
        
        # Map readiness to difficulty: low readiness = easier questions, high readiness = harder
        # Inverse relationship: readiness 0.0 -> difficulty 1-2, readiness 1.0 -> difficulty 4-5
        base_difficulty = 1.0 + (1.0 - readiness_score) * 3.0  # Range: 1.0 to 4.0
        difficulty_range = f"{max(1, int(base_difficulty - 0.5))}-{min(5, int(base_difficulty + 1.5))}"

        # Generate test using LLM
        system_prompt = """You are an expert assessment designer. Create comprehensive MCQ tests for skill evaluation.
Generate UNIQUE, NON-REPETITIVE questions that test practical knowledge and understanding.

CRITICAL REQUIREMENTS:
- Each question must be UNIQUE - no repetition of concepts or wording
- Vary question types: conceptual, practical application, scenario-based, technical details
- Questions should test real-world understanding, not just memorization
- Each question must have exactly 4 options (A, B, C, D)
- Provide clear, detailed explanations for correct answers
- Difficulty should match the specified range

Return ONLY valid JSON object, no markdown."""

        user_prompt = f"""Create a dynamic MCQ assessment test for the skill:

Skill Name: {skill_name}
Skill Description: {skill_description}
Number of Questions: {num_questions}
Difficulty Level: {difficulty_range} (1=beginner, 5=expert)

Generate {num_questions} UNIQUE questions that:
1. Test practical understanding of {skill_name}
2. Cover different aspects: fundamentals, application, best practices, troubleshooting
3. Vary in question style (conceptual, scenario-based, technical)
4. Match the difficulty range {difficulty_range}
5. Include detailed explanations for each correct answer

Return JSON with this structure:
{{
  "questions": [
    {{
      "question_id": "q1",
      "question": "unique question text",
      "options": [
        {{"option_id": "a", "text": "option A text"}},
        {{"option_id": "b", "text": "option B text"}},
        {{"option_id": "c", "text": "option C text"}},
        {{"option_id": "d", "text": "option D text"}}
      ],
      "correct_answer_id": "a",
      "difficulty": 2.5,
      "explanation": "detailed explanation of why this answer is correct"
    }}
  ],
  "average_difficulty": 2.5
}}

CRITICAL: Ensure ALL questions are UNIQUE and NON-REPETITIVE. Return ONLY valid JSON object."""

        try:
            response = self.llm._call_llm(
                system_prompt,
                user_prompt,
                response_format={"type": "json_object"}
            )
            
            # Clean response
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()
            
            # Find JSON object
            if "{" in response:
                start = response.index("{")
                brace_count = 0
                end = start
                for i in range(start, len(response)):
                    if response[i] == "{":
                        brace_count += 1
                    elif response[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                response = response[start:end]
            
            parsed = json.loads(response)
            questions = parsed.get("questions", [])
            avg_difficulty = parsed.get("average_difficulty", base_difficulty)
            
            # Remove duplicates
            seen_questions = set()
            unique_questions = []
            for q in questions:
                q_text = q.get("question", "").lower().strip()
                if q_text and q_text not in seen_questions:
                    seen_questions.add(q_text)
                    unique_questions.append(q)
            
            if len(unique_questions) < num_questions:
                print(f"⚠️  Generated {len(unique_questions)} unique questions, requested {num_questions}")
            
            # Create assessment record
            assessment = SkillAssessment(
                employee_id=UUID(employee_id),
                skill_id=UUID(skill_id),
                questions=unique_questions,
                difficulty_level=avg_difficulty,
                readiness_score=readiness_score,
                status="pending",
            )
            self.db.add(assessment)
            self.db.commit()
            self.db.refresh(assessment)
            
            return {
                "assessment_id": str(assessment.assessment_id),
                "skill_id": skill_id,
                "skill_name": skill_name,
                "questions": unique_questions,
                "difficulty_level": avg_difficulty,
                "estimated_duration_minutes": len(unique_questions) * 1.5,  # ~1.5 min per question
            }
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed in assessment generation: {e}")
            raise ValueError(f"Failed to generate assessment: Invalid JSON response from AI")
        except Exception as e:
            print(f"Assessment generation failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def submit_assessment(
        self,
        assessment_id: str,
        employee_id: str,
        answers: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Submit answers and calculate proficiency score.
        Updates cognitive profile using IRT.
        """
        assessment = self.db.get(SkillAssessment, UUID(assessment_id))
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        if str(assessment.employee_id) != employee_id:
            raise ValueError("Assessment does not belong to this employee")
        
        if assessment.status == "completed":
            raise ValueError("Assessment already completed")
        
        questions = assessment.questions or []
        if not questions:
            raise ValueError("Assessment has no questions")
        
        # Grade answers
        correct_count = 0
        total_questions = len(questions)
        questions_with_feedback = []
        assessment_items = []  # For IRT update
        
        for q in questions:
            q_id = q.get("question_id", "")
            user_answer = answers.get(q_id, "")
            correct_answer = q.get("correct_answer_id", "")
            difficulty = float(q.get("difficulty", 2.5))
            is_correct = user_answer.lower() == correct_answer.lower()
            
            if is_correct:
                correct_count += 1
            
            # Prepare for IRT update
            assessment_items.append({
                "skill_id": str(assessment.skill_id),
                "difficulty": difficulty,
                "correct": is_correct,
            })
            
            # Prepare feedback
            questions_with_feedback.append({
                "question_id": q_id,
                "question": q.get("question", ""),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": q.get("explanation", ""),
                "difficulty": difficulty,
            })
        
        # Calculate score
        percentage_correct = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Map percentage to proficiency level (0-5 scale)
        # 0-20% = 1.0, 20-40% = 2.0, 40-60% = 3.0, 60-80% = 4.0, 80-100% = 5.0
        if percentage_correct < 20:
            proficiency_score = 1.0
        elif percentage_correct < 40:
            proficiency_score = 2.0
        elif percentage_correct < 60:
            proficiency_score = 3.0
        elif percentage_correct < 80:
            proficiency_score = 4.0
        else:
            proficiency_score = 5.0
        
        # Update cognitive profile using IRT
        try:
            updated_profile = self.cognitive_service.update_profile(
                employee_id,
                assessment_items
            )
            # Get updated skill data
            skill_data = updated_profile.get(str(assessment.skill_id), {})
            updated_theta = skill_data.get("theta", 0.0)
            updated_level = skill_data.get("level", 0.0)
            
            # Use the higher of: assessment-based score or IRT-calculated level
            # This ensures good assessment performance increases skill level
            # If user scores well (e.g., 10/10 = 5.0), use that or the IRT level, whichever is higher
            # If user scores poorly, use IRT which may be lower
            if percentage_correct >= 80:  # Excellent performance (80%+)
                # For excellent scores, use the assessment score or current level, whichever is higher
                # This rewards good performance
                updated_proficiency = max(proficiency_score, updated_level)
            elif percentage_correct >= 60:  # Good performance (60-79%)
                # For good scores, average between assessment and IRT
                updated_proficiency = (proficiency_score + updated_level) / 2
            else:
                # For lower scores, trust IRT more (it accounts for difficulty)
                updated_proficiency = updated_level
            
            # Ensure proficiency is within bounds
            updated_proficiency = max(0.0, min(5.0, updated_proficiency))
            
            # Update the level in the cognitive profile to reflect the assessment result
            skill_data["level"] = updated_proficiency
            updated_profile[str(assessment.skill_id)] = skill_data
            
            # Save the updated profile back
            from app.db.models import EmployeeProfile
            emp = self.db.get(EmployeeProfile, UUID(employee_id))
            if emp:
                emp.cognitive_profile = updated_profile
                self.db.add(emp)
                self.db.commit()
                self.db.refresh(emp)
                
        except Exception as e:
            print(f"Failed to update cognitive profile: {e}")
            import traceback
            traceback.print_exc()
            updated_proficiency = proficiency_score
        
        # Update assessment record
        assessment.answers = answers
        correct_answers_dict = {q.get("question_id"): q.get("correct_answer_id") for q in questions}
        assessment.correct_answers = correct_answers_dict
        assessment.score = proficiency_score
        assessment.status = "completed"
        assessment.completed_at = datetime.utcnow()
        
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        
        return {
            "assessment_id": assessment_id,
            "skill_id": str(assessment.skill_id),
            "skill_name": assessment.skill.name if assessment.skill else "Unknown",
            "score": proficiency_score,
            "percentage_correct": percentage_correct,
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "questions_with_feedback": questions_with_feedback,
            "updated_proficiency": updated_proficiency,
        }

    def get_assessment(self, assessment_id: str, employee_id: str) -> Dict[str, Any]:
        """Get assessment details (without answers if not completed)."""
        assessment = self.db.get(SkillAssessment, UUID(assessment_id))
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")
        
        if str(assessment.employee_id) != employee_id:
            raise ValueError("Assessment does not belong to this employee")
        
        questions = assessment.questions or []
        
        # If not completed, don't show correct answers
        if assessment.status != "completed":
            questions_for_display = []
            for q in questions:
                q_display = {
                    "question_id": q.get("question_id"),
                    "question": q.get("question"),
                    "options": q.get("options", []),
                    "difficulty": q.get("difficulty"),
                }
                questions_for_display.append(q_display)
        else:
            questions_for_display = questions
        
        return {
            "assessment_id": str(assessment.assessment_id),
            "skill_id": str(assessment.skill_id),
            "skill_name": assessment.skill.name if assessment.skill else "Unknown",
            "questions": questions_for_display,
            "difficulty_level": assessment.difficulty_level,
            "status": assessment.status,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        }

    def get_assessment_history(self, employee_id: str, skill_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get assessment history for an employee."""
        query = self.db.query(SkillAssessment).filter(
            SkillAssessment.employee_id == UUID(employee_id)
        )
        
        if skill_id:
            query = query.filter(SkillAssessment.skill_id == UUID(skill_id))
        
        assessments = query.order_by(SkillAssessment.created_at.desc()).all()
        
        return [
            {
                "assessment_id": str(a.assessment_id),
                "skill_id": str(a.skill_id),
                "skill_name": a.skill.name if a.skill else "Unknown",
                "score": a.score,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in assessments
        ]

