import React from "react";

export default function DashboardAdmin() {
  // Datos quemados (estáticos) extraídos del diseño de la interfaz
  const estadisticas = [
    { titulo: "Proyectos activos", valor: "24", icono: "🚀" },
    { titulo: "Emprendedores", valor: "31", icono: "👥" },
    { titulo: "Eventos este mes", valor: "9", icono: "📅" },
    { titulo: "Progreso promedio", valor: "68%", icono: "📈" },
  ];

  const proyectosPorEspecialidad = [
    { carrera: "Ing. en Sistemas", cantidad: 9 },
    { carrera: "Ing. Industrial", cantidad: 6 },
    { carrera: "Ing. en Gestión", cantidad: 5 },
    { carrera: "Ing. Mecatrónica", cantidad: 4 },
  ];

  const estatusProyectos = [
    { estado: "En proceso", cantidad: 13, color: "bg-blue-100 text-blue-800" },
    { estado: "Completados", cantidad: 8, color: "bg-green-100 text-green-800" },
    { estado: "Pendientes", cantidad: 3, color: "bg-yellow-100 text-yellow-800" },
  ];

  return (
    <div className="min-h-screen bg-appbg font-body p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="font-display text-3xl text-guinda-dark mb-1">
            Estadísticas Generales
          </h1>
          <p className="text-gray-600">
            Hola, Ana Martínez. Aquí está el panorama numérico de la incubadora.
          </p>
        </header>

        {/* Tarjetas de métricas principales */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {estadisticas.map((stat, idx) => (
            <div
              key={idx}
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-100"
            >
              <div className="flex justify-between items-start mb-4">
                <span className="text-3xl font-display text-guinda">
                  {stat.valor}
                </span>
                <span className="text-2xl">{stat.icono}</span>
              </div>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                {stat.titulo}
              </h3>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Panel de Especialidades */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h2 className="font-display text-xl text-institucional mb-6">
              Proyectos por especialidad
            </h2>
            <div className="space-y-4">
              {proyectosPorEspecialidad.map((item, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center border-b border-gray-50 pb-3 last:border-0"
                >
                  <span className="text-gray-700">{item.carrera}</span>
                  <span className="font-medium text-guinda-dark bg-gray-100 px-3 py-1 rounded-full text-sm">
                    {item.cantidad}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Panel de Estatus */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h2 className="font-display text-xl text-institucional mb-6">
              Estatus de proyectos
            </h2>
            <div className="space-y-4">
              {estatusProyectos.map((item, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center border-b border-gray-50 pb-3 last:border-0"
                >
                  <span className="text-gray-700">{item.estado}</span>
                  <span
                    className={`font-medium px-3 py-1 rounded-full text-sm ${item.color}`}
                  >
                    {item.cantidad}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}