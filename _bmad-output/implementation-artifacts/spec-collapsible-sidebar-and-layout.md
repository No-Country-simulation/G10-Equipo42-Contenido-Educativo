---
title: 'Collapsible Sidebar Rail, Layout Clean-up, Mobile Drawer & AI-Titled History'
type: 'feature'
created: '2026-10-24'
status: 'ready-for-dev'
baseline_commit: 'f949231b3b80e0b5d9b32a10dcab46c7fda99881'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** 
1. La barra superior `.app-header` consume espacio vertical valioso y sobrecarga la pantalla con un banner permanente.
2. En pantallas de escritorio, la barra lateral de historial es estática y rígida (280px fijos), sin posibilidad de colapsarse para maximizar el área de estudio del contenido pedagógico.
3. **Comportamiento defectuoso en móviles/pantallas estrechas:** La media query `@media (max-width: 600px)` actual convierte el sidebar en una barra horizontal superior fija (`max-height: 200px`) con scroll horizontal que ocupa más de media pantalla en celulares, bloquea la vista del contenido pedagógico y no se puede ocultar.
4. El panel de configuración y carga de documentos (`#input-panel`) permanece visible en todo momento, incluso durante la generación o al explorar paquetes de estudio terminados, saturando la vista.
5. Las tarjetas del historial carecen de un título distintivo del contenido generado: sólo muestran formato y perfil, haciendo que múltiples adaptaciones del mismo tipo resulten visualmente indistinguibles entre sí.

**Approach:** 
1. **Rediseño del Layout:** Eliminar la barra horizontal `.app-header` y trasladar el branding `🧠 NuevaMente` a la cabecera de la barra lateral.
2. **Barra Lateral Colapsable en Escritorio (Desktop):**
   - **Estado expandido por defecto:** Siempre que se carga o refresca el sitio, la barra se inicia abierta (~260px). En su cabecera incluye el logo a la izquierda, y a la derecha los botones de búsqueda (🔍) y colapso (◨). Debajo incorpora el botón destacado `[✏️ Nuevo]`, el buscador en vivo y la lista con scrollbar.
   - **Riel colapsado (~52px):** Se contrae con una animación suave mostrando 3 botones alineados verticalmente:
     - **Botón superior (Cerebro / Toggle):** En reposo muestra el cerebro `🧠`. Al posar el cursor (hover), el cerebro se transforma con una microanimación en el ícono `◨` de abrir barra lateral, con tooltip *"Mostrar/ocultar barra lateral"*. Al hacer clic, expande la barra.
     - **Segundo botón (Nuevo):** Ícono de lápiz `✏️` con tooltip *"Nuevo"*. Al hacer clic, muestra el formulario inicial y oculta el material abierto.
     - **Tercer botón (Buscar):** Ícono de lupa `🔍` con tooltip *"Buscar"*. Al hacer clic, expande la barra y enfoca automáticamente el campo de búsqueda.
3. **Experiencia Móvil Moderna (Drawer / Off-Canvas):**
   - Eliminar por completo el layout de franja horizontal superior de `max-width: 600px`.
   - En pantallas móviles (`max-width: 768px`):
     - El sidebar funciona como un **cajón deslizante vertical completo (drawer off-canvas)** con `position: fixed; inset: 0 auto 0 0; width: 85%; max-width: 320px; z-index: 100;`.
     - Por defecto en móvil o al colapsar: se desliza fuera de pantalla (`transform: translateX(-100%)`).
     - En el área principal móvil se ubica un botón superior discreto (ícono de toggle/cerebro) para abrir el historial.
     - Al abrirse: despliega un fondo oscuro de superposición (backdrop overlay) para enfocar el menú.
     - Al seleccionar un ítem del historial, hacer clic en "Nuevo", pulsar el botón de cerrar o tocar el backdrop: el cajón se cierra automáticamente liberando el 100% de la pantalla para el estudio.
4. **Flujo de Pantalla Limpio (Formulario vs. Contenido):**
   - Al hacer clic en "Generar" o al seleccionar una generación del historial, se oculta el `#input-panel`. La pantalla queda dedicada exclusivamente al progreso o al paquete educativo generado.
   - Al hacer clic en "Nuevo" (desde el sidebar, el riel o el drawer móvil), se oculta el resultado o progreso abierto y se vuelve a mostrar únicamente el `#input-panel` limpio y listo para una nueva carga.
