from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.lesson import router as lesson_router

app = FastAPI(
    title="LessonSynth - 教学活动设计 Agent",
    description="基于 LangGraph 的多智能体教学活动设计系统",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lesson_router)


@app.get("/")
def root():
    return {"service": "LessonSynth", "status": "running", "model": settings.deepseek_model}


@app.get("/health")
def health():
    return {"status": "ok"}
