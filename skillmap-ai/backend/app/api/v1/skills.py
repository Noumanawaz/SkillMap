from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.skills import SkillCreate, SkillOut, SkillMatchRequest, SkillMatchResult
from app.services.ontology_service import OntologyService


router = APIRouter()


@router.post("/", response_model=SkillOut)
def create_skill(payload: SkillCreate, db: Session = Depends(get_db)):
    service = OntologyService(db)
    return service.create_skill(payload)


@router.get("/", response_model=List[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    service = OntologyService(db)
    return service.list_skills()


@router.post("/match", response_model=List[SkillMatchResult])
def match_skill(req: SkillMatchRequest, db: Session = Depends(get_db)):
    service = OntologyService(db)
    return service.match_skill(req)