5. **Títulos del Historial Generados por IA:**
   - Extraer y persistir el campo `titulo` del contenido adaptado generado por la IA (ej. *"Dominando las Expresiones Regulares en Python"*).
   - El ítem del historial muestra como elemento jerárquico principal dicho título en negrita, acompañado por badges de formato y perfil, más la fecha.
   - Resiliencia OCI: si OCI está desconectado o en fallo de red, se mantiene la semántica *best-effort* sin lanzar errores no controlados.

## Boundaries & Constraints

**Always:**
- La barra lateral **siempre** debe iniciar en estado expandido al cargar la página en desktop (sin persistencia en `localStorage`). En móviles inicia cerrada para no tapar la pantalla inicial.
- En móvil, el sidebar nunca debe dividirse horizontalmente ni recortar la altura de lectura: debe cubrir verticalmente en overlay y cerrarse al interactuar.
- El botón "Nuevo" debe forzosamente ocultar `#result-panel`, `#progress-panel` y `#error-panel`, dejando a la vista únicamente `#input-panel`.
- Al generar o seleccionar del historial, `#input-panel` debe ocultarse de inmediato.
- Transiciones CSS suaves (`transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), width 0.25s ease`).
- Soportar navegación por teclado y accesibilidad ARIA (`aria-expanded`, `aria-label`, `title`).
- Escapar todo texto dinámico con `escapeHtml` y `escapeAttr` para mitigar riesgos XSS.
- Mantener la resiliencia *best-effort* del backend: si OCI no está configurado o falla la conexión, la app responde con lista vacía y no interrumpe el flujo del usuario.

**Never:**
- No volver a usar la franja horizontal superior en móviles (`flex-direction: column` con `max-height: 200px` en `.sidebar`).
- No guardar el estado colapsado en `localStorage` (debe resetearse a abierto en desktop en cada carga).
- No modificar los contratos de esquemas Pydantic en `nuevamente.core.schemas`.
- No alterar los renderers pedagógicos de Story 3.2 (Flashcards, Quiz, Tutorial, Resumen, Guión).

## I/O & Edge-Case Matrix

| Escenario | Entrada / Estado | Salida / Comportamiento Esperado | Manejo de Excepción / Fallback |
| :--- | :--- | :--- | :--- |
| Carga inicial en escritorio (>=769px) | Carga o recarga (F5) en desktop | Sidebar expandido (~260px) mostrando logo, botones (🔍, ◨), botón `[✏️ Nuevo]` y lista de historial. `#input-panel` visible. | Siempre abierto por defecto. |
| Carga inicial en móvil (<=768px) | Carga en pantalla móvil | Pantalla limpia al 100% con botón superior de apertura de menú. Sidebar cerrado off-canvas (`translateX(-100%)`). | No ocupa espacio vertical del viewport. |
| Apertura en móvil | Clic en botón toggle en móvil | Sidebar se desliza verticalmente ocupando 85% del ancho sobre un backdrop semitransparente. | Al pulsar fuera o tocar cerrar, se contrae suavemente. |
| Clic en item en móvil | Selección de paquete desde historial móvil | Se oculta el `#input-panel`, se cierra automáticamente el drawer móvil y se visualiza el paquete en el 100% de la pantalla. | Animación fluida sin parpadeos. |
| Colapsar sidebar en desktop | Clic en botón `◨` en desktop | Sidebar se contrae a riel de 52px con 3 botones: Cerebro, Lápiz y Lupa. Área principal expande su ancho. | Animación fluida sin desborde horizontal. |
| Hover sobre el cerebro en riel | Cursor sobre el botón del cerebro en riel | El cerebro desaparece y se muestra el ícono `◨` con tooltip *"Mostrar/ocultar barra lateral"*. | Al quitar el cursor vuelve a mostrarse el cerebro. |
| Clic en cerebro en riel | Clic en el botón superior del riel | Sidebar se expande nuevamente a 260px. | Atributo `aria-expanded="true"`. |
| Clic en "Nuevo" (riel, sidebar o móvil) | Clic en `[✏️ Nuevo]` | `#result-panel`, `#progress-panel` y `#error-panel` se ocultan. `#input-panel` se hace visible y se limpia el formulario. Se cierra el drawer móvil si estaba abierto. | Si el usuario ya estaba en el form inicial, solo limpia los inputs. |
| Clic en "Buscar" desde riel | Clic en botón 🔍 del riel | Sidebar se expande automáticamente y el `input` de búsqueda recibe foco con el cursor listo para escribir. | Si ya estaba abierto, solo hace toggle/focus del input de búsqueda. |
| Búsqueda de historial en vivo | Usuario tipea término en el buscador | La lista filtra en tiempo real comparando contra `titulo`, `formato` y `perfil`. | Si no hay coincidencias, muestra mensaje sutil *"Sin coincidencias"*. |
| Clic en "Generar" | Formulario válido enviado a `/adaptar` | `#input-panel` se oculta inmediatamente. Aparece `#progress-panel` en el área principal. | Si la validación falla, `#input-panel` permanece visible con los errores marcados. |
| Carga de ítem desde historial | Clic en una tarjeta del historial | `#input-panel` se oculta. Se muestra indicador de carga y luego `#result-panel` con el contenido del paquete. | En caso de error de red, muestra `#error-panel` con opción de reintentar. |
| Ítem sin título explícito (legado/fallback) | Paquete en OCI sin campo `titulo` en metadatos | Se muestra el nombre del `formato` o una descripción pedagógica por defecto como título de la tarjeta. | Sin campos en blanco ni errores en consola. |

