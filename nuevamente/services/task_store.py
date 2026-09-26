"""Almacen en memoria para el seguimiento de tareas de adaptacion.

Mantiene el estado de cada tarea (pending, processing, completed, failed)
y su resultado o mensaje de error. Disenado para concurrencia 1 (un pipeline
activo a la vez), sin persistencia entre reinicios del servidor.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TaskStore:
    """Almacen en memoria de tareas de adaptacion.

    Cada tarea se representa como un dict con las claves:
    - status: "pending" | "processing" | "completed" | "failed"
    - resultado: dict con el paquete educativo (solo cuando status="completed")
    - error: str con el mensaje de error (solo cuando status="failed")
    """

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}

    def create(self, task_id: str) -> None:
        """Registra una nueva tarea en estado pendiente.

        Args:
            task_id: Identificador unico de la tarea (UUID string).
        """
        self._tasks[task_id] = {"status": "pending"}
        logger.debug("task_store: tarea creada task_id=%s", task_id)

    def set_processing(self, task_id: str) -> None:
        """Marca la tarea como en procesamiento.

        Args:
            task_id: Identificador de la tarea.
        """
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "processing"
            logger.debug("task_store: tarea en procesamiento task_id=%s", task_id)

    def set_completed(self, task_id: str, resultado: dict[str, Any]) -> None:
        """Marca la tarea como completada y almacena el resultado.

        Args:
            task_id: Identificador de la tarea.
            resultado: Paquete educativo generado (educational_package dict).
        """
        if task_id in self._tasks:
            self._tasks[task_id] = {"status": "completed", "resultado": resultado}
            logger.info("task_store: tarea completada task_id=%s", task_id)

    def set_failed(self, task_id: str, error: str) -> None:
        """Marca la tarea como fallida y almacena el mensaje de error.

        Args:
            task_id: Identificador de la tarea.
            error: Descripcion del error ocurrido.
        """
        if task_id in self._tasks:
            self._tasks[task_id] = {"status": "failed", "error": error}
            logger.error("task_store: tarea fallida task_id=%s error=%s", task_id, error)

    def get(self, task_id: str) -> dict[str, Any] | None:
        """Retorna el dict de estado de la tarea, o None si no existe.

        Args:
            task_id: Identificador de la tarea.

        Returns:
            Dict con las claves status (y resultado o error segun corresponda),
            o None si el task_id no esta registrado.
        """
        return self._tasks.get(task_id)


# Instancia modulo-nivel: compartida por toda la aplicacion en el mismo proceso.
task_store = TaskStore()
