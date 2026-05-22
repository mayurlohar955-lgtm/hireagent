


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from pydantic import BaseModel
# from typing import Optional
# from app.database import get_db
# from app.models.job import Job
# from app.models.enums import JobStatus
# from app.agents.mock_agent import generate_job_description
# import uuid

# router = APIRouter()
# DEMO_TENANT = "tenant_demo"


# class JobCreateRequest(BaseModel):
#     title: str
#     department: str
#     location: str
#     employment_type: str = "full-time"
#     experience_min: int = 2
#     experience_max: int = 6
#     skills: list[str]
#     salary_min: Optional[int] = None
#     salary_max: Optional[int] = None
#     additional_context: Optional[str] = None

# class JobUpdateRequest(BaseModel):
#     title: Optional[str] = None
#     status: Optional[JobStatus] = None
#     description: Optional[str] = None
#     requirements: Optional[list[str]] = None
#     skills_required: Optional[list[str]] = None

# class ImproveJDRequest(BaseModel):
#     existing_jd: str


# @router.post("/generate", status_code=201)
# async def generate_and_create_job(
#     req: JobCreateRequest,
#     db: AsyncSession = Depends(get_db)
# ):
#     try:
#         ai_result = await generate_job_description(
#             title=req.title,
#             department=req.department,
#             experience_min=req.experience_min,
#             experience_max=req.experience_max,
#             skills=req.skills,
#             location=req.location,
#             employment_type=req.employment_type,
#             salary_min=req.salary_min,
#             salary_max=req.salary_max,
#             additional_context=req.additional_context,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

#     job = Job(
#         id=str(uuid.uuid4()),
#         tenant_id=DEMO_TENANT,
#         title=req.title,
#         department=req.department,
#         location=req.location,
#         employment_type=req.employment_type,
#         experience_min=req.experience_min,
#         experience_max=req.experience_max,
#         description=ai_result["description"],
#         requirements=ai_result.get("requirements", []),
#         skills_required=ai_result.get("skills_required", req.skills),
#         salary_min=req.salary_min,
#         salary_max=req.salary_max,
#         bias_flags=ai_result.get("bias_flags", []),
#         status=JobStatus.draft,
#     )
#     db.add(job)
#     await db.flush()

#     return {
#         "job": _job_to_dict(job),
#         "ai_extras": {
#             "what_you_will_do": ai_result.get("what_you_will_do", []),
#             "what_we_offer":    ai_result.get("what_we_offer", []),
#             "bias_flags":       ai_result.get("bias_flags", []),
#         }
#     }


# @router.post("/improve")
# async def improve_jd(req: ImproveJDRequest):
#     return {
#         "improved_description": req.existing_jd,
#         "changes_made": ["Mock mode - no real changes applied"],
#         "bias_flags": []
#     }


# @router.get("/")
# async def list_jobs(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(
#         select(Job).where(Job.tenant_id == DEMO_TENANT).order_by(Job.created_at.desc())
#     )
#     return [_job_to_dict(j) for j in result.scalars().all()]


# @router.get("/{job_id}")
# async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
#     return _job_to_dict(await _get_job_or_404(job_id, db))


# @router.patch("/{job_id}")
# async def update_job(job_id: str, req: JobUpdateRequest, db: AsyncSession = Depends(get_db)):
#     job = await _get_job_or_404(job_id, db)
#     for field, value in req.model_dump(exclude_none=True).items():
#         setattr(job, field, value)
#     await db.flush()
#     return _job_to_dict(job)


# @router.delete("/{job_id}", status_code=204)
# async def delete_job(job_id: str, db: AsyncSession = Depends(get_db)):
#     await db.delete(await _get_job_or_404(job_id, db))


# async def _get_job_or_404(job_id: str, db: AsyncSession) -> Job:
#     result = await db.execute(
#         select(Job).where(Job.id == job_id, Job.tenant_id == DEMO_TENANT)
#     )
#     job = result.scalar_one_or_none()
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
#     return job

