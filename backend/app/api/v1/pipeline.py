from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.database import get_db
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.enums import PipelineStage
from app.api.deps import get_current_user, CurrentUser

router = APIRouter()

class MoveStageRequest(BaseModel):
    stage: PipelineStage
    notes: str = ""


@router.get("/{job_id}/board")
async def get_pipeline_board(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_user.tenant_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(
        select(Application, Candidate)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .where(Application.job_id == job_id, Application.tenant_id == current_user.tenant_id)
    )
    rows = result.all()

    board = {stage.value: [] for stage in PipelineStage}
    for app, cand in rows:
        board[app.stage.value].append({
            "application_id":   app.id,
            "candidate_id":     cand.id,
            "name":             cand.name,
            "email":            cand.email,
            "experience_years": cand.experience_years,
            "skills":           (cand.skills or [])[:5],
            "score_total":      app.score_total,
            "score_skills":     app.score_skills,
            "score_experience": app.score_experience,
            "score_relevance":  app.score_relevance,
            "strengths":        (app.score_strengths or [])[:2],
            "gaps":             (app.score_gaps or [])[:2],
            "reasoning":        app.score_reasoning,
            "notes":            app.notes,
            "screened":         app.score_total > 0,
            "updated_at":       app.updated_at.isoformat() if app.updated_at else None,
        })

    for stage in board:
        board[stage].sort(key=lambda x: x["score_total"], reverse=True)

    column_meta = {
        "applied":   {"label": "Applied",   "color": "#6366f1"},
        "screening": {"label": "Screening", "color": "#f59e0b"},
        "interview": {"label": "Interview", "color": "#3b82f6"},
        "offer":     {"label": "Offer",     "color": "#8b5cf6"},
        "hired":     {"label": "Hired",     "color": "#10b981"},
        "rejected":  {"label": "Rejected",  "color": "#ef4444"},
    }

    return {
        "job": {"id": job.id, "title": job.title, "status": job.status},
        "columns": [
            {
                **column_meta[stage],
                "stage": stage,
                "count": len(board[stage]),
                "cards": board[stage],
            }
            for stage in ["applied", "screening", "interview", "offer", "hired", "rejected"]
        ],
        "total_candidates": len(rows),
    }


@router.patch("/{job_id}/applications/{application_id}/move")
async def move_candidate_stage(
    job_id: str,
    application_id: str,
    req: MoveStageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Application).where(
            Application.id == application_id,
            Application.job_id == job_id,
            Application.tenant_id == current_user.tenant_id,
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    old_stage = application.stage
    application.stage = req.stage
    if req.notes:
        application.notes = req.notes
    await db.flush()
    return {"application_id": application_id, "from_stage": old_stage, "to_stage": req.stage, "updated": True}


@router.get("/{job_id}/stats")
async def get_pipeline_stats(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Application.stage, func.count(Application.id), func.avg(Application.score_total))
        .where(Application.job_id == job_id, Application.tenant_id == current_user.tenant_id)
        .group_by(Application.stage)
    )
    stats = {}
    for stage, count, avg_score in result.all():
        stats[stage.value] = {"count": count, "avg_score": round(avg_score or 0, 1)}
    return stats