from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1 import strategy, skills, profiles, gaps, learning, assessments


settings = get_settings()

app = FastAPI(title="SkillMap AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategy.router, prefix="/v1/strategy", tags=["strategy"])
app.include_router(skills.router, prefix="/v1/skills", tags=["skills"])
app.include_router(profiles.router, prefix="/v1/profiles", tags=["profiles"])
app.include_router(gaps.router, prefix="/v1/gaps", tags=["gaps"])
app.include_router(learning.router, prefix="/v1", tags=["learning"])
app.include_router(assessments.router, prefix="/v1/assessments", tags=["assessments"])


@app.get("/health")
def health():
    return {"status": "ok"}


