"""Validated inputs for the staged entrepreneurial route."""
from datetime import date
from decimal import Decimal
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, Field, StrictBool, StrictInt, field_validator, model_validator


class CalculadoraInput(BaseModel):
    inversion_inicial: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    costos_fijos: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    costo_variable_unitario: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    precio_venta: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    unidades_estimadas: StrictInt = Field(ge=0, le=1000000000)
    observaciones: str = Field(default='', max_length=500)


class ClasificacionInput(BaseModel):
    depende_tecnologia: StrictBool
    requiere_validacion_tecnica: StrictBool
    activo_protegible: StrictBool
    tipo_proyecto: Literal['normal', 'tecnologica', 'no_seguro']
    razon: str = Field(default='', max_length=3000)
    version: StrictInt = Field(ge=0)


class DatosRutaInput(BaseModel):
    datos: dict[str, str]
    version: StrictInt = Field(ge=0)

    @field_validator('datos')
    @classmethod
    def bounded_fields(cls, value):
        if len(value) > 60:
            raise ValueError('Guarda como máximo 60 respuestas por sección.')
        for key, item in value.items():
            if not key or len(key) > 80 or len(item) > 3000:
                raise ValueError('Revisa los campos de respuesta; cada texto admite hasta 3000 caracteres.')
        return value


class PasoRutaInput(BaseModel):
    estado: Literal['pendiente', 'en_proceso', 'en_revision', 'completado', 'no_aplica']
    respuesta: str = Field(default='', max_length=3000)
    evidencia_texto: str = Field(default='', max_length=3000)
    evidencia_url: str = Field(default='', max_length=2000)
    documento_id: UUID | None = None
    justificacion: str = Field(default='', max_length=3000)
    version: StrictInt = Field(ge=0)

    @field_validator('evidencia_url')
    @classmethod
    def safe_url(cls, value):
        if not value:
            return value
        try:
            url = urlsplit(value)
            if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
                raise ValueError()
            url.port
        except ValueError:
            raise ValueError('La evidencia debe ser un enlace HTTP/HTTPS válido.') from None
        return value


class TareaRutaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    descripcion: str = Field(default='', max_length=3000)
    paso_codigo: str = Field(default='', max_length=12)
    responsable_id: UUID
    fecha_objetivo: date
    evidencia_esperada: str = Field(min_length=1, max_length=1000)

    @field_validator('nombre', 'evidencia_esperada')
    @classmethod
    def trim_required(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Este campo es obligatorio.')
        return value


class TareaRutaActualizar(BaseModel):
    estado: Literal['Pendiente', 'En proceso', 'Completada', 'Cancelada']
    evidencia_texto: str = Field(default='', max_length=3000)
    evidencia_url: str = Field(default='', max_length=2000)
    documento_id: UUID | None = None
    version: StrictInt = Field(ge=0)

    @field_validator('evidencia_url')
    @classmethod
    def safe_url(cls, value):
        if not value:
            return value
        try:
            url = urlsplit(value)
            if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
                raise ValueError()
            url.port
        except ValueError:
            raise ValueError('La evidencia debe ser un enlace HTTP/HTTPS válido.') from None
        return value


class RevisionTareaRuta(BaseModel):
    decision: Literal['Aprobada', 'Corrección requerida']
    notas: str = Field(min_length=1, max_length=3000)
    version: StrictInt = Field(ge=0)

    @field_validator('notas')
    @classmethod
    def trim_notes(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Indica el resultado de la revisión.')
        return value


class CanalizacionRutaCrear(BaseModel):
    necesidad: str = Field(min_length=1, max_length=1000)
    motivo: str = Field(min_length=1, max_length=3000)
    destino: str = Field(min_length=1, max_length=300)
    informacion_usuario: str = Field(min_length=1, max_length=3000)
    resultado_esperado: str = Field(min_length=1, max_length=2000)
    fecha_objetivo: date
    paso_codigo: str = Field(default='', max_length=12)
    documento_id: UUID | None = None
    evidencia_url: str = Field(default='', max_length=2000)

    @field_validator('necesidad', 'motivo', 'destino', 'informacion_usuario', 'resultado_esperado')
    @classmethod
    def trim_channel_fields(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Este campo es obligatorio.')
        return value

    @field_validator('evidencia_url')
    @classmethod
    def safe_url(cls, value):
        if not value:
            return value
        try:
            url = urlsplit(value)
            if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
                raise ValueError()
            url.port
        except ValueError:
            raise ValueError('La evidencia debe ser un enlace HTTP/HTTPS válido.') from None
        return value


class CanalizacionRutaActualizar(BaseModel):
    resultado: str = Field(default='', max_length=3000)
    siguiente_accion: str = Field(default='', max_length=3000)
    estado: Literal['Abierta', 'Cerrada', 'Cancelada']
    motivo_cancelacion: str = Field(default='', max_length=3000)
    evidencia_url: str = Field(default='', max_length=2000)
    documento_id: UUID | None = None
    version: StrictInt = Field(ge=0)

    @model_validator(mode='after')
    def closure(self):
        if self.estado == 'Cerrada' and (not self.resultado.strip() or not self.siguiente_accion.strip()):
            raise ValueError('Para cerrar, registra resultado y siguiente acción interna.')
        if self.estado == 'Cancelada' and not self.motivo_cancelacion.strip():
            raise ValueError('Para cancelar, indica el motivo.')
        return self

    @field_validator('evidencia_url')
    @classmethod
    def safe_url(cls, value):
        if not value:
            return value
        try:
            url = urlsplit(value)
            if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
                raise ValueError()
            url.port
        except ValueError:
            raise ValueError('La evidencia debe ser un enlace HTTP/HTTPS válido.') from None
        return value


class EstadoRutaInput(BaseModel):
    estado: Literal['Registrado', 'Diagnóstico', 'Revisión económica', 'En desarrollo', 'En validación', 'En validación tecnológica', 'En formalización', 'En operación', 'Canalizado', 'Pausado', 'Abandonado', 'Concluido']
    motivo: str = Field(default='', max_length=3000)
    cierre_administrativo: StrictBool = False
    version: StrictInt = Field(ge=0)


class PlantillaPaso(BaseModel):
    codigo: str = Field(pattern=r'^(N[1-7]|T(10|[1-9])|F[1-8])$')
    titulo: str = Field(min_length=1, max_length=160)
    criterio_salida: str = Field(min_length=1, max_length=1000)
    orden: StrictInt = Field(ge=1, le=100)
    obligatorio: StrictBool = True
    activo: StrictBool = True


class ConfigRutaInput(BaseModel):
    margen_minimo: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    meses_recuperacion_max: StrictInt = Field(ge=1, le=600)
    dias_inactividad: StrictInt | None = Field(default=None, ge=1, le=3650)
    plantillas_ruta: dict[str, list[PlantillaPaso]]
    version: StrictInt = Field(ge=0)

    @model_validator(mode='after')
    def valid_templates(self):
        if set(self.plantillas_ruta) != {'normal', 'tecnologica', 'comun'}:
            raise ValueError('La plantilla debe contener ruta normal, tecnológica y común.')
        expected_codes = {
            'normal': {f'N{i}' for i in range(1, 8)},
            'tecnologica': {f'T{i}' for i in range(1, 11)},
            'comun': {f'F{i}' for i in range(1, 9)},
        }
        for route, steps in self.plantillas_ruta.items():
            if not steps:
                raise ValueError('Cada ruta debe conservar al menos un paso.')
            codes = set()
            for step in steps:
                expected = {'normal': 'N', 'tecnologica': 'T', 'comun': 'F'}[route]
                if not step.codigo.startswith(expected) or step.codigo in codes:
                    raise ValueError('El código del paso no corresponde a su ruta o está repetido.')
                codes.add(step.codigo)
                if not step.activo or not step.obligatorio:
                    raise ValueError('Los pasos definidos por la guía deben permanecer activos y obligatorios.')
            if codes != expected_codes[route]:
                raise ValueError('Conserva todos los pasos de la guía; puedes editar su nombre y criterio de salida.')
        return self
