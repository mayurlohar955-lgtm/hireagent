


from sqlalchemy import Column, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc)
def new_uuid(): return str(uuid.uuid4())

class Candidate(Base):
    __tablename__ = "candidates"

    id               = Column(String, primary_key=True, default=new_uuid)
    tenant_id        = Column(String, nullable=False, index=True)
    name             = Column(String(200))
    email            = Column(String(200), index=True)
    phone            = Column(String(50))
    location         = Column(String(100))
    resume_url       = Column(String(500))
    resume_text      = Column(Text)
    parsed_data      = Column(JSON)
    skills           = Column(JSON, default=list)
    experience_years = Column(Float, default=0)
    education        = Column(JSON, default=list)
    previous_roles   = Column(JSON, default=list)
    resume_embedding = Column(Vector(1536))
    created_at       = Column(DateTime(timezone=True), default=utcnow)

    applications     = relationship("Application", back_populates="candidate", cascade="all, delete")