</frozen-after-approval>

## Code Map

- `nuevamente/app/static/index.html`
  - Eliminar bloque `<header class="app-header">...</header>`.
  - Reestructurar `<aside class="sidebar">`:
    - Incorporar el riel (`.sidebar-rail`) con los 3 botones: toggle con swap cerebro/◨, botón nuevo ✏️ y botón buscar 🔍.
    - Incorporar la cabecera expandida (`.sidebar-header-expanded`) con logo `🧠 NuevaMente`, botón lupa 🔍 y botón colapsar ◨.
    - Añadir el botón principal `[✏️ Nuevo]` (`#btn-sidebar-new`).
    - Añadir el contenedor del input de búsqueda interactivo (`#sidebar-search-container`).
  - Añadir botón de toggle flotante móvil (`#btn-mobile-sidebar-toggle`) y overlay de backdrop (`#sidebar-backdrop`).
  - Asegurar que `#input-panel` admita la clase de ocultamiento `.hidden-panel`.

- `nuevamente/app/static/style.css`
  - Reglas de layout flex y transiciones para `.sidebar` y `.sidebar.collapsed` (`width: 52px`) en desktop.
  - Reglas de visibilidad para riel vs. panel expandido.
  - Implementación del efecto hover swap en el botón superior del riel:
    - `.rail-btn-toggle .icon-toggle { display: none; }`
    - `.rail-btn-toggle:hover .icon-brain { display: none; }`
    - `.rail-btn-toggle:hover .icon-toggle { display: inline-flex; }`
  - **Reescritura completa de media queries responsive:**
    - Eliminar `.app-layout { flex-direction: column; }` y la franja horizontal de 200px.
    - En `<= 768px`, convertir `.sidebar` en drawer off-canvas (`position: fixed; z-index: 100; transform: translateX(-100%); transition: transform 0.3s;`).
    - Clase `.sidebar.mobile-open` (`transform: translateX(0);`).
    - Estilos para backdrop oscuro `#sidebar-backdrop`.
    - Estilos para botón móvil `#btn-mobile-sidebar-toggle`.
  - Estilos del botón `[✏️ Nuevo]` (diseño tipo píldora moderna con padding holgado, borde sutil y estado hover).
  - Estilos para la barra de búsqueda y las nuevas tarjetas de historial con título destacado de IA (`.hist-item-title`), badges compactos de formato/perfil y fecha legible.
  - Reglas para `.input-panel.hidden-panel` (`display: none;`).

