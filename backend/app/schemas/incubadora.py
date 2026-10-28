from datetime import date
from typing import Literal
from uuid import UUID
from urllib.parse import urlsplit
from pydantic import Field, StrictInt, StrictBool, field_validator, model_validator
from app.schemas.innovatec import Input
from app.schemas.validation import Name
from app.schemas.portal import Description

PERFILES = ('idea de negocio', 'proyecto académico', 'negocio digital', 'emprendimiento', 'público externo')
NECESIDADES = ('cliente / mercado / validación', 'estrategia comercial / ventas', 'cómo iniciar / modelo de negocio', 'legal / SAT / marca', 'seguimiento / mentoría', 'costos / precios', 'financiamiento', 'tecnología')


class VersionInput(Input):
    version: StrictInt = Field(ge=0)


class ConfiguracionInput(VersionInput):
    dias_inactividad: StrictInt | None = Field(default=None, ge=1, le=3650)
    aviso_privacidad: str = Field(default='', max_length=20000)
    aviso_aprobado: StrictBool = False

    @model_validator(mode='after')
    def approved(self):
        if self.aviso_aprobado and (len(self.aviso_privacidad) < 20 or '[Por definir' in self.aviso_privacidad):
            raise ValueError('Configura el aviso de privacidad institucional aprobado.')
        return self


class ServicioInput(VersionInput):
    nombre: Name
    etapa: StrictInt = Field(ge=1, le=4)
    nivel: StrictInt = Field(ge=1, le=3)
    objetivo: Description
    resultado_esperado: Description
    canalizacion: str = Field(default='', max_length=3000)
    orden: StrictInt = Field(default=0, ge=0, le=10000)
    activo: StrictBool = True

    @model_validator(mode='after')
    def referral(self):
        if self.nivel == 3 and not self.canalizacion:
            raise ValueError('El nivel 3 requiere una canalización, o el marcador [Por definir].')
        return self


class HitoInput(VersionInput):
    servicio_id: UUID
    nombre: Name
    orden: StrictInt = Field(default=0, ge=0, le=10000)
    activo: StrictBool = True
    propuesta: StrictBool = True


class DiagnosticoInput(VersionInput):
    proyecto_id: UUID | None = None
    registro_id: UUID | None = None
    telefono: str = Field(pattern=r'^[0-9+ ()-]{10,20}$')
    tipo_usuario: Literal['alumno', 'docente', 'egresado', 'público externo']
    carrera: str = Field(default='', max_length=160)
    semestre: StrictInt | None = Field(default=None, ge=1, le=20)
    perfil: Literal['idea de negocio', 'proyecto académico', 'negocio digital', 'emprendimiento', 'público externo']
    etapa: Literal['antes de vender o formalizar', 'vendiendo o formalizado']
    descripcion: Description
    estado_actual: Literal['idea', 'negocio ya iniciado']
    necesidades: list[Literal['cliente / mercado / validación', 'estrategia comercial / ventas', 'cómo iniciar / modelo de negocio', 'legal / SAT / marca', 'seguimiento / mentoría', 'costos / precios', 'financiamiento', 'tecnología']] = Field(min_length=1, max_length=8)
    canal_llegada: Literal['recomendación', 'proyecto escolar', 'redes sociales', 'Día de Enlaces', 'plática', 'visita a salón', 'InnovaTec', 'otro']
    proyecto_pausado: StrictBool
    motivo_pausa: str = Field(default='', max_length=3000)
    frecuencia: Literal['semanal', 'cada 15 días', 'mensual'] = 'cada 15 días'
    modalidad: Literal['en línea', 'presencial', 'mixta'] = 'mixta'
    acepto_privacidad: StrictBool
    version_aviso: StrictInt = Field(ge=1)

    @model_validator(mode='after')
    def origin(self):
        if not self.proyecto_id and not self.registro_id:
            raise ValueError('Enlaza el proyecto o registro de ingreso existente.')
        return self

    @model_validator(mode='after')
    def coherent(self):
        if self.tipo_usuario == 'alumno' and (not self.carrera or self.semestre is None):
            raise ValueError('Indica carrera y semestre del alumno.')
        if self.tipo_usuario != 'alumno' and self.semestre is not None:
            raise ValueError('El semestre corresponde únicamente a alumnos.')
        if self.proyecto_pausado and not self.motivo_pausa:
            raise ValueError('Indica por qué se pausó el proyecto.')
        if not self.proyecto_pausado and self.motivo_pausa:
            raise ValueError('El motivo de pausa solo aplica si se pausó un proyecto.')
        if not self.acepto_privacidad or len(set(self.necesidades)) != len(self.necesidades):
            raise ValueError('Acepta el aviso y selecciona necesidades sin repetir.')
        return self


class RegistroProyectoInput(DiagnosticoInput):
    nombre: Name
    producto_servicio: Description

    @model_validator(mode='after')
    def origin(self):
        if self.proyecto_id is not None or self.registro_id is not None or self.version != 0:
            raise ValueError('El registro público crea un expediente nuevo; no puede reemplazar un origen existente.')
        return self


class EvidenciaInput(Input):
    documento_id: UUID | None = None
    evidencia_url: str = Field(default='', max_length=2000)

    @field_validator('evidencia_url')
    @classmethod
    def safe_link(cls, value):
        if not value:
            return value
        try:
            url = urlsplit(value)
            if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
                raise ValueError()
            url.port
        except ValueError:
            raise ValueError('La evidencia debe ser un enlace HTTP/HTTPS sin credenciales.') from None
        return value


class AtencionInput(EvidenciaInput):
    version: StrictInt = Field(ge=0)
    fecha: date
    tipo: Literal['diagnostico', 'asesoria', 'seguimiento', 'canalizacion', 'cierre', 'recuperacion']
    servicio_id: UUID | None = None
    actividad: Description
    responsable_id: UUID
    fecha_revision: date
    resultado: str = Field(default='', max_length=3000)
    siguiente_accion: str = Field(min_length=1, max_length=3000)
    evidencia_esperada: str = Field(min_length=1, max_length=1000)

    @field_validator('siguiente_accion', 'evidencia_esperada')
    @classmethod
    def required_followup(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Registra la siguiente acción y la evidencia esperada.')
        return value

    @field_validator('fecha_revision', mode='before')
    @classmethod
    def revision_date(cls, value):
        return cls.calendar_date(value)

    @model_validator(mode='after')
    def dates(self):
        if self.fecha_revision < self.fecha:
            raise ValueError('La fecha de revisión debe ser igual o posterior a la atención.')
        return self


class EstadoInput(VersionInput):
    estado: Literal['activo', 'en_seguimiento', 'pausado', 'concluido', 'formalizado']
    motivo: Description
    fecha: date


class AsignacionInput(VersionInput):
    asesor_id: UUID
    primer_contacto: date


class CumplimientoInput(EvidenciaInput):
    version: StrictInt = Field(ge=0)
    estado: Literal['pendiente', 'en_curso', 'cumplido']
    fecha: date | None = None

    @model_validator(mode='after')
    def completed(self):
        if self.estado == 'cumplido' and self.fecha is None:
            raise ValueError('Indica la fecha del hito cumplido.')
        return self


class CanalizacionInput(EvidenciaInput):
    version: StrictInt = Field(ge=0)
    atencion_id: UUID
    destino: str = Field(min_length=1, max_length=300)
    motivo: Description
    fecha: date
    resultado: str = Field(default='', max_length=3000)
