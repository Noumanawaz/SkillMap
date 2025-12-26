from datetime import datetime
from typing import Dict, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import EmployeeProfile, Skill, StrategicGoal, StrategicGoalRequiredSkill
from app.vector.base import get_vector_store


class GapEngine:
    """
    Computes scalar gaps and a simple vector-based gap index for individuals and teams.
    Current skill levels are read from EmployeeProfile.cognitive_profile["level"] when present,
    otherwise default to 0.
    """

    def __init__(self, db: Session):
        self.db = db
        self.vectors = get_vector_store()
        # Initialize LLM service only if OpenAI API key is available
        self.llm = None
        try:
            from app.services.llm_service import LLMService
            from app.core.config import get_settings
            import os
            
            # Get settings and check environment
            settings = get_settings()
            env_key = os.getenv("OPENAI_API_KEY")
            
            # Check if API key is configured
            api_key = settings.openai_api_key or env_key
            
            if not api_key:
                print("⚠️  OPENAI_API_KEY not found in settings or environment variables.")
                print(f"   Settings openai_api_key: {'Set' if settings.openai_api_key else 'Not set'}")
                print(f"   Environment OPENAI_API_KEY: {'Set' if env_key else 'Not set'}")
                print("   AI features will be disabled.")
                self.llm = None
            elif not api_key.startswith("sk-"):
                print(f"⚠️  OPENAI_API_KEY appears invalid (should start with 'sk-'). Found: {api_key[:10]}...")
                self.llm = None
            else:
                try:
                    self.llm = LLMService()
                    print(f"✅ LLM Service initialized successfully (model: {settings.openai_model})")
                    print(f"   API Key: {api_key[:7]}...{api_key[-4:]}")
                except ValueError as ve:
                    print(f"❌ LLM Service ValueError: {ve}")
                    self.llm = None
                except Exception as init_error:
                    print(f"❌ Failed to initialize LLM Service: {type(init_error).__name__}: {init_error}")
                    import traceback
                    traceback.print_exc()
                    self.llm = None
        except ImportError as import_error:
            print(f"❌ Failed to import LLMService: {import_error}")
            import traceback
            traceback.print_exc()
            self.llm = None
        except Exception as e:
            print(f"❌ Unexpected error initializing LLM: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.llm = None

    def _current_skill_level(self, emp: EmployeeProfile, skill_id: str) -> float:
        profile = emp.cognitive_profile or {}
        skill_state = profile.get(skill_id, {})
        return float(skill_state.get("level", skill_state.get("theta", 0.0)))

    def _required_skills(self, goal_id: str) -> List[StrategicGoalRequiredSkill]:
        return (
            self.db.query(StrategicGoalRequiredSkill)
            .filter(StrategicGoalRequiredSkill.goal_id == UUID(goal_id))
            .all()
        )

    def _bundle_embedding(self, skill_ids: List[str], weights: List[float]) -> List[float]:
        import numpy as np

        vectors = []
        for sid, w in zip(skill_ids, weights):
            v = self.vectors.fetch(sid)
            if v is None:
                continue
            vectors.append(w * np.array(v, dtype=float))
        if not vectors:
            return []
        arr = sum(vectors)
        return (arr / (sum(weights) + 1e-8)).tolist()

    def _similarity(self, a: List[float], b: List[float]) -> float:
        import numpy as np

        if not a or not b:
            return 0.0
        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        denom = (np.linalg.norm(va) * np.linalg.norm(vb)) + 1e-8
        return float((va @ vb) / denom)

    def gaps_for_employee(self, employee_id: str, goal_id: str) -> Dict:
        """
        Compute skill gaps for an employee against a strategic goal.
        This performs the full cognitive AI analysis:
        1. Fetches required skills for the goal (or extracts them if missing)
        2. Retrieves employee's current cognitive profile
        3. Calculates scalar gaps (required_level - current_level)
        4. Computes vector similarity between employee and required skill profiles
        5. Generates gap index (overall gap severity)
        """
        emp = self.db.get(EmployeeProfile, UUID(employee_id))
        if not emp:
            raise ValueError("Employee not found")
        goal = self.db.get(StrategicGoal, UUID(goal_id))
        if not goal:
            raise ValueError("Goal not found")

        # Step 1: Get required skills for the goal
        req_skills = self._required_skills(goal_id)
        
        # Step 2: Auto-extract skills if none exist and LLM is available
        skills_extracted = False
        if not req_skills:
            try:
                from app.services.skill_extraction_service import SkillExtractionService
                extraction_service = SkillExtractionService(self.db)
                if not extraction_service.llm:
                    return {
                        "employee_id": str(emp.employee_id),
                        "goal_id": str(goal.goal_id),
                        "scalar_gaps": {},
                        "skill_names": {},
                        "similarity": 0.0,
                        "gap_index": 0.0,
                        "processing_info": {
                            "skills_analyzed": 0,
                            "skills_extracted": False,
                            "employee_skills_found": 0,
                            "total_gaps": 0,
                            "critical_gaps": 0,
                        },
                        "message": "No skills extracted for this goal. Please extract skills first using the Strategy Dashboard. OpenAI API key may not be configured.",
                    }
                # Try to extract skills using LLM
                try:
                    extraction_service.extract_skills_for_goal(goal_id)
                    req_skills = self._required_skills(goal_id)
                    skills_extracted = len(req_skills) > 0
                except Exception as extract_error:
                    # Extraction failed, return error
                    return {
                        "employee_id": str(emp.employee_id),
                        "goal_id": str(goal.goal_id),
                        "scalar_gaps": {},
                        "skill_names": {},
                        "similarity": 0.0,
                        "gap_index": 0.0,
                        "message": f"Failed to extract skills: {str(extract_error)}. Please try extracting skills manually from the Strategy Dashboard.",
                    }
                
                # If still no skills after extraction, return message
                if not req_skills:
                    return {
                        "employee_id": str(emp.employee_id),
                        "goal_id": str(goal.goal_id),
                        "scalar_gaps": {},
                        "skill_names": {},
                        "similarity": 0.0,
                        "gap_index": 0.0,
                        "processing_info": {
                            "skills_analyzed": 0,
                            "skills_extracted": True,
                            "employee_skills_found": 0,
                            "total_gaps": 0,
                            "critical_gaps": 0,
                        },
                        "message": "No skills could be extracted for this goal. Please try extracting skills manually from the Strategy Dashboard.",
                    }
            except ValueError as e:
                # LLM service not available
                return {
                    "employee_id": str(emp.employee_id),
                    "goal_id": str(goal.goal_id),
                    "scalar_gaps": {},
                    "skill_names": {},
                    "similarity": 0.0,
                    "gap_index": 0.0,
                    "processing_info": {
                        "skills_analyzed": 0,
                        "skills_extracted": False,
                        "employee_skills_found": 0,
                        "total_gaps": 0,
                        "critical_gaps": 0,
                    },
                    "message": "No skills extracted for this goal. Please extract skills first using the Strategy Dashboard. OpenAI API key may not be configured.",
                }
            except Exception as e:
                # Other extraction errors
                return {
                    "employee_id": str(emp.employee_id),
                    "goal_id": str(goal.goal_id),
                    "scalar_gaps": {},
                    "skill_names": {},
                    "similarity": 0.0,
                    "gap_index": 0.0,
                    "processing_info": {
                        "skills_analyzed": 0,
                        "skills_extracted": False,
                        "employee_skills_found": 0,
                        "total_gaps": 0,
                        "critical_gaps": 0,
                    },
                    "message": f"No skills extracted for this goal. Error: {str(e)}. Please try extracting skills manually from the Strategy Dashboard.",
                }
        
        # Step 3: Prepare data for AI analysis FIRST (prioritize AI over exact matching)
        profile = emp.cognitive_profile or {}
        
        # Build comprehensive employee skills list for AI
        employee_skills_for_ai = []
        employee_skill_name_map: Dict[str, str] = {}  # skill_name -> skill_id in employee profile
        for emp_skill_id, emp_skill_data in profile.items():
            try:
                emp_skill = self.db.get(Skill, UUID(emp_skill_id))
                if emp_skill:
                    level = emp_skill_data.get("level", 0.0)
                    if level == 0.0 and "theta" in emp_skill_data:
                        theta = emp_skill_data.get("theta", 0.0)
                        level = max(1, min(5, int((theta + 3) * 5 / 6) + 1))
                    employee_skills_for_ai.append({
                        "name": emp_skill.name,
                        "proficiency_level": float(level),
                        "domain": emp_skill.domain or "",
                        "category": emp_skill.category or "",
                    })
                    # Normalize skill name for matching (lowercase, strip)
                    normalized_name = emp_skill.name.lower().strip()
                    employee_skill_name_map[normalized_name] = emp_skill_id
            except (ValueError, TypeError):
                continue
        
        # Build required skills list for AI
        required_skills_for_ai = []
        required_levels: Dict[str, float] = {}
        weights: List[float] = []
        skill_ids: List[str] = []

        for rs in req_skills:
            skill = self.db.get(Skill, rs.skill_id)
            if skill:
                sid = str(rs.skill_id)
                required_levels[sid] = float(rs.target_level)
                w = float(rs.importance_weight or 1.0)
                weights.append(w)
                skill_ids.append(sid)
                required_skills_for_ai.append({
                    "name": skill.name,
                    "target_level": float(rs.target_level),
                    "domain": skill.domain or "",
                    "category": skill.category or "",
                    "importance_weight": float(rs.importance_weight or 1.0),
                })

        # Step 4: Use AI to intelligently analyze ALL gaps (AI is REQUIRED, NO FALLBACK)
        ai_gap_analysis = None
        current_levels: Dict[str, float] = {}
        ai_processed_all_skills = False
        
        # REQUIRE AI - no fallback to keyword matching
        if not self.llm:
            return {
                "employee_id": str(emp.employee_id),
                "goal_id": str(goal.goal_id),
                "scalar_gaps": {},
                "skill_names": {},
                "similarity": 0.0,
                "gap_index": 0.0,
                "processing_info": {
                    "skills_analyzed": 0,
                    "skills_extracted": skills_extracted,
                    "employee_skills_found": 0,
                    "total_gaps": 0,
                    "critical_gaps": 0,
                    "ai_analysis_used": False,
                    "ai_processing_method": "ai_required_but_not_available",
                },
                "message": "AI-powered gap analysis is required but OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file to enable AI features.",
            }
        
        # If AI is available, use it to process ALL skills - no keyword matching
        if employee_skills_for_ai and required_skills_for_ai:
            try:
                # Get AI gap analysis with employee context - AI processes EVERYTHING
                ai_gap_analysis = self.llm.analyze_skill_gaps(
                    employee_skills_for_ai,
                    required_skills_for_ai,
                    goal.title,
                    goal.description or "",
                    emp.name,
                    emp.description or "",
                )
                
                if ai_gap_analysis:
                    # Initialize all current_levels to 0 first
                    for rs in req_skills:
                        sid = str(rs.skill_id)
                        current_levels[sid] = 0.0
                    
                    # Process AI matches - AI determines employee levels for matched skills
                    if ai_gap_analysis.get("skill_matches"):
                        for match in ai_gap_analysis["skill_matches"]:
                            req_skill_name = match.get("required_skill", "")
                            match_confidence = match.get("match_confidence", 0.5)
                            
                            # Trust AI matches with any confidence (AI is smart, trust it)
                            if match_confidence >= 0.1:  # Very low threshold - trust AI
                                # Find the required skill_id for this match
                                for rs in req_skills:
                                    skill = self.db.get(Skill, rs.skill_id)
                                    if skill and skill.name == req_skill_name:
                                        req_sid = str(rs.skill_id)
                                        # AI gap_value is already calculated as required - employee
                                        ai_gap = match.get("gap_value", 0.0)
                                        # Calculate employee level from gap: required - gap = employee
                                        emp_level = max(0.0, required_levels[req_sid] - ai_gap)
                                        current_levels[req_sid] = emp_level
                                        break
                    
                    # For skills not in AI matches, AI has determined they are missing
                    # The missing_skills list tells us which ones AI identified as truly missing
                    # For those, current_level stays 0.0 (already initialized above)
                    
                    ai_processed_all_skills = True
                    print(f"AI processed {len(required_skills_for_ai)} skills using semantic understanding")
                    
            except Exception as e:
                print(f"❌ AI gap analysis failed: {e}")
                import traceback
                traceback.print_exc()
                ai_gap_analysis = None
                ai_processed_all_skills = False
        
        # Step 5: NO FALLBACK - AI is required
        if not ai_processed_all_skills:
            # AI failed to process - return error instead of falling back
            return {
                "employee_id": str(emp.employee_id),
                "goal_id": str(goal.goal_id),
                "scalar_gaps": {},
                "skill_names": {},
                "similarity": 0.0,
                "gap_index": 0.0,
                "processing_info": {
                    "skills_analyzed": len(skill_ids),
                    "skills_extracted": skills_extracted,
                    "employee_skills_found": 0,
                    "total_gaps": 0,
                    "critical_gaps": 0,
                    "ai_analysis_used": False,
                    "ai_processing_method": "ai_analysis_failed",
                },
                "message": "AI-powered gap analysis failed. Please check your OpenAI API key configuration and ensure the API is accessible.",
            }

        # Step 6: Calculate scalar gaps based on AI analysis (or keyword matching if AI unavailable)
        # If AI processed everything, use AI's gap values directly
        scalar_gaps = {}
        
        if ai_processed_all_skills and ai_gap_analysis:
            # Use AI's analysis for all skills
            # First, get gaps from matches
            for match in ai_gap_analysis.get("skill_matches", []):
                req_skill_name = match.get("required_skill", "")
                ai_gap = match.get("gap_value", 0.0)
                # Find the skill_id for this required skill
                for rs in req_skills:
                    skill = self.db.get(Skill, rs.skill_id)
                    if skill and skill.name == req_skill_name:
                        sid = str(rs.skill_id)
                        scalar_gaps[sid] = max(0.0, ai_gap)
                        break
            
            # Then, add gaps from missing skills (AI identified as truly missing)
            for missing in ai_gap_analysis.get("missing_skills", []):
                req_skill_name = missing.get("required_skill", "")
                ai_gap = missing.get("gap_value", 0.0)
                # Find the skill_id for this required skill
                for rs in req_skills:
                    skill = self.db.get(Skill, rs.skill_id)
                    if skill and skill.name == req_skill_name:
                        sid = str(rs.skill_id)
                        # Use AI's gap value (it's already calculated correctly)
                        scalar_gaps[sid] = max(0.0, ai_gap)
                        break
            
            # Ensure all required skills have a gap value (even if AI didn't explicitly mention them)
            for sid in required_levels:
                if sid not in scalar_gaps:
                    # Calculate from current_levels (which AI set)
                    scalar_gaps[sid] = max(0.0, required_levels[sid] - current_levels.get(sid, 0.0))
        else:
            # This should never happen if AI is required, but handle gracefully
            return {
                "employee_id": str(emp.employee_id),
                "goal_id": str(goal.goal_id),
                "scalar_gaps": {},
                "skill_names": {},
                "similarity": 0.0,
                "gap_index": 0.0,
                "processing_info": {
                    "skills_analyzed": len(skill_ids),
                    "skills_extracted": skills_extracted,
                    "employee_skills_found": 0,
                    "total_gaps": 0,
                    "critical_gaps": 0,
                    "ai_analysis_used": False,
                    "ai_processing_method": "ai_required_but_failed",
                },
                "message": "AI-powered gap analysis is required but failed. No fallback available. Please ensure OpenAI API is properly configured and accessible.",
            }

        # Fetch skill names for all skill IDs
        skill_names = {}
        for sid in skill_ids:
            skill = self.db.get(Skill, UUID(sid))
            if skill:
                skill_names[sid] = skill.name
            else:
                skill_names[sid] = f"Unknown Skill ({sid[:8]}...)"

        # Step 6: Compute vector-based similarity using semantic embeddings
        # Employee embedding: weighted average of skill vectors by current proficiency
        emp_weights = [current_levels.get(sid, 0.0) for sid in skill_ids]
        emp_vec = self._bundle_embedding(skill_ids, emp_weights)
        # Required embedding: weighted average by importance
        req_vec = self._bundle_embedding(skill_ids, weights)
        # Cosine similarity between employee and required profiles
        similarity = self._similarity(emp_vec, req_vec) if emp_vec and req_vec else 0.0
        
        # Step 7: Calculate gap index (overall severity)
        # Combines vector similarity (1 - similarity) with average scalar gap
        avg_gap = sum(scalar_gaps.values()) / (len(scalar_gaps) + 1e-8) if scalar_gaps else 0.0
        gap_index = (1.0 - similarity) + avg_gap

        # Count employee skills found (including name-based and AI matches)
        employee_skills_found = len([sid for sid in skill_ids if current_levels.get(sid, 0.0) > 0])
        
        # Prepare AI insights for response with detailed explanations
        ai_insights = None
        
        if ai_gap_analysis:
            overall_assessment = ai_gap_analysis.get("overall_assessment", {})
            
            # Build detailed gap breakdown from AI analysis
            gap_breakdown = ai_gap_analysis.get("gap_breakdown", [])
            if not gap_breakdown:
                # Build gap breakdown from matches and missing skills
                for match in ai_gap_analysis.get("skill_matches", []):
                    req_skill_name = match.get("required_skill", "")
                    gap_val = match.get("gap_value", 0.0)
                    if gap_val > 0:
                        # Find required level
                        req_level = 0.0
                        for rs in req_skills:
                            skill = self.db.get(Skill, rs.skill_id)
                            if skill and skill.name == req_skill_name:
                                req_level = float(rs.target_level)
                                break
                        gap_breakdown.append({
                            "skill_name": req_skill_name,
                            "current_level": max(0.0, req_level - gap_val),
                            "required_level": req_level,
                            "gap_value": gap_val,
                            "severity": "critical" if gap_val >= 3 else "high" if gap_val >= 2 else "moderate" if gap_val >= 1 else "low",
                            "explanation": match.get("explanation", f"Gap of {gap_val:.1f} levels between current and required proficiency."),
                        })
                
                for missing in ai_gap_analysis.get("missing_skills", []):
                    req_skill_name = missing.get("required_skill", "")
                    gap_val = missing.get("gap_value", 0.0)
                    # Find required level
                    req_level = 0.0
                    for rs in req_skills:
                        skill = self.db.get(Skill, rs.skill_id)
                        if skill and skill.name == req_skill_name:
                            req_level = float(rs.target_level)
                            break
                    gap_breakdown.append({
                        "skill_name": req_skill_name,
                        "current_level": 0.0,
                        "required_level": req_level,
                        "gap_value": gap_val,
                        "severity": missing.get("severity", "critical" if gap_val >= 3 else "high"),
                        "explanation": missing.get("detailed_explanation", missing.get("reason", f"Skill is missing and required at level {req_level:.1f}.")),
                    })
            
            # Ensure all required skills are in the breakdown (even if no gap)
            existing_skill_names = {g.get("skill_name") for g in gap_breakdown}
            for rs in req_skills:
                skill = self.db.get(Skill, rs.skill_id)
                if skill and skill.name not in existing_skill_names:
                    sid = str(rs.skill_id)
                    current_lvl = current_levels.get(sid, 0.0)
                    req_lvl = float(rs.target_level)
                    gap_val = max(0.0, req_lvl - current_lvl)
                    if gap_val > 0:
                        gap_breakdown.append({
                            "skill_name": skill.name,
                            "current_level": current_lvl,
                            "required_level": req_lvl,
                            "gap_value": gap_val,
                            "severity": "critical" if gap_val >= 3 else "high" if gap_val >= 2 else "moderate" if gap_val >= 1 else "low",
                            "explanation": f"Gap of {gap_val:.1f} levels between current proficiency ({current_lvl:.1f}/5) and required level ({req_lvl:.1f}/5).",
                        })
            
            # Sort by severity and gap value
            gap_breakdown.sort(key=lambda x: (
                {"critical": 0, "high": 1, "moderate": 2, "low": 3}.get(x.get("severity", "low"), 3),
                -x.get("gap_value", 0.0)
            ))
            
            ai_insights = {
                "readiness_score": overall_assessment.get("readiness_score", 0.0),
                "summary": overall_assessment.get("summary", ""),
                "detailed_report": overall_assessment.get("detailed_report", ""),
                "key_gaps": overall_assessment.get("key_gaps", []),
                "matches_found": len(ai_gap_analysis.get("skill_matches", [])),
                "missing_skills_count": len(ai_gap_analysis.get("missing_skills", [])),
                "gap_breakdown": gap_breakdown,
            }
        
        # Return comprehensive gap analysis results
        return {
            "employee_id": str(emp.employee_id),
            "goal_id": str(goal.goal_id),
            "scalar_gaps": scalar_gaps,
            "skill_names": skill_names,
            "similarity": similarity,
            "gap_index": gap_index,
            "ai_insights": ai_insights,  # Add AI-powered insights
            "processing_info": {
                "skills_analyzed": len(skill_ids),
                "skills_extracted": skills_extracted,
                "employee_skills_found": employee_skills_found,
                "total_gaps": len([g for g in scalar_gaps.values() if g > 0]),
                "critical_gaps": len([g for g in scalar_gaps.values() if g >= 3.0]),
                "ai_analysis_used": ai_processed_all_skills,
                "ai_processing_method": "semantic_understanding" if ai_processed_all_skills else "keyword_matching_fallback",
            },
        }

    def gaps_for_team(self, manager_id: str, goal_id: str) -> Dict:
        members = self.db.query(EmployeeProfile).filter(
            EmployeeProfile.manager_id == UUID(manager_id)
        ).all()
        indiv = [self.gaps_for_employee(str(m.employee_id), goal_id) for m in members]
        if not indiv:
            return {"team_size": 0, "members": [], "avg_gap_index": 0.0}
        avg_gap_index = sum(i["gap_index"] for i in indiv) / len(indiv)
        return {"team_size": len(indiv), "members": indiv, "avg_gap_index": avg_gap_index}


