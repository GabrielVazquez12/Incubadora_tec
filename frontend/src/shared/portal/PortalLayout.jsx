import {
  Outlet,
  useLocation,
  useNavigate,
  useOutletContext,
} from "react-router-dom";
import { coordinationNavigation } from "../../modules/coordinacion/navigation";
import { studentNavigation } from "../../modules/estudiantes/navigation";
import { externalNavigation } from "../../modules/externos/navigation";
import Navigation from "../design/Navigation.jsx";
import InstitutionalFooter from "../InstitutionalFooter.jsx";
import { demoPeople, roleNames, rolePaths } from "./data.js";
import { usePortal } from "./PortalContext.jsx";

const links = {
  estudiante: studentNavigation,
  admin: coordinationNavigation,
  externo: externalNavigation,
};

export const usePortalRoute = () => useOutletContext();
export default function PortalLayout({
  role,
  preview = false,
  innovation = false,
}) {
  const { notice, notify, user, loading, error, busy, refresh } = usePortal();
  if (!preview && user) role = user.rol;
  const navigate = useNavigate();
  const location = useLocation();
  const base = `${preview ? "/vista-previa" : ""}/${innovation ? "innovatecnm" : rolePaths[role]}`;
  const home = `${preview ? "/vista-previa" : ""}/${rolePaths[role]}/inicio`;
  const query = innovation && preview ? `?rol=${role}` : "";
  const nav = innovation
    ? [
        ["inicio", "Inicio"],
        ["certamen", "Certamen"],
        ["hackatec", "HackaTec"],
        ["innobotica", "InnoBótica"],
        ["innovaccion", "InnovAcción"],
        ["retos", "Retos Nacionales"],
        ["registros", "Registros"],
      ]
    : [
        links[role][0],
        ["boletin", "Boletín"],
        ...links[role]
          .slice(1)
          .map(([path, title]) => [
            path,
            path === "publicaciones" ? "Gestionar noticias" : title,
          ]),
      ];
  const logout = () => {
    if (!preview) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("rol");
    }
    navigate("/");
  };
  const submenus =
    role === "admin" && !innovation
      ? {
          publicaciones: [
            ["difusion", "Difusión"],
            ["difusion/visitas", "Visitas a salones"],
            ["difusion/plantillas", "Plantillas de mensajes"],
            ["difusion/preguntas", "Preguntas frecuentes"],
            ["difusion/contacto", "Contacto y configuración"],
          ],
          eventos: [["eventos/fichas", "Fichas institucionales"]],
          ...(user?.gestiona_accesos
            ? {
                roles: [
                  ["roles/accesos", "Perfiles complementarios"],
                  ["roles/auditoria", "Auditoría"],
                ],
              }
            : {}),
          reportes: [
            ["reportes/proyectos", "Proyectos"],
            ["reportes/emprendedores", "Emprendedores"],
            ["reportes/avances", "Avances"],
            ["reportes/estadisticas", "Estadísticas"],
            ["reportes/indicadores", "Indicadores"],
          ],
          seguimiento: [
            ["seguimiento/semana", "Seguimientos de la semana"],
            ["seguimiento/vencidos", "Seguimientos vencidos"],
            ["seguimiento/inactivos", "Inactivos"],
            ["seguimiento/ruta", "Ruta emprendedora"],
          ],
        }
      : {};
  const items = nav.map(([path, label]) => ({
    to: `${base}/${path}${query}`,
    label,
    end: path === "inicio",
    children: submenus[path]?.map(([child, title]) => ({
      to: `${base}/${child}`,
      label: title,
    })),
  }));
  if (role === "admin" && !innovation) {
    for (const [path, label, children] of [
      [
        "encuestas",
        "Encuestas",
        [
          ["encuestas", "Gestión"],
          ["encuestas/resultados", "Resultados"],
        ],
      ],
      [
        "catalogo",
        "Catálogo",
        [
          ["catalogo", "Servicios"],
          ["catalogo/hitos", "Hitos"],
          ["catalogo/ruta", "Configuración de ruta"],
        ],
      ],
      [
        "innovatec",
        "Gestión InnovaTec",
        [
          ["innovatec/convocatoria", "Convocatoria"],
          ["innovatec/equipos", "Equipos"],
          ["innovatec/platicas", "Pláticas"],
          ["innovatec/diplomas", "Diplomas"],
          ["innovatec/seguimiento", "Seguimiento de equipos"],
        ],
      ],
    ])
      items.push({
        to: `${base}/${path}`,
        label,
        children: children.map(([child, title]) => ({
          to: `${base}/${child}`,
          label: title,
        })),
      });
  }
  if (!innovation && !preview && user?.perfil === "asesor")
    items.push({ to: `${base}/asesoria`, label: "Expedientes asignados" });
  if (innovation) items.push({ to: home, label: "Incubadora" });
  else if (role !== "externo")
    items.push({
      to: `${preview ? "/vista-previa" : ""}/innovatecnm/inicio${preview ? `?rol=${role}` : ""}`,
      label: "InnovaTecNM",
      accent: true,
      description: "Módulo interno de innovación",
    });
  const account = (
    <div className="account">
      <span className="avatar" aria-hidden="true">
        {preview ? demoPeople[role][0] : user?.nombre?.[0]}
      </span>
      <div>
        <strong>{preview ? demoPeople[role] : user?.nombre}</strong>
        <small>{roleNames[role]}</small>
      </div>
      <button type="button" className="text-button" onClick={logout}>
        {preview ? "Salir de vista previa" : "Cerrar sesión"}
      </button>
    </div>
  );
  return (
    <div className="portal-app">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <Navigation home={home} items={items} account={account} />
      <main className="portal-main" id="contenido">
        {preview && (
          <div className="preview-bar">
            <div>
              <strong>Vista de demostración</strong>
              <span>
                Datos de ejemplo. Los cambios duran hasta recargar; no se
                realizan cobros.
              </span>
            </div>
            {preview && (
              <label>
                Cambiar rol
                <select
                  aria-label="Cambiar rol de vista previa"
                  value={role}
                  onChange={(e) => {
                    notify("");
                    navigate(
                      `/vista-previa/${rolePaths[e.target.value]}/inicio`,
                    );
                  }}
                >
                  <option value="estudiante">Emprendedor</option>
                  <option value="admin">Coordinador</option>
                  <option value="externo">Externo</option>
                </select>
              </label>
            )}
          </div>
        )}
        {notice && (
          <div className="notice" role="status">
            <span>{notice}</span>
            <button aria-label="Cerrar aviso" onClick={() => notify("")}>
              ×
            </button>
          </div>
        )}
        {!preview && (
          <div className="row between">
            <span role="status">
              {busy ? "Guardando cambios…" : "Tu cuenta está conectada"}
            </span>
            <button className="text-button" disabled={busy} onClick={refresh}>
              Actualizar datos
            </button>
          </div>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {loading ? (
          <p role="status">Cargando datos…</p>
        ) : (
          <fieldset
            disabled={busy}
            style={{ border: 0, padding: 0, margin: 0, minWidth: 0 }}
            key={location.pathname}
          >
            <Outlet
              context={{
                role,
                preview,
                base,
                query,
                userId: preview
                  ? role === "admin"
                    ? "ana"
                    : role === "externo"
                      ? "karla"
                      : "diego"
                  : user?.id,
              }}
            />
          </fieldset>
        )}
      </main>
      <InstitutionalFooter navigation={false} />
    </div>
  );
}
