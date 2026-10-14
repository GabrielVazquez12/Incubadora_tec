from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import Field, StrictBool, StrictInt, field_validator, model_validator, TypeAdapter
from app.schemas.innovatec import Input
from app.schemas.incubadora import EvidenciaInput, VersionInput
from app.schemas.validation import Name, Email
from app.schemas.portal import Description

Canal = Literal['Instagram', 'TikTok', 'WhatsApp', 'Facebook', 'docentes', 'coordinadores', 'salones']


class PiezaInput(VersionInput):
    titulo: Name
    canal: Canal
    fecha: date
    responsable_id: UUID
    estado: Literal['planeada', 'publicada']
    enlace: str = Field(default='', max_length=2000)
    publicacion_id: UUID | None = None
    tipo: Literal['publicacion', 'reel', 'historia', 'video', 'experiencia'] = 'publicacion'
    visible: StrictBool = False

    @field_validator('enlace')
    @classmethod
    def link(cls, value):
        return EvidenciaInput.safe_link(value)

    @model_validator(mode='after')
    def publication(self):
        if self.estado == 'publicada' and not self.enlace and not self.publicacion_id:
            raise ValueError('Una pieza publicada requiere enlace o noticia existente.')
        return self


class VisitaInput(VersionInput):
    grupo: Name
    docente_coordinador: Name
    fecha: date
    responsable_id: UUID
    asistentes: StrictInt = Field(ge=0, le=10000)
    resultado: Description


class PlantillaInput(VersionInput):
    titulo: Name
    publico: Literal['alumnos', 'docentes']
    contenido: Description
    activa: StrictBool = True


class EnvioInput(Input):
    plantilla_id: UUID
    destinatario: Name
    fecha: date
    canal: Canal
    responsable_id: UUID


class FAQInput(VersionInput):
    seccion: Literal['incubadora', 'innovatec']
    pregunta: Name
    respuesta: Description
    orden: StrictInt = Field(default=0, ge=0, le=10000)
    activa: StrictBool = True


class ContactosInput(Input):
    correo: str = Field(default='', max_length=254)
    telefono: str = Field(default='', max_length=20, pattern=r'^(?:[0-9+ ()-]{10,20})?$')
    horario: str = Field(default='', max_length=300)
    instagram: str = Field(default='', max_length=2000)
    tiktok: str = Field(default='', max_length=2000)
    whatsapp: str = Field(default='', max_length=2000)
    facebook: str = Field(default='', max_length=2000)

    @field_validator('correo')
    @classmethod
    def mail(cls, value):
        return str(TypeAdapter(Email).validate_python(value)).lower() if value else ''

    @field_validator('instagram', 'tiktok', 'whatsapp', 'facebook')
    @classmethod
    def links(cls, value):
        return EvidenciaInput.safe_link(value)


class ConfiguracionEnlacesInput(VersionInput):
    vinculacion: str = Field(default='', max_length=10000)
    contactos: ContactosInput


class ContactoInput(Input):
    nombre: Name
    correo: Email
    telefono: str = Field(default='', max_length=20, pattern=r'^(?:[0-9+ ()-]{10,20})?$')
    asunto: Name
    mensaje: Description
    origen: Literal['contacto', 'vinculacion']
    acepto_privacidad: StrictBool
    version_aviso: StrictInt = Field(ge=1)

    @model_validator(mode='after')
    def consent(self):
        if not self.acepto_privacidad:
            raise ValueError('Acepta el aviso de privacidad institucional.')
        return self


class ContactoReview(VersionInput):
    estado: Literal['nuevo', 'atendido']
    nota: Description


class FichaEventoInput(VersionInput):
    titulo: Name
    descripcion: Description
    lema: str = Field(default='', max_length=300)
    lugar: str = Field(default='', max_length=300)
    evento_id: UUID | None = None
    publicada: StrictBool = False
