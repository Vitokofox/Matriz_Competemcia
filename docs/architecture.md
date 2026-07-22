# Arquitectura inicial

La aplicación está separada en dos procesos:

- **Backend:** API REST con FastAPI, configuración mediante variables de
  entorno y persistencia local con SQLAlchemy y SQLite.
- **Frontend:** aplicación de página única con React, TypeScript y Vite.

El frontend accede al backend a través de `VITE_API_URL`. Durante el desarrollo,
FastAPI permite solicitudes desde `http://localhost:5173` mediante CORS.

## Dominio de competencias

El backend contiene el modelo relacional de trabajadores, supervisores,
evaluadores, estructura organizativa, puestos, máquinas, actividades,
competencias y evaluaciones. Alembic administra la evolución del esquema.

Las consultas de dominio se mantienen en `app/services`. La consulta de
capacitación determina si una evaluación completada cumple todos los requisitos
vigentes del puesto sin depender de que exista una máquina asociada.
