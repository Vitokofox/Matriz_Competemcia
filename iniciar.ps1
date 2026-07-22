$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$python = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "No existe el entorno virtual. Ejecute: python -m venv backend/.venv y luego instale backend/requirements.txt"
}

if (-not (Test-Path -LiteralPath (Join-Path $frontendDir "node_modules"))) {
    throw "No existen las dependencias del frontend. Ejecute: npm install --prefix frontend"
}

$backendCommand = @"
& '$python' -m alembic -c '$backendDir\alembic.ini' upgrade head
if (-not `$?) { throw 'No se pudo aplicar la migración de la base de datos' }
& '$python' -m uvicorn app.main:app --reload --app-dir '$backendDir'
"@

$frontendCommand = @"
npm run dev -- --host 0.0.0.0
"@

Start-Process powershell.exe `
    -WorkingDirectory $backendDir `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand)

Start-Process powershell.exe `
    -WorkingDirectory $frontendDir `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand)

Write-Host "Backend:  http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:5173"
