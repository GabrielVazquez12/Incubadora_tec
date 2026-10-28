const paths = {
  menu: ['M4 6h16M4 12h16M4 18h16'],
  close: ['m6 6 12 12M18 6 6 18'],
  chevron: ['m6 9 6 6 6-6'],
  external: ['M14 4h6v6M20 4l-9 9', 'M10 4H4v16h16v-6'],
  emprendimiento: ['M12 3c4 2 6 6 6 10l-6 4-6-4c0-4 2-8 6-10Z', 'm6 10-3 6 4-1M18 10l3 6-4-1M10 20v1M14 20v1', 'M12 8h.01'],
  innovacion: ['M9 17h6M9 20h6M10 23h4', 'M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 3H9c0-1 0-2-1-3Z'],
  vinculacion: ['m3 10 4-4 5 2 5-2 4 4-5 8-4-2-4 2-5-8Z', 'm8 9 4 3 3-3M12 12l4 4'],
  eventos: ['M4 5h16v16H4ZM8 3v4M16 3v4M4 10h16', 'm9 16 2 2 4-4'],
};

export default function Icon({ name, className = '' }) {
  return <svg className={`line-icon ${className}`} viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{(paths[name] || paths.chevron).map((path, i) => <path key={i} d={path} />)}</svg>;
}
