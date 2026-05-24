from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models.candidate import Candidate
from app.models.application import Application
from app.models.job import Job
from app.models.enums import PipelineStage
from app.agents.mock_agent import screen_resume_from_bytes
from app.api.deps import get_current_user, CurrentUser
import uuid

router = APIRouter()
MAX_PDF_SIZE = 5 * 1024 * 1024


async def _screen_and_save(candidate_id: str, pdf_bytes: bytes, job_id: str, tenant_id: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                return
            screening = await screen_resume_from_bytes(
                pdf_bytes=pdf_bytes,
                job_title=job.title,
                job_description=job.description or "",
                skills_required=job.skills_required or [],
                experience_min=job.experience_min or 0,
                experience_max=job.experience_max or 10,
            )
            result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
            candidate = result.scalar_one_or_none()
            if candidate:
                candidate.name             = screening.get("name") or candidate.name
                candidate.email            = screening.get("email") or candidate.email
                candidate.phone            = screening.get("phone")
                candidate.location         = screening.get("location")
                candidate.resume_text      = screening["resume_text"]
                candidate.parsed_data      = screening["parsed_data"]
                candidate.skills           = screening.get("skills", [])
                candidate.experience_years = screening.get("experience_years", 0)
                candidate.education        = screening.get("education", [])
                candidate.previous_roles   = screening.get("previous_roles", [])
            result = await db.execute(
                select(Application).where(
                    Application.candidate_id == candidate_id,
                    Application.job_id == job_id,
                )
            )
            application = result.scalar_one_or_none()
            scores = screening["scores"]
            if application:
                application.score_skills     = scores["skills_score"]
                application.score_experience = scores["experience_score"]
                application.score_relevance  = scores["relevance_score"]
                application.score_total      = scores["total_score"]
                application.score_reasoning  = scores["reasoning"]
                application.score_strengths  = scores.get("strengths", [])
                application.score_gaps       = scores.get("gaps", [])
                application.stage            = PipelineStage.screening
            await db.commit()
        except Exception as e:
            await db.rollback()
            print(f"Screening error for candidate {candidate_id}: {e}")


@router.post("/upload/{job_id}", status_code=202)
async def upload_resume(
    job_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    candidate_name: Optional[str] = Form(None),
    candidate_email: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    candidate = Candidate(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=candidate_name or "Processing...",
        email=candidate_email or "",
        resume_url=f"uploads/{job_id}/{file.filename}",
    )
    db.add(candidate)
    application = Application(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        candidate_id=candidate.id,
        stage=PipelineStage.applied,
    )
    db.add(application)
    await db.flush()
    background_tasks.add_task(
        _screen_and_save,
        candidate_id=candidate.id,
        pdf_bytes=pdf_bytes,
        job_id=job_id,
        tenant_id=current_user.tenant_id,
    )
    return {
        "candidate_id":   candidate.id,
        "application_id": application.id,
        "status":         "processing",
        "message":        "Resume received. AI screening running in background."
    }


@router.post("/bulk-upload/{job_id}", status_code=202)
async def bulk_upload_resumes(
    job_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 resumes per batch")
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    submitted = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            submitted.append({"file": file.filename, "status": "skipped", "reason": "not a PDF"})
            continue
        pdf_bytes = await file.read()
        if len(pdf_bytes) > MAX_PDF_SIZE:
            submitted.append({"file": file.filename, "status": "skipped", "reason": "too large"})
            continue
        candidate = Candidate(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            name="Processing...",
            resume_url=f"uploads/{job_id}/{file.filename}",
        )
        db.add(candidate)
        application = Application(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            job_id=job_id,
            candidate_id=candidate.id,
            stage=PipelineStage.applied,
        )
        db.add(application)
        await db.flush()
        background_tasks.add_task(
            _screen_and_save,
            candidate_id=candidate.id,
            pdf_bytes=pdf_bytes,
            job_id=job_id,
            tenant_id=current_user.tenant_id,
        )
        submitted.append({"file": file.filename, "status": "processing", "candidate_id": candidate.id})
    return {
        "submitted": len([s for s in submitted if s["status"] == "processing"]),
        "details": submitted
    }


@router.get("/{job_id}/ranked")
async def get_ranked_candidates(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Application, Candidate)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .where(Application.job_id == job_id, Application.tenant_id == current_user.tenant_id)
        .order_by(Application.score_total.desc())
    )
    return [
        {
            "application_id":   app.id,
            "candidate_id":     cand.id,
            "name":             cand.name,
            "email":            cand.email,
            "experience_years": cand.experience_years,
            "skills":           cand.skills,
            "stage":            app.stage,
            "scores": {
                "skills":     app.score_skills,
                "experience": app.score_experience,
                "relevance":  app.score_relevance,
                "total":      app.score_total,
            },
            "strengths": app.score_strengths,
            "gaps":      app.score_gaps,
            "reasoning": app.score_reasoning,
            "screened":  app.score_total > 0,
        }
        for app, cand in result.all()
    ]