from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import FRONTEND_DIR, LANDING_DIR, settings
from backend.routers import run, scenarios


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(scenarios.router, prefix=settings.api_prefix)
    app.include_router(run.router, prefix=settings.api_prefix)

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")

    @app.get("/")
    def landing() -> FileResponse:
        return FileResponse(LANDING_DIR / "index.html")

    @app.get("/scrollcraft.css")
    def landing_css() -> FileResponse:
        return FileResponse(LANDING_DIR / "scrollcraft.css", media_type="text/css")

    @app.get("/scrollcraft.js")
    def landing_js() -> FileResponse:
        return FileResponse(LANDING_DIR / "scrollcraft.js", media_type="text/javascript")

    @app.get("/lab")
    @app.get("/lab/")
    def lab() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
