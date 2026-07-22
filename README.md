# Matriz de Competencias

Aplicación web para administrar catálogos, trabajadores, puestos, competencias,
evaluaciones y usuarios autorizados.

- Backend: FastAPI, SQLAlchemy, Alembic y SQLite.
- Frontend: React, TypeScript y Vite.
- Inicio automático disponible para Windows PowerShell y Linux Bash.

## Requisitos

Instale antes de comenzar:

- Python 3.11 o superior.
- Node.js 22 o superior.
- npm 10 o superior.
- Git.
- PowerShell 5.1 o superior en Windows.
- Bash en Linux.

## Instalación Desde Cero

### Windows PowerShell

Abra PowerShell y ejecute:

```powershell
git clone https://github.com/Vitokofox/Matriz_Competemcia.git
Set-Location Matriz_Competemcia

Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env

python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

npm install --prefix frontend
```

El entorno virtual `backend/.venv`, las dependencias de Node y la base de datos
local no se versionan en Git. Por eso estos pasos son necesarios después de cada
clon nuevo.

### Linux Bash

Abra una terminal y ejecute:

```bash
git clone https://github.com/Vitokofox/Matriz_Competemcia.git
cd Matriz_Competemcia

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt

npm install --prefix frontend
```

## Configuración

### Backend

Edite `backend/.env` antes del primer inicio:

```dotenv
APP_NAME=Matriz de Competencias API
API_PREFIX=/api
DATABASE_URL=sqlite:///./matriz_competencias.db
CORS_ORIGINS=["http://localhost:5173"]
JWT_SECRET=reemplace-este-valor-por-un-secreto-de-32-caracteres
ACCESS_TOKEN_MINUTES=60
ADMIN_INITIAL_PASSWORD=Cambiar123!
```

Recomendaciones:

- Cambie `JWT_SECRET` por un valor largo y privado.
- Cambie `ADMIN_INITIAL_PASSWORD` antes del primer inicio en ambientes reales.
- No suba `backend/.env` a GitHub.
- La base SQLite se crea dentro de `backend/` porque los comandos de Alembic y
  el script de inicio ejecutan el backend desde esa carpeta.

### Frontend

El archivo `frontend/.env` debe contener:

```dotenv
VITE_API_URL=http://localhost:8000
```

Si el backend se publica en otra dirección, cambie esta URL y agregue el origen
correspondiente en `CORS_ORIGINS` del backend.

## Migración Inicial

El inicio automático aplica las migraciones pendientes. Para ejecutarlas de
forma manual, desde la raíz del proyecto use el comando correspondiente:

### Windows PowerShell

```powershell
Set-Location backend
.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
Set-Location ..
```

### Linux Bash

```bash
(
  cd backend
  .venv/bin/python -m alembic -c alembic.ini upgrade head
)
```

Esto crea la base SQLite, sus tablas, permisos, roles y secuencias para generar
códigos automáticos como `TRB-001`, `SUP-001`, `EVA-001`, `CMP-001`, `MAQ-001`,
`PST-001` y `PRO-001`.

## Inicio Automático

Desde la raíz del proyecto:

### Windows

```powershell
.\iniciar.ps1
```

También puede ejecutar `iniciar.bat` con doble clic.

### Linux

```bash
./iniciar.sh
```

Si Git no conservó el permiso de ejecución, asígnelo una vez:

```bash
chmod +x iniciar.sh
```

Los lanzadores de Windows y Linux:

1. Verifica que exista `backend/.venv`.
2. Verifica que exista `frontend/node_modules`.
3. Ejecuta las migraciones pendientes.
4. Inician FastAPI y Vite.

En Linux, ambos servicios se mantienen asociados a la terminal actual y se
detienen al pulsar `Ctrl+C`. En Windows se abren en ventanas de PowerShell
separadas.

Direcciones disponibles:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Inicio Manual

### Backend en Windows PowerShell

