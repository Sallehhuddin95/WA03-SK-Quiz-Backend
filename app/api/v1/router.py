from fastapi import APIRouter

from app.api.v1 import (
    auth,
    kelas,
    kuiz_pratonton,
    questions,
    quiz_attempts,
    subjects,
    topics,
    users,
)

api_router = APIRouter()
api_router.include_router(subjects.router)
api_router.include_router(topics.router)
api_router.include_router(questions.router)
api_router.include_router(quiz_attempts.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(kelas.router)
api_router.include_router(kelas.guru_router)
api_router.include_router(kuiz_pratonton.router)