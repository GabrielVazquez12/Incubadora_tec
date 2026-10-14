from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import Field, StrictBool, StrictInt, model_validator, field_validator
from app.schemas.innovatec import Input
from app.schemas.validation import Name, valid_text
from app.schemas.portal import Description


class PreguntaInput(Input):
    id: UUID
    titulo: Name
    tipo: Literal['seleccion_unica', 'multiseleccion', 'escala', 'texto']
    obligatoria: StrictBool = True
    opciones: list[Name] = Field(default_factory=list, max_length=30)
    minimo: StrictInt = Field(default=1, ge=1, le=10)
    maximo: StrictInt = Field(default=5, ge=1, le=10)

    @model_validator(mode='after')
    def format(self):
        if self.tipo in ('seleccion_unica', 'multiseleccion') and len(self.opciones) < 2:
            raise ValueError('Una pregunta de selección necesita al menos dos opciones.')
        if len({option.casefold() for option in self.opciones}) != len(self.opciones):
            raise ValueError('No repitas opciones de una pregunta.')
        if self.tipo not in ('seleccion_unica', 'multiseleccion') and self.opciones:
            raise ValueError('Las opciones corresponden únicamente a preguntas de selección.')
        if self.tipo == 'escala' and self.minimo >= self.maximo:
            raise ValueError('El máximo de la escala debe ser mayor que su mínimo.')
        return self


class EncuestaInput(Input):
    titulo: Name
    descripcion: Description
    publico: Literal['alumnos', 'docentes', 'usuarios de la Incubadora']
    anonima: StrictBool = True
    publicada: StrictBool = False
    apertura: date | None = None
    cierre: date | None = None
    preguntas: list[PreguntaInput] = Field(min_length=1, max_length=40)
    version: StrictInt = Field(default=0, ge=0)

    @field_validator('apertura', 'cierre', mode='before')
    @classmethod
    def dates(cls, value):
        return cls.calendar_date(value)

    @model_validator(mode='after')
    def coherent(self):
        if self.apertura and self.cierre and self.cierre < self.apertura:
            raise ValueError('El cierre debe ser igual o posterior a la apertura.')
        if self.publicada and (not self.apertura or not self.cierre):
            raise ValueError('Configura apertura y cierre antes de publicar.')
        if len({q.id for q in self.preguntas}) != len(self.preguntas):
            raise ValueError('No repitas identificadores de preguntas.')
        return self


class RespuestaInput(Input):
    id: UUID
    respuestas: dict[UUID, str | StrictInt | list[str]] = Field(max_length=40)
    acepto_privacidad: StrictBool = False
    version_encuesta: StrictInt = Field(ge=1)

    @field_validator('respuestas')
    @classmethod
    def text_values(cls, values):
        for value in values.values():
            for item in value if isinstance(value, list) else [value]:
                if isinstance(item, str):
                    valid_text(item)
                    if len(item) > 3000:
                        raise ValueError('Las respuestas de texto admiten hasta 3000 caracteres.')
        return values
