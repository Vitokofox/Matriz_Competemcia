# Modelo de datos

## Catálogos

- `areas`: áreas organizativas.
- `cargos`: cargos generales, por ejemplo Operador o Ayudante.
- `turnos`: identificadores rotativos, sin rango horario fijo.
- `maquinas`: equipos opcionales para los puestos.
- `puestos`: posiciones concretas asociadas a un cargo y un área.
- `actividades`: tareas que pueden repetirse en varios puestos.
- `actividad_areas` y `actividad_maquinas`: contexto operativo reutilizable de una
  actividad sin limitarla a una sola área o máquina.
- `competencias`: capacidades que se evalúan en una escala de 0 a 4.
- `competencias.dimension`: técnica, conductual, seguridad, calidad o coordinación.
- `competencias.critica`: identifica competencias cuyo incumplimiento requiere atención especial.
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

`importaciones_matriz` registra cada lote por máquina, contenido normalizado y
versión de reglas. `matriz_puesto_versiones` permite que una misma carga publique
matrices independientes para Operador y Ayudante, manteniendo una sola versión
publicada por puesto y preservando las versiones retiradas.

`borradores_importacion_matriz` conserva el perfil normalizado y la configuración
revisada antes de publicar. Sus estados son analizado, configurado, validado,
publicado o fallido. La publicación usa exactamente el contenido validado y crea
todas las matrices de la configuración dentro de una sola transacción.

`actividad_criterios` contiene los criterios observables de cada actividad, con su
referencia documental, orden y criticidad. `actividad_criterio_competencias`
relaciona cada criterio con las competencias que ayuda a evidenciar.

La creación guiada de una ficha operativa registra en una sola transacción la
actividad, su contexto, criterios, competencias y asignaciones a puestos. Las
relaciones se mantienen separadas para evitar duplicar actividades reutilizables.

Esto permite usar la misma actividad y competencia con diferente experiencia:

```text
Operador Máquina X  -> Operación segura -> nivel mínimo 3
Ayudante Máquina X  -> Operación segura -> nivel mínimo 2
```

## Evaluaciones

- `evaluaciones`: trabajador, evaluador, puesto, fecha, estado y observaciones.
- `evaluacion_detalles`: requisito evaluado, nivel obtenido, mínimo histórico y
  observaciones.
- `evaluacion_criterios`: nivel observado de 0 a 4, evidencia, observaciones y
  snapshot histórico por criterio.

Los niveles tienen restricciones de base de datos entre 0 y 4. Una competencia
se aprueba cuando `nivel_obtenido >= nivel_minimo`. El mínimo se copia al
detalle para conservar qué regla se aplicó históricamente.

- 0: no puede realizar la tarea o aún no está entrenado.
- 1: recibió entrenamiento teórico y comprende los principios básicos.
- 2: está familiarizado con la tarea y puede realizarla con ayuda.
- 3: trabaja autónomamente sin ayuda.
- 4: es experto y puede entrenar a otras personas.

El evaluador puntúa los criterios observables. El nivel de cada competencia se
calcula como el menor nivel de sus criterios obligatorios. Un criterio crítico de
seguridad bajo nivel 3 reprueba la evaluación, y un nivel 4 no compensa una brecha
en otro criterio.

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