# def _job_to_dict(job: Job) -> dict:
#     return {
#         "id":              job.id,
#         "title":           job.title,
#         "department":      job.department,
#         "location":        job.location,
#         "employment_type": job.employment_type,
#         "experience_min":  job.experience_min,
#         "experience_max":  job.experience_max,
#         "description":     job.description,
#         "requirements":    job.requirements,
#         "skills_required": job.skills_required,
#         "salary_min":      job.salary_min,
#         "salary_max":      job.salary_max,
#         "status":          job.status,
#         "bias_flags":      job.bias_flags,
#         "created_at":      job.created_at.isoformat() if job.created_at else None,
#     }




# backend/app/api/v1/jobs.py  — FULL FILE WITH AUTH
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.job import Job
from app.models.enums import JobStatus
from app.agents.mock_agent import generate_job_description
from app.api.deps import get_current_user, CurrentUser
import uuid

router = APIRouter()


class JobCreateRequest(BaseModel):
    title: str
    department: str
    location: str
    employment_type: str = "full-time"
    experience_min: int = 2
    experience_max: int = 6
    skills: list[str]
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    additional_context: Optional[str] = None

class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[JobStatus] = None
    description: Optional[str] = None
    requirements: Optional[list[str]] = None
    skills_required: Optional[list[str]] = None

class ImproveJDRequest(BaseModel):
    existing_jd: str


@router.post("/generate", status_code=201)
async def generate_and_create_job(
    req: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),   # ← real auth
):
    try:
        ai_result = await generate_job_description(
            title=req.title,
            department=req.department,
            experience_min=req.experience_min,
            experience_max=req.experience_max,
            skills=req.skills,
            location=req.location,
            employment_type=req.employment_type,
            salary_min=req.salary_min,
            salary_max=req.salary_max,
            additional_context=req.additional_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    job = Job(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,     # ← real tenant from JWT
        title=req.title,
        department=req.department,
        location=req.location,
        employment_type=req.employment_type,
        experience_min=req.experience_min,
        experience_max=req.experience_max,
        description=ai_result["description"],
        requirements=ai_result.get("requirements", []),
        skills_required=ai_result.get("skills_required", req.skills),
        salary_min=req.salary_min,
        salary_max=req.salary_max,
        bias_flags=ai_result.get("bias_flags", []),
        status=JobStatus.draft,
    )
    db.add(job)
    await db.flush()

    return {
        "job": _job_to_dict(job),
        "ai_extras": {
            "what_you_will_do": ai_result.get("what_you_will_do", []),
            "what_we_offer":    ai_result.get("what_we_offer", []),
            "bias_flags":       ai_result.get("bias_flags", []),
        }
    }


@router.post("/improve")
async def improve_jd(
    req: ImproveJDRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    return {
        "improved_description": req.existing_jd,
        "changes_made": ["Mock mode"],
        "bias_flags": []
    }


@router.get("/")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Job)
        .where(Job.tenant_id == current_user.tenant_id)
        .order_by(Job.created_at.desc())
    )
    return [_job_to_dict(j) for j in result.scalars().all()]


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return _job_to_dict(await _get_job_or_404(job_id, current_user.tenant_id, db))


@router.patch("/{job_id}")
async def update_job(
    job_id: str,
    req: JobUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    job = await _get_job_or_404(job_id, current_user.tenant_id, db)
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(job, field, value)
    await db.flush()
    return _job_to_dict(job)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    await db.delete(await _get_job_or_404(job_id, current_user.tenant_id, db))


async def _get_job_or_404(job_id: str, tenant_id: str, db: AsyncSession) -> Job:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def _job_to_dict(job: Job) -> dict:
    return {
        "id":              job.id,
        "title":           job.title,
        "department":      job.department,
        "location":        job.location,
        "employment_type": job.employment_type,
        "experience_min":  job.experience_min,
        "experience_max":  job.experience_max,
        "description":     job.description,
        "requirements":    job.requirements,
        "skills_required": job.skills_required,
        "salary_min":      job.salary_min,
        "salary_max":      job.salary_max,
        "status":          job.status,
        "bias_flags":      job.bias_flags,
        "created_at":      job.created_at.isoformat() if job.created_at else None,
    }




