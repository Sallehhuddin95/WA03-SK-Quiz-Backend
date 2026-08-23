from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import ApiError


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError):
        body: dict = {"mesej": exc.mesej, "kod": exc.kod}
        if exc.butiran:
            body["butiran"] = exc.butiran
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": body},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        butiran: dict[str, list[str]] = {}
        for error in exc.errors():
            loc = [str(part) for part in error.get("loc", [])]
            field = ".".join(
                part for part in loc if part not in ("body", "query", "path")
            )
            if not field:
                field = "borang"
            butiran.setdefault(field, []).append(str(error.get("msg", "Nilai tidak sah.")))
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "mesej": "Data yang dihantar tidak sah.",
                    "kod": "VALIDASI_GAGAL",
                    "butiran": butiran,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "mesej": "Ralat tidak dijangka. Sila cuba lagi.",
                    "kod": "RALAT_TIDAK_DIJANGKA",
                }
            },
        )

    return app


app = create_app()