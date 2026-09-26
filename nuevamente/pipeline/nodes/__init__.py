"""Nodos del grafo LangGraph de NuevaMente.

Cada nodo es un callable (state: NuevaMenteState) -> dict que retorna
un dict parcial para fusionar en el state.
"""

from nuevamente.pipeline.nodes.ingest import ingest_node

__all__ = ["ingest_node"]
