import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    JSON,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class EmployeeProfile(Base):
    __tablename__ = "employee_profile"

    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Employee description/bio
    role_id = Column(UUID(as_uuid=True), ForeignKey("role.role_id"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employee_profile.employee_id"), nullable=True)
    hire_date = Column(Date, nullable=True)
    location = Column(String, nullable=True)
    cognitive_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="employees")
    manager = relationship("EmployeeProfile", remote_side=[employee_id])


class Role(Base):
    __tablename__ = "role"

    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employees = relationship("EmployeeProfile", back_populates="role")


class Skill(Base):
    __tablename__ = "skill"

    skill_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    parent_skill_id = Column(UUID(as_uuid=True), ForeignKey("skill.skill_id"), nullable=True)
    prerequisites = Column(JSON, nullable=True)  # Changed from ARRAY for SQLite compatibility
    is_future_skill = Column(Boolean, default=False)
    ontology_version = Column(String, nullable=False)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Skill", remote_side=[skill_id])


class StrategicGoal(Base):
    __tablename__ = "strategic_goal"

    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    time_horizon_year = Column(Integer, nullable=True)
    business_unit = Column(String, nullable=True)
    priority = Column(Integer, nullable=True)
    owner_employee_id = Column(
        UUID(as_uuid=True), ForeignKey("employee_profile.employee_id"), nullable=True
    )
    source_document_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    required_skills = relationship(
        "StrategicGoalRequiredSkill", back_populates="goal", cascade="all, delete-orphan"
    )


class StrategicGoalRequiredSkill(Base):
    __tablename__ = "strategic_goal_required_skill"

    goal_id = Column(
        UUID(as_uuid=True), ForeignKey("strategic_goal.goal_id"), primary_key=True
    )
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skill.skill_id"), primary_key=True)
    target_level = Column(Integer, nullable=False)
    required_by_year = Column(Integer, nullable=False)
    importance_weight = Column(Float, nullable=False, default=1.0)

    goal = relationship("StrategicGoal", back_populates="required_skills")
    skill = relationship("Skill")


class LearningModule(Base):
    __tablename__ = "learning_module"

    module_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    format = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(Integer, nullable=True)
    language = Column(String, nullable=True)
    skills = Column(JSON, nullable=True)  # Changed from ARRAY for SQLite compatibility
    module_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    is_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SkillAssessment(Base):
    __tablename__ = "skill_assessment"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employee_profile.employee_id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skill.skill_id"), nullable=False)
    questions = Column(JSON, nullable=False)  # Store the generated test questions
    answers = Column(JSON, nullable=True)  # Store user's answers
    correct_answers = Column(JSON, nullable=True)  # Store correct answers for grading
    score = Column(Float, nullable=True)  # Calculated proficiency score (0-5)
    difficulty_level = Column(Float, nullable=True)  # Average difficulty of questions
    readiness_score = Column(Float, nullable=True)  # Readiness score used to determine difficulty
    status = Column(String, default="pending")  # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = relationship("EmployeeProfile")
    skill = relationship("Skill")


