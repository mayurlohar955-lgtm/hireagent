



from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.database import get_db
from app.services.auth_service import decode_token
from app.models.user import User, Company

bearer_scheme = HTTPBearer()


class CurrentUser:
    """Injected into every protected route via Depends(get_current_user)."""
    def __init__(self, user: User, company: Company):
        self.id         = user.id
        self.email      = user.email
        self.full_name  = user.full_name
        self.role       = user.role
        self.company_id = company.id
        # this replaces DEMO_TENANT everywhere
        self.tenant_id  = company.slug   
        self.company    = company


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    token = credentials.credentials
    payload = decode_token(token)

    user_id    = payload.get("sub")
    company_id = payload.get("company_id")

    if not user_id or not company_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Load user
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Load company
    result = await db.execute(select(Company).where(Company.id == company_id, Company.is_active == True))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=401, detail="Company not found or inactive")

   
    now = datetime.now(timezone.utc)
    if company.plan == "trial":
        if company.trial_ends_at and now > company.trial_ends_at:
            raise HTTPException(
                status_code=402,
                detail="Your free trial has expired. Please upgrade to continue."
            )
    elif company.plan in ("starter", "growth", "scale"):
        if company.paid_until and now > company.paid_until:
            raise HTTPException(
                status_code=402,
                detail="Your subscription has expired. Please renew to continue."
            )
        

    return CurrentUser(user=user, company=company)


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Use this dependency for admin-only routes."""
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user