import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RolUsuario(str, enum.Enum):
    admin = "admin"
    estudiante = "estudiante"
    externo = "externo"


class Usuario(Base):
    """
    Modelo de ejemplo para arrancar. Ajusten los campos conforme definan
    el modelo de datos completo (docs/modelo-de-datos.md).
    """

    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    rol = Column(Enum(RolUsuario), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)