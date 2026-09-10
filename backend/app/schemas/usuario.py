import uuid
from pydantic import BaseModel, EmailStr

from app.models.usuario import RolUsuario


class UsuarioCreate(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    rol: RolUsuario


class UsuarioOut(BaseModel):
    id: uuid.UUID
    nombre: str
    correo: EmailStr
    rol: RolUsuario

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"