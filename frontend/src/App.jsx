import { BrowserRouter, Routes, Route } from "react-router-dom";
import RutaProtegida from "./routes/RutaProtegida.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Registro from "./pages/Registro.jsx";
// IMPORTA TUS ARCHIVOS REALES AQUÍ
import DashboardAdmin from "./pages/DashboardAdmin.jsx";
import PortalEstudiante from "./pages/PortalEstudiante.jsx";

// Si aún no creas el archivo físico de PortalExterno, deja esto temporalmente. 
// Pero bórralo en cuanto hagas el archivo en pages/
function PortalExterno() {
  return <h1 className="p-6 text-xl">Portal Externo (pendiente)</h1>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Registro />} />
        
        <Route
          path="/coordinador/inicio"
          element={
            <RutaProtegida rolesPermitidos={["admin"]}>
              <DashboardAdmin />
            </RutaProtegida>
          }
        />
        <Route
          path="/emprendedor/inicio"
          element={
            <RutaProtegida rolesPermitidos={["estudiante"]}>
              <PortalEstudiante />
            </RutaProtegida>
          }
        />
        <Route
          path="/externo/inicio"
          element={
            <RutaProtegida rolesPermitidos={["externo"]}>
              <PortalExterno />
            </RutaProtegida>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}