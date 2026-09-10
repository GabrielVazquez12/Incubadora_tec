import React from "react";
import { Link } from "react-router-dom";

export default function PortalEstudiante() {
  // Datos simulados para la maqueta
  const anuncios = [
    {
      id: 1,
      tipo: "Convocatoria",
      titulo: "Apertura HackaTec 2026",
      fecha: "15 SEP",
      descripcion: "Se abren inscripciones para el certamen nacional. Registra tu equipo en la plataforma.",
      color: "text-institucional bg-blue-50 border-blue-200"
    },
    {
      id: 2,
      tipo: "Taller",
      titulo: "Taller: Pitch de Negocios",
      fecha: "22 SEP",
      descripcion: "Aprende a vender tu idea en 3 minutos. Obligatorio para proyectos en fase de incubación.",
      color: "text-guinda-dark bg-red-50 border-red-200"
    }
  ];

  const miProyecto = {
    nombre: "Vishand - Prótesis Robótica",
    estatus: "En revisión",
    progreso: 25,
    siguientePaso: "Subir formato de modelo de negocio (Canvas)."
  };

  return (
    <div className="min-h-screen bg-appbg font-body p-6 md:p-10">
      <div className="max-w-5xl mx-auto">
        
        <header className="mb-10 flex justify-between items-end">
          <div>
            <h1 className="font-display text-3xl text-guinda-dark mb-2">
              Portal del Emprendedor
            </h1>
            <p className="text-gray-600 text-sm">
              Bienvenido. Revisa tus avisos y el avance de tu proyecto.
            </p>
          </div>
          <button className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm hover:bg-gray-50 transition-colors">
            Cerrar sesión
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Columna Izquierda: Mi Proyecto */}
          <div className="lg:col-span-2 space-y-6">
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="font-display text-xl text-institucional">Mi Proyecto Activo</h2>
                <span className="bg-yellow-100 text-yellow-800 text-xs font-medium px-3 py-1 rounded-full">
                  {miProyecto.estatus}
                </span>
              </div>
              
              <h3 className="text-2xl font-bold text-gray-800 mb-2">{miProyecto.nombre}</h3>
              
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Progreso de incubación</span>
                  <span>{miProyecto.progreso}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-institucional h-2 rounded-full" 
                    style={{ width: `${miProyecto.progreso}%` }}
                  ></div>
                </div>
              </div>

              <div className="bg-gray-50 border border-gray-100 rounded-md p-4">
                <p className="text-sm text-gray-600 font-medium mb-1">Acción requerida:</p>
                <p className="text-sm text-gray-800">{miProyecto.siguientePaso}</p>
              </div>
            </section>
          </div>

          {/* Columna Derecha: Tablero de Anuncios */}
          <div className="space-y-6">
            <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="font-display text-xl text-institucional mb-6">Tablero de Avisos</h2>
              
              <div className="space-y-4">
                {anuncios.map((anuncio) => (
                  <div key={anuncio.id} className={`border rounded-lg p-4 ${anuncio.color}`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold uppercase tracking-wider">
                        {anuncio.tipo}
                      </span>
                      <span className="text-xs font-medium opacity-75">
                        {anuncio.fecha}
                      </span>
                    </div>
                    <h4 className="font-bold mb-1 text-sm">{anuncio.titulo}</h4>
                    <p className="text-xs opacity-90">{anuncio.descripcion}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>

        </div>
      </div>
    </div>
  );
}