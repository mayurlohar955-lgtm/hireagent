



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.user import User, Company
from app.services.auth_service import (
    hash_password, verify_password, create_access_token,
    validate_password_strength, make_slug
)
from app.api.deps import get_current_user, CurrentUser
import uuid

router = APIRouter()


#  Schemas 

class RegisterRequest(BaseModel):
    company_name: str
    full_name:    str
    email:        str
    password:     str

class LoginRequest(BaseModel):
    email:    str
    password: str

class InviteUserRequest(BaseModel):
    email:     str
    full_name: str
    role:      str = "recruiter"   # admin, recruiter, 
    password:  str

class ActivatePlanRequest(BaseModel):
    company_id: str
    plan:       str   # starter, growth, scale
    days:       int   # how many days to activate

class BlockCompanyRequest(BaseModel):
    company_id: str
    reason: str = "non-payment"


# Register new company + admin user 

@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Creates a new company and its first admin user in one step.
    This is the onboarding flow — HR manager signs up, company is created.
    """
    validate_password_strength(req.password)

    # Check email not already used
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    # Generate unique slug for tenant isolation
    base_slug = make_slug(req.company_name)
    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Company).where(Company.slug == slug))
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create company
    company = Company(
        id=str(uuid.uuid4()),
        name=req.company_name,
        slug=slug,
        plan="trial",
        # change 30 to any number
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),  
    )
    db.add(company)
    await db.flush()

    # Create first user as admin
    user = User(
        id=str(uuid.uuid4()),
        company_id=company.id,
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role="admin",
    )
    db.add(user)
    await db.flush()

    token = create_access_token(user.id, company.id, user.role)

    return {
        "token":   token,
        "user":    _user_dict(user),
        "company": _company_dict(company),
        "message": f"Welcome to HireAgent, {req.full_name}! Your company workspace is ready.",
    }


# Login 

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == req.email.lower(), User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")

    # Load company
    result = await db.execute(select(Company).where(Company.id == user.company_id))
    company = result.scalar_one_or_none()
    if not company or not company.is_active:
        raise HTTPException(403, "Company account is inactive")

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    token = create_access_token(user.id, company.id, user.role)

    return {
        "token":   token,
        "user":    _user_dict(user),
        "company": _company_dict(company),
    }


# Get current user

@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)):
    return {
        "id":         current_user.id,
        "email":      current_user.email,
        "full_name":  current_user.full_name,
        "role":       current_user.role,
        "tenant_id":  current_user.tenant_id,
        "company": {
            "id":   current_user.company.id,
            "name": current_user.company.name,
            "plan": current_user.company.plan,
        }
    }


# Invite team member 

@router.post("/invite", status_code=201)
async def invite_user(
    req: InviteUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin invites a colleague to join the same company workspace."""
    if current_user.role != "admin":
        raise HTTPException(403, "Only admins can invite users")

    validate_password_strength(req.password)

    result = await db.execute(select(User).where(User.email == req.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        company_id=current_user.company_id,
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    db.add(user)
    await db.flush()

    return {
        "user":    _user_dict(user),
        "message": f"{req.full_name} added to {current_user.company.name}",
    }


# Helpers 

def _user_dict(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role}

def _company_dict(c: Company) -> dict:
    return {"id": c.id, "name": c.name, "slug": c.slug, "plan": c.plan}



# Add to backend/app/api/v1/auth.py
@router.post("/admin/activate", status_code=200)
async def activate_plan(
    req: ActivatePlanRequest,
    db: AsyncSession = Depends(get_db),
    # In production add: admin_key: str = Header(...)
):
    result = await db.execute(select(Company).where(Company.id == req.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(404, "Company not found")

    company.plan       = req.plan
    company.paid_until = datetime.now(timezone.utc) + timedelta(days=req.days)
    await db.flush()

    return {
        "company":    company.name,
        "plan":       company.plan,
        "paid_until": company.paid_until.isoformat(),
        "message":    f"{company.name} activated on {req.plan} for {req.days} days"
    }

@router.post("/admin/block", status_code=200)
async def block_company(
    req: BlockCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == req.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(404, "Company not found")

    # this blocks ALL access immediately
    company.is_active = False    
    await db.flush()

    return {
        "company": company.name,
        "blocked": True,
        "reason":  req.reason,
        "message": f"{company.name} access blocked immediately"
    }


@router.get("/admin/billing-status")
async def billing_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.is_active == True))
    companies = result.scalars().all()
    now = datetime.now(timezone.utc)

    return [
        {
            "name":          c.name,
            "id":            c.id,
            "plan":          c.plan,
            "status":        _get_status(c, now),
            "trial_ends_at": c.trial_ends_at.isoformat() if c.trial_ends_at else None,
            "paid_until":    c.paid_until.isoformat() if c.paid_until else None,
            "days_left":     _days_left(c, now),
        }
        for c in companies
    ]

def _get_status(c: Company, now) -> str:
    if not c.is_active:
        return "blocked"
    if c.plan == "trial":
        if not c.trial_ends_at: return "trial-no-expiry"
        return "active-trial" if now < c.trial_ends_at else "trial-expired"
    if c.paid_until:
        return "active-paid" if now < c.paid_until else "payment-overdue"
    return "unknown"

def _days_left(c: Company, now) -> int:
    if c.plan == "trial" and c.trial_ends_at:
        return max(0, (c.trial_ends_at - now).days)
    if c.paid_until:
        return max(0, (c.paid_until - now).days)
    return 0



# List all companies 

@router.get("/admin/companies")
async def list_all_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = result.scalars().all()
    now = datetime.now(timezone.utc)
    return [
        {
            "id":            c.id,
            "name":          c.name,
            "slug":          c.slug,
            "plan":          c.plan,
            "is_active":     c.is_active,
            "status":        _get_status(c, now),
            "days_left":     _days_left(c, now),
            "trial_ends_at": c.trial_ends_at.isoformat() if c.trial_ends_at else None,
            "paid_until":    c.paid_until.isoformat() if c.paid_until else None,
            "created_at":    c.created_at.isoformat() if c.created_at else None,
        }
        for c in companies
    ]


# List all users 

@router.get("/admin/users")
async def list_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User, Company)
        .join(Company, User.company_id == Company.id)
        .order_by(User.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "user_id":      u.id,
            "full_name":    u.full_name,
            "email":        u.email,
            "role":         u.role,
            "is_active":    u.is_active,
            "last_login":   u.last_login.isoformat() if u.last_login else "never",
            "created_at":   u.created_at.isoformat() if u.created_at else None,
            "company_id":   c.id,
            "company_name": c.name,
            "company_plan": c.plan,
        }
        for u, c in rows
    ]


# Unblock company 

@router.post("/admin/unblock", status_code=200)
async def unblock_company(
    req: BlockCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == req.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(404, "Company not found")

    company.is_active  = True
    company.plan       = "trial"
    company.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=30)
    await db.flush()

    return {
        "company":   company.name,
        "unblocked": True,
        "message":   f"{company.name} unblocked, trial reset to 30 days"
    }



