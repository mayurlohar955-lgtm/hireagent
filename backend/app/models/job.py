


from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.models.enums import JobStatus
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc)
def new_uuid(): return str(uuid.uuid4())

class Job(Base):
    __tablename__ = "jobs"

    id              = Column(String, primary_key=True, default=new_uuid)
    tenant_id       = Column(String, nullable=False, index=True)
    title           = Column(String(200), nullable=False)
    department      = Column(String(100))
    location        = Column(String(100))
    employment_type = Column(String(50))
    experience_min  = Column(Integer, default=0)
    experience_max  = Column(Integer, default=10)
    description     = Column(Text)
    requirements    = Column(JSON, default=list)
    skills_required = Column(JSON, default=list)
    salary_min      = Column(Integer)
    salary_max      = Column(Integer)
    status          = Column(SAEnum(JobStatus), default=JobStatus.draft)
    bias_flags      = Column(JSON, default=list)
    jd_embedding    = Column(Vector(1536))
    created_at      = Column(DateTime(timezone=True), default=utcnow)
    updated_at      = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    applications    = relationship("Application", back_populates="job", cascade="all, delete")