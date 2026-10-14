from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.modules.autenticacion import routes as auth
from app.modules.coordinacion import routes as admin, portal_routes as coordination
from app.modules.estudiantes import portal_routes as students
from app.modules.compartido import routes as portal
from app.modules.compartido import documents
from app.modules.compartido import newsletter
from app.modules.compartido import editorial_media
from app.modules.innovacion import routes as innovatec
from botocore.exceptions import BotoCoreError, ClientError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from fastapi.exceptions import RequestValidationError
from app.request_safety import BodyLimitMiddleware
from app.schemas.validation import validation_errors
import app.models  # noqa: F401 — el esquema se administra con Alembic


app = FastAPI(title="Incubadora TecNM Saltillo — API")
app.add_middleware(BodyLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(portal.router)
app.include_router(coordination.router)
app.include_router(students.router)
app.include_router(documents.router)
app.include_router(newsletter.router)
app.include_router(editorial_media.router)
app.include_router(innovatec.router)
app.include_router(innovatec.public)


@app.exception_handler(RequestValidationError)
async def request_validation_error(request, exc):
    # FastAPI's default includes submitted values; never reflect passwords/files.
    errors = validation_errors(exc.errors())
    return JSONResponse(status_code=422, content={"detail": errors})


@app.middleware("http")
async def response_headers(request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:
        logging.getLogger(__name__).error("Request failed: %s", type(exc).__name__)
        response = JSONResponse(status_code=503 if isinstance(exc, SQLAlchemyError) else 500,
                                content={"detail": "El servicio no está disponible temporalmente. Inténtalo de nuevo."})
    response.headers["X-Content-Type-Options"] = "nosniff"
    if not request.url.path.startswith("/public/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(BotoCoreError)
@app.exception_handler(ClientError)
async def storage_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "El almacenamiento de documentos no está disponible. Inténtalo de nuevo."})


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409, content={"detail": "El registro ya existe o tiene datos asociados. Actualiza la página e inténtalo de nuevo."})


@app.get("/health")
def health():
    return {"status": "ok"}
