from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.api.routes import router
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Rol, Usuario

settings = get_settings()


def create_initial_admin() -> None:
    """Create a development administrator after the first migration."""
    try:
        with SessionLocal() as db:
            if db.query(Usuario).first() is not None:
                return
            role = db.query(Rol).filter_by(nombre="Administrador").first()
            if role is None:
                return
            db.add(
                Usuario(
                    username="admin",
                    correo="admin@matriz.local",
                    nombre_completo="Administrador del sistema",
                    password_hash=hash_password(settings.admin_initial_password),
                    roles=[role],
                )
            )
            db.commit()
    except OperationalError:
        # The database may not have been migrated yet during CLI imports.
        return


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_initial_admin()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)
