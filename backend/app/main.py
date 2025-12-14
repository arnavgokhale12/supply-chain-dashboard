from fastapi import FastAPI

from app.core.config import settings
from app.routers.health import router as health_router
from app.routers.series import router as series_router
from app.routers.observations import router as observations_router
from app.routers.composite import router as composite_router

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(series_router)
app.include_router(observations_router)
app.include_router(composite_router)
