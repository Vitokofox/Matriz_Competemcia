# Plan de Estilos Frontend

## Objetivo

Adoptar el sistema visual de referencia ubicado en:

```text
E:\Seguridad\Matriz Competencias\matriz_competencias\frontend
```

La aplicación debe conservar la lógica y los endpoints actuales, pero utilizar
una interfaz institucional consistente, responsive y reutilizable.

## Identidad visual

Usar los tokens institucionales definidos en `tokens.css`:

- Gris oscuro: `#49433e`.
- Gris secundario: `#696158`.
- Verde: `#9a9500` y `#bfb800`.
- Naranja: `#c96200` y `#ea7600`.
- Beige: `#dfd1a7` y `#f6f1e3`.
- Fondo: `#f5f4f1`.
- Superficie: `#ffffff`.
- Bordes: `#d8d4cf`.
- Texto: `#292622`.

Estados funcionales:

- Éxito: `#287a50`.
- Advertencia: `#9d4f00`.
- Peligro: `#b42318`.
- Información: `#28648c`.

## Tipografía

- Usar `Segoe UI`, Arial y Helvetica.
- Mantener títulos en gris oscuro.
- Utilizar `eyebrow` para etiquetas superiores en mayúscula.
- Mantener contraste suficiente y tamaños legibles.
- Centralizar tamaños y alturas en variables CSS.

## Layout

Reemplazar el layout actual por una estructura equivalente a `AppShell`:

- Sidebar fija de aproximadamente `17.5rem`.
- Barra superior sticky.
- Contenido principal con ancho máximo de `90rem`.
- Menú lateral responsive para móvil.
- Backdrop para cerrar el menú móvil.
- Menú de usuario con avatar, perfil y cierre de sesión.
- Indicador de conexión con la API.

Estructura objetivo:

```text
frontend/src/
  components/
  layouts/
    AppShell.tsx
  pages/
  features/
  styles/
```

## Estilos base

Crear o adaptar los siguientes archivos:

```text
styles/tokens.css
styles/reset.css
styles/typography.css
styles/base.css
styles/layout.css
styles/utilities.css
```

`base.css` debe importar los estilos globales y los estilos de componentes.

## Componentes reutilizables

Adoptar los patrones de la referencia para:

- Botones primarios, secundarios, de acento y peligro.
- Inputs, selects y textareas con estados hover, focus y error.
- Formularios en grid responsive.
- Tablas con scroll horizontal en dispositivos pequeños.
- Badges para estados.
- Alertas informativas, de advertencia y error.
- Diálogos de confirmación.
- Estados de carga y estados vacíos.

Clases principales:

```text
.button
.button--primary
.button--accent
.button--secondary
.button--danger
.field
.field__label
.field__control
.form-grid
.table-container
.data-table
.badge
.alert
.empty-state
```

## Dashboard

Aplicar el estilo de `dashboard.css` y `DashboardPage.tsx`:

- Tarjetas métricas.
- Paneles blancos sobre fondo gris claro.
- Barras de progreso.
- Indicadores circulares.
- Actividad reciente.
- Tablas desktop.
- Tarjetas equivalentes para móvil.

## Configuración

Usar pestañas horizontales para los catálogos:

```text
Área
Proceso
Máquina
Puestos
Actividad
Competencia
Competencia por puesto
Turno
Trabajadores
Supervisores
Evaluadores
Usuarios
Roles
Permisos
```

La pestaña activa debe utilizar borde inferior de color institucional y ser
desplazable horizontalmente en móviles.

## Módulos visuales

Aplicar estilos específicos para:

```text
auth.css
catalogs.css
evaluations.css
matrix.css
gaps.css
training.css
imports.css
workerDetail.css
positionActivities.css
settings.css
```

Módulos prioritarios:

1. Login.
2. Layout principal.
3. Dashboard.
4. Configuración y catálogos.
5. Trabajadores y detalle del trabajador.
6. Evaluación y checklist.
7. Matriz de competencias.
8. Consulta de brechas y capacitación.

## Reglas de implementación

- No mezclar los colores actuales con la identidad institucional.
- Mantener los endpoints y permisos existentes.
- Ocultar módulos según los permisos del usuario.
- Usar componentes reutilizables antes de crear estilos específicos.
- Mantener soporte para escritorio, tablet y móvil.
- Usar atributos ARIA y foco visible.
- Mantener estados de carga, error, vacío y éxito.
- No perder la información de historial al editar o desactivar registros.

## Orden de trabajo

1. Copiar y adaptar tokens, reset y tipografía.
2. Crear `AppShell` con sidebar y topbar.
3. Migrar login al estilo institucional.
4. Migrar botones, formularios, tablas y feedback.
5. Convertir Configuración en páginas independientes.
6. Aplicar estilos al módulo de trabajadores.
7. Aplicar estilos al checklist de evaluación.
8. Aplicar estilos a matriz, brechas y capacitación.
9. Revisar permisos y navegación dinámica.
10. Verificar responsive y accesibilidad.
11. Ejecutar lint y build de producción.

## Verificación

```powershell
npm run lint --prefix frontend
npm run build --prefix frontend
```

Validar manualmente:

- Sidebar en escritorio.
- Menú lateral en móvil.
- Tablas con scroll horizontal.
- Formularios en una y dos columnas.
- Estados de error y éxito.
- Navegación condicionada por permisos.
- Contraste y foco visible.
