import AccessDenied from '../../shared/design/AccessDenied.jsx';
import { Navigate } from "react-router-dom";
import { usePortal } from '../../shared/portal/PortalContext.jsx';
import { rolePaths } from '../../shared/portal/data.js';
import { Skeleton } from '../../shared/portal/ui.jsx';

export default function RutaProtegida({ children, rolesPermitidos, perfilesPermitidos, requiereAdministracion = false }) {
  const token = localStorage.getItem("access_token");
  const { user, loading, error, refresh } = usePortal();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (loading || !user) {
    return <div className="panel">{error ? <p role="alert">{error}</p> : <Skeleton label="Cargando tu cuenta…" />}{error && <button className="button" onClick={refresh}>Reintentar</button>}</div>;
  }
  if (rolesPermitidos && !rolesPermitidos.includes(user.rol)) {
    return <Navigate to={`/${rolePaths[user.rol]}/inicio`} replace />;
  }

  if (perfilesPermitidos && !perfilesPermitidos.includes(user.perfil) || requiereAdministracion && !user.gestiona_accesos) return <AccessDenied />;
  return children;
}
