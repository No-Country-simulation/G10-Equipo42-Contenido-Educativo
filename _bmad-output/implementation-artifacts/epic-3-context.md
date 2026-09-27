# Epic 3 Context: Interfaz Web Completa

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Proveer una interfaz web moderna servida por FastAPI como archivos estáticos (`app/static/`) que permita al usuario realizar el flujo completo sin herramientas externas: subir un documento (o seleccionar uno previo), configurar los tres parámetros de adaptación, lanzar la generación con feedback de progreso en tiempo real, visualizar el resultado renderizado según el formato pedagógico, y consultar un historial de generaciones anteriores desde una barra lateral. Cubre el requisito obligatorio del hackathon de interfaz interactiva (requisito 5).

## Stories

- Story 3.1: Upload de Documentos y Configuración de Parámetros
- Story 3.2: Generación con Feedback de Progreso y Visualización de Resultados
- Story 3.3: Historial de Generaciones

## Requirements & Constraints

- La interfaz es HTML/CSS/JS **estático** servido por FastAPI via `StaticFiles`. Sin SSR, sin framework JS pesado — renderización client-side pura.
- Los archivos estáticos se montan en `app/static/` y FastAPI los sirve en `/` o `/static/` (la URL raíz debe retornar la SPA).
- Los tres parámetros de adaptación son **obligatorios**: perfil, formato y nicho. No se puede lanzar generación sin completarlos. Validación en el cliente.
- `Perfil` tiene 4 opciones predefinidas (Principiante, Junior, Senior, Lider Tecnico/Arquitecto). `FormatoPedagogico` tiene 5 (Flashcards, Quiz Interactivo, Tutorial Paso a Paso, Resumen Ejecutivo, Guion de Clase). `Nicho` tiene 4 predefinidos (General, Fintech, Salud, E-commerce) + texto libre.
- La interfaz debe ser **ligera**: sólo sirve estáticos y consume la API existente. No agrega carga al servidor de 1GB RAM.
- Feedback de progreso via **polling** al endpoint `GET /api/v1/adaptar/{task_id}` — el campo `status` puede ser `pending`, `processing`, `completed` o `failed`.
- El historial consulta OCI Object Storage; no hay base de datos adicional. Si OCI está deshabilitado, el historial muestra estado vacío sin error.
- Diseño: interfaz moderna y profesional (dark mode, colores curados, tipografía web, micro-animaciones). El usuario debe poder usarla sin instrucciones.

## Technical Decisions

- **Montaje de estáticos:** FastAPI soporta `StaticFiles` de Starlette. Montar con `app.mount("/static", StaticFiles(directory="...", html=True))`. La ruta raíz `/` debe retornar `index.html` — esto se logra con `html=True` o con un endpoint GET que retorne `FileResponse`.
- **Historial desde OCI:** Requiere `list_objects` en `OCIStorageClient` (no implementado aún). El prefijo `"paquetes/"` da la lista de paquetes. Los metadatos (documento, perfil, formato, fecha) se extraen del nombre del objeto (`paquetes/{document_id}_{perfil}_{formato}_{timestamp}.json`).
- **Endpoint `GET /api/v1/historial`:** Definido en la arquitectura (sec. 7.1). Retorna lista de generaciones desde OCI. Si OCI deshabilitado, retorna lista vacía.
- **Descarga de paquete por ID:** Para cargar un paquete del historial, el JS llama a un endpoint que retorna el JSON del paquete — puede ser `GET /api/v1/historial/{objeto_id_encoded}` o reutilizar el task_store si el paquete aún está en memoria. Story 3.3 define el detalle de implementación.
- **Polling interval:** 2 segundos durante generación activa. Stop automático en `completed` o `failed`.
- **Regla de dependencia:** `app/static/` no importa nada del backend Python. La comunicación es exclusivamente vía `fetch()` a la API REST.

## UX & Interaction Patterns

- **Layout:** Barra lateral izquierda (historial) + área principal (upload, parámetros, generación, resultado).
- **Upload:** Zona drag-and-drop + click para seleccionar. Acepta PDF, .md, .txt. Muestra nombre del archivo seleccionado y feedback visual.
- **Parámetros:** Tres controles: selects para Perfil y Formato (opciones del enum), control mixto para Nicho (select + texto libre).
- **Lanzar generación:** Botón prominente, deshabilitado hasta que documento + 3 parámetros estén completos. Al presionar, envía `POST /api/v1/adaptar` como `multipart/form-data`.
- **Progreso:** Spinner/barra de progreso animada con mensajes descriptivos durante polling. Manejo de error con mensaje en español + botón "reintentar".
- **Resultado:** Renderizado específico por formato (Story 3.2). Story 3.1 sólo establece la estructura; Story 3.2 implementa los renderers.
- **Historial:** Lista en la barra lateral. Click en entrada carga el paquete y lo renderiza. Estado vacío con mensaje indicativo cuando no hay generaciones.

## Cross-Story Dependencies

- Story 3.1 establece la estructura base (HTML/CSS/JS, montaje en FastAPI, endpoint `/historial`). Stories 3.2 y 3.3 extienden sobre ella.
- Story 3.2 implementa los renderers de formato (Flashcards, Quiz, Tutorial, Resumen, Guion) y el ciclo completo de polling → visualización.
- Story 3.3 implementa la carga de paquetes desde OCI y la interacción del historial (depende de `list_objects` y `get_object` en OCI).
- Epic 2 (done): `StorageService` y `OCIStorageClient` ya existen. Story 3.1 extiende `OCIStorageClient` con `list_objects`; Story 3.3 necesita `get_object`.
