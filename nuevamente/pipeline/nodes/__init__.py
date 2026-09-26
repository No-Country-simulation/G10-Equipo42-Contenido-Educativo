"""Nodos del grafo LangGraph de NuevaMente.

Cada nodo es un callable (state: NuevaMenteState) -> dict que retorna
un dict parcial para fusionar en el state.
"""

from nuevamente.pipeline.nodes.draft import draft_node
from nuevamente.pipeline.nodes.ingest import ingest_node
from nuevamente.pipeline.nodes.retrieve import retrieve_node
from nuevamente.pipeline.nodes.review import review_node

__all__ = ["draft_node", "ingest_node", "retrieve_node", "review_node"]