- `nuevamente/app/static/app.js`
  - Inicializar controladores de estado para la barra lateral tanto en desktop como en móvil:
    - Funciones `collapseSidebar()`, `expandSidebar()`, `toggleSidebar()`, `openMobileSidebar()`, `closeMobileSidebar()`.
    - Garantizar que al cargar el DOM en desktop inicie siempre expandido, y en móvil cerrado.
  - Implementar `handleNew()`:
    - Oculta resultado, progreso y errores (`hideResult()`, `hideProgress()`, `hideErrorPanel()`).
    - Remueve `.hidden-panel` de `#input-panel`.
    - Resetea el formulario y deselecciona los ítems del historial.
    - Cierra el menú móvil si estaba abierto.
  - Modificar `handleGenerate()` y `loadPaqueteFromHistorial()`:
    - Ocultar `#input-panel` añadiendo `.hidden-panel`.
    - Cerrar el menú móvil tras seleccionar un ítem del historial.
  - Implementar lógica del buscador de historial:
    - Filtro instantáneo sobre la colección de generaciones en memoria.
  - Actualizar `renderHistorial(generaciones)`:
    - Renderizar cada ítem con el campo `titulo` generado por la IA en primer plano, seguido de badges de perfil y formato.

- `nuevamente/services/storage.py` & `nuevamente/app/routers/adaptar.py`
  - Al generar el paquete y persistirlo en OCI:
    - Asociar el campo `titulo` del contenido generado (de `package_dict["contenido_adaptado"]["titulo"]`).
    - En `list_paquetes()`, incluir `titulo` en el diccionario de retorno de cada generación (mediante slug en el nombre del objeto o extracción directa).
    - Preservar el comportamiento *best-effort* si OCI no se encuentra accesible.

## Tasks & Acceptance

**Execution:**
- [ ] `nuevamente/app/static/index.html` -- Remover header superior, agregar backdrop/botón móvil y actualizar estructura del sidebar (riel colapsable, botones de acción, botón Nuevo y buscador).
- [ ] `nuevamente/app/static/style.css` -- Crear estilos para riel, hover swap del cerebro a `◨`, botón Nuevo, buscador, tarjetas con título de IA, transiciones y drawer off-canvas móvil (eliminando la franja horizontal fija).
- [ ] `nuevamente/app/static/app.js` -- Implementar lógica de toggle (desktop + drawer móvil), botón Nuevo, buscador en vivo, ocultamiento de formulario al generar y renderizado de títulos de IA.
- [ ] `nuevamente/services/storage.py` y `nuevamente/app/routers/adaptar.py` -- Asegurar que `/api/v1/historial` proporcione el campo `titulo` de cada paquete de forma resiliente.

**Verification:**
1. Cargar el sitio en navegador desktop: la barra debe iniciar expandida mostrando el logo `🧠 NuevaMente`. No debe existir la barra superior horizontal anterior.
2. Hacer clic en el botón de colapso en desktop: la barra debe contraerse suavemente al riel de ~52px con los 3 botones (cerebro, lápiz, lupa).
3. Posar el cursor sobre el cerebro en el riel: debe transformarse fluidamente en el ícono `◨` con tooltip *"Mostrar/ocultar barra lateral"*. Al hacer clic, debe expandir la barra.
4. Con la barra colapsada, hacer clic en la lupa: debe expandir la barra y colocar el foco en el input de búsqueda.
5. Probar vista móvil (< 768px): el sidebar NO debe aparecer como una barra horizontal arriba ocupando media pantalla. Debe estar oculto y abrirse como drawer lateral sobre un backdrop al pulsar el botón de menú.
6. Al hacer clic en un ítem o botón en móvil: el drawer debe cerrarse automáticamente dejando libre toda la pantalla.
7. Escribir en el buscador: el historial debe filtrarse de inmediato por título, formato o perfil.
8. Subir un archivo y pulsar "Generar": el formulario de carga debe desaparecer de inmediato, quedando visible únicamente el progreso y posteriormente el resultado pedagógico.
9. Pulsar el botón "Nuevo" (desde el riel o desde la barra expandida): el contenido de estudio actual debe desaparecer y el formulario `#input-panel` debe volver a aparecer limpio y listo.
10. Los ítems del historial deben presentar el título descriptivo generado por la IA de forma clara y diferenciable.
11. Ejecutar suite de pruebas (`uv run pytest tests/`) para verificar que no haya regresiones en el almacenamiento ni endpoints.
