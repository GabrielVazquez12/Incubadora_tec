"""Shared request rules; keep JSON IDs/dates compatible without numeric coercion."""
from datetime import date, time
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Email = Annotated[EmailStr, Field(max_length=254)]


def password_value(value, minimum=8):
    try:
        byte_length = len(value.encode("utf-8")) if isinstance(value, str) else 0
    except UnicodeEncodeError:
        raise ValueError("La contraseña contiene caracteres Unicode no válidos.") from None
    if not isinstance(value, str) or len(value) < minimum or byte_length > 72:
        raise ValueError("La contraseña debe tener al menos %s caracteres y hasta 72 bytes." % minimum)
    return value


def valid_text(value):
    if any(ord(char) < 32 and char not in "\t\n\r" or 0xD800 <= ord(char) <= 0xDFFF or ord(char) in (0xFFFE, 0xFFFF) for char in value):
        raise ValueError("El texto contiene caracteres de control o Unicode no válidos.")
    return value


class RequestInput(BaseModel):
    # Existing portal clients send display metadata. Only declared fields are saved.
    @field_validator("telefono", "especialidad", "comentario", "siguiente_paso", "observaciones", check_fields=False, mode="before")
    @classmethod
    def optional_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("*", mode="after")
    @classmethod
    def text_characters(cls, value):
        return valid_text(value) if isinstance(value, str) else value

    @field_validator("correo", check_fields=False)
    @classmethod
    def normalized_email(cls, value):
        return value.lower()

    @field_validator("fecha", "vence", check_fields=False, mode="before")
    @classmethod
    def calendar_date(cls, value):
        if value is None or type(value) is date:
            return value
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("Indica una fecha válida en formato AAAA-MM-DD.")
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValueError("Indica una fecha real en formato AAAA-MM-DD.") from None

    @field_validator("hora", "inicio", "fin", check_fields=False, mode="before")
    @classmethod
    def local_clock(cls, value):
        if not isinstance(value, (str, time)):
            raise ValueError("Indica una hora válida.")
        try:
            clock = time.fromisoformat(value) if isinstance(value, str) else value
        except ValueError:
            raise ValueError("Indica una hora real en formato HH:MM.") from None
        if clock.tzinfo or clock.second or clock.microsecond:
            raise ValueError("Utiliza horas y minutos de Ciudad de México, sin zona horaria ni segundos.")
        return clock


def validation_errors(errors):
    messages = {
        "missing": "El campo es obligatorio.",
        "string_type": "Debe ser un texto.",
        "int_type": "Debe ser un número entero.",
        "int_parsing": "Debe ser un número entero.",
        "bool_type": "Debe ser un booleano JSON: true o false.",
        "literal_error": "Selecciona una opción válida.",
        "enum": "Selecciona una opción válida.",
        "uuid_parsing": "El identificador UUID no es válido.",
        "finite_number": "Debe ser un número finito.",
        "decimal_max_places": "El importe admite hasta dos decimales.",
    }
    result = []
    for error in errors:
        kind, context = error["type"], error.get("ctx", {})
        message = messages.get(kind, error["msg"])
        if kind == "string_too_short":
            message = f"Debe contener al menos {context['min_length']} caracteres."
        elif kind == "string_too_long":
            message = f"Admite como máximo {context['max_length']} caracteres."
        elif kind == "greater_than_equal":
            message = f"El valor mínimo es {context['ge']}."
        elif kind == "less_than_equal":
            message = f"El valor máximo es {context['le']}."
        result.append({"loc": error["loc"], "msg": message, "type": kind})
    return result
