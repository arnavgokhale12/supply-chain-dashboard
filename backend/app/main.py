from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.routers.health import router as health_router
from backend.app.routers.series import router as series_router
from backend.app.routers.observations import router as observations_router
from backend.app.routers.composite import router as composite_router
from backend.app.routers.market import router as market_router

app = FastAPI(title=settings.app_name)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(series_router)
app.include_router(observations_router)
app.include_router(composite_router)
app.include_router(market_router)
