


from sqlalchemy import Column, String, Float, Text, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import PipelineStage
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc)
def new_uuid(): return str(uuid.uuid4())

class Application(Base):
    __tablename__ = "applications"          # ← was "application", now plural

    id               = Column(String, primary_key=True, default=new_uuid)
    tenant_id        = Column(String, nullable=False, index=True)
    job_id           = Column(String, ForeignKey("jobs.id"), nullable=False)
    candidate_id     = Column(String, ForeignKey("candidates.id"), nullable=False)
    stage            = Column(SAEnum(PipelineStage), default=PipelineStage.applied)

    score_skills     = Column(Float, default=0)
    score_experience = Column(Float, default=0)
    score_relevance  = Column(Float, default=0)
    score_total      = Column(Float, default=0)
    score_reasoning  = Column(Text)
    score_strengths  = Column(JSON, default=list)
    score_gaps       = Column(JSON, default=list)
    notes            = Column(Text)
    created_at       = Column(DateTime(timezone=True), default=utcnow)
    updated_at       = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    job              = relationship("Job",       back_populates="applications")
    candidate        = relationship("Candidate", back_populates="applications")