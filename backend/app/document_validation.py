"""Bounded validation shared by uploads and the legacy project form."""
import base64
import binascii
from io import BytesIO
from zipfile import BadZipFile, ZipFile
from fastapi import HTTPException

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
TYPES = {"pdf": "application/pdf", "doc": "application/msword",
         "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def validate_document(name, content):
    if (not isinstance(name, str) or not 1 <= len(name) <= 240
            or any(ord(c) < 32 for c in name) or "/" in name or "\\" in name):
        raise HTTPException(422, "El nombre del archivo no es válido.")
    ext = name.lower().rsplit(".", 1)[-1]
    if ext not in TYPES or not content or len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(422, "Adjunta un PDF, DOC o DOCX de hasta 5 MB.")
    valid = content.startswith({"pdf": b"%PDF-", "doc": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "docx": b"PK"}[ext])
    if valid and ext == "docx":
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
                valid = {"[Content_Types].xml", "word/document.xml"} <= names and not any(n.endswith("vbaProject.bin") for n in names)
        except BadZipFile:
            valid = False
    if not valid:
        raise HTTPException(422, "El contenido no corresponde al formato indicado.")
    return TYPES[ext]


def decode_document(file):
    raw = file.get("data")
    if not isinstance(raw, str) or len(raw) > 7 * 1024 * 1024:
        raise HTTPException(422, "El archivo supera 5 MB o no es válido.")
    try:
        content = base64.b64decode(raw.split(",")[-1], validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(422, "No se pudo leer el archivo.")
    return content, validate_document(file.get("name"), content)
