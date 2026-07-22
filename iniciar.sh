#!/usr/bin/env bash

set -Eeuo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backend_dir="$project_root/backend"
frontend_dir="$project_root/frontend"
python="$backend_dir/.venv/bin/python"
backend_pid=""
frontend_pid=""

if [[ ! -x "$python" ]]; then
    printf '%s\n' "No existe el entorno virtual. Ejecute: python3 -m venv backend/.venv y luego instale backend/requirements.txt" >&2
    exit 1
fi

if [[ ! -d "$frontend_dir/node_modules" ]]; then
    printf '%s\n' "No existen las dependencias del frontend. Ejecute: npm install --prefix frontend" >&2
    exit 1
fi

cleanup() {
    [[ -n "$backend_pid" ]] && kill "$backend_pid" 2>/dev/null || true
    [[ -n "$frontend_pid" ]] && kill "$frontend_pid" 2>/dev/null || true
    [[ -n "$backend_pid" ]] && wait "$backend_pid" 2>/dev/null || true
    [[ -n "$frontend_pid" ]] && wait "$frontend_pid" 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

(
    cd "$backend_dir"
    "$python" -m alembic -c alembic.ini upgrade head
)

(
    cd "$backend_dir"
    exec "$python" -m uvicorn app.main:app --reload --host 0.0.0.0
) &
backend_pid=$!

(
    cd "$frontend_dir"
    exec npm run dev -- --host 0.0.0.0
) &
frontend_pid=$!

printf '%s\n' "Backend:  http://localhost:8000/docs"
printf '%s\n' "Frontend: http://localhost:5173"
printf '%s\n' "Presione Ctrl+C para detener los servicios."

wait "$backend_pid" "$frontend_pid"
