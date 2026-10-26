---
title: 'Fix Flashcard Flip Visibility, Layout & Adaptive Text Density'
type: 'bugfix'
created: '2026-10-23'
status: 'done'
baseline_commit: 'c7f1f800808bd50231a7842552c1eb7f0be6fe09'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** 
1. Al dar vuelta una flashcard en la interfaz web, el texto del frente continúa visible a través del dorso en efecto espejo (invertido), superponiéndose y tapando la respuesta pedagógica y pista didáctica. Esto se debe a la ausencia de una transformación 3D explícita en `.flashcard-front` dentro del contexto `preserve-3d` (lo que impide a navegadores Blink/WebKit ejecutar el descarte de cara posterior vía `backface-visibility: hidden`) y a la falta de un fondo base opaco bajo el degradado del dorso.
2. La grilla estrecha multicolumna comprime el contenido horizontalmente (~280px), provocando que rutas de archivo continuas o cadenas técnicas sin espacios (ej. rutas de registro de Windows) desborden y se recorten por los lados.
3. El contenido extenso del dorso (explicación pedagógica + pista didáctica) se corta verticalmente en los extremos si la tarjeta tiene dimensiones fijas rígidas sin adaptación tipográfica.

**Approach:** 
1. Añadir `transform: rotateY(0deg)` en `.flashcard-front` para forzar la inicialización de la matriz tridimensional requerida para el descarte de caras, dotar a ambas caras de una base sólida opaca (`background-color: var(--bg-secondary)`) antes de los degradados estéticos para anular cualquier sangrado por transparencia.
2. Reestructurar el layout de flashcards a una sola columna vertical centrada (`max-width: 680px`), manteniendo dimensiones estándar y uniformes para todas las tarjetas (altura estándar de 230px).
3. Implementar adaptación automática de densidad tipográfica (texto estándar a 13.5px, `.text-compact` a 12px para >180 caracteres y `.text-dense` a 11px para >300 caracteres) tanto preventiva en `renderFlashcards` como reactiva en `adjustFlashcardTypography()`.
4. Blindar el desbordamiento horizontal con `overflow-wrap: anywhere; word-break: break-word;` y mantener `overflow-y: auto` como red de seguridad con scrollbar estética.

## Boundaries & Constraints

**Always:**
- Preservar la fluidez y duración de la animación de giro 3D (0.5s con cubic-bezier).
- Mantener la accesibilidad mediante teclado (teclas Enter y Espacio) y atributos ARIA ya existentes.
- Mantener simetría visual: todas las tarjetas deben compartir la misma altura y ancho estándar.
- Garantizar que todo el texto generado por la IA (respuesta y pista didáctica) sea 100% legible y accesible.

**Never:**
- No alterar los contratos de datos en `nuevamente.core.schemas`.
- No eliminar el soporte para `focus-visible` o pistas didácticas.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Estado inicial | Tarjeta no volteada (`.flashcard` sin clase `.flipped`) | Se muestra únicamente la cara frontal con el término/pregunta centrada en tarjeta de ancho 680px | N/A |
| Voltear tarjeta | Clic o Enter/Espacio (`.flashcard.flipped`) | La tarjeta rota 180°; la cara frontal se oculta al 100% y se muestra de forma nítida la cara dorsal | N/A |
| Texto corto/estándar | Respuesta breve (hasta 180 caracteres) | Se muestra con tamaño estándar (13.5px / 15px) y espaciado holgado | N/A |
| Texto técnico medio | Respuesta explicativa (181 a 300 caracteres) | Se adapta automáticamente con clase `.text-compact` (12px) entrando en el alto estándar | N/A |
| Texto técnico extenso con rutas | Rutas de registro, comandos o explicaciones >300 caracteres | Se adapta con clase `.text-dense` (11px) y `overflow-wrap: anywhere`, evitando cortes horizontales y verticales | `overflow-y: auto` de respaldo |
| Re-voltear | Segundo clic o tecla Enter/Espacio | La tarjeta vuelve al frente; el dorso se oculta completamente | N/A |

</frozen-after-approval>

## Code Map

- `nuevamente/app/static/style.css` -- Reglas CSS de `.flashcards-grid` (1 columna 680px), `.flashcard` (altura estándar 230px), clases `.text-compact` y `.text-dense`, y propiedades de ruptura de palabras.
- `nuevamente/app/static/app.js` -- `renderFlashcards` con inyección de clases de densidad preventiva y función `adjustFlashcardTypography()` post-render.

## Tasks & Acceptance

**Execution:**
- [x] `nuevamente/app/static/style.css` -- Aplicar `transform: rotateY(0deg)`, base de fondo opaca y propiedades de contención a `.flashcard-front` y `.flashcard-back`.
- [x] `nuevamente/app/static/style.css` -- Unificar a 1 sola columna vertical (`max-width: 680px`), altura uniforme estándar (230px) y reglas de densidad `.text-compact` y `.text-dense`.
- [x] `nuevamente/app/static/app.js` -- Asignar clases de densidad según longitud de texto en `renderFlashcards` y conectar `adjustFlashcardTypography()` en `showResult()`.
- [x] Validación visual de usuario en interfaz web.
- [x] Pruebas automatizadas -- Ejecutar `uv run pytest` para verificar la estabilidad de todo el sistema.

**Acceptance Criteria:**
- Given una flashcard renderizada en la interfaz, when el usuario hace clic o presiona Enter/Espacio para voltearla, then la tarjeta gira 180° mostrando el dorso sin ningún rastro visual ni texto invertido proveniente del frente.
- Given una tarjeta volteada con contenido extenso y pista didáctica, when se visualiza el dorso, then todo el texto es visible en su totalidad sin recortes superiores, inferiores ni laterales.
- Given un listado de múltiples tarjetas, then todas presentan idéntico tamaño estándar y alineación vertical uniforme.

## Implementation Notes

- Modificado `nuevamente/app/static/style.css`:
  - Se configuró `.flashcards-grid` en una sola columna vertical (`display: flex; flex-direction: column; max-width: 680px; margin: 0 auto;`).
  - Se fijó una altura estándar y uniforme de `230px` para todas las `.flashcard`.
  - Se añadieron variantes tipográficas adaptativas: `.text-compact` (12px, interlineado 1.42) y `.text-dense` (11px, interlineado 1.34).
  - Se aplicó `overflow-wrap: anywhere; word-break: break-word;` en todas las capas de texto.
  - Se mantuvo la rotación 3D pura con `transform: rotateY(0deg)` y base opaca `var(--bg-secondary)`.
- Modificado `nuevamente/app/static/app.js`:
  - `renderFlashcards()` calcula los caracteres totales e inyecta la clase de densidad preventiva correspondiente.
  - Se implementó `adjustFlashcardTypography()` para comprobar desbordamientos residuales post-renderizado vía `requestAnimationFrame`.
- Verificación ejecutada: `uv run pytest` pasando al 100% (18/18 pruebas superadas).

## Spec Change Log

- 2026-10-23: Rediseño a columna única vertical de 680px con altura uniforme estándar de 230px y auto-ajuste de tamaño de texto para explicaciones largas.

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest` -- expected: 100% de la suite de pruebas pasando (18/18 passed).
