/**
 * NuevaMente — Lógica de la Interfaz Web
 *
 * Módulo principal client-side. Maneja:
 * - Drag-and-drop y selección de archivo
 * - Validación de formulario (tipo de archivo, parámetros obligatorios)
 * - Envío de POST /api/v1/adaptar como multipart/form-data
 * - Polling de GET /api/v1/adaptar/{task_id} para estado
 * - Carga y renderizado del historial desde GET /api/v1/historial
 *
 * Story 3.2 extenderá este archivo con los renderers de formato pedagógico.
 */

'use strict';

// ---------------------------------------------------------------------------
// Constantes
// ---------------------------------------------------------------------------

const API_BASE = '/api/v1';
const POLL_INTERVAL_MS = 2000;
const ACCEPTED_EXTENSIONS = ['.pdf', '.md', '.txt'];

// Mensajes de progreso según el estado de la tarea
const PROGRESS_MESSAGES = {
  pending: 'Iniciando pipeline de adaptación...',
  processing: 'Procesando documento y generando contenido educativo...',
};

// ---------------------------------------------------------------------------
// Estado de la aplicación
// ---------------------------------------------------------------------------

/** @type {{ file: File|null, pollInterval: number|null, currentTaskId: string|null, submitAttempted: boolean }} */
const appState = {
  file: null,
  pollInterval: null,
  currentTaskId: null,
  submitAttempted: false, // true tras el primer intento de generar; habilita feedback de error en selects
};

// ---------------------------------------------------------------------------
// Referencias DOM (inicializadas en DOMContentLoaded)
// ---------------------------------------------------------------------------

let uploadZone, fileInput, fileInfoEl, fileInfoName, btnClearFile;
let fileErrorEl, fileErrorText;
let selectPerfil, selectFormato, selectNicho, inputNichoCustom;
let btnGenerate, progressPanel, progressMessage;
let errorPanel, errorMessage, btnRetry;
let resultPanel, resultFormatoBadge, resultScoreDisplay, resultScoreValue, resultContent;
let sidebarList, histCount;

// ---------------------------------------------------------------------------
// Inicialización
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  // Capturar referencias DOM
  uploadZone      = document.getElementById('upload-zone');
  fileInput       = document.getElementById('file-input');
  fileInfoEl      = document.getElementById('file-info');
  fileInfoName    = document.getElementById('file-info-name');
  btnClearFile    = document.getElementById('btn-clear-file');
  fileErrorEl     = document.getElementById('file-error');
  fileErrorText   = document.getElementById('file-error-text');
  selectPerfil    = document.getElementById('select-perfil');
  selectFormato   = document.getElementById('select-formato');
  selectNicho     = document.getElementById('select-nicho');
  inputNichoCustom = document.getElementById('input-nicho-custom');
  btnGenerate     = document.getElementById('btn-generate');
  progressPanel   = document.getElementById('progress-panel');
  progressMessage = document.getElementById('progress-message');
  errorPanel      = document.getElementById('error-panel');
  errorMessage    = document.getElementById('error-message');
  btnRetry        = document.getElementById('btn-retry');
  resultPanel     = document.getElementById('result-panel');
  resultFormatoBadge  = document.getElementById('result-formato-badge');
  resultScoreDisplay  = document.getElementById('result-score-display');
  resultScoreValue    = document.getElementById('result-score-value');
  resultContent       = document.getElementById('result-content');
  sidebarList = document.getElementById('sidebar-list');
  histCount   = document.getElementById('hist-count');

  // Registrar listeners
  initUploadZone();
  initParamListeners();
  initGenerateButton();

  // Cargar historial al iniciar
  loadHistorial();
});

// ---------------------------------------------------------------------------
// Upload — Drag-and-Drop y selección por click
// ---------------------------------------------------------------------------

function initUploadZone() {
  // Click en la zona dispara el input oculto
  uploadZone.addEventListener('click', () => fileInput.click());
  uploadZone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  // Drag events
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
  });

  uploadZone.addEventListener('dragleave', (e) => {
    if (!uploadZone.contains(e.relatedTarget)) {
      uploadZone.classList.remove('drag-over');
    }
  });

  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const dt = e.dataTransfer;
    if (dt && dt.files.length > 0) {
      handleFileSelected(dt.files[0]);
    }
  });

  // Input file change
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  // Botón limpiar archivo
  btnClearFile.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFile();
  });
}

