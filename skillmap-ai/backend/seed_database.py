"""
Seed the database with sample data for testing.
Run this script to populate the database with employees, goals, and skills.
"""
import sys
from pathlib import Path
from datetime import date, datetime
from uuid import uuid4

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models import (
    EmployeeProfile,
    StrategicGoal,
    StrategicGoalRequiredSkill,
    Skill,
    Role,
)
from app.core.config import get_settings

def seed_database():
    """Populate database with sample data."""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding database with sample data...")
        
        # Create roles
        print("   Creating roles...")
        roles = {}
        role_data = [
            {"name": "Software Engineer", "description": "Develops and maintains software applications"},
            {"name": "Data Scientist", "description": "Analyzes data and builds ML models"},
            {"name": "DevOps Engineer", "description": "Manages infrastructure and CI/CD pipelines"},
            {"name": "Product Manager", "description": "Manages product development and strategy"},
            {"name": "Engineering Manager", "description": "Leads engineering teams"},
        ]
        
        for role_info in role_data:
            role = Role(
                role_id=uuid4(),
                name=role_info["name"],
                description=role_info["description"],
            )
            db.add(role)
            roles[role_info["name"]] = role
        
        db.commit()
        print(f"   ✅ Created {len(roles)} roles")
        
        # Create skills
        print("   Creating skills...")
        skills = {}
        skill_data = [
            {"name": "Python Programming", "description": "Proficient in Python development", "category": "technical", "domain": "Software Development"},
            {"name": "Machine Learning", "description": "Building and deploying ML models", "category": "technical", "domain": "AI/ML"},
            {"name": "Docker", "description": "Containerization and container orchestration", "category": "technical", "domain": "DevOps"},
            {"name": "Kubernetes", "description": "Container orchestration platform", "category": "technical", "domain": "DevOps"},
            {"name": "React", "description": "Frontend framework for building UIs", "category": "technical", "domain": "Frontend Development"},
            {"name": "FastAPI", "description": "Modern Python web framework", "category": "technical", "domain": "Backend Development"},
            {"name": "PostgreSQL", "description": "Relational database management", "category": "technical", "domain": "Database"},
            {"name": "CI/CD Pipelines", "description": "Continuous integration and deployment", "category": "technical", "domain": "DevOps"},
            {"name": "Natural Language Processing", "description": "NLP techniques and models", "category": "technical", "domain": "AI/ML"},
            {"name": "Cloud Architecture", "description": "Designing scalable cloud solutions", "category": "technical", "domain": "Cloud Computing"},
            {"name": "Team Leadership", "description": "Leading and managing technical teams", "category": "leadership", "domain": "Management"},
            {"name": "Agile Methodology", "description": "Agile development practices", "category": "behavioral", "domain": "Project Management"},
        ]
        
        for skill_info in skill_data:
            skill = Skill(
                skill_id=uuid4(),
                name=skill_info["name"],
                description=skill_info["description"],
                category=skill_info["category"],
                domain=skill_info["domain"],
                ontology_version="1.0.0",
                is_future_skill=False,
            )
            db.add(skill)
            skills[skill_info["name"]] = skill
        
        db.commit()
        print(f"   ✅ Created {len(skills)} skills")
        
        # Create employees with cognitive profiles
        print("   Creating employees...")
        employees = {}
        employee_data = [
            {
                "name": "Alice Johnson",
                "email": "alice.johnson@example.com",
                "description": "Alice is a senior software engineer with 8 years of experience in Python, FastAPI, and React. She specializes in building scalable backend services and has strong expertise in PostgreSQL. Alice is also proficient in Docker and has experience with CI/CD pipelines.",
                "role": "Software Engineer",
                "location": "San Francisco",
                "skills": {
                    "Python Programming": 4.5,
                    "FastAPI": 4.0,
                    "React": 3.5,
                    "PostgreSQL": 4.0,
                    "Docker": 3.5,
                    "CI/CD Pipelines": 3.0,
                }
            },
            {
                "name": "Bob Chen",
                "email": "bob.chen@example.com",
                "description": "Bob is a data scientist with expertise in machine learning and natural language processing. He has 6 years of experience building ML models and deploying them to production. Bob is skilled in Python, Docker, and cloud architecture.",
                "role": "Data Scientist",
                "location": "New York",
                "skills": {
                    "Python Programming": 4.5,
                    "Machine Learning": 4.5,
                    "Natural Language Processing": 4.0,
                    "Docker": 3.0,
                    "Cloud Architecture": 3.5,
                }
            },
            {
                "name": "Carol Martinez",
                "email": "carol.martinez@example.com",
                "description": "Carol is a DevOps engineer with 7 years of experience in infrastructure automation, CI/CD, Docker, and Kubernetes. She has strong skills in cloud architecture and is experienced in managing large-scale deployments.",
                "role": "DevOps Engineer",
                "location": "Austin",
                "skills": {
                    "Docker": 4.5,
                    "Kubernetes": 4.5,
                    "CI/CD Pipelines": 4.5,
                    "Cloud Architecture": 4.0,
                    "Python Programming": 3.0,
                }
            },
            {
                "name": "David Kim",
                "email": "david.kim@example.com",
                "description": "David is an engineering manager with 10 years of experience. He has strong technical skills in Python and React, but his main expertise is in team leadership, agile methodology, and product management.",
                "role": "Engineering Manager",
                "location": "Seattle",
                "skills": {
                    "Python Programming": 3.5,
                    "React": 3.0,
                    "Team Leadership": 4.5,
                    "Agile Methodology": 4.5,
                }
            },
        ]
        
        for emp_info in employee_data:
            role = roles.get(emp_info["role"])
            emp = EmployeeProfile(
                employee_id=uuid4(),
                email=emp_info["email"],
                name=emp_info["name"],
                description=emp_info["description"],
                role_id=role.role_id if role else None,
                hire_date=date(2020, 1, 15),
                location=emp_info["location"],
            )
            
            # Create cognitive profile with skills
            cognitive_profile = {}
            for skill_name, level in emp_info["skills"].items():
                if skill_name in skills:
                    skill_id = str(skills[skill_name].skill_id)
                    # Convert level (1-5) to theta (-3 to +3)
                    theta = (level - 3) * 0.6
                    cognitive_profile[skill_id] = {
                        "theta": theta,
                        "alpha": 1.0,
                        "level": level,
                    }
            
            emp.cognitive_profile = cognitive_profile
            db.add(emp)
            employees[emp_info["name"]] = emp
        
        db.commit()
        print(f"   ✅ Created {len(employees)} employees with cognitive profiles")
        
        # Create strategic goals
        print("   Creating strategic goals...")
        goals = {}
        goal_data = [
            {
                "title": "Migrate to Cloud-Native Architecture",
                "description": "Complete migration of all services to Kubernetes-based cloud infrastructure by 2026. This includes containerizing all applications, setting up CI/CD pipelines, and implementing cloud-native monitoring and logging.",
                "business_unit": "Technology",
                "time_horizon_year": 2026,
                "priority": 1,
                "required_skills": {
                    "Kubernetes": 4,
                    "Docker": 4,
                    "CI/CD Pipelines": 4,
                    "Cloud Architecture": 4,
                }
            },
            {
                "title": "Build AI-Powered Features",
                "description": "Develop and deploy AI-powered features using machine learning and NLP by 2027. Focus on natural language processing capabilities and recommendation systems.",
                "business_unit": "Technology",
                "time_horizon_year": 2027,
                "priority": 2,
                "required_skills": {
                    "Machine Learning": 4,
                    "Natural Language Processing": 4,
                    "Python Programming": 4,
                    "Docker": 3,
                }
            },
            {
                "title": "Enhance Frontend Capabilities",
                "description": "Modernize frontend applications using React and improve user experience across all products by 2026.",
                "business_unit": "Technology",
                "time_horizon_year": 2026,
                "priority": 3,
                "required_skills": {
                    "React": 4,
                    "Python Programming": 3,
                }
            },
        ]
        
        for goal_info in goal_data:
            goal = StrategicGoal(
                goal_id=uuid4(),
                title=goal_info["title"],
                description=goal_info["description"],
                business_unit=goal_info["business_unit"],
                time_horizon_year=goal_info["time_horizon_year"],
                priority=goal_info["priority"],
                created_at=datetime.utcnow(),
            )
            db.add(goal)
            db.flush()
            
            # Link required skills to goal
            for skill_name, target_level in goal_info["required_skills"].items():
                if skill_name in skills:
                    required_skill = StrategicGoalRequiredSkill(
                        goal_id=goal.goal_id,
                        skill_id=skills[skill_name].skill_id,
                        target_level=target_level,
                        required_by_year=goal_info["time_horizon_year"],
                        importance_weight=1.0,
                    )
                    db.add(required_skill)
            
            goals[goal_info["title"]] = goal
        
        db.commit()
        print(f"   ✅ Created {len(goals)} strategic goals with required skills")
        
        print("\n✅ Database seeding completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   - {len(roles)} roles")
        print(f"   - {len(skills)} skills")
        print(f"   - {len(employees)} employees (with cognitive profiles)")
        print(f"   - {len(goals)} strategic goals (with required skills)")
        print(f"\n🎯 You can now test:")
        print(f"   - View employees and their skills")
        print(f"   - View strategic goals and required skills")
        print(f"   - Run gap analysis between employees and goals")
        print(f"   - Generate learning paths")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)

