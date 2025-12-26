"""
LLM service using OpenAI GPT-3.5 for strategy extraction, skill inference, and content generation.
"""
import json
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.core.config import get_settings


class LLMService:
    """Service for interacting with OpenAI GPT-3.5 API."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        try:
            # Initialize OpenAI client with explicit api_key parameter
            # OpenAI v2.x supports this directly
            self.client = OpenAI(api_key=self.settings.openai_api_key)
        except ImportError as import_error:
            raise ValueError(f"OpenAI library not installed: {import_error}")
        except TypeError as type_error:
            error_msg = str(type_error)
            # If there's still an issue, try using environment variable
            import os
            original_key = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = self.settings.openai_api_key
            try:
                self.client = OpenAI()
            finally:
                if original_key is not None:
                    os.environ["OPENAI_API_KEY"] = original_key
                elif "OPENAI_API_KEY" in os.environ:
                    del os.environ["OPENAI_API_KEY"]
        except Exception as e:
            # Handle OpenAI client initialization errors
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
        self.model = self.settings.openai_model
        self.temperature = self.settings.openai_temperature
        self.max_tokens = self.settings.openai_max_tokens

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Make a call to OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def extract_strategic_goals(self, text: str, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract strategic goals from strategy document text."""
        system_prompt = """You are an expert strategic analyst. Extract strategic goals from corporate strategy documents.
Return a JSON array of goals. Each goal should have:
- title: Short, clear title (max 200 chars)
- description: Detailed description (max 500 chars)
- time_horizon_year: The target year (integer, e.g., 2028)
- priority: Priority level 1-5 (1 = highest)

Extract ALL strategic goals mentioned. Be thorough and precise. Return ONLY a JSON array."""
        
        user_prompt = f"""Extract strategic goals from this strategy document:

{text}

{f'Business Unit: {business_unit}' if business_unit else ''}

Return ONLY a valid JSON array of goals, no markdown, no code blocks, no other text."""
        
        try:
            response = self._call_llm(system_prompt, user_prompt)
            # Clean response (remove markdown code blocks if present)
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()
            
            # Remove any leading/trailing text and find JSON array
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                response = response[start:end]
            
            # Try to parse as JSON array directly
            if response.startswith("["):
                goals = json.loads(response)
            else:
                # If wrapped in object, try to extract array
                parsed = json.loads(response)
                if isinstance(parsed, dict) and "goals" in parsed:
                    goals = parsed["goals"]
                elif isinstance(parsed, list):
                    goals = parsed
                else:
                    goals = [parsed] if isinstance(parsed, dict) else []
            
            # Validate and normalize
            normalized = []
            for g in goals:
                if isinstance(g, dict):
                    normalized.append({
                        "title": str(g.get("title", "Untitled Goal"))[:200],
                        "description": str(g.get("description", g.get("title", "")))[:500],
                        "time_horizon_year": int(g.get("time_horizon_year", 2028)),
                        "priority": int(g.get("priority", 3)),
                    })
            return normalized if normalized else self._fallback_goal(text, business_unit)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}, using fallback")
            return self._fallback_goal(text, business_unit)
        except Exception as e:
            print(f"LLM extraction failed: {e}, using fallback")
            return self._fallback_goal(text, business_unit)

    def _fallback_goal(self, text: str, business_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fallback if LLM fails."""
        from datetime import datetime
        return [{
            "title": "Strategic Transformation",
            "description": text[:500],
            "time_horizon_year": datetime.utcnow().year + 3,
            "priority": 3,
        }]

    def extract_skills_from_goal(
        self, goal_title: str, goal_description: str, existing_skills: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Extract required skills from a strategic goal."""
        system_prompt = """You are an expert in workforce planning and skill analysis. 
Given a strategic goal, identify the specific skills required to achieve it.
For each skill, provide:
- name: The skill name (be specific, e.g., "Quantum Algorithm Design" not just "Quantum")
- description: What this skill entails
- category: technical, behavioral, domain, or leadership
- domain: The domain area (e.g., "Quantum Computing", "AI/ML", "Data Science")
- target_level: Required proficiency level 1-5 (1=basic, 5=expert)
- importance_weight: How critical this skill is (0.0-1.0)

Return ONLY a JSON array of skills, no markdown, no code blocks."""
        
        skills_context = ""
        if existing_skills:
            skills_context = f"\n\nExisting skills in ontology (for reference):\n"
            for s in existing_skills[:20]:  # Limit context
                skills_context += f"- {s.get('name', '')}: {s.get('description', '')}\n"
        
        user_prompt = f"""Strategic Goal:
Title: {goal_title}
Description: {goal_description}
{skills_context}

Identify ALL skills required to achieve this goal. Be specific and comprehensive.
Return ONLY a valid JSON array of skills, no markdown, no other text."""
        
        try:
            response = self._call_llm(system_prompt, user_prompt)
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()
            
            # Find JSON array in response
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                response = response[start:end]
            
            if response.startswith("["):
                skills = json.loads(response)
            else:
                parsed = json.loads(response)
                if isinstance(parsed, dict) and "skills" in parsed:
                    skills = parsed["skills"]
                elif isinstance(parsed, list):
                    skills = parsed
                else:
                    skills = []
            
            normalized = []
            for s in skills:
                if isinstance(s, dict) and s.get("name"):
                    normalized.append({
                        "name": str(s["name"])[:200],
                        "description": str(s.get("description", ""))[:1000],
                        "category": str(s.get("category", "technical")).lower(),
                        "domain": str(s.get("domain", ""))[:200],
                        "target_level": max(1, min(5, int(s.get("target_level", 3)))),
                        "importance_weight": max(0.0, min(1.0, float(s.get("importance_weight", 0.7)))),
                    })
            return normalized if normalized else []
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed in skill extraction: {e}")
            return []
        except Exception as e:
            print(f"Skill extraction failed: {e}")
            return []

    def generate_learning_content(
        self,
        skill_name: str,
        skill_description: str,
        target_level: int,
        employee_theta: float = 0.0,
        learning_style: str = "balanced",
    ) -> Dict[str, Any]:
        """Generate personalized learning module content."""
        system_prompt = """You are an expert instructional designer. Create personalized learning content.
Generate a complete learning module with:
- title: Engaging, unique module title
- description: Unique overview of what will be learned
- content: Detailed, non-repetitive lesson content (structured, clear, practical)
- exercises: 3-5 UNIQUE practice exercises with solutions (vary question types)
- assessment: 3-5 UNIQUE assessment questions with answers (diverse difficulty levels)

CRITICAL REQUIREMENTS:
- NO repetition - each exercise and question must be unique
- Vary question types: multiple choice, practical, conceptual, application
- Adapt difficulty to target level
- Make it practical and actionable
- Ensure all content is original and non-repetitive

Return ONLY valid JSON object, no markdown, no code blocks."""
        
        user_prompt = f"""Create a UNIQUE learning module for:
Skill: {skill_name}
Description: {skill_description}
Target Proficiency Level: {target_level}/5
Learner Current Level: {employee_theta:.2f} (on scale -3 to +3)
Learning Style: {learning_style}

CRITICAL: Generate FRESH, NON-REPETITIVE content:
- Unique title and description
- Original exercises with varied question types
- Diverse assessment questions
- No repetition of concepts or wording

Return JSON with:
{{
  "title": "unique engaging title",
  "description": "unique overview",
  "content": "detailed unique lesson content",
  "exercises": [
    {{"question": "unique question 1", "solution": "detailed solution"}},
    {{"question": "unique question 2", "solution": "detailed solution"}},
    {{"question": "unique question 3", "solution": "detailed solution"}}
  ],
  "assessment": [
    {{"question": "unique assessment question 1", "answer": "answer", "difficulty": 1-5}},
    {{"question": "unique assessment question 2", "answer": "answer", "difficulty": 1-5}},
    {{"question": "unique assessment question 3", "answer": "answer", "difficulty": 1-5}}
  ]
}}

Return ONLY valid JSON object, no markdown, no code blocks."""
        
        try:
            # Use JSON mode for structured output
            response = self._call_llm(
                system_prompt, 
                user_prompt,
                response_format={"type": "json_object"}
            )
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()
            
            # Find JSON object in response with proper brace matching
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
            
            # Remove duplicates from exercises and assessment
            exercises = parsed.get("exercises", [])
            seen_exercises = set()
            unique_exercises = []
            for ex in exercises:
                q = ex.get("question", "")
                if q and q not in seen_exercises:
                    seen_exercises.add(q)
                    unique_exercises.append(ex)
            
            assessment = parsed.get("assessment", [])
            seen_assessment = set()
            unique_assessment = []
            for ass in assessment:
                q = ass.get("question", "")
                if q and q not in seen_assessment:
                    seen_assessment.add(q)
                    unique_assessment.append(ass)
            
            return {
                "title": parsed.get("title", f"Learn {skill_name}"),
                "description": parsed.get("description", ""),
                "content": parsed.get("content", ""),
                "exercises": unique_exercises,
                "assessment": unique_assessment,
            }
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed in content generation: {e}")
            # Try to fix common JSON issues
            if 'response' in locals():
                try:
                    fixed = re.sub(r',\s*}', '}', response)
                    fixed = re.sub(r',\s*]', ']', fixed)
                    parsed = json.loads(fixed)
                    return {
                        "title": parsed.get("title", f"Learn {skill_name}"),
                        "description": parsed.get("description", ""),
                        "content": parsed.get("content", ""),
                        "exercises": parsed.get("exercises", []),
                        "assessment": parsed.get("assessment", []),
                    }
                except:
                    pass
            return {
                "title": f"Introduction to {skill_name}",
                "description": f"Learn the fundamentals of {skill_name}",
                "content": f"This module covers {skill_description}. Target level: {target_level}.",
                "exercises": [],
                "assessment": [],
            }
        except Exception as e:
            print(f"Content generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "title": f"Introduction to {skill_name}",
                "description": f"Learn the fundamentals of {skill_name}",
                "content": f"This module covers {skill_description}",
                "exercises": [],
                "assessment": [],
            }

    def extract_skills_from_description(
        self, description: str, existing_skills: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Extract skills from an employee description/bio using LLM."""
        system_prompt = """You are an expert in workforce analysis and skill identification.
Given an employee's description, bio, or resume text, identify the specific skills they possess.
For each skill, provide:
- name: The skill name (be specific, e.g., "Python Programming" not just "Python")
- description: Brief description of the skill
- category: technical, behavioral, domain, or leadership
- domain: The domain area (e.g., "Software Development", "Data Science", "Project Management")
- proficiency_level: Estimated proficiency level 1-5 (1=beginner, 5=expert) based on the description

Return ONLY a JSON array of skills, no markdown."""
        
        skills_context = ""
        if existing_skills:
            skills_context = f"\n\nExisting skills in ontology (for reference):\n"
            for s in existing_skills[:20]:
                skills_context += f"- {s.get('name', '')}: {s.get('description', '')}\n"
        
        user_prompt = f"""Employee Description:
{description}
{skills_context}

Identify ALL skills mentioned or implied in this description. Be specific and comprehensive.
Return ONLY a valid JSON array of skills, no markdown, no other text."""
        
        try:
            response = self._call_llm(system_prompt, user_prompt)
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()
            
            # Find JSON array in response
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                response = response[start:end]
            
            if response.startswith("["):
                skills = json.loads(response)
            else:
                parsed = json.loads(response)
                if isinstance(parsed, dict) and "skills" in parsed:
                    skills = parsed["skills"]
                elif isinstance(parsed, list):
                    skills = parsed
                else:
                    skills = []
            
            normalized = []
            for s in skills:
                if isinstance(s, dict) and s.get("name"):
                    normalized.append({
                        "name": str(s["name"])[:200],
                        "description": str(s.get("description", ""))[:1000],
                        "category": str(s.get("category", "technical")).lower(),
                        "domain": str(s.get("domain", ""))[:200],
                        "proficiency_level": max(1, min(5, int(s.get("proficiency_level", s.get("level", 3))))),
                    })
            return normalized if normalized else []
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed in employee skill extraction: {e}")
            return []
        except Exception as e:
            print(f"Employee skill extraction failed: {e}")
            return []

    def analyze_skill_gaps(
        self,
        employee_skills: List[Dict[str, Any]],
        required_skills: List[Dict[str, Any]],
        goal_title: str,
        goal_description: str,
        employee_name: str = "",
        employee_description: str = "",
    ) -> Dict[str, Any]:
        """
        Use AI to intelligently analyze skill gaps using NLP and semantic understanding.
        Understands professional roles, skill relationships, and contextual meaning.
        Returns gap analysis with matched skills, gaps, and AI insights.
        """
        system_prompt = """You are an expert workforce analyst with deep understanding of professional roles, 
skill domains, and semantic relationships between technical skills. You use natural language processing 
and contextual understanding, not keyword matching.

CRITICAL INSTRUCTIONS - NO REPETITION:
1. Analyze each required skill EXACTLY ONCE - no duplicates
2. Generate UNIQUE explanations for each gap - vary wording and focus
3. Ensure all JSON arrays contain distinct, non-repetitive entries
4. Use semantic understanding, not keyword matching

ROLE-BASED INFERENCE:
- "DevOps Specialist" = DevOps, CI/CD, automation, infrastructure, containerization skills (4-5/5)
- "Software Engineer" = programming, development, technical skills
- "Data Scientist" = ML, statistics, data analysis skills
- Infer skills from role titles and descriptions

SEMANTIC EQUIVALENCE:
- "CI/CD Pipelines" = "Continuous Integration" = "Continuous Deployment"
- "Docker" = "Containerization" = "Container Orchestration"
- "Infrastructure as Code" = "IaC" = "Terraform" = "CloudFormation"
- "DevOps" = automation, CI/CD, infrastructure, monitoring, cloud platforms
- "System Reliability Engineering" = "SRE" = "Site Reliability"

SKILL HIERARCHIES:
- Advanced skills imply foundational knowledge (Kubernetes → Docker)
- Domain expertise implies related skills (DevOps → related tools)
- Professional experience suggests skill depth

Analyze:
1. Which employee skills semantically match required skills (considering roles, context, meaning)
2. Which required skills are truly missing (not just name mismatches)
3. The severity of each gap (accounting for semantic matches and role-based expertise)
4. Overall assessment considering professional role and experience

CRITICAL: Return valid JSON with NO duplicates, NO repetition, UNIQUE content for each entry.

Return a JSON object with:
{
  "skill_matches": [
    {
      "employee_skill": "skill name from employee",
      "required_skill": "skill name from requirements",
      "match_type": "exact" | "semantic" | "role_based" | "hierarchical",
      "match_confidence": 0.0-1.0 (higher for stronger semantic/role-based matches),
      "gap_value": 0.0-5.0 (required_level - employee_level, can be negative if employee exceeds),
      "explanation": "detailed explanation of why this match was made and what the gap means"
    }
  ],
  "missing_skills": [
    {
      "required_skill": "skill name",
      "gap_value": 0.0-5.0,
      "severity": "critical" | "high" | "moderate" | "low",
      "reason": "why this skill is needed and why it's truly missing",
      "detailed_explanation": "comprehensive explanation of: 1) Why this skill is critical for the goal, 2) What specific capabilities are missing, 3) How this gap impacts the employee's ability to contribute to the goal, 4) What level of proficiency is needed and why"
    }
  ],
  "overall_assessment": {
    "readiness_score": 0.0-1.0,
    "summary": "comprehensive assessment considering role, skills, and semantic understanding",
    "key_gaps": ["list of most critical gaps that are truly missing"],
    "detailed_report": "A comprehensive, detailed report (2-3 paragraphs) explaining: 1) Overall readiness assessment, 2) Strengths the employee brings, 3) Critical skill gaps and their impact, 4) Recommendations for addressing gaps, 5) Expected timeline for skill development"
  },
  "gap_breakdown": [
    {
      "skill_name": "name of required skill",
      "current_level": 0.0-5.0,
      "required_level": 0.0-5.0,
      "gap_value": 0.0-5.0,
      "severity": "critical" | "high" | "moderate" | "low",
      "explanation": "detailed explanation of this specific gap, why it exists, and what it means"
    }
  ]
}

Use NLP and semantic understanding. A DevOps Specialist should be recognized as having strong 
DevOps-related capabilities. Return ONLY valid JSON, no markdown."""
        
        # Format employee skills with context
        emp_skills_text = "\n".join([
            f"- {s.get('name', '')} (Proficiency: {s.get('proficiency_level', s.get('level', 0))}/5, Domain: {s.get('domain', 'N/A')}, Category: {s.get('category', 'N/A')})"
            for s in employee_skills
        ]) if employee_skills else "None explicitly listed"
        
        # Format required skills
        req_skills_text = "\n".join([
            f"- {s.get('name', '')} (Required: {s.get('target_level', s.get('level', 0))}/5, Domain: {s.get('domain', 'N/A')}, Importance: {s.get('importance_weight', 1.0):.2f})"
            for s in required_skills
        ])
        
        # Build context about employee role
        employee_context = ""
        if employee_name:
            employee_context += f"Employee Name: {employee_name}\n"
        if employee_description:
            employee_context += f"Employee Role/Description: {employee_description}\n"
        
        user_prompt = f"""Strategic Goal:
Title: {goal_title}
Description: {goal_description}

{employee_context}
Employee's Explicitly Listed Skills:
{emp_skills_text}

Required Skills for Goal:
{req_skills_text}

CRITICAL INSTRUCTIONS:
1. Use semantic understanding, NOT keyword matching
2. Analyze each required skill ONCE - no duplicates
3. Generate unique, non-repetitive explanations for each gap
4. Return valid JSON only

ANALYSIS RULES:
- "DevOps Specialist" role implies DevOps, CI/CD, automation, infrastructure skills
- Match skills semantically: "CI/CD" = "Continuous Integration", "Docker" = "Containerization"
- Infer from role: DevOps roles have 4-5/5 in related skills
- Only mark missing if TRULY absent after semantic analysis

For EACH required skill (analyze each ONCE):
- If employee has it: calculate gap, provide unique explanation
- If missing: mark in missing_skills with unique detailed explanation

IMPORTANT: 
- NO repetition - each skill analyzed exactly once
- Unique explanations - vary wording, focus on specific aspects
- Valid JSON structure - ensure proper formatting

Return JSON with:
{{
  "skill_matches": [{{"employee_skill": "...", "required_skill": "...", "match_type": "...", "match_confidence": 0.0-1.0, "gap_value": 0.0-5.0, "explanation": "unique detailed explanation"}}],
  "missing_skills": [{{"required_skill": "...", "gap_value": 0.0-5.0, "severity": "...", "reason": "...", "detailed_explanation": "unique comprehensive explanation"}}],
  "overall_assessment": {{
    "readiness_score": 0.0-1.0,
    "summary": "concise unique summary",
    "key_gaps": ["list without duplicates"],
    "detailed_report": "comprehensive unique 2-3 paragraph report"
  }},
  "gap_breakdown": [{{"skill_name": "...", "current_level": 0.0-5.0, "required_level": 0.0-5.0, "gap_value": 0.0-5.0, "severity": "...", "explanation": "unique explanation"}}]
}}

Return ONLY valid JSON object, no markdown."""
        
        try:
            # Use JSON mode for structured output
            response = self._call_llm(
                system_prompt, 
                user_prompt,
                response_format={"type": "json_object"}
            )
            
            # Clean response
            response = re.sub(r"```json\s*", "", response)
            response = re.sub(r"```\s*", "", response)
            response = response.strip()
            
            # Find JSON object in response
            if "{" in response:
                start = response.index("{")
                # Find matching closing brace
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
            
            # Remove duplicates and ensure unique skills
            skill_matches = parsed.get("skill_matches", [])
            seen_matches = set()
            unique_matches = []
            for match in skill_matches:
                key = (match.get("required_skill", ""), match.get("employee_skill", ""))
                if key not in seen_matches:
                    seen_matches.add(key)
                    unique_matches.append(match)
            
            missing_skills = parsed.get("missing_skills", [])
            seen_missing = set()
            unique_missing = []
            for missing in missing_skills:
                skill_name = missing.get("required_skill", "")
                if skill_name not in seen_missing:
                    seen_missing.add(skill_name)
                    unique_missing.append(missing)
            
            return {
                "skill_matches": unique_matches,
                "missing_skills": unique_missing,
                "overall_assessment": parsed.get("overall_assessment", {
                    "readiness_score": 0.0,
                    "summary": "Analysis incomplete",
                    "key_gaps": [],
                    "detailed_report": ""
                }),
                "gap_breakdown": parsed.get("gap_breakdown", []),
            }
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed in gap analysis: {e}")
            print(f"Response preview: {response[:500] if 'response' in locals() else 'N/A'}")
            # Try to fix common JSON issues
            if 'response' in locals():
                try:
                    # Try fixing trailing commas
                    fixed = re.sub(r',\s*}', '}', response)
                    fixed = re.sub(r',\s*]', ']', fixed)
                    parsed = json.loads(fixed)
                    return {
                        "skill_matches": parsed.get("skill_matches", []),
                        "missing_skills": parsed.get("missing_skills", []),
                        "overall_assessment": parsed.get("overall_assessment", {}),
                    }
                except:
                    pass
            return self._fallback_gap_analysis(employee_skills, required_skills)
        except Exception as e:
            print(f"AI gap analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_gap_analysis(employee_skills, required_skills)
    
    def _fallback_gap_analysis(
        self, employee_skills: List[Dict[str, Any]], required_skills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback gap analysis if AI fails."""
        matches = []
        missing = []
        
        emp_skill_names = {s.get("name", "").lower(): s for s in employee_skills}
        
        for req_skill in required_skills:
            req_name = req_skill.get("name", "").lower()
            req_level = float(req_skill.get("target_level", req_skill.get("level", 0)))
            
            # Simple name matching
            matched = False
            for emp_name, emp_skill in emp_skill_names.items():
                if req_name in emp_name or emp_name in req_name:
                    emp_level = float(emp_skill.get("proficiency_level", emp_skill.get("level", 0)))
                    gap = max(0.0, req_level - emp_level)
                    matches.append({
                        "employee_skill": emp_skill.get("name", ""),
                        "required_skill": req_skill.get("name", ""),
                        "match_type": "exact" if req_name == emp_name else "partial",
                        "match_confidence": 0.7 if req_name == emp_name else 0.5,
                        "gap_value": gap,
                    })
                    matched = True
                    break
            
            if not matched:
                missing.append({
                    "required_skill": req_skill.get("name", ""),
                    "gap_value": req_level,
                    "severity": "critical" if req_level >= 4 else "high" if req_level >= 3 else "moderate",
                    "reason": "Skill not found in employee profile",
                })
        
        return {
            "skill_matches": matches,
            "missing_skills": missing,
            "overall_assessment": {
                "readiness_score": 1.0 - (len(missing) / max(len(required_skills), 1)),
                "summary": f"Found {len(matches)} matches, {len(missing)} missing skills",
                "key_gaps": [m["required_skill"] for m in missing[:3]],
            },
        }