/**
 * Procesa el archivo seleccionado: valida extensión y actualiza la UI.
 * @param {File} file
 */
function handleFileSelected(file) {
  hideFileError();

  const ext = getExtension(file.name);
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    showFileError(
      `Tipo de archivo no soportado (.${file.name.split('.').pop()}). ` +
      `Usa PDF, Markdown (.md) o texto plano (.txt).`
    );
    clearFile();
    return;
  }

  appState.file = file;
  uploadZone.classList.add('has-file');
  fileInfoName.textContent = file.name;
  fileInfoEl.style.display = 'flex';
  // Reset del input para permitir re-seleccionar el mismo archivo
  fileInput.value = '';

  updateGenerateButton();
}

/**
 * Limpia el archivo seleccionado y restaura el estado visual.
 */
function clearFile() {
  appState.file = null;
  uploadZone.classList.remove('has-file');
  fileInfoEl.style.display = 'none';
  fileInfoName.textContent = '';
  fileInput.value = '';
  hideFileError(); // BH-2: limpiar también el error de archivo
  updateGenerateButton();
}

/** @param {string} msg */
function showFileError(msg) {
  fileErrorText.textContent = msg;
  fileErrorEl.style.display = 'flex';
}

function hideFileError() {
  fileErrorEl.style.display = 'none';
  fileErrorText.textContent = '';
}

/**
 * Retorna la extensión en minúsculas con punto (ej: ".pdf").
 * @param {string} filename
 * @returns {string}
 */
function getExtension(filename) {
  const parts = filename.toLowerCase().split('.');
  return parts.length > 1 ? '.' + parts[parts.length - 1] : '';
}

// ---------------------------------------------------------------------------
// Parámetros — listeners y validación
// ---------------------------------------------------------------------------

function initParamListeners() {
  selectPerfil.addEventListener('change', updateGenerateButton);
  selectFormato.addEventListener('change', updateGenerateButton);
  selectNicho.addEventListener('change', () => {
    const isCustom = selectNicho.value === '__custom__';
    inputNichoCustom.style.display = isCustom ? 'block' : 'none';
    if (!isCustom) {
      inputNichoCustom.classList.remove('error');
    }
    updateGenerateButton();
  });
  inputNichoCustom.addEventListener('input', updateGenerateButton);
}

/**
 * Retorna el valor efectivo del campo Nicho (predefinido o custom).
 * @returns {string}
 */
function getNichoValue() {
  if (selectNicho.value === '__custom__') {
    return inputNichoCustom.value.trim();
  }
  return selectNicho.value;
}

/**
 * Determina si el formulario está listo para enviar.
 * @returns {boolean}
 */
function isFormReady() {
  return Boolean(
    appState.file &&
    selectPerfil.value &&
    selectFormato.value &&
    getNichoValue()
  );
}

/**
 * Actualiza el estado (enabled/disabled) del botón Generar.
 * Los indicadores de error en los selects solo se muestran después de que
 * el usuario haya intentado enviar al menos una vez (submitAttempted),
 * para no marcar campos en rojo antes de que el usuario los toque.
 */
