---
title: 'Story 3.2: Generación con Feedback de Progreso y Visualización de Resultados'
type: 'feature'
created: '2026-09-27'
baseline_commit: '3a1501d'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context:
  - _bmad-output/implementation-artifacts/epic-3-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problema:** El resultado de la generación se muestra como JSON crudo (`renderResultPlaceholder`), lo que hace la interfaz inutilizable para usuarios no técnicos y no cumple el requisito de visualización pedagógica del hackathon.

**Approach:** Reemplazar `showResult` / `renderResultPlaceholder` en `app.js` con cinco renderers específicos por formato (Flashcards, Quiz Interactivo, Tutorial Paso a Paso, Resumen Ejecutivo, Guión de Clase), y agregar en `style.css` los estilos visuales que cada renderer requiere. El Quiz Interactivo incluye interactividad client-side (selección de opción, validación de respuesta). No hay cambios en el backend.

## Boundaries & Constraints

**Always:**
- Puro client-side: sólo se modifican `app.js` y `style.css`. Sin cambios en Python, endpoints ni esquemas.
- Los renderers leen la estructura tal como la retorna el endpoint `GET /api/v1/adaptar/{task_id}`: `data.resultado.contenido_adaptado` (con `titulo`, `introduccion_contextualizada`, `items[]`) y `data.resultado.metadatos` / `data.resultado.evaluacion_calidad`.
- `escapeHtml()` en todo texto proveniente del servidor antes de inyectarlo en el DOM.
- Los IDs del DOM ya existentes no se modifican. Los nuevos elementos que agreguen los renderers no necesitan IDs a menos que sean interactivos.
- Quiz: el usuario selecciona una opción y recibe feedback visual inmediato (correcto/incorrecto + justificación). No hay envío al servidor; la respuesta correcta ya está en `items[i].respuesta_correcta`.
- Mantener compatibilidad con el CSS existente (variables, clases base). No eliminar reglas CSS existentes.

**Never:**
- No usar frameworks JS externos (React, Vue, etc.).
- No hacer llamadas adicionales a la API para obtener el resultado — ya está en `data.resultado`.
- No implementar carga de paquetes desde OCI (eso es Story 3.3).
- No modificar archivos Python, tests, ni configuración.

## I/O & Edge-Case Matrix

| Escenario | Input / Estado | Output / Comportamiento Esperado | Manejo de Error |
|-----------|---------------|----------------------------------|-----------------|
| Resultado Flashcards recibido | `contenido_adaptado.items` con `frente`, `dorso`, `pista_didactica` | Cards con cara frontal visible, click para revelar dorso | Si `items` vacío: mensaje "No se generaron flashcards" |
| Resultado Quiz recibido | `items` con `pregunta`, `opciones[]`, `respuesta_correcta`, `justificacion` | Preguntas con botones de opción; al seleccionar, resalta correcta/incorrecta + muestra justificación | Si `items` vacío: mensaje indicativo |
| Resultado Tutorial recibido | `items` con `paso`, `titulo`, `explicacion`, `ejemplo` | Lista numerada de pasos, ejemplo en bloque de código si existe | — |
| Resultado Resumen Ejecutivo recibido | `items` con `seccion`, `contenido`, `implicacion` | Cards por sección con título, cuerpo e implicación destacada | — |
| Resultado Guión de Clase recibido | `items` con `fase`, `contenido`, `duracion_minutos`, `notas_formador` | Timeline visual con fase, duración y contenido; notas del formador si no está vacío | Si `notas_formador` vacío: ocultar sección |
| Formato desconocido o `resultado` vacío | `formato` no reconocido o `contenido_adaptado` ausente | Fallback: mostrar JSON en `<pre>` con `renderResultPlaceholder` | — |
| Score de fidelidad ausente | `evaluacion_calidad` nulo o sin `anclaje_fuente_score` | Ocultar el badge de score (comportamiento actual ya correcto) | — |

</frozen-after-approval>

## Code Map

