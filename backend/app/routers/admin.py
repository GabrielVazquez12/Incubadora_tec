from fastapi import APIRouter, Depends

from app.auth.security import require_role
from app.models.usuario import RolUsuario

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(RolUsuario.admin))],
)


@router.get("/dashboard")
def dashboard_resumen():
    """
    Endpoint de ejemplo — solo accesible por coordinadoras (rol admin).
    Aquí se conectarían las agregaciones para el dashboard (pandas, etc.)
    """
    return {"mensaje": "Solo coordinadoras pueden ver esto"}