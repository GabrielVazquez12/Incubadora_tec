import { Navigate } from "react-router-dom";

export default function RutaProtegida({ children, rolesPermitidos }) {
  const token = localStorage.getItem("access_token");
  const rol = localStorage.getItem("rol");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (rolesPermitidos && !rolesPermitidos.includes(rol)) {
    // Si tiene token pero no el rol adecuado, lo mandas fuera
    return <Navigate to="/" replace />;
  }

  return children;
}