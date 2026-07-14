"""Lab2FHIR FastAPI 应用入口"""
import os
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ..config import get_settings
from .routes_reports import router as reports_router
from .routes_convert import router as convert_router
from ..db.models import init_db, init_fts

_settings = get_settings()

# 日志配置（控制台 + 文件，保留最近 10MB × 3）
LOG_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_FILE = os.path.join(LOG_DIR, "lab2fhir.log")

root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, _settings.LOG_LEVEL))

# 控制台
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
root_logger.addHandler(console)

# 文件
try:
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    root_logger.addHandler(file_handler)
except Exception as e:
    print(f"WARNING: 无法创建日志文件 {LOG_FILE}: {e}")

logger = logging.getLogger("lab2fhir")
logger.info(f"Lab2FHIR 启动，日志: {LOG_FILE}")


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
