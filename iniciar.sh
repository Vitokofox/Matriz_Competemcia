#!/usr/bin/env bash

set -Eeuo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backend_dir="$project_root/backend"
frontend_dir="$project_root/frontend"
python="$backend_dir/.venv/bin/python"
vite="$frontend_dir/node_modules/.bin/vite"
backend_pid=""
frontend_pid=""

if [[ ! -x "$python" ]]; then
    printf '%s\n' "No existe el entorno virtual. Ejecute: python3 -m venv backend/.venv y luego instale backend/requirements.txt" >&2
    exit 1
fi

if [[ ! -x "$vite" ]]; then
    printf '%s\n' "No existen las dependencias del frontend. Ejecute: npm install --prefix frontend" >&2
    exit 1
fi

port_in_use() {
    local port="$1"
    local listener

    if command -v ss >/dev/null 2>&1; then
        while IFS= read -r listener; do
            [[ -n "$listener" ]] && return 0
        done < <(ss -ltnH "sport = :$port")
        return 1
    fi

    (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null
}

require_free_port() {
    local port="$1"
    local service="$2"

    if port_in_use "$port"; then
        printf '%s\n' "$service no puede iniciar: el puerto $port ya está ocupado." >&2
        printf '%s\n' "Detenga la instancia anterior y vuelva a ejecutar ./iniciar.sh" >&2
        exit 1
    fi
}

cleanup() {
    [[ -n "$frontend_pid" ]] && kill "$frontend_pid" 2>/dev/null || true
    [[ -n "$backend_pid" ]] && kill "$backend_pid" 2>/dev/null || true
    [[ -n "$frontend_pid" ]] && wait "$frontend_pid" 2>/dev/null || true
    [[ -n "$backend_pid" ]] && wait "$backend_pid" 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

require_free_port 8000 "Backend"
require_free_port 5173 "Frontend"

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
    exec "$vite" --host 0.0.0.0 --strictPort
) &
frontend_pid=$!

printf '%s\n' "Backend:  http://localhost:8000/docs"
printf '%s\n' "Frontend: http://localhost:5173"
printf '%s\n' "Presione Ctrl+C para detener los servicios."

if wait -n "$backend_pid" "$frontend_pid"; then
    exit 0
else
    exit $?
fi
