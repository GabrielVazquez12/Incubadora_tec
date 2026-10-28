"""Bounded validation shared by uploads and the legacy project form."""
import base64
import binascii
from io import BytesIO
from zipfile import BadZipFile, ZipFile
import warnings
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException
from app.schemas.validation import valid_text

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
TYPES = {"pdf": "application/pdf", "doc": "application/msword",
         "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def validate_filename(name):
    if (not isinstance(name, str) or not 1 <= len(name) <= 240
            or not name.strip() or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or "/" in name or "\\" in name):
        raise HTTPException(422, "El nombre del archivo no es válido.")
    try:
        valid_text(name)
    except ValueError:
        raise HTTPException(422, "El nombre del archivo no es válido.") from None


def validate_annex(extension, content):
    if extension == "pdf":
        return
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                expected = "PNG" if extension == "png" else "JPEG"
                if image.format != expected or image.width * image.height > 25_000_000 or getattr(image, "n_frames", 1) != 1:
                    raise ValueError()
                image.verify()
            with Image.open(BytesIO(content)) as image:
                image.load()
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "El anexo debe ser una imagen PNG o JPG válida de hasta 25 megapíxeles.")


def validate_document(name, content):
    validate_filename(name)
    ext = name.lower().rsplit(".", 1)[-1]
    if ext not in TYPES or not content or len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(422, "Adjunta un PDF, DOC o DOCX de hasta 5 MB.")
    valid = content.startswith({"pdf": b"%PDF-", "doc": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "docx": b"PK"}[ext])
    if valid and ext == "docx":
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
                entries = archive.infolist()
                valid = ({"[Content_Types].xml", "word/document.xml"} <= names
                         and len(entries) <= 2000 and sum(e.file_size for e in entries) <= 25 * 1024 * 1024
                         and not any(e.flag_bits & 1 or e.file_size > max(e.compress_size, 1) * 200 for e in entries)
                         and not any(n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/")
                                     or n.lower().endswith("vbaproject.bin") for n in names))
        except (BadZipFile, ValueError):
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
