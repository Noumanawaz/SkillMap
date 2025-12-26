from typing import List, Optional
from uuid import UUID

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.db.models import Skill
from app.schemas.skills import SkillCreate, SkillOut, SkillMatchRequest, SkillMatchResult
from app.vector.base import get_vector_store


_ST_MODEL: Optional[SentenceTransformer] = None


def _get_st_model() -> SentenceTransformer:
    global _ST_MODEL
    if _ST_MODEL is None:
        _ST_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _ST_MODEL


class OntologyService:
    def __init__(self, db: Session):
        self.db = db
        self.vectors = get_vector_store()

    def create_skill(self, payload: SkillCreate) -> SkillOut:
        skill = Skill(
            name=payload.name,
            category=payload.category,
            domain=payload.domain,
            description=payload.description,
            parent_skill_id=UUID(payload.parent_skill_id) if payload.parent_skill_id else None,
            prerequisites=[str(UUID(p)) for p in payload.prerequisites] if payload.prerequisites else None,  # JSON stores as strings
            is_future_skill=payload.is_future_skill,
            ontology_version=payload.ontology_version,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
        )
        self.db.add(skill)
        self.db.flush()

        emb = self._embed_skill(skill)
        self.vectors.upsert(
            id=str(skill.skill_id),
            vector=emb,
            metadata={
                "name": skill.name,
                "domain": skill.domain,
                "category": skill.category,
                "ontology_version": skill.ontology_version,
            },
        )
        self.db.commit()
        self.db.refresh(skill)
        return SkillOut(
            skill_id=str(skill.skill_id),
            name=skill.name,
            category=skill.category,
            domain=skill.domain,
            description=skill.description,
            is_future_skill=skill.is_future_skill,
            ontology_version=skill.ontology_version,
            created_at=skill.created_at,
        )

    def list_skills(self) -> List[SkillOut]:
        rows = self.db.query(Skill).all()
        return [
            SkillOut(
                skill_id=str(r.skill_id),
                name=r.name,
                category=r.category,
                domain=r.domain,
                description=r.description,
                is_future_skill=r.is_future_skill,
                ontology_version=r.ontology_version,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def match_skill(self, req: SkillMatchRequest) -> List[SkillMatchResult]:
        model = _get_st_model()
        vec = model.encode([req.phrase])[0].tolist()
        results = self.vectors.query(vec, top_k=req.top_k)

        out: List[SkillMatchResult] = []
        for sid, score, _meta in results:
            row = self.db.get(Skill, UUID(sid))
            if not row:
                continue
            out.append(
                SkillMatchResult(
                    skill=SkillOut(
                        skill_id=str(row.skill_id),
                        name=row.name,
                        category=row.category,
                        domain=row.domain,
                        description=row.description,
                        is_future_skill=row.is_future_skill,
                        ontology_version=row.ontology_version,
                        created_at=row.created_at,
                    ),
                    score=score,
                )
            )
        return out

    def _embed_skill(self, skill: Skill) -> List[float]:
        model = _get_st_model()
        text = f"{skill.name}. {skill.description or ''} [{skill.domain or ''} {skill.category or ''}]"
        return model.encode([text])[0].tolist()


