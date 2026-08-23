from fastapi import APIRouter

from app.api.v1 import questions, quiz_attempts, subjects, topics

api_router = APIRouter()
api_router.include_router(subjects.router)
api_router.include_router(topics.router)
api_router.include_router(questions.router)
api_router.include_router(quiz_attempts.router)