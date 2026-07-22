# Matriz de Competencias

Esqueleto técnico para una aplicación de gestión de competencias. El backend
expone una API REST con FastAPI y SQLite; el frontend consume esa API desde
React y TypeScript.

## Requisitos

- Python 3.11 o superior
- Node.js 22 o superior
- npm 10 o superior

## Backend

Para abrir backend y frontend en ventanas separadas, ejecute desde la raíz:

```powershell
.\iniciar.ps1
```

También puede abrir `iniciar.bat` con doble clic.

El entorno virtual ya está ubicado en `backend/.venv`. Para reconstruirlo en
otro equipo y arrancar la API:

```powershell
python -m venv backend/.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
backend\.venv\Scripts\python -m uvicorn app.main:app --reload --app-dir backend
```

La API estará disponible en `http://localhost:8000` y su documentación en
`http://localhost:8000/docs`.

El CRUD expone más de 40 rutas bajo `/api`, incluyendo catálogos (`areas`, `cargos`,
`turnos`, `procesos`, `supervisores`, `evaluadores`, `maquinas`, `actividades`,
`competencias`, `puestos`), trabajadores, historial, requisitos,
evaluaciones y la consulta de trabajadores capacitados.

Ejemplo para crear un área:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/areas `
  -ContentType 'application/json' `
  -Body '{"nombre":"Producción","descripcion":"Área operativa"}'
```

La documentación Swagger en `/docs` contiene los esquemas y operaciones
disponibles.

## Frontend

```powershell
npm install --prefix frontend
npm run dev --prefix frontend
```

La interfaz estará disponible en `http://localhost:5173`.

## Configuración

Los valores predeterminados funcionan para desarrollo local. Si necesitas
cambiarlos, copia `backend/.env.example` a `backend/.env` y
`frontend/.env.example` a `frontend/.env`.

La migración crea la base SQLite `matriz_competencias.db`, sus 26 tablas y los
identificadores `Turno 1`, `Turno 2` y `Turno 3`. Este archivo es local y Git no
lo versiona.

La migración de seguridad crea permisos y roles predefinidos. En el primer
arranque se crea el usuario `admin`; su contraseña inicial se controla con
`ADMIN_INITIAL_PASSWORD` en `backend/.env`. Debe cambiarse mediante
`POST /api/auth/change-password`.

Para generar una migración después de modificar los modelos:

```powershell
backend\.venv\Scripts\python -m alembic -c backend\alembic.ini revision --autogenerate -m "descripcion del cambio"
backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
```

## Verificación

```powershell
backend\.venv\Scripts\python -m pytest backend\tests
backend\.venv\Scripts\python -m ruff check backend
backend\.venv\Scripts\python -m alembic -c backend\alembic.ini check
npm run lint --prefix frontend
npm run build --prefix frontend
```

## Estructura

```text
backend/
  app/
    api/      Rutas HTTP
    core/     Configuración de la aplicación
    db/       Motor y sesiones de base de datos
    models/   Modelo relacional
    services/ Consultas y reglas de negocio
  alembic/    Migraciones de base de datos
  tests/      Pruebas automatizadas
frontend/
  src/
    lib/      Cliente de la API
docs/         Documentación de arquitectura
```

El modelo de datos y sus reglas están descritos en `docs/data-model.md`.