- `nuevamente/app/static/app.js` — MODIFICAR. Reemplazar `showResult()` y `renderResultPlaceholder()` con dispatcher + 5 renderers: `renderFlashcards()`, `renderQuiz()`, `renderTutorial()`, `renderResumenEjecutivo()`, `renderGuionClase()`. La función `showResult(data)` pasa a ser un dispatcher por `resultado.formato`. El estado de interactividad del Quiz vive en el DOM (clases CSS), no en `appState`.
- `nuevamente/app/static/style.css` — MODIFICAR. Agregar estilos para los renderers: `.flashcard`, `.flashcard-front`, `.flashcard-back`, `.flashcard.flipped`; `.quiz-question`, `.quiz-option`, `.quiz-option.correct`, `.quiz-option.incorrect`, `.quiz-justificacion`; `.tutorial-step`, `.tutorial-step-number`, `.tutorial-ejemplo`; `.resumen-card`, `.resumen-implicacion`; `.guion-fase`, `.guion-duracion`, `.guion-notas`.
- `nuevamente/core/schemas.py` — SOLO LECTURA. Confirmar estructura: `contenido_adaptado.titulo`, `contenido_adaptado.introduccion_contextualizada`, `contenido_adaptado.items[]` con campos por formato (líneas 80–174).
- `nuevamente/app/static/index.html` — NO MODIFICAR. El `<div id="result-content">` ya existe (línea 215) y es donde los renderers inyectan HTML.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/app/static/app.js` — REFACTORIZAR `showResult(data)`: extraer `resultado = data.resultado || {}`, `formato = resultado.formato || resultado.contenido_adaptado?.formato_generado || selectFormato.value`, despachar a renderer por `formato`. Si formato no coincide, usar `renderResultPlaceholder(resultado)`.
- [x] `nuevamente/app/static/app.js` — IMPLEMENTAR `renderFlashcards(contenido)`: genera HTML con un `<div class="flashcard">` por item de `contenido.items`. Cada card tiene `<div class="flashcard-front">frente</div>` y `<div class="flashcard-back"><p>dorso</p><p class="pista">pista_didactica</p></div>`. Al hacer click sobre la card, toggle de clase `flipped` para revelar el dorso. Incluir intro (`contenido.titulo`, `contenido.introduccion_contextualizada`) y conteo de tarjetas.
- [x] `nuevamente/app/static/app.js` — IMPLEMENTAR `renderQuiz(contenido)`: genera HTML con una `<div class="quiz-question">` por item. Cada pregunta tiene `<div class="quiz-options">` con un botón por opción. Al click: marcar la opción elegida como `correct` o `incorrect`, marcar la correcta como `correct`, mostrar `<div class="quiz-justificacion">`, deshabilitar todos los botones de esa pregunta. Incluir intro y contador de preguntas.
- [x] `nuevamente/app/static/app.js` — IMPLEMENTAR `renderTutorial(contenido)`: genera HTML con un `<div class="tutorial-step">` por item. Cada paso muestra número de paso, título, explicación y (si `ejemplo` no está vacío) un `<pre class="tutorial-ejemplo">` con el ejemplo. Incluir intro.
- [x] `nuevamente/app/static/app.js` — IMPLEMENTAR `renderResumenEjecutivo(contenido)`: genera HTML con un `<div class="resumen-card">` por item. Cada card muestra `seccion` como título, `contenido` como cuerpo, y `implicacion` destacada con label "Implicación:". Incluir intro.
- [x] `nuevamente/app/static/app.js` — IMPLEMENTAR `renderGuionClase(contenido)`: genera HTML con un `<div class="guion-fase">` por item. Cada fase muestra `fase` como título con badge de `duracion_minutos` min, luego `contenido`, y (si `notas_formador` no está vacío) `<div class="guion-notas">` con el texto. Incluir intro.
- [x] `nuevamente/app/static/style.css` — AGREGAR estilos para los cinco renderers. Ver Design Notes para referencia visual.

**Acceptance Criteria:**
- Given una generación completada en formato Flashcards, when el polling recibe `status: completed`, then el panel de resultado muestra cards con frente visible; al hacer click en una card se revela el dorso y la pista didáctica.
- Given una generación completada en formato Quiz Interactivo, when el usuario selecciona una opción, then esa opción se marca en rojo o verde según sea incorrecta o correcta, la opción correcta siempre se marca en verde, y aparece la justificación; los botones de esa pregunta quedan deshabilitados.
- Given una generación completada en formato Tutorial Paso a Paso, when se muestra el resultado, then aparece una lista numerada de pasos con número, título, explicación, y (si existe) el ejemplo en bloque de código.
- Given una generación completada en formato Resumen Ejecutivo, when se muestra el resultado, then aparecen cards con la sección, el contenido y la implicación destacada.
- Given una generación completada en formato Guión de Clase, when se muestra el resultado, then aparecen las fases con badge de duración; si hay notas_formador, se muestran.
- Given cualquier formato, when se recibe el resultado, then el título `contenido_adaptado.titulo` y la `introduccion_contextualizada` se muestran antes de los items.
- Given el score de fidelidad presente en `evaluacion_calidad.anclaje_fuente_score`, when se muestra el resultado, then el badge de score muestra el porcentaje correctamente.
- Given formato desconocido o `resultado` vacío, when se recibe el resultado, then se muestra el fallback JSON en `<pre>` sin error JavaScript.

## Implementation Notes

- `app.js`: `showResult(data)` refactorizada con dispatcher `RENDERERS`. El score se lee ahora desde `resultado.evaluacion_calidad.anclaje_fuente_score` (con fallback a `resultado.anclaje_fuente_score` para compatibilidad).
- `app.js`: `renderFlashcards()` genera grid CSS con flip 3D via `.flashcard.flipped`. Interactividad (click + teclado) via `initQuizInteractivity()` registrado en `DOMContentLoaded`.
- `app.js`: `renderQuiz()` genera preguntas con botones por opción. La función `initQuizInteractivity()` usa event delegation sobre `#result-content` para manejar tanto quiz como flashcard clicks en un solo listener.
- `app.js`: `renderTutorial()`, `renderResumenEjecutivo()`, `renderGuionClase()` siguen el mismo patrón: intro + items con manejo de campos vacíos.
- `app.js`: Corrección del bug preexistente de Story 3.1: llave `}` faltante en `updateGenerateButton()`.
- `style.css`: +435 líneas. Estilos para: `.renderer-intro/.renderer-titulo/.renderer-meta/.renderer-empty` (comunes), `.flashcards-grid/.flashcard-inner` (flip 3D), `.quiz-option.correct/.incorrect/.quiz-justificacion`, `.tutorial-step-number` (círculo gradiente), `.resumen-implicacion`, `.guion-duracion/.guion-notas`.
- Verificación: `uv run python -c "from nuevamente.app.main import app; print('app ok')"` → `app ok` ✓