function updateGenerateButton() {
  const ready = isFormReady();
  btnGenerate.disabled = !ready;
  btnGenerate.setAttribute('aria-disabled', String(!ready));

  // BH-3: solo mostrar error en selects si el usuario ya intentó generar
  if (appState.submitAttempted) {
    selectPerfil.classList.toggle('error', !selectPerfil.value);
    selectFormato.classList.toggle('error', !selectFormato.value);

    const nichoVal = getNichoValue();
    if (selectNicho.value === '__custom__') {
      inputNichoCustom.classList.toggle('error', !nichoVal);
    } else {
      selectNicho.classList.toggle('error', !selectNicho.value);
  }
}

// ---------------------------------------------------------------------------
// Botón Generar — envío y polling
// ---------------------------------------------------------------------------

function initGenerateButton() {
  btnGenerate.addEventListener('click', handleGenerate);
  btnRetry.addEventListener('click', resetToInputForm);
}

/**
 * Maneja el click en "Generar": arma el FormData y llama a la API.
 */
async function handleGenerate() {
  if (!isFormReady()) return;

  const formData = new FormData();
  formData.append('archivo', appState.file, appState.file.name);
  formData.append('perfil_destinatario', selectPerfil.value);
  formData.append('formato_salida', selectFormato.value);
  formData.append('nicho_sector', getNichoValue());

  appState.submitAttempted = true; // habilita feedback de error en selects desde este momento
  showProgress('Enviando documento al servidor...');
  hideResult();
  hideErrorPanel();
  btnGenerate.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/adaptar`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ mensaje: response.statusText }));
      throw new Error(err.mensaje || `Error ${response.status}`);
    }

    const data = await response.json();
    appState.currentTaskId = data.task_id;
    startPolling(data.task_id);

  } catch (err) {
    showErrorPanel(`No se pudo enviar el documento: ${err.message}`);
    hideProgress();
    btnGenerate.disabled = false;
  }
}

/**
 * Inicia el polling del estado de la tarea.
 * @param {string} taskId
 */
function startPolling(taskId) {
  stopPolling();
  appState.pollInterval = setInterval(() => pollStatus(taskId), POLL_INTERVAL_MS);
  // Primera consulta inmediata
  pollStatus(taskId);
}

function stopPolling() {
  if (appState.pollInterval !== null) {
    clearInterval(appState.pollInterval);
    appState.pollInterval = null;
  }
}

/**
 * Consulta el estado de la tarea y reacciona al resultado.
 * @param {string} taskId
 */
async function pollStatus(taskId) {
  try {
    const response = await fetch(`${API_BASE}/adaptar/${taskId}`);
    if (!response.ok) {
      throw new Error(`Error ${response.status} consultando estado`);
    }
    const data = await response.json();
    handleStatusUpdate(data);
  } catch (err) {
    // Errores de red son transitorios — seguir haciendo polling
    setProgressMessage(`Esperando respuesta del servidor... (${err.message})`);
  }
}

/**
 * Procesa la respuesta del endpoint de status.
 * @param {{ status: string, resultado?: object, mensaje?: string }} data
 */
function handleStatusUpdate(data) {
  const status = data.status;

  if (status === 'pending' || status === 'processing') {
    const msg = PROGRESS_MESSAGES[status] || 'Procesando...';
    setProgressMessage(msg);
    return; // Seguir haciendo polling
  }

  stopPolling();

  if (status === 'completed') {
    hideProgress();
    showResult(data);
    // Recargar historial después de una generación exitosa
    setTimeout(loadHistorial, 2000);
    return;
  }

  if (status === 'failed') {
    hideProgress();
    const errMsg = data.mensaje || 'Error desconocido durante el procesamiento.';
    showErrorPanel(`Pipeline fallido: ${errMsg}`);
    btnGenerate.disabled = false;
    return;
  }

  // Estado desconocido — seguir esperando
  setProgressMessage(`Estado desconocido: ${status}`);
}

// ---------------------------------------------------------------------------
// UI — helpers de estado
// ---------------------------------------------------------------------------

/** @param {string} msg */
function showProgress(msg) {
  progressMessage.textContent = msg;
  progressPanel.classList.add('visible');
}

function hideProgress() {
  progressPanel.classList.remove('visible');
}

/** @param {string} msg */
function setProgressMessage(msg) {
  progressMessage.textContent = msg;
}

/** @param {string} msg */
function showErrorPanel(msg) {
  errorMessage.textContent = msg;
  errorPanel.classList.add('visible');
}

function hideErrorPanel() {
  errorPanel.classList.remove('visible');
}

function hideResult() {
  resultPanel.classList.remove('visible');
}

/**
 * Muestra el resultado de la generación.
 * Story 3.2 reemplazará esta función con renderers específicos por formato.
 * @param {object} data - Respuesta completa del endpoint de status.
 */
function showResult(data) {
  const resultado = data.resultado || {};
  const formato = resultado.formato || selectFormato.value || 'Resultado';
  const score = resultado.anclaje_fuente_score ?? null;

  resultFormatoBadge.textContent = formato;

  if (score !== null) {
    resultScoreValue.textContent = (score * 100).toFixed(0) + '%';
    resultScoreDisplay.style.display = 'block';
  } else {
    resultScoreDisplay.style.display = 'none';
  }

  // Placeholder de resultado — Story 3.2 implementará los renderers
  resultContent.innerHTML = renderResultPlaceholder(resultado);
  resultPanel.classList.add('visible');
}

/**
 * Renderizado provisional del resultado (Story 3.2 implementará los renderers reales).
 * @param {object} resultado
 * @returns {string} HTML
 */
function renderResultPlaceholder(resultado) {
  if (!resultado || Object.keys(resultado).length === 0) {
    return '<div class="result-placeholder">Resultado recibido. Los renderers detallados se activarán en la próxima versión.</div>';
  }
  const json = JSON.stringify(resultado, null, 2);
  return `<pre class="result-raw">${escapeHtml(json)}</pre>`;
}

/**
 * Resetea la interfaz al estado inicial para un nuevo intento.
 */
function resetToInputForm() {
  stopPolling();
  hideErrorPanel();
  hideProgress();
  hideResult();
  appState.currentTaskId = null;
  appState.submitAttempted = false;
  // Quitar clases error de todos los selects
  selectPerfil.classList.remove('error');
  selectFormato.classList.remove('error');
  selectNicho.classList.remove('error');
  inputNichoCustom.classList.remove('error');
  btnGenerate.disabled = !isFormReady();
}

// ---------------------------------------------------------------------------
// Historial
// ---------------------------------------------------------------------------

/**
 * Carga el historial desde la API y renderiza los items en la sidebar.
 */
async function loadHistorial() {
  try {
    const response = await fetch(`${API_BASE}/historial`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderHistorial(data.generaciones || []);
  } catch (err) {
    sidebarList.innerHTML = `
      <div class="sidebar-empty">
        <div class="sidebar-empty-icon" aria-hidden="true">📡</div>
        <div class="sidebar-empty-text">No se pudo cargar el historial.</div>
      </div>`;
    histCount.textContent = '';
  }
}

/**
 * Renderiza la lista de generaciones en la sidebar.
 * @param {Array<{objeto_id: string, perfil: string, formato: string, fecha_iso: string}>} generaciones
 */
function renderHistorial(generaciones) {
  if (generaciones.length === 0) {
    histCount.textContent = 'Sin generaciones aún';
    sidebarList.innerHTML = `
      <div class="sidebar-empty">
        <div class="sidebar-empty-icon" aria-hidden="true">🗂️</div>
        <div class="sidebar-empty-text">
          Aquí aparecerán tus generaciones anteriores una vez que completes tu primera adaptación.
        </div>
      </div>`;
    return;
  }

  histCount.textContent = `${generaciones.length} generación${generaciones.length !== 1 ? 'es' : ''}`;

  const items = generaciones.map((gen) => {
    const fecha = formatFecha(gen.fecha_iso);
    return `
      <div
        class="hist-item"
        role="button"
        tabindex="0"
        data-objeto-id="${escapeAttr(gen.objeto_id)}"
        aria-label="${escapeAttr(gen.formato)} - ${escapeAttr(gen.perfil)} - ${escapeAttr(fecha)}"
      >
        <div class="hist-item-formato">${escapeHtml(gen.formato)}</div>
        <div class="hist-item-perfil">${escapeHtml(gen.perfil)}</div>
        <div class="hist-item-fecha">${escapeHtml(fecha)}</div>
      </div>`;
  });

  sidebarList.innerHTML = items.join('');

  // Nota: la carga del paquete completo desde OCI es responsabilidad de Story 3.3.
  // Por ahora los items son informativos (solo visualización del historial).
}

/**
 * Formatea una fecha ISO a formato legible en español.
 * @param {string} isoString
 * @returns {string}
 */
function formatFecha(isoString) {
  try {
    const d = new Date(isoString);
    return d.toLocaleString('es-AR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString || '—';
  }
}

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------

/**
 * Escapa caracteres HTML para prevenir XSS.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Escapa para uso en atributos HTML.
 * @param {string} str
 * @returns {string}
 */
function escapeAttr(str) {
  return escapeHtml(str);
}
