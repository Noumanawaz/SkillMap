from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class MCQOption(BaseModel):
    option_id: str
    text: str


class MCQQuestion(BaseModel):
    question_id: str
    question: str
    options: List[MCQOption]
    correct_answer_id: str
    difficulty: float
    explanation: Optional[str] = None


class SkillAssessmentGenerateRequest(BaseModel):
    skill_id: str
    skill_name: Optional[str] = None
    skill_description: Optional[str] = None
    readiness_score: Optional[float] = None  # 0-1, determines difficulty
    num_questions: int = 10  # Default 10 questions


class SkillAssessmentGenerateResponse(BaseModel):
    assessment_id: str
    skill_id: str
    skill_name: str
    questions: List[MCQQuestion]
    difficulty_level: float
    estimated_duration_minutes: int = 15


class SkillAssessmentSubmitRequest(BaseModel):
    assessment_id: str
    answers: Dict[str, str]  # question_id -> option_id


class SkillAssessmentResult(BaseModel):
    assessment_id: str
    skill_id: str
    skill_name: str
    score: float  # 0-5 proficiency level
    percentage_correct: float  # 0-100
    total_questions: int
    correct_answers: int
    questions_with_feedback: List[Dict[str, Any]]  # Questions with user answer, correct answer, explanation
    updated_proficiency: Optional[float] = None  # Updated proficiency level after test


class SkillAssessmentHistory(BaseModel):
    assessment_id: str
    skill_id: str
    skill_name: str
    score: float
    status: str
    created_at: str
    completed_at: Optional[str] = None

