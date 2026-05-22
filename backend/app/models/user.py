



from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid

def utcnow(): return datetime.now(timezone.utc)
def new_uuid(): return str(uuid.uuid4())


# class Company(Base):
#     __tablename__ = "companies"

#     id           = Column(String, primary_key=True, default=new_uuid)
#     name         = Column(String(200), nullable=False)
#     slug         = Column(String(100), unique=True, nullable=False)  # used as tenant_id
#     email_domain = Column(String(100))   # e.g. "infosys.com" for auto-join
#     plan         = Column(String(50), default="starter")  # starter, growth, scale
#     is_active    = Column(Boolean, default=True)                                                               # Billing control fields — add these:
#     trial_ends_at   = Column(DateTime(timezone=True))          # when free trial expires
#     paid_until      = Column(DateTime(timezone=True))          # when subscription expires
#     stripe_customer_id = Column(String(200))                   # for Stripe later
#     created_at      = Column(DateTime(timezone=True), default=utcnow)
#     users           = relationship("User", back_populates="company", cascade="all, delete")


class Company(Base):
    __tablename__ = "companies"

    id                 = Column(String, primary_key=True, default=new_uuid)
    name               = Column(String(200), nullable=False)
    slug               = Column(String(100), unique=True, nullable=False)
    email_domain       = Column(String(100))
    plan               = Column(String(50), default="trial")
    is_active          = Column(Boolean, default=True)
    trial_ends_at      = Column(DateTime(timezone=True))
    paid_until         = Column(DateTime(timezone=True))
    stripe_customer_id = Column(String(200))
    created_at         = Column(DateTime(timezone=True), default=utcnow)

    users = relationship("User", back_populates="company", cascade="all, delete")

    
class User(Base):
    __tablename__ = "users"

    id             = Column(String, primary_key=True, default=new_uuid)
    company_id     = Column(String, ForeignKey("companies.id"), nullable=False)
    email          = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password= Column(String(500), nullable=False)
    full_name      = Column(String(200))
    role           = Column(String(50), default="recruiter")  # admin, recruiter, viewer
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime(timezone=True), default=utcnow)
    last_login     = Column(DateTime(timezone=True))

    company = relationship("Company", back_populates="users")