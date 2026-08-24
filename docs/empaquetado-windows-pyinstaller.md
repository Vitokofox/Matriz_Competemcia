# Empaquetado para Windows con PyInstaller

Esta guía describe cómo distribuir **Matriz de Competencias** como una aplicación
Windows que inicia el backend FastAPI, sirve el frontend React compilado y guarda
la base SQLite fuera del ejecutable.

> Estado actual: el repositorio incluye `backend/portable_entry.py`, montaje del
> frontend compilado y `packaging/matriz_competencias.spec`. El build genera una
> distribución `onedir` y mantiene SQLite fuera del bundle.

## Arquitectura revisada

- Backend: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy y Alembic.
- Frontend: React, TypeScript y Vite; el resultado está en `frontend/dist`.
- Persistencia: SQLite, configurada actualmente como
  `sqlite:///./matriz_competencias.db`.
- Migraciones: 12 revisiones en `backend/alembic/versions`.
- Configuración: `backend/.env`, cargado desde una ruta relativa al código.
- No existe aún un entrypoint ejecutable ni un archivo `.spec`.

La distribución recomendada inicialmente es `onedir`:

```text
MatrizCompetencias/
├── MatrizCompetencias.exe
├── _internal/                 # dependencias administradas por PyInstaller
└── data/                      # se crea al iniciar; no se empaqueta
    └── matriz_competencias.db
```

`onedir` simplifica el diagnóstico de DLL y recursos. Conviene evaluar `onefile`
solo después de validar esta variante.

## Preparación implementada

Antes del primer build se deben implementar y probar estos cambios en el
repositorio:

1. Crear, por ejemplo, `backend/portable_entry.py`. Debe:
   - determinar la carpeta persistente de la aplicación;
   - crear `data/` si no existe;
   - definir la URL SQLite absoluta **antes** de importar `app.main`;
   - ejecutar `alembic upgrade head` mediante la API de Alembic;
   - iniciar `uvicorn.run(app, host="127.0.0.1", port=8000)`;
   - abrir `http://127.0.0.1:8000` en el navegador cuando el servidor esté listo.
2. Hacer que `backend/app/main.py` monte `frontend/dist` con
   `StaticFiles` y entregue `index.html` como fallback de la SPA. Las rutas `/api`,
   `/docs` y `/redoc` deben registrarse antes del fallback.
3. Resolver recursos embebidos desde `sys._MEIPASS` cuando
   `getattr(sys, "frozen", False)` sea verdadero. Esto aplica al frontend,
   `alembic.ini` y `backend/alembic/`.
4. Mantener la base de datos fuera de `_MEIPASS`. Una ubicación portable puede
   ser `data/` junto al `.exe`; para una instalación tradicional es preferible
   `%LOCALAPPDATA%\\MatrizCompetencias\\data`.
5. Compilar el frontend para el mismo origen del backend. Crear un archivo de
   entorno de producción con:

   ```dotenv
   VITE_API_URL=http://127.0.0.1:8000
   ```

   Alternativamente, adaptar `frontend/src/lib/api.ts` para aceptar una URL base
   vacía y usar rutas `/api` relativas.
6. Decidir cómo suministrar secretos. `backend/.env` y cualquier base real no
   deben quedar dentro del bundle. En producción se debe exigir un `JWT_SECRET`
   propio y cambiar `ADMIN_INITIAL_PASSWORD` antes de distribuir.

### Orden de inicialización requerido

El orden es importante porque `app.core.config` y `app.db.session` crean la
configuración y el motor SQLAlchemy al importarse:

```text
portable_entry.py
  → determina directorio de datos
  → define DATABASE_URL absoluta
  → configura y ejecuta Alembic
  → importa app.main:app
  → inicia Uvicorn
```

No se debe cambiar `DATABASE_URL` después de importar `app.db.session`, porque el
motor ya apuntaría a la ubicación anterior.

## Archivo `.spec` recomendado

Después de crear el entrypoint, agregar `packaging/matriz_competencias.spec`.
Esta es la estructura de referencia; las rutas deben validarse desde la raíz del
repositorio:

```python
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPECPATH).resolve().parent.parent
backend = root / "backend"

hiddenimports = collect_submodules("uvicorn") + collect_submodules("alembic")

a = Analysis(
    [str(backend / "portable_entry.py")],
    pathex=[str(backend)],
    binaries=[],
    datas=[
        (str(root / "frontend" / "dist"), "frontend/dist"),
        (str(backend / "alembic"), "backend/alembic"),
        (str(backend / "alembic.ini"), "backend"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MatrizCompetencias",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="MatrizCompetencias",
)
```

Durante la puesta a punto se recomienda `console=True`, porque conserva los
errores de arranque. Cambiarlo a `False` únicamente cuando exista un registro en
archivo y el ejecutable haya sido validado.

## Construcción en Windows

La vía más simple es construir en Windows con Python x64 de la misma versión que
se usará para la aplicación:

```powershell
Set-Location C:\ruta\Matriz_Competemcia

python -m venv .venv-build
.venv-build\Scripts\python.exe -m pip install --upgrade pip
.venv-build\Scripts\python.exe -m pip install -r backend\requirements.txt
.venv-build\Scripts\python.exe -m pip install --upgrade pyinstaller

npm ci --prefix frontend
$env:VITE_API_URL = "http://127.0.0.1:8000"
npm run build --prefix frontend

.venv-build\Scripts\python.exe -m PyInstaller `
  --clean `
  --noconfirm `
  packaging\matriz_competencias.spec