## Spec Change Log

## Review Triage Log

- Finding BH-1: XSS en innerHTML — verdict: `false` — Todo el texto del servidor pasa por `escapeHtml()` antes de inyectarse. Verificado en líneas 80-120 del diff y todos los renderers.
- Finding BH-2: Falta keyboard/ARIA en flashcards — verdict: `false` — Las flashcards tienen `tabindex="0"`, `role="button"`, `aria-label`, y el handler `keydown` Enter/Space está en `initQuizInteractivity()` (diff líneas 384-393).
- Finding BH-3: Defensive schema validation — verdict: `false` — Todos los renderers usan `|| []` y `|| ''`; campos opcionales protegidos con ternario. Backend valida con Pydantic.
- Finding BH-4: ARIA live para feedback de Quiz — verdict: `low` — Real pero cosmético para MVP. La spec no requiere `aria-live`. Route: defer.
- Finding BH-5: Touch events para flip — verdict: `false` — El flip se activa via listener `click` (no hover CSS), funciona en touch.
- Finding BH-6: Hardcoded colors en CSS — verdict: `false` — Los estilos usan variables CSS del sistema de diseño (`var(--color-success)`, `var(--color-error)`, `var(--accent-from)`, etc.).
- Finding BH-7: Listener accumulation — verdict: `false` — `initQuizInteractivity()` se llama una sola vez. Los listeners van sobre `resultContent` (elemento estático), event delegation sobrevive los reemplazos de innerHTML.
- Finding BH-8: Missing plain-text export — verdict: `low` — Out of scope de esta historia. Route: defer.
- Finding EC-1: `respuesta_correcta` null en data-correct — verdict: `false` — Pydantic requiere el campo como `str` no-nullable; no puede ser null en producción.
- Finding VG-1: No hay tests automatizados — verdict: `low` — Patrón pre-existente del proyecto (verificación manual establecida). Route: defer.

## Design Notes

**Flashcards — flip visual con CSS 3D:**
```
.flashcards-grid  → display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px
.flashcard        → perspective: 800px; height: 200px; cursor: pointer
.flashcard-inner  → position: relative; width/height: 100%; transform-style: preserve-3d; transition: 0.5s
.flashcard.flipped .flashcard-inner → transform: rotateY(180deg)
.flashcard-front, .flashcard-back → position: absolute; backface-visibility: hidden; display: flex; align-items: center; justify-content: center
.flashcard-back   → transform: rotateY(180deg)
```

**Quiz — estado por pregunta (DOM-only):**
El estado de respuesta vive únicamente en clases CSS sobre los botones. No se usa `appState`. Cada pregunta tiene un atributo `data-answered="false"` para evitar re-responder. El contador de respondidas/total se actualiza incrementalmente en el DOM.

**Dispatcher en `showResult`:**
```js
const RENDERERS = {
  'Flashcards': renderFlashcards,
  'Quiz Interactivo': renderQuiz,
  'Tutorial Paso a Paso': renderTutorial,
  'Resumen Ejecutivo': renderResumenEjecutivo,
  'Guion de Clase': renderGuionClase,
};
const contenido = resultado.contenido_adaptado || {};
const renderer = RENDERERS[formato];
resultContent.innerHTML = renderer ? renderer(contenido) : renderResultPlaceholder(resultado);
```

**Nota sobre `formato`:** Verificar qué campo contiene el formato en el resultado real. El endpoint retorna el paquete completo serializado; lo más probable es que `resultado.metadatos.formato_generado` sea la fuente canónica. Usar `selectFormato.value` como fallback final.

## Verification

**Commands:**
- `uv run python -c "from nuevamente.app.main import app; print('app ok')"` — expected: `app ok`

**Manual checks:**
- Iniciar con `uv run uvicorn nuevamente.app.main:app --reload` y abrir `http://localhost:8000`.
- Generar con formato Flashcards: cards aparecen, flip funciona al hacer click.
- Generar con formato Quiz: selección de opción da feedback correcto/incorrecto, botones quedan deshabilitados.
- Generar con formato Tutorial: lista de pasos numerados con ejemplos en bloque.
- Generar con formato Resumen Ejecutivo: cards con sección, contenido e implicación.
- Generar con formato Guión de Clase: fases con badge de duración y notas del formador.
