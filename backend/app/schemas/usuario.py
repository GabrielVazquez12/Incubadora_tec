import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.usuario import RolUsuario
from app.schemas.validation import Email, Name, RequestInput, password_value


class UsuarioCreate(RequestInput):
    nombre: Name
    correo: Email
    password: str = Field(min_length=8)
    rol: RolUsuario

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        return password_value(value)


class UsuarioOut(BaseModel):
    id: uuid.UUID
    nombre: str
    correo: EmailStr
    rol: RolUsuario

    class Config:
        from_attributes = True


class LoginRequest(RequestInput):
    correo: Email
    password: str = Field(min_length=1, max_length=72)

    @field_validator("password")
    @classmethod
    def bounded_password(cls, value):
        return password_value(value, minimum=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
