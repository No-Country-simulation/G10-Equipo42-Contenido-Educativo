"""Excepciones de dominio para NuevaMente.

Cada excepcion lleva un codigo HTTP sugerido para que la capa de API
pueda traducirla directamente en una respuesta HTTP apropiada.
"""


class NuevaMenteError(Exception):
    """Excepcion base del dominio NuevaMente."""

    http_status: int = 500
    codigo: str = "error_interno"

    def __init__(self, mensaje: str) -> None:
        self.mensaje = mensaje
        super().__init__(mensaje)


class DocumentoNoSoportado(NuevaMenteError):
    """El formato del documento no es soportado (PDF, .md, .txt unicamente).

    Corresponde a HTTP 415 Unsupported Media Type.
    """

    http_status: int = 415
    codigo: str = "formato_no_soportado"


class DocumentoVacio(NuevaMenteError):
    """El documento esta vacio o no se puede extraer texto de el.

    Corresponde a HTTP 422 Unprocessable Entity.
    """

    http_status: int = 422
    codigo: str = "documento_vacio"


class PipelineError(NuevaMenteError):
    """Error durante la ejecucion del pipeline de transformacion.

    Corresponde a HTTP 500 Internal Server Error.
    Incluye informacion sobre que agente fallo y con que input.
    """

    http_status: int = 500
    codigo: str = "error_pipeline"

    def __init__(self, mensaje: str, *, agente: str = "", detalle: str = "") -> None:
        self.agente = agente
        self.detalle = detalle
        super().__init__(mensaje)


class ServicioNoDisponible(NuevaMenteError):
    """Un servicio externo requerido no esta disponible.

    Corresponde a HTTP 503 Service Unavailable.
    Aplica cuando Gemini, Voyage AI u OCI no responden.
    """

    http_status: int = 503
    codigo: str = "servicio_no_disponible"
