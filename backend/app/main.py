from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.modules.autenticacion import routes as auth
from app.modules.coordinacion import routes as admin, portal_routes as coordination
from app.modules.estudiantes import portal_routes as students
from app.modules.compartido import routes as portal
from app.modules.compartido import documents
import app.models  # noqa: F401 — el esquema se administra con Alembic

# --- IMPORTACIONES PARA LAS MÉTRICAS DE INSCRIPCIONES ---
from sqlalchemy import extract
from collections import defaultdict
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.portal import Inscripcion  # <- Modelo de inscripciones agregado
# ----------------------------------------------

app = FastAPI(title="Incubadora TecNM Saltillo — API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(portal.router)
app.include_router(coordination.router)
app.include_router(students.router)
app.include_router(documents.router)


# --- ENDPOINT DE MÉTRICAS ACTUALIZADO (AHORA CON EVENTOS) ---
@app.get("/api/admin/metricas")
def obtener_metricas(
    ano: str,
    agrupacion: str,
    tipo: str,
    mes: Optional[str] = "todos",
    db: Session = Depends(get_db)
):
    # Consultamos las INSCRIPCIONES en lugar de solo Usuarios
    query = db.query(Inscripcion).filter(extract('year', Inscripcion.creado_en) == int(ano))
    
    # Filtrar por mes si aplica
    if mes and mes != "todos":
        query = query.filter(extract('month', Inscripcion.creado_en) == int(mes))
        
    inscripciones = query.all()

    lista_alumnos = []
    grafica_dict = defaultdict(lambda: defaultdict(int))

    for ins in inscripciones:
        u = ins.usuario
        ev = ins.evento

        # Validamos que la inscripción tenga un usuario válido
        if not u:
            continue

        # Obtenemos el nombre del evento
        nombre_evento = ev.nombre if ev else "Evento General"

        # Categorizar para dibujar las líneas de la gráfica
        if tipo == "rol":
            categoria = u.rol.value if u.rol else "Desconocido"
        elif tipo == "carrera":
            categoria = u.especialidad if u.especialidad else "Sin carrera"
        elif tipo == "evento":
            categoria = nombre_evento
        else:
            categoria = getattr(u, 'genero', 'No especificado')

        # Agrupar fecha
        fecha_ref = ins.creado_en
        if agrupacion == "dia":
            periodo = fecha_ref.strftime("%d/%b")
        elif agrupacion == "mes":
            periodo = fecha_ref.strftime("%b")
        else:
            periodo = fecha_ref.strftime("%Y")

        # Sumar 1 a la métrica
        grafica_dict[periodo][categoria] += 1

        genero_usuario = getattr(u, 'genero', 'No especificado')

        # Agregamos TODAS las columnas que pidió coordinación, incluyendo EVENTO
        lista_alumnos.append({
            "id": str(ins.id),
            "fecha": fecha_ref.strftime("%Y-%m-%d"),
            "evento": nombre_evento,
            "nombre": u.nombre,
            "correo": u.correo,
            "genero": genero_usuario,
            "carrera": u.especialidad if u.especialidad else "Sin carrera",
            "categoria": categoria
        })

    resumen_grafica = []
    for periodo, valores in grafica_dict.items():
        fila = {"periodo": periodo}
        fila.update(valores)
        resumen_grafica.append(fila)

    return {
        "resumenGrafica": resumen_grafica,
        "listaAlumnos": lista_alumnos
    }
# ----------------------------------


@app.exception_handler(BotoCoreError)
@app.exception_handler(ClientError)
async def storage_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "El almacenamiento de documentos no está disponible. Inténtalo de nuevo."})


@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    return JSONResponse(status_code=409, content={"detail": "El registro ya existe o tiene datos asociados. Actualiza la página e inténtalo de nuevo."})


@app.get("/health")
def health():
    return {"status": "ok"}