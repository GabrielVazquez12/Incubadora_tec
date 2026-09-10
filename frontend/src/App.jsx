import { BrowserRouter, Routes, Route } from "react-router-dom";
import RutaProtegida from "./routes/RutaProtegida.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Registro from "./pages/Registro.jsx";

function DashboardAdmin() {
  return <h1 className="p-6 text-xl">Dashboard Coordinadoras (pendiente)</h1>;
}
function PortalEstudiante() {
  return <h1 className="p-6 text-xl">Portal Estudiante (pendiente)</h1>;
}
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