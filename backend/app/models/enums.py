



import enum

class JobStatus(str, enum.Enum):
    draft     = "draft"
    active    = "active"
    paused    = "paused"
    closed    = "closed"

class PipelineStage(str, enum.Enum):
    applied   = "applied"
    screening = "screening"
    interview = "interview"
    offer     = "offer"
    hired     = "hired"
    rejected  = "rejected"