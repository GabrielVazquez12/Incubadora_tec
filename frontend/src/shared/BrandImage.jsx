export const brandAlt = 'Logotipo de Enlaces Institucionales ITS, Tecnológico Nacional de México, Instituto Tecnológico de Saltillo';

export default function BrandImage({ priority = false, maxWidth = 420, sizes = '(min-width: 1024px) 420px, 46vw', className = '' }) {
  return <div className={`brand-full ${className}`} style={{ '--brand-image-max': `${maxWidth}px` }}>
    <picture>
      <source type="image/webp" srcSet="/brand/enlaces-institucionales-400.webp 400w, /brand/enlaces-institucionales-800.webp 800w, /brand/enlaces-institucionales-1200.webp 1200w" sizes={sizes} />
      <img src="/brand/enlaces-institucionales.jpeg" srcSet="/brand/enlaces-institucionales-400.jpeg 400w, /brand/enlaces-institucionales-800.jpeg 800w, /brand/enlaces-institucionales-1200.jpeg 1200w" sizes={sizes} alt={brandAlt} width="1254" height="1254" loading={priority ? 'eager' : 'lazy'} fetchpriority={priority ? 'high' : undefined} decoding="async" />
    </picture>
  </div>;
}
