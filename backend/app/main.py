


# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# from app.database import create_tables
# from app.api.v1 import jobs, candidates, pipeline, auth   # add auth
# import app.models

# from app.api.v1 import jobs, candidates, pipeline

# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await create_tables()
#     yield

# app = FastAPI(title="HR Agent API", version="1.0.0", lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(jobs.router,       prefix="/api/v1/jobs",       tags=["Jobs"])
# app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["Candidates"])
# app.include_router(pipeline.router,   prefix="/api/v1/pipeline",   tags=["Pipeline"])

# @app.get("/health")
# async def health():
#     return {"status": "ok"}



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import create_tables
import app.models

from app.api.v1 import jobs, candidates, pipeline, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield

app = FastAPI(title="HR Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["Auth"])
app.include_router(jobs.router,       prefix="/api/v1/jobs",       tags=["Jobs"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["Candidates"])
app.include_router(pipeline.router,   prefix="/api/v1/pipeline",   tags=["Pipeline"])

@app.get("/health")
async def health():
    return {"status": "ok"}


