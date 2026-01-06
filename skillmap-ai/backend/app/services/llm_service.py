"""
LLM service using Google Gemini for strategy extraction, skill inference, and content generation.
"""
import json
import re
import os
import time
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import get_settings


class LLMService:
    """Service for interacting with Google Gemini API."""

    def __init__(self, allow_demo_mode: bool = False):
        self.settings = get_settings()
        self.model_name = self.settings.gemini_model or "gemini-2.0-flash"
        self.model = None
        
        # Check if API key is present
        if not self.settings.gemini_api_key and not allow_demo_mode:
            env_key = os.getenv("GEMINI_API_KEY")
            error_msg = "GEMINI_API_KEY not set in environment. Please set it in Coolify Environment Variables section."
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # If in demo mode and no API key, set client to None
        if not self.settings.gemini_api_key and allow_demo_mode:
            return

        try:
            # Configure Gemini
            genai.configure(api_key=self.settings.gemini_api_key)
            
            # Default safety settings - block only high probability harm to avoid over-filtering
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }
            
            # Default generation config
            self.generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            )
            
            # Initialize default model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
        except Exception as e:
            print(f"❌ Failed to initialize Gemini client: {e}")
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def _is_demo_mode(self, user_email: Optional[str] = None) -> bool:
        """Check if demo mode is enabled for this user."""
        if self.settings.demo_mode:
            if self.settings.demo_user_email:
                return user_email == self.settings.demo_user_email
            return True  # Demo mode for all users
        return False
    
    # ... keep existing demo methods ...
    def _get_demo_skills_from_description(self, description: str) -> List[Dict[str, Any]]:
        """Generate realistic demo skills from employee description."""
        skills = []
        description_lower = description.lower()
        
        # Python skills
        if any(word in description_lower for word in ["python", "backend", "api", "rest", "django", "flask"]):
            skills.append({
                "name": "Python Programming",
                "description": "Proficient in Python development, including API design and backend services",
                "category": "technical",
                "domain": "Software Development",
                "proficiency_level": 4
            })
        
        # JavaScript skills
        if any(word in description_lower for word in ["javascript", "js", "node", "frontend", "react"]):
            skills.append({
                "name": "JavaScript Development",
                "description": "Experience with JavaScript and modern frameworks",
                "category": "technical",
                "domain": "Software Development",
                "proficiency_level": 3
            })
        
        # Database skills
        if any(word in description_lower for word in ["database", "sql", "postgres", "mysql", "data"]):
            skills.append({
                "name": "Database Design",
                "description": "Database design and management skills",
                "category": "technical",
                "domain": "Data Management",
                "proficiency_level": 3
            })
        
        # Cloud skills
        if any(word in description_lower for word in ["cloud", "aws", "azure", "gcp", "deployment"]):
            skills.append({
                "name": "Cloud-Native Development",
                "description": "Experience with cloud platforms and services",
                "category": "technical",
                "domain": "Cloud Computing",
                "proficiency_level": 3
            })
        
        # Docker/Containerization
        if "docker" in description_lower or "container" in description_lower:
            skills.append({
                "name": "Docker & Containerization",
                "description": "Containerization and orchestration with Docker",
                "category": "technical",
                "domain": "DevOps",
                "proficiency_level": 4
            })
        
        # Machine Learning
        if any(word in description_lower for word in ["machine learning", "ml", "ai", "data science", "data processing"]):
            skills.append({
                "name": "Machine Learning Fundamentals",
                "description": "Understanding of ML concepts and data processing",
                "category": "technical",
                "domain": "Data Science",
                "proficiency_level": 2
            })
        
        # Agile/Team collaboration
        if "agile" in description_lower or "collaborat" in description_lower:
            skills.append({
                "name": "Agile Methodologies",
                "description": "Experience working in agile environments",
                "category": "behavioral",
                "domain": "Project Management",
                "proficiency_level": 3
            })
        
        # RESTful services
        if "rest" in description_lower or "api" in description_lower:
            skills.append({
                "name": "RESTful API Design",
                "description": "Design and implementation of REST APIs",
                "category": "technical",
                "domain": "Software Development",
                "proficiency_level": 4
            })
        
        # Distributed systems
        if "distributed" in description_lower or "scalable" in description_lower:
            skills.append({
                "name": "Distributed Systems",
                "description": "Building scalable and distributed systems",
                "category": "technical",
                "domain": "Software Architecture",
                "proficiency_level": 3
            })
        
        # If no skills matched, add some default ones
        if not skills:
            skills = [
                {
                    "name": "Software Development",
                    "description": "General software development skills",
                    "category": "technical",
                    "domain": "Software Development",
                    "proficiency_level": 3
                }
            ]
        
        return skills

    def _get_demo_skills_from_goal(self, goal_title: str, goal_description: str) -> List[Dict[str, Any]]:
        """Generate realistic demo skills for a strategic goal."""
        skills = []
        text = f"{goal_title} {goal_description}".lower()
        
        # AI/ML goals
        if any(word in text for word in ["ai", "machine learning", "ml", "artificial intelligence"]):
            skills.extend([
                {
                    "name": "Machine Learning",
                    "description": "Advanced machine learning algorithms and model development",
                    "category": "technical",
                    "domain": "Data Science",
                    "target_level": 4,
                    "importance_weight": 0.9
                },
                {
                    "name": "Data Engineering",
                    "description": "Building data pipelines and infrastructure",
                    "category": "technical",
                    "domain": "Data Science",
                    "target_level": 3,
                    "importance_weight": 0.8
                }
            ])
        
        # Quantum computing
        if "quantum" in text:
            skills.extend([
                {
                    "name": "Quantum Algorithm Design",
                    "description": "Design and implementation of quantum algorithms",
                    "category": "technical",
                    "domain": "Quantum Computing",
                    "target_level": 5,
                    "importance_weight": 1.0
                },
                {
                    "name": "Quantum Computing Fundamentals",
                    "description": "Understanding of quantum computing principles",
                    "category": "technical",
                    "domain": "Quantum Computing",
                    "target_level": 4,
                    "importance_weight": 0.9
                }
            ])
        
        # Cloud/Infrastructure
        if any(word in text for word in ["cloud", "infrastructure", "scalable", "distributed"]):
            skills.extend([
                {
                    "name": "Cloud Architecture",
                    "description": "Designing scalable cloud-based systems",
                    "category": "technical",
                    "domain": "Cloud Computing",
                    "target_level": 4,
                    "importance_weight": 0.85
                },
                {
                    "name": "Distributed Systems",
                    "description": "Building and managing distributed systems",
                    "category": "technical",
                    "domain": "Software Architecture",
                    "target_level": 4,
                    "importance_weight": 0.8
                }
            ])
        
        # Default skills if none matched
        if not skills:
            skills = [
                {
                    "name": "Strategic Planning",
                    "description": "Ability to plan and execute strategic initiatives",
                    "category": "leadership",
                    "domain": "Strategy",
                    "target_level": 3,
                    "importance_weight": 0.7
                },
                {
                    "name": "Project Management",
                    "description": "Managing complex projects and teams",
                    "category": "leadership",
                    "domain": "Project Management",
                    "target_level": 3,
                    "importance_weight": 0.6
                }
            ]
        
        return skills

    def _get_demo_gap_analysis(self, employee_skills: List[Dict], required_skills: List[Dict], 
                               goal_title: str) -> Dict[str, Any]:
        """Generate realistic demo gap analysis."""
        skill_matches = []
        missing_skills = []
        gap_breakdown = []
        
        # Create some matches
        for req_skill in required_skills[:3]:  # Match first 3
            emp_skill = next((s for s in employee_skills if s.get("name", "").lower() in req_skill.get("name", "").lower() or 
                            req_skill.get("name", "").lower() in s.get("name", "").lower()), None)
            if emp_skill:
                current = emp_skill.get("proficiency_level", 3)
                required = req_skill.get("target_level", 4)
                gap = max(0, required - current)
                skill_matches.append({
                    "employee_skill": emp_skill.get("name"),
                    "required_skill": req_skill.get("name"),
                    "match_type": "semantic",
                    "match_confidence": 0.85,
                    "gap_value": gap,
                    "explanation": f"Employee has {emp_skill.get('name')} at level {current}/5, but goal requires {required}/5. Gap of {gap:.1f} levels."
                })
                gap_breakdown.append({
                    "skill_name": req_skill.get("name"),
                    "current_level": current,
                    "required_level": required,
                    "gap_value": gap,
                    "severity": "critical" if gap >= 3 else "high" if gap >= 2 else "moderate" if gap >= 1 else "low",
                    "explanation": f"Current proficiency is {current}/5, target is {required}/5. Focus on advanced concepts and practical applications."
                })
            else:
                gap = req_skill.get("target_level", 4)
                missing_skills.append({
                    "required_skill": req_skill.get("name"),
                    "gap_value": gap,
                    "severity": "critical" if gap >= 4 else "high",
                    "reason": "Skill not found in employee profile",
                    "detailed_explanation": f"{req_skill.get('name')} is required for this goal but not currently in the employee's skill set. Consider targeted training."
                })
                gap_breakdown.append({
                    "skill_name": req_skill.get("name"),
                    "current_level": 0,
                    "required_level": gap,
                    "gap_value": gap,
                    "severity": "critical" if gap >= 4 else "high",
                    "explanation": f"Skill is missing from employee profile. Requires comprehensive training to reach target level {gap}/5."
                })
        
        # Add remaining required skills to gap breakdown
        for req_skill in required_skills[3:]:
            gap = req_skill.get("target_level", 4)
            gap_breakdown.append({
                "skill_name": req_skill.get("name"),
                "current_level": 0,
                "required_level": gap,
                "gap_value": gap,
                "severity": "critical" if gap >= 4 else "high" if gap >= 3 else "moderate",
                "explanation": f"Skill needs to be developed from scratch. Target proficiency level: {gap}/5."
            })
        
        # Calculate readiness score
        total_gaps = sum(g.get("gap_value", 0) for g in gap_breakdown)
        max_possible_gap = len(gap_breakdown) * 5
        readiness_score = max(0, 1 - (total_gaps / max_possible_gap)) if max_possible_gap > 0 else 0.5
        
        return {
            "skill_matches": skill_matches,
            "missing_skills": missing_skills,
            "overall_assessment": {
                "readiness_score": readiness_score,
                "summary": f"Employee shows {len(skill_matches)} matching skills with an overall readiness of {readiness_score*100:.1f}%. Key focus areas identified.",
                "key_gaps": [g.get("skill_name") for g in gap_breakdown[:3] if g.get("gap_value", 0) > 0],
                "detailed_report": f"Analysis of {goal_title} reveals {len(skill_matches)} skills where the employee has existing proficiency, and {len(missing_skills)} skills that need to be developed. The employee's current skill profile aligns {readiness_score*100:.0f}% with the goal requirements. Priority should be given to developing the missing critical skills while building upon existing strengths."
            },
            "gap_breakdown": gap_breakdown
        }

    def _get_demo_learning_content(self, skill_name: str, target_level: int) -> Dict[str, Any]:
        """Generate realistic demo learning content."""
        return {
            "title": f"Mastering {skill_name} - Level {target_level}",
            "description": f"Comprehensive course covering {skill_name} concepts and practical applications at level {target_level}",
            "content": f"""
# {skill_name} - Comprehensive Guide

## Introduction
This module provides an in-depth exploration of {skill_name}, designed for learners targeting proficiency level {target_level}.

## Core Concepts
- Fundamental principles of {skill_name}
- Advanced techniques and best practices
- Real-world applications and case studies
- Common pitfalls and how to avoid them

## Practical Applications
Learn how to apply {skill_name} in real-world scenarios through hands-on examples and exercises.

## Summary
By completing this module, you'll have a solid understanding of {skill_name} at level {target_level} proficiency.
            """.strip(),
            "exercises": [
                {
                    "question": f"Explain the key concept of {skill_name} and provide a practical example.",
                    "solution": f"A practical example of {skill_name} would involve applying the core principles in a real-world scenario, demonstrating understanding through implementation."
                },
                {
                    "question": f"What are the main challenges when working with {skill_name}?",
                    "solution": f"The main challenges include understanding the underlying principles, applying them correctly, and troubleshooting common issues."
                },
                {
                    "question": f"How would you apply {skill_name} to solve a complex problem?",
                    "solution": f"To apply {skill_name}, first analyze the problem, identify relevant concepts, then systematically apply the principles to develop a solution."
                }
            ],
            "assessment": [
                {
                    "question": f"Which of the following best describes {skill_name}?",
                    "answer": "A comprehensive approach to the subject",
                    "difficulty": target_level
                },
                {
                    "question": f"What is the primary benefit of mastering {skill_name}?",
                    "answer": "Enhanced problem-solving capabilities",
                    "difficulty": target_level
                }
            ]
        }

    def _get_demo_assessment(self, skill_name: str, num_questions: int) -> Dict[str, Any]:
        """Generate realistic demo assessment questions."""
        questions = []
        for i in range(num_questions):
            questions.append({
                "question_id": f"q{i+1}",
                "question": f"Question {i+1}: Which statement best describes {skill_name}?",
                "options": [
                    {"option_id": "a", "text": "Option A: Basic understanding"},
                    {"option_id": "b", "text": "Option B: Intermediate knowledge"},
                    {"option_id": "c", "text": "Option C: Advanced proficiency"},
                    {"option_id": "d", "text": "Option D: Expert level mastery"}
                ],
                "correct_answer_id": "c",
                "difficulty": 2.5 + (i * 0.3),
                "explanation": f"This question tests understanding of {skill_name} at an intermediate level."
            })
        
        return {
            "questions": questions,
            "average_difficulty": 2.5
        }

    def _clean_and_parse_json(self, text: str) -> Any:
        """Clean and parse JSON from LLM response, with basic repair for truncation."""
        if not text:
            return None
            
        # Remove markdown code blocks
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()
        
        # Try to find JSON structure if there's surrounding text
        if "{" in text or "[" in text:
            try:
                # Find first and last braces/brackets
                first_curly = text.find("{")
                last_curly = text.rfind("}")
                first_square = text.find("[")
                last_square = text.rfind("]")
                
                # Determine which one starts first (curly or square)
                start = -1
                end = -1
                
                if first_curly != -1 and (first_square == -1 or first_curly < first_square):
                    start = first_curly
                    end = last_curly + 1
                    is_array = False
                elif first_square != -1:
                    start = first_square
                    end = last_square + 1
                    is_array = True
                else:
                    is_array = False
                    
                if start != -1 and end != -1:
                    json_str = text[start:end]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        print(f"      ⚠️  JSON parsing of extracted block failed: {e}")
                        # If it failed, maybe it's truncated? 
                        # Only return to main logic to try repair
            except Exception as e:
                print(f"      ⚠️ Basic JSON extraction failed: {e}")
                
        # Default fallback to direct parsing or repair
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"      ❌ JSON parsing failed: {e}. Attempting repair...")
            
            # Simple Repair Strategy for Truncated JSON
            try:
                # 1. Aggressive cleaning (trailing commas)
                fixed = re.sub(r',\s*}', '}', text)
                fixed = re.sub(r',\s*]', ']', fixed)
                try:
                    return json.loads(fixed)
                except: pass

                # 2. Repairing truncated arrays/objects using a stack
                last_good = max(text.rfind("}"), text.rfind("]"))
                if last_good != -1:
                    repair = text[:last_good+1]
                    repair = re.sub(r',[ \n\r\t]*$', '', repair)
                    
                    # Stack-based closing
                    stack = []
                    for char in repair:
                        if char == "{":
                            stack.append("}")
                        elif char == "[":
                            stack.append("]")
                        elif char in ("}", "]"):
                            if stack and stack[-1] == char:
                                stack.pop()
                    
                    # Close in reverse order
                    while stack:
                        repair += stack.pop()
                        
                    try:
                        return json.loads(repair)
                    except:
                        pass
            except Exception as repair_err:
                print(f"      ❌ JSON repair failed: {repair_err}")
                
            return None

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Make a call to Google Gemini API."""
        if self.model is None:
            raise ValueError("Gemini client not initialized. Demo mode should use demo methods instead.")
        
        start_time = time.time()
        
        try:
            print(f"      Making Gemini API call ({self.model_name})...")
            
            # For Gemini 1.5+, system instruction is best provided in the constructor
            # But creating a new model instance per-call is fine for stateless requests
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction=system_prompt
            )
            
            # If JSON response requested, we can use generation config to enforce it
            generation_config = self.generation_config
            if response_format and response_format.get("type") == "json_object":
                 generation_config = genai.types.GenerationConfig(
                    temperature=self.generation_config.temperature,
                    max_output_tokens=self.generation_config.max_output_tokens,
                    response_mime_type="application/json"
                )

            response = model.generate_content(
                user_prompt,
                generation_config=generation_config
            )
            
            elapsed = time.time() - start_time
            
            # Handle response candidates (safety can block ALL candidates)
            if not response.candidates:
                 print(f"      ❌ Gemini API call BLOCKED by safety filters after {elapsed:.2f}s")
                 return ""
            
            # check if the first candidate has parts
            if not response.candidates[0].content.parts:
                print(f"      ❌ Gemini API returned empty content (possibly safety block) after {elapsed:.2f}s")
                # Log why it was blocked if possible
                if response.prompt_feedback:
                    print(f"         Prompt feedback: {response.prompt_feedback}")
                return ""

            print(f"      ✅ Gemini API call completed in {elapsed:.2f}s")
            return response.text

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"      ❌ Gemini API call failed after {elapsed:.2f}s: {e}")
            raise

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
            # Force JSON mode by using response_format
            response = self._call_llm(system_prompt, user_prompt, response_format={"type": "json_object"})
            
            # Clean and parse JSON
            goals_data = self._clean_and_parse_json(response)
            
            if not goals_data:
                return self._fallback_goal(text, business_unit)
                
            # Normalize to list
            if isinstance(goals_data, dict):
                if "goals" in goals_data:
                    goals = goals_data["goals"]
                else:
                    goals = [goals_data]
            else:
                goals = goals_data if isinstance(goals_data, list) else []
            
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
        self, goal_title: str, goal_description: str, existing_skills: List[Dict[str, str]], user_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract required skills from a strategic goal."""
        if self._is_demo_mode(user_email):
            print("🎬 DEMO MODE: Using mock goal skill extraction")
            return self._get_demo_skills_from_goal(goal_title, goal_description)
        
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
            response = self._call_llm(system_prompt, user_prompt, response_format={"type": "json_object"})
            skills_data = self._clean_and_parse_json(response)
            
            if not skills_data:
                return []
                
            if isinstance(skills_data, dict) and "skills" in skills_data:
                skills = skills_data["skills"]
            elif isinstance(skills_data, list):
                skills = skills_data
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
        module_index: int = 1,
        total_modules: int = 1,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate personalized learning module content."""
        if self._is_demo_mode(user_email):
            print("🎬 DEMO MODE: Using mock learning content")
            return self._get_demo_learning_content(skill_name, target_level)
        
        system_prompt = """You are an expert instructional designer. Create personalized learning content.