```

El resultado esperado es:

```text
dist/MatrizCompetencias/MatrizCompetencias.exe
```

No usar el Python nativo de Linux para generar un `.exe` de Windows.

## Construcción desde Ubuntu/Linux con Wine

Se necesita Wine x64 y una instalación de Python **para Windows** dentro de un
prefix dedicado. Wine y Python Windows se instalan una sola vez; este proceso no
debe reutilizar el prefix personal predeterminado.

```bash
export WINEPREFIX="$PWD/.wine-pyinstaller"
wineboot -u
wine --version
```

Instalar Python Windows x64 en ese prefix y localizar su ejecutable:

```bash
find "$WINEPREFIX/drive_c" -iname python.exe \
  -not -path '*/Lib/venv/*' 2>/dev/null
```

Guardar la ruta seleccionada en una variable específica, por ejemplo:

```bash
WIN_PY="$WINEPREFIX/drive_c/users/$USER/AppData/Local/Programs/Python/Python312/python.exe"
wine "$WIN_PY" --version
wine "$WIN_PY" -m pip --version
```

Instalar las dependencias Windows y construir:

```bash
wine "$WIN_PY" -m pip install --upgrade pip
wine "$WIN_PY" -m pip install -r backend/requirements.txt
wine "$WIN_PY" -m pip install --upgrade pyinstaller

npm ci --prefix frontend
VITE_API_URL=http://127.0.0.1:8000 npm run build --prefix frontend

wine "$WIN_PY" -m PyInstaller \
  --clean \
  --noconfirm \
  packaging/matriz_competencias.spec
```

No es necesario agregar `tzdata` actualmente: la revisión del código no encontró
uso de `zoneinfo` ni zonas IANA. Se debe incorporarlo si más adelante se usa una
zona como `America/Santiago`.

## Configuración del release

Distribuir el directorio completo generado por `onedir`. Junto al ejecutable se
puede colocar un `.env` de instalación, pero nunca debe contener valores reales
en Git ni en el artefacto público. Como mínimo:

```dotenv
APP_NAME=Matriz de Competencias API
API_PREFIX=/api
JWT_SECRET=generar-un-secreto-unico-largo-y-privado
ACCESS_TOKEN_MINUTES=60
ADMIN_INITIAL_PASSWORD=definir-una-clave-inicial-segura
```

La aplicación debe establecer internamente una URL SQLite absoluta. No confiar
en `sqlite:///./matriz_competencias.db`: al abrir el programa mediante un acceso
directo, el directorio de trabajo puede ser distinto al del ejecutable.

No incluir en el release:

- `backend/.env` de desarrollo;
- `matriz_competencias.db` con datos reales;
- archivos Excel de trabajo de `Actividades/`;
- backups, uploads, cachés, `.venv` o `node_modules`;
- tests, Ruff o dependencias exclusivas de desarrollo.

## Pruebas obligatorias

Primero ejecutar con Wine o en una máquina Windows limpia:

```bash
wine dist/MatrizCompetencias/MatrizCompetencias.exe
```

Validar, en este orden:

1. El proceso inicia sin `ModuleNotFoundError`, DLL faltantes ni errores de rutas.
2. `http://127.0.0.1:8000/api/health` responde correctamente.
3. `http://127.0.0.1:8000/` carga React y sus archivos JS/CSS responden `200`.
4. Al recargar una ruta de la SPA, FastAPI devuelve `index.html`.
5. Alembic crea una base vacía y aplica las 12 migraciones.
6. El administrador inicial se crea y permite iniciar sesión.
7. La descarga de `plantilla_carga_masiva.xlsx` funciona.
8. Se pueden crear, cerrar y volver a abrir registros sin perder datos.
9. La base permanece en el directorio persistente y no en `_MEIPASS`.
10. Una actualización del ejecutable conserva la base existente y aplica solo
    las migraciones pendientes.

Para comprobar un release real, probarlo en Windows sin Python, Node ni Git
instalados. El frontend compilado no necesita Node en el equipo de destino.

## Diagnóstico frecuente

| Síntoma | Causa probable | Comprobación |
|---|---|---|
| El `.exe` termina inmediatamente | excepción sin consola o entrypoint incompleto | mantener `console=True` y ejecutar desde `cmd.exe` |
| `ModuleNotFoundError` de Uvicorn/Alembic | importación dinámica no detectada | revisar `hiddenimports` y volver a construir con `--clean` |
| El frontend muestra una pantalla vacía | `frontend/dist` ausente o URL de API incorrecta | revisar `datas`, DevTools y `VITE_API_URL` de build |
| La base aparece en una carpeta inesperada | URL SQLite relativa al directorio de trabajo | construir una URL absoluta antes de importar la app |
| Alembic no encuentra migraciones | `script_location` apunta fuera del bundle | configurar la ruta de `_MEIPASS/backend/alembic` por código |
| Los datos desaparecen al reiniciar `onefile` | se escribieron dentro de `_MEIPASS` | mover la persistencia junto al `.exe` o a `%LOCALAPPDATA%` |
| Windows bloquea o alerta por el binario | ejecutable sin firma/reputación | firmar el release y publicar checksum desde una fuente confiable |

## Criterio de finalización

El empaquetado se considera terminado cuando el `.exe` funciona en un Windows
limpio, sirve frontend y API, ejecuta migraciones, conserva SQLite fuera del
bundle y el release no contiene secretos ni datos productivos.
