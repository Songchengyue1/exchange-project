import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings

logger = logging.getLogger(__name__)
from app.db import init_database, run_seed_data
from app.routers import admin, ai, auth, categories, feedback, orders, products, reviews, user_addresses, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("uploads").mkdir(parents=True, exist_ok=True)
    init_database()
    if settings.seed_on_startup:
        run_seed_data(include_demo_admin=False)
    if settings.ai_embed_batch_on_startup:
        from app.database import SessionLocal
        from app.services.ai.embedding_index import EmbeddingIndexService

        db = SessionLocal()
        try:
            n = EmbeddingIndexService(db).index_all_approved()
            logger.info("AI embedding index on startup: %s products", n)
        except Exception as exc:
            logger.warning("AI embedding index skipped: %s", exc)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(user_addresses.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")

Path("uploads").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/v1")
def api_root():
    return {
        "message": "酱菜交易平台 API",
        "docs": "/docs",
        "auth": "/api/v1/auth/register | /api/v1/auth/login",
        "users": "/api/v1/users/me",
        "categories": "/api/v1/categories",
        "products": "/api/v1/products | /api/v1/products/favorites",
        "orders": "/api/v1/orders | /api/v1/orders/{id}/fulfill",
        "reviews": "/api/v1/reviews/mine | POST /api/v1/orders/{id}/review",
        "feedback": "/api/v1/feedback | /api/v1/feedback/mine",
        "admin": "/api/v1/admin/users | /api/v1/admin/orders | /api/v1/admin/categories | /api/v1/admin/products/pending | /api/v1/admin/feedback | /api/v1/admin/audit-logs",
        "ai": "/api/v1/ai/search | /api/v1/ai/chat (SSE) | /api/v1/ai/recommendations",
    }