Generate a complete learning module with:
- title: Engaging, unique module title that reflects the specific focus (e.g., Fundamentals, Intermediate Applications, Advanced Scenarios)
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
- TITLES MUST BE UNIQUE: Do not call every module "Introduction to...". Use descriptive titles like "Building Blocks of...", "Deep Dive into...", "Mastering...", "Case Studies in...", etc.

Return ONLY valid JSON object, no markdown, no code blocks."""
        
        user_prompt = f"""Create a UNIQUE learning module for:
Skill: {skill_name}
Description: {skill_description}
Target Proficiency Level: {target_level}/5
Learner Current Level: {employee_theta:.2f} (on scale -3 to +3)
Learning Style: {learning_style}

MODULE CONTEXT: This is module {module_index} of {total_modules} in the learning sequence for this skill.
{"CRITICAL: This is a LATER module (Part " + str(module_index) + "). DO NOT repeat introductory concepts. Focus on advanced applications, complex real-world scenarios, troubleshooting, or specialized advanced sub-topics." if module_index > 1 else "CRITICAL: This is the FIRST module (Part 1). Focus on core essentials, primary definitions, and basic logic."}

CRITICAL: Generate FRESH, NON-REPETITIVE content:
- **Unique title**: MUST follow the theme of 'Part {module_index}: [Specific Focus Area]' (e.g., 'Mastering Complex {skill_name} Workflows' if Part > 1)
- Unique description (specific to module {module_index})
- Original exercises with varied question types
- Diverse assessment questions
- No repetition of concepts or wording from typical introductory material

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
            parsed = self._clean_and_parse_json(response)
            
            if not parsed:
                raise ValueError("Failed to parse learning content JSON")
            
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
            # Improved fallbacks to prevent identical titles
            if module_index == 1:
                title = f"Fundamental Concepts of {skill_name}"
            elif module_index == total_modules:
                title = f"Advanced Mastery: {skill_name}"
            else:
                title = f"{skill_name}: Applied Applications (Part {module_index})"
                
            return {
                "title": title,
                "description": f"Targeted learning for {skill_name} (Module {module_index}/{total_modules})",
                "content": f"Structured lesson on {skill_name} covering relevant topics for proficiency level {target_level}.",
                "exercises": [],
                "assessment": [],
            }

    def extract_skills_from_description(
        self, 
        description: str, 
        skills_context: List[Dict[str, Any]] = [], 
        user_email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract skills from employee description using LLM."""
        if self._is_demo_mode(user_email):
            print("🎬 DEMO MODE: Using mock skill extraction")
            return self._get_demo_skills_from_description(description)
            
        # Format existing skills for context
        context_str = ""
        if skills_context:
            context_str = "\nExisting skills in our database (reuse names if applicable):\n"
            for s in skills_context[:50]:  # Limit context size
                context_str += f"- {s['name']}: {s.get('description', '')[:100]}\n"

        system_prompt = f"""You are an expert HR analyst. Extract a comprehensive list of professional skills from the employee description.
For each skill, provide:
- name: Standardized skill name
- description: Brief description of the skill context
- category: technical, soft_skill, leadership, etc.
- domain: The general domain (e.g. Software Development, Marketing)
- proficiency_level: Estimated level 1-5 based on context (default to 3 if unclear)
{context_str}
Return ONLY a JSON array of skills."""

        user_prompt = f"""Employee Description:
{description}

Extract ALL relevant skills. Return valid JSON array."""

        try:
            response = self._call_llm(system_prompt, user_prompt, response_format={"type": "json_object"})
            skills_data = self._clean_and_parse_json(response)
            
            if not skills_data:
                return []
                
            if isinstance(skills_data, dict) and "skills" in skills_data:
                skills = skills_data["skills"]
            else:
                skills = skills_data if isinstance(skills_data, list) else []
                
            return skills
        except Exception as e:
            print(f"Skill extraction from description failed: {e}")
            return []

    def analyze_skill_gaps(
        self,
        employee_skills: List[Dict],
        required_skills: List[Dict],
        goal_title: str,
        goal_description: str,
        employee_name: Optional[str] = None,
        employee_description: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze skill gaps for a specific goal."""
        
        if self._is_demo_mode(user_email):
            print("🎬 DEMO MODE: Using mock gap analysis")
            return self._get_demo_gap_analysis(employee_skills, required_skills, goal_title)
            
        system_prompt = """You are an expert workforce planner. Analyze the gap between an employee's current skills and the skills required for a strategic goal.
        
Provide a detailed JSON analysis with:
- skill_matches: List of objects for skills the employee has that match requirements. Each object MUST have:
  - "required_skill": Exact name of the required skill from the provided list
  - "gap_value": Numeric gap (0 if no gap, positive if lacking)
  - "match_confidence": 0-1
  - "explanation": Brief reason
- missing_skills: List of objects for required skills the employee completely lacks. Each object MUST have:
  - "required_skill": Exact name of the required skill from the provided list
  - "gap_value": Numeric value (usually the full target level)
  - "severity": high/medium/low
  - "reason": Brief reason
- overall_assessment: { readiness_score (0-1), summary, key_gaps, detailed_report }
- gap_breakdown: List of all required skills with current vs required levels and gap details

Return ONLY valid JSON."""

        emp_skills_str = json.dumps(employee_skills, indent=2)
        req_skills_str = json.dumps(required_skills, indent=2)
        
        user_prompt = f"""Goal: {goal_title}
Description: {goal_description}

Employee: {employee_name or 'Employee'}
Profile: {employee_description or 'N/A'}

Employee Skills:
{emp_skills_str}

Required Skills:
{req_skills_str}

Perform a detailed gap analysis. Return valid JSON."""

        try:
            response = self._call_llm(
                system_prompt,
                user_prompt,
                response_format={"type": "json_object"}
            )
            parsed = self._clean_and_parse_json(response)
            
            if not parsed:
                 return self._get_demo_gap_analysis(employee_skills, required_skills, goal_title)
                 
            return parsed
        except Exception as e:
            print(f"Gap analysis failed: {e}")
            return {
                "skill_matches": [],
                "missing_skills": [],
                "overall_assessment": {"readiness_score": 0, "summary": "Analysis failed", "key_gaps": []},
                "gap_breakdown": []
            }
