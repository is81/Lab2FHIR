"""Lab2FHIR FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ..config import get_settings
from .routes_reports import router as reports_router
from .routes_convert import router as convert_router
from ..db.models import init_db, init_fts

_settings = get_settings()

# 日志配置
logging.basicConfig(
    level=getattr(logging, _settings.LOG_LEVEL),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("lab2fhir")


# 4.2 修复：使用 lifespan 替代 deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_fts()
    logger.info("Lab2FHIR started")
    yield


app = FastAPI(
    title="Lab2FHIR",
    description="化验单 PDF → FHIR R4 转换服务",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router, prefix="/api")
app.include_router(convert_router, prefix="/api")

from .routes_auth import router as auth_router
app.include_router(auth_router, prefix="/api")


# 2.4 修复：全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "服务器内部错误", "detail": str(exc)})


@app.get("/api/health")
def health():
    return {"status": "ok"}