En una terminal:

```powershell
Set-Location backend
.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Backend en Linux Bash

```bash
cd backend
.venv/bin/python -m alembic -c alembic.ini upgrade head
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0
```

### Frontend en Windows PowerShell

En otra terminal, desde la raíz:

```powershell
npm run dev --prefix frontend
```

### Frontend en Linux Bash

En otra terminal, desde la raíz:

```bash
npm run dev --prefix frontend
```

Para permitir acceso desde otros dispositivos de la red:

```text
npm run dev --prefix frontend -- --host 0.0.0.0
```

## Primer Acceso

Después de aplicar las migraciones, el primer arranque crea el usuario
administrador si todavía no existe:

```text
Usuario: admin
Contraseña: Cambiar123!
```

Si cambió `ADMIN_INITIAL_PASSWORD` en `backend/.env`, use ese valor.

Cambie la contraseña inmediatamente desde el endpoint autenticado:

```text
POST /api/auth/change-password
```

El usuario debe tener permisos para administrar la configuración. Para crear un
usuario evaluador no basta con asignar el rol: también debe crear un registro en
**Configuración → Evaluadores**, vincularle un usuario activo y asignarle el
permiso `evaluaciones.crear`.

## Flujo Inicial Recomendado

1. Inicie sesión como administrador.
2. Revise áreas, cargos y turnos.
3. Cree procesos y máquinas.
4. Cree actividades y competencias.
5. Cree puestos y asigne sus actividades y requisitos.
6. Cree supervisores y evaluadores.
7. Vincule cada persona autorizada con un usuario activo.
8. Cree trabajadores y sus asignaciones.
9. Configure usuarios, roles y permisos.
10. Registre y complete evaluaciones desde el detalle del trabajador.

## Carga Masiva Excel

La carga se encuentra en **Configuración → Carga masiva**.

El flujo es:

1. Descargar `plantilla_carga_masiva.xlsx`.
2. Completar las hojas necesarias.
3. Mantener la columna oculta `__ejemplo__`; las filas marcadas como ejemplo se
   ignoran.
4. No escribir códigos: el sistema los genera automáticamente.
5. Subir el archivo y pulsar **Validar archivo**.
6. Corregir los errores indicados por hoja y fila.
7. Elegir el modo de importación.
8. Confirmar la importación.

El modo predeterminado es **Actualizar campos informados**. Las celdas vacías
no sobrescriben datos existentes. La segunda opción es **Omitir registros
existentes**.

La plantilla contiene hojas para áreas, cargos, turnos, procesos, máquinas,
actividades, competencias, puestos, requisitos, supervisores, evaluadores,
trabajadores y asignaciones.

La importación valida columnas obligatorias, duplicados, fechas, referencias,
niveles de competencia, tipos de puesto y relaciones entre entidades. Si hay
errores críticos, la carga completa se rechaza y no se guarda parcialmente.

## Verificación

Backend:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests
backend\.venv\Scripts\python.exe -m ruff check backend
backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini check
```

Frontend:

```powershell
npm run lint --prefix frontend
npm run build --prefix frontend
```

## Estructura

```text
backend/
  app/                 Código de la API y reglas de negocio
  alembic/             Migraciones de base de datos
  tests/               Pruebas automatizadas
frontend/
  src/                 Aplicación React y cliente de API
iniciar.ps1            Inicio automático en Windows
iniciar.bat            Lanzador de PowerShell
iniciar.sh             Inicio automático en Linux
```

## Producción

Para producción no use los valores predeterminados:

- Defina un `JWT_SECRET` seguro.
- Use una contraseña inicial administrada de forma segura.
- Restrinja `CORS_ORIGINS` a los dominios reales.
- Ejecute el backend detrás de un proxy HTTPS.
- No exponga Swagger públicamente sin protección adicional.
- Respaldar periódicamente `backend/matriz_competencias.db` si se mantiene
  SQLite.
