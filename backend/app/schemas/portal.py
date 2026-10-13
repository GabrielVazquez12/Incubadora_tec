from datetime import date, time
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field, StringConstraints, StrictBool, StrictInt, field_validator
from app.schemas.validation import Email, Name, RequestInput, password_value

Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]
Status = Literal["Pendiente", "En revisión", "En proceso", "En incubación", "Completado"]


class ProjectInput(RequestInput):
    registro_id: UUID | None = None
    nombre: Name
    descripcion: str = Field(default="", max_length=3000)
    especialidad: str = Field(default="", max_length=160)
    comentario: str = Field(default="", max_length=2000)
    fecha: date
    progreso: StrictInt = Field(default=0, ge=0, le=100)
    estatus: Status = "Pendiente"
    siguiente_paso: str | None = Field(default=None, max_length=1000)
    file: dict | None = None
    producto_servicio: str = Field(default="", max_length=3000)
    telefono: str = Field(default="", pattern=r"^(?:[0-9+ ()-]{10,20})?$")


class UserInput(RequestInput):
    nombre: Name
    correo: Email
    rol: Literal["admin", "estudiante", "externo"]
    especialidad: str = Field(default="", max_length=160)
    password: str | None = None

    @field_validator("password")
    @classmethod
    def password_length(cls, value):
        return password_value(value) if value else value


class MilestoneInput(RequestInput):
    project: UUID
    hito: Name
    notas: Description
    fecha: date
    progreso: StrictInt = Field(ge=0, le=100)


class TaskInput(RequestInput):
    project: UUID
    nombre: Name
    fecha: date
    estatus: Literal["Pendiente", "Completado"] = "Pendiente"


class EventInput(RequestInput):
    nombre: Name
    descripcion: Description
    tipo: Name
    fecha: date
    hora: time
    cupo: StrictInt = Field(ge=1, le=10000)
    precio: Decimal = Field(ge=0, le=100000, decimal_places=2)
    modalidad: Literal["Presencial", "En línea", "Híbrida"]
    estatus: Literal["Activo", "Pendiente", "Inactivo"]

    @field_validator("precio", mode="before")
    @classmethod
    def numeric_price(cls, value):
        if type(value) not in (int, float, Decimal):
            raise ValueError("El precio debe enviarse como un número.")
        return value


class SlotInput(RequestInput):
    fecha: date
    inicio: time
    fin: time


class AppointmentInput(RequestInput):
    slot: UUID
    estatus: Literal["Confirmada", "Completado", "Cancelada"] = "Confirmada"


class ApplicationInput(RequestInput):
    registro_id: UUID | None = None
    nombre: Name
    descripcion: Description
    especialidad: str = Field(default="", max_length=160)
    producto_servicio: str = Field(default="", max_length=3000)
    telefono: str = Field(default="", pattern=r"^(?:[0-9+ ()-]{10,20})?$")
    estatus: Literal["En revisión", "Aprobada", "Rechazada"] = "En revisión"
    observaciones: str = Field(default="", max_length=5000)


class InnovationInput(RequestInput):
    nombre: Name
    equipo: Name
    lider: Name
    asesor: Name
    descripcion: Description
    modulo: Name
    categoria: Name
    etapa: Literal["Local", "Regional", "Nacional"] = "Local"
    estatus: Literal["Borrador", "En revisión", "Correcciones solicitadas", "Aprobada", "Rechazada"] = "Borrador"
    estatus_anterior: str | None = None
    observaciones: str = Field(default="", max_length=5000)


class RegistrationInput(RequestInput):
    resultado: Literal["Pagado", "Rechazado"] | None = None


class AttendanceInput(RequestInput):
    asistio: StrictBool


class InitialFormInput(RequestInput):
    datos: dict[str, str] = Field(default_factory=dict)
    administracion: dict[str, str] = Field(default_factory=dict)
    archivos: dict[str, dict | None] = Field(default_factory=dict)
    estatus: Literal["Borrador", "Pendiente"] = "Borrador"


class RegistrationReviewInput(RequestInput):
    estatus: Literal["En revisión", "Correcciones solicitadas", "Aprobado"]
    estatus_anterior: Literal["Pendiente", "En revisión"]
    observaciones: str = Field(default="", max_length=5000)


class EventTypeInput(RequestInput):
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class MemberInput(RequestInput):
    correo: Email
