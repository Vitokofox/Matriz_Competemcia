# Modelo de datos

## Catálogos

- `areas`: áreas organizativas.
- `cargos`: cargos generales, por ejemplo Operador o Ayudante.
- `turnos`: identificadores rotativos, sin rango horario fijo.
- `maquinas`: equipos opcionales para los puestos.
- `puestos`: posiciones concretas asociadas a un cargo y un área.
- `actividades`: tareas que pueden repetirse en varios puestos.
- `competencias`: capacidades que se evalúan en una escala de 1 a 5.
- `procesos`: procesos operativos pertenecientes a un área.

Los puestos sin máquina permiten representar procesos manuales como Ayudante de
carga o Clasificador.

Una máquina solo puede tener un proceso activo en `maquina_procesos`; los cambios
de proceso conservan sus fechas. Los puestos tienen un proceso para la operación
nueva, una máquina opcional y un tipo: `operador`, `ayudante` o `manual`.

## Personas

- `trabajadores`: personas evaluadas y disponibles para cubrir puestos.
- `supervisores`: catálogo independiente administrado desde Configuración.
- `evaluadores`: catálogo independiente autorizado para evaluar a cualquier
  trabajador.

## Historial

- `asignaciones_laborales`: cargo, área y turno del trabajador. Un índice
  parcial garantiza una sola asignación activa por trabajador.
- `trabajador_supervisores`: conserva cambios de supervisor y garantiza uno
  activo por trabajador.
- `trabajador_puestos`: conserva los puestos cubiertos por cada trabajador y
  permite varios puestos activos.
- `trabajador_supervisores`: asigna un supervisor activo por trabajador y
  conserva los cambios históricos.
- `puesto_maquinas`: conserva la máquina vinculada a un puesto. Una máquina
  puede tener simultáneamente puestos diferentes de Operador y Ayudante.

Una fila vigente tiene `fecha_fin` nula. Las fechas cerradas no pueden terminar
antes de `fecha_inicio`.

## Requisitos

`puesto_actividades` implementa la relación muchos-a-muchos entre puestos y
actividades. `puesto_actividad_competencias` agrega las competencias y el nivel
mínimo requerido para cada combinación.

Esto permite usar la misma actividad y competencia con diferente experiencia:

```text
Operador Máquina X  -> Operación segura -> nivel mínimo 4
Ayudante Máquina X  -> Operación segura -> nivel mínimo 3
```

## Evaluaciones

- `evaluaciones`: trabajador, evaluador, puesto, fecha, estado y observaciones.
- `evaluacion_detalles`: requisito evaluado, nivel obtenido, mínimo histórico y
  observaciones.

Los niveles tienen restricciones de base de datos entre 1 y 5. Una competencia
se aprueba cuando `nivel_obtenido >= nivel_minimo`. El mínimo se copia al
detalle para conservar qué regla se aplicó históricamente.

La consulta `obtener_trabajadores_capacitados` devuelve trabajadores activos
con una evaluación completada que aprueba todos los requisitos vigentes del
puesto. Un puesto sin requisitos no produce trabajadores capacitados.

## Seguridad

- `usuarios`: cuentas de acceso, hash de contraseña y estado.
- `roles`: agrupaciones de permisos predefinidas o personalizadas.
- `permisos`: permisos del sistema; los marcados como sistema son los
  predefinidos y el administrador puede crear permisos adicionales.
- `usuario_roles` y `rol_permisos`: relaciones de autorización.

Supervisores y evaluadores pueden vincularse a una cuenta mediante `usuario_id`.
Una evaluación se ejecuta con el usuario autenticado y debe estar vinculada a
un supervisor o evaluador activo, nunca a una identidad enviada libremente por
el frontend.

## Códigos automáticos

`secuencias_codigos` administra códigos no editables para trabajadores,
supervisores, evaluadores, competencias, máquinas, puestos y procesos:

```text
TRB-0001  SUP-0001  EVA-0001  CMP-0001
MAQ-0001  PST-0001  PRO-0001
```

Los números son independientes por entidad, no se reutilizan al desactivar un
registro y se generan dentro de la misma transacción de creación.
