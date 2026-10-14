from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import ConfigDict, Field, StrictBool, StrictInt, model_validator, field_validator
from app.schemas.validation import RequestInput, Name, Email
from app.schemas.portal import Description, EventInput


class Input(RequestInput):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class FechasEtapa(Input):
    etapa: Literal["local", "regional", "nacional"]
    fecha: date | None = None
    sede: str = Field(default="", max_length=300)


class ConvocatoriaInput(Input):
    anio: StrictInt = Field(ge=2000, le=2100)
    titulo: Name
    descripcion: Description
    version_manual: str = Field(default="", max_length=160)
    apertura: date | None = None
    cierre: date | None = None
    fechas: list[FechasEtapa] = Field(default_factory=list, max_length=3)
    requisitos: list[Name] = Field(default_factory=list, max_length=40)
    categorias: list[Name] = Field(min_length=1, max_length=40)
    aviso_privacidad: str = Field(default="", max_length=20000)
    aviso_aprobado: StrictBool = False
    publicada: StrictBool = False
    version: StrictInt = Field(default=0, ge=0)

    @field_validator("apertura", "cierre", mode="before")
    @classmethod
    def dates(cls, value):
        return cls.calendar_date(value)

    @model_validator(mode="after")
    def coherent(self):
        if self.apertura and self.cierre and self.apertura > self.cierre:
            raise ValueError("La apertura debe ser anterior o igual al cierre.")
        if len({f.etapa for f in self.fechas}) != len(self.fechas):
            raise ValueError("No repitas etapas.")
        ordered = [next((f.fecha for f in self.fechas if f.etapa == stage), None) for stage in ("local", "regional", "nacional")]
        dates = [d for d in ordered if d]
        if dates != sorted(dates):
            raise ValueError("Las fechas deben respetar el orden local, regional y nacional.")
        for values in (self.requisitos, self.categorias):
            if len({v.casefold() for v in values}) != len(values):
                raise ValueError("No repitas requisitos o categorías.")
        if self.publicada and (not self.apertura or not self.cierre or not self.aviso_aprobado or len(self.aviso_privacidad.strip()) < 20 or "[Por definir" in self.aviso_privacidad):
            raise ValueError("Publicar requiere apertura, cierre y aviso de privacidad aprobado, sin marcadores.")
        return self


class IntegranteInput(Input):
    nombre: Name
    correo: Email
    carrera: str = Field(default="", max_length=160)
    semestre: StrictInt | None = Field(default=None, ge=1, le=20)
    tipo: Literal["participante", "asesor"] = "participante"

    @model_validator(mode="after")
    def academic(self):
        if self.tipo == "participante" and (not self.carrera.strip() or self.semestre is None):
            raise ValueError("Los participantes requieren carrera y semestre.")
        return self


class EquipoInput(Input):
    id: UUID
    convocatoria_id: UUID
    innovacion_id: UUID | None = None
    nombre: Name
    equipo: Name
    descripcion: Description
    categoria: Name
    integrantes: list[IntegranteInput] = Field(min_length=1, max_length=50)
    acepto_privacidad: StrictBool
    version_convocatoria: StrictInt = Field(ge=1)

    @model_validator(mode="after")
    def members(self):
        if not self.acepto_privacidad:
            raise ValueError("Debes aceptar el aviso de privacidad.")
        if len({m.correo for m in self.integrantes}) != len(self.integrantes):
            raise ValueError("No repitas correos de integrantes.")
        if not any(m.tipo == "participante" for m in self.integrantes) or not any(m.tipo == "asesor" for m in self.integrantes):
            raise ValueError("Registra al menos un participante y un asesor docente.")
        return self


class EquipoEditInput(EquipoInput):
    version: StrictInt = Field(ge=1)


class CambioEstado(Input):
    estado: Literal["inscrito", "documentacion_recibida", "etapa_local", "acreditado", "etapa_regional", "etapa_nacional", "no_acreditado", "baja"]
    version: StrictInt = Field(ge=1)
    motivo: Description


class RevisionDocumento(Input):
    estado: Literal["recibido", "observado", "aprobado"]
    estado_anterior: Literal["recibido", "observado", "aprobado"]
    comentarios: str = Field(default="", max_length=3000)


class Gestion(Input):
    nombre: Name
    responsable: Name
    estado: Literal["pendiente", "en_curso", "completada"]


class SeguimientoInput(Input):
    version: StrictInt = Field(ge=1)
    etapa: Literal["local", "regional", "nacional"]
    fecha: date | None = None
    sede: str = Field(default="", max_length=300)
    responsables: str = Field(default="", max_length=1000)
    jurado: str = Field(default="", max_length=3000)
    resultados: str = Field(default="", max_length=3000)
    transporte: str = Field(default="", max_length=3000)
    hospedaje: str = Field(default="", max_length=3000)
    gestiones: list[Gestion] = Field(default_factory=list, max_length=100)


class DiplomaInput(Input):
    estado: Literal["pendiente", "generado", "entregado"]
    estado_anterior: Literal["pendiente", "generado", "entregado"]
    fecha_anterior: date | None = None
    fecha: date | None = None

    @field_validator("fecha_anterior", mode="before")
    @classmethod
    def previous_date(cls, value):
        return cls.calendar_date(value)

    @model_validator(mode="after")
    def delivery(self):
        from app.modules.compartido.services import today
        if self.estado == "entregado" and (not self.fecha or self.fecha > today()):
            raise ValueError("La entrega requiere una fecha real que no sea futura.")
        if self.estado != "entregado" and self.fecha is not None:
            raise ValueError("Registra fecha de entrega únicamente cuando el diploma está entregado.")
        return self


class PlaticaInput(Input):
    evento_id: UUID | None = None
    evento: EventInput
    publico: Literal["alumnos", "docentes"]
    contenido: Description
    sede: str = Field(default="", max_length=300)
