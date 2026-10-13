import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export const Dashboard = () => {
  const [filtroAno, setFiltroAno] = useState('2026');
  const [filtroMes, setFiltroMes] = useState('10');
  const [agrupacion, setAgrupacion] = useState('mes'); 
  const [filtroTipo, setFiltroTipo] = useState('evento'); // Por defecto analizamos Eventos
  
  const [datosGrafica, setDatosGrafica] = useState([]);
  const [lineasActivas, setLineasActivas] = useState([]);
  const [listaDetallada, setListaDetallada] = useState([]);

  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        const url = `/api/admin/metricas?ano=${filtroAno}&mes=${filtroMes}&agrupacion=${agrupacion}&tipo=${filtroTipo}`;
        const respuesta = await fetch(url);
        
        if (respuesta.ok) {
          const data = await respuesta.json();
          setDatosGrafica(data.resumenGrafica);
          setListaDetallada(data.listaAlumnos);
          
          // Magia para generar los colores dinámicamente según los datos (Eventos, Carreras, etc)
          if (data.resumenGrafica.length > 0) {
            const colores = ['#6d1b32', '#3b82f6', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#64748b'];
            let lineasEncontradas = new Set();
            
            data.resumenGrafica.forEach(item => {
              Object.keys(item).forEach(key => {
                if (key !== 'periodo') lineasEncontradas.add(key);
              });
            });

            const nuevasLineas = Array.from(lineasEncontradas).map((key, index) => ({
              key,
              color: colores[index % colores.length]
            }));
            setLineasActivas(nuevasLineas);
          } else {
             setLineasActivas([]); // Limpia las líneas si no hay datos en ese mes
          }

        } else {
          console.error("Error del servidor:", respuesta.status);
        }
      } catch (error) {
        console.error("No se pudo conectar a la API:", error);
      }
    };

    obtenerDatos();
  }, [filtroAno, filtroMes, agrupacion, filtroTipo]);

  // LA MAGIA DEL EXCEL ACTUALIZADA (Ahora soporta acentos)
  const exportarAExcel = () => {
    if (listaDetallada.length === 0) return;
    
    const encabezados = "Fecha,Evento,Nombre,Correo,Género,Carrera\n";
    
    // Encerramos evento, nombre y carrera en comillas por si traen comas (ej. Ing. Sistemas, Computación)
    const filas = listaDetallada.map(p => 
      `${p.fecha},"${p.evento}","${p.nombre}",${p.correo},${p.genero},"${p.carrera}"`
    ).join("\n");
    
    // \uFEFF fuerza a Excel a leerlo en formato UTF-8 para que los acentos funcionen perfecto
    const blob = new Blob(["\uFEFF" + encabezados + filas], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Reporte_Inscripciones_${filtroMes === 'todos' ? 'Anual' : 'Mes_'+filtroMes}_${filtroAno}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1100px', margin: '0 auto' }}>
      
      {/* Cabecera y Botón */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ color: '#6d1b32', margin: 0 }}>Reportes de Inscripción a Eventos</h2>
        <button onClick={exportarAExcel} style={estiloBotonExcel}>
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style={{marginRight: '8px'}}>
            <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
            <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
          </svg>
          Exportar Lista a Excel
        </button>
      </div>

      {/* Panel de Filtros */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginBottom: '25px', backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <label style={estiloLabel}>Año</label>
          <select value={filtroAno} onChange={(e) => setFiltroAno(e.target.value)} style={estiloSelect}>
            <option value="2025">2025</option>
            <option value="2026">2026</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <label style={estiloLabel}>Mes a reportar</label>
          <select value={filtroMes} onChange={(e) => setFiltroMes(e.target.value)} style={estiloSelect}>
            <option value="todos">Todos los meses</option>
            <option value="01">Enero</option>
            <option value="08">Agosto</option>
            <option value="09">Septiembre</option>
            <option value="10">Octubre</option>
            <option value="11">Noviembre</option>
            <option value="12">Diciembre</option>
          </select>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <label style={estiloLabel}>Agrupar por</label>
          <select value={agrupacion} onChange={(e) => setAgrupacion(e.target.value)} style={estiloSelect}>
            <option value="dia">Ver días</option>
            <option value="mes">Ver meses completos</option>
            <option value="ano">Ver año general</option>
          </select>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <label style={estiloLabel}>Categoría a graficar</label>
          <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)} style={estiloSelect}>
            <option value="evento">Evento (HackaTec, Talleres...)</option>
            <option value="carrera">Carrera</option>
            <option value="genero">Género</option>
            <option value="rol">Rol (Estudiantes / Externos)</option>
          </select>
        </div>
      </div>

      {/* Gráfica Dinámica */}
      <div style={{ width: '100%', height: 400, backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', marginBottom: '30px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={datosGrafica} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="periodo" />
            <YAxis />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            {lineasActivas.map((linea) => (
              <Line key={linea.key} type="monotone" dataKey={linea.key} stroke={linea.color} strokeWidth={3} activeDot={{ r: 8 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla de Detalle con Evento */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
        <h3 style={{ color: '#444', marginTop: 0, marginBottom: '15px' }}>Detalle de Participantes ({listaDetallada.length})</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f5f9', color: '#334155', borderBottom: '2px solid #e2e8f0' }}>
                <th style={{ padding: '12px 15px' }}>Fecha</th>
                <th style={{ padding: '12px 15px' }}>Evento</th>
                <th style={{ padding: '12px 15px' }}>Nombre</th>
                <th style={{ padding: '12px 15px' }}>Correo Electrónico</th>
                <th style={{ padding: '12px 15px' }}>Género</th>
                <th style={{ padding: '12px 15px' }}>Carrera</th>
              </tr>
            </thead>
            <tbody>
              {listaDetallada.map((persona) => (
                <tr key={persona.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '12px 15px', color: '#64748b', whiteSpace: 'nowrap' }}>{persona.fecha}</td>
                  <td style={{ padding: '12px 15px', color: '#6d1b32', fontWeight: 'bold' }}>{persona.evento}</td>
                  <td style={{ padding: '12px 15px', fontWeight: '500' }}>{persona.nombre}</td>
                  <td style={{ padding: '12px 15px', color: '#3b82f6' }}>{persona.correo}</td>
                  <td style={{ padding: '12px 15px', color: '#64748b' }}>{persona.genero}</td>
                  <td style={{ padding: '12px 15px' }}>
                    <span style={{ backgroundColor: '#e2e8f0', padding: '4px 8px', borderRadius: '12px', fontSize: '12px', whiteSpace: 'nowrap' }}>
                      {persona.carrera}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Estilos
const estiloSelect = { padding: '8px 12px', borderRadius: '6px', border: '1px solid #d1d5db', backgroundColor: '#fff', minWidth: '150px', cursor: 'pointer' };
const estiloLabel = { fontSize: '12px', fontWeight: 'bold', color: '#555' };
const estiloBotonExcel = { backgroundColor: '#107c41', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center' };