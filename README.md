# Incubadora en Linea/ Sistema que integre y automatice los procesos de la incubadora de empresas e Innovatec


> Plataforma para digitalizar y sistematizar los procesos de la incubadora del Tecnológico de Saltillo, sustituyendo el manejo manual actual (correos, PDFs, impresión) por un sistema centralizado con roles.

## 📋 Descripción

Actualmente las coordinadoras de la incubadora gestionan todo de forma manual: reciben correos con información en PDF, imprimen documentos y dan seguimiento a estudiantes/proyectos sin un sistema centralizado. Este proyecto busca sistematizar ese flujo mediante una plataforma web con tres roles:

- **Coordinadoras (admin):** dashboard de seguimiento, generación de reportes y Excel, gestión de documentos, comunicación con estudiantes.
- **Estudiantes:** registro, subida de documentos, descarga de formatos/constancias, seguimiento de su estatus.
- **Externos:** (definir alcance específico — empresas, mentores, etc.)

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | FastAPI (Python) |
| Base de datos | PostgreSQL (Amazon RDS) |
| ORM / Migraciones | SQLAlchemy + Alembic |
| Autenticación | JWT (python-jose) + bcrypt (passlib) |
| Almacenamiento de archivos | Amazon S3 |
| Frontend | React + Tailwind CSS |
| Gráficas | Recharts |
| Generación de Excel | pandas / openpyxl |
| Generación de PDF | WeasyPrint / ReportLab |
| Pagos | Stripe / Mercado Pago (sandbox) — Quentli como opción institucional a futuro |
| Hosting backend | AWS App Runner |
| Hosting frontend | S3 + CloudFront / Amplify |

> Ver `docs/stack-tecnologico.md` para el detalle de alternativas consideradas y justificación de cada decisión.

## 📁 Estructura del proyecto

```
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Esquemas Pydantic
│   │   ├── routers/         # Endpoints por módulo/rol
│   │   ├── auth/            # JWT, dependencias de autorización por rol
│   │   ├── services/        # Lógica de negocio (Excel, PDF, pagos)
│   │   └── database.py
│   ├── alembic/              # Migraciones
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/            # Vistas por rol (admin/estudiante/externo)
│   │   ├── routes/           # Rutas protegidas por rol
│   │   └── services/         # Cliente API
│   ├── package.json
│   └── .env.example
├── docs/
│   ├── stack-tecnologico.md
│   ├── modelo-de-datos.md
│   └── arquitectura-aws.md
└── README.md
```

## 🚀 Instalación y ejecución local

### Requisitos previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (o Docker)
- Cuenta de AWS (para S3, opcional en desarrollo local)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env con tus credenciales locales

alembic upgrade head        # Aplica migraciones
uvicorn app.main:app --reload
```

Backend corriendo en `http://localhost:8000` — docs automáticas en `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install

cp .env.example .env
# Edita .env con la URL del backend

npm run dev
```

Frontend corriendo en `http://localhost:5173`.

## 🐳 Ejecución con Docker (recomendado)

En vez de instalar Python/Node/Postgres localmente, puedes levantar todo con Docker Compose.

### Requisitos

- Docker y Docker Compose instalados

### Pasos

```bash
# 1. Copia los archivos de ejemplo de variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Levanta todo (Postgres + backend + frontend)
docker compose up --build

# 3. En otra terminal, aplica las migraciones (primera vez o tras cambios de modelo)
docker compose exec backend alembic upgrade head
```

- Backend: `http://localhost:8000` (docs en `/docs`)
- Frontend: `http://localhost:5173`
- Postgres: `localhost:5432` (usuario/clave definidos en `docker-compose.yml`, solo para desarrollo local)

### Comandos útiles

```bash
docker compose down                     # Apaga los servicios
docker compose down -v                  # Apaga y borra también el volumen de la BD (reset total)
docker compose logs -f backend          # Ver logs del backend en vivo
docker compose exec backend bash        # Entrar a la terminal del contenedor backend
docker compose exec db psql -U incubadora  # Entrar a psql directo
```

### Estructura de archivos Docker

```
.
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   └── .dockerignore
└── frontend/
    ├── Dockerfile
    └── .dockerignore
```

> El `Dockerfile` del frontend tiene dos etapas: `dev` (usada por `docker-compose.yml`, con hot-reload) y `production` (build optimizado servido por nginx, usada al desplegar en AWS).

## 🔐 Variables de entorno

### Backend (`.env`)

```
DATABASE_URL=postgresql://usuario:password@localhost:5432/incubadora
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
STRIPE_SECRET_KEY=
```

### Frontend (`.env`)

```
VITE_API_URL=http://localhost:8000
```

> ⚠️ Nunca commitear el `.env` real. Está incluido en `.gitignore`.

## 👥 Roles y permisos

| Rol | Permisos |
|---|---|
| Admin (coordinadora) | Acceso total: gestión de estudiantes, proyectos, documentos, reportes, configuración |
| Estudiante | Registro propio, subida/descarga de sus documentos, ver su estatus |
| Externo | (definir alcance) |

## 📊 Roadmap

- [ ] Modelo de datos y migraciones iniciales
- [ ] Autenticación y autorización por rol
- [ ] CRUD de estudiantes y proyectos
- [ ] Subida de documentos a S3
- [ ] Generación de reportes Excel
- [ ] Generación de constancias/documentos PDF
- [ ] Dashboard con gráficas para coordinadoras
- [ ] Integración de pagos (sandbox)
- [ ] Deploy en AWS

## 📄 Licencia

Proyecto académico — Residencia Profesional, Tecnológico Nacional de México campus Saltillo.

## 👤 Autor

Carlos Gabriel Vázquez Vélez — Jose Enrique Vazquez Garcia - Mariana Nahomi Reyes Esparza