"""Planificación, generación vectorial y auditoría visual de presentaciones.

El paquete mantiene separadas las reglas (``dominio``), la comparación
semántica (``semantica``) y los adaptadores de archivos (``pptx_adapter`` y
``vector``).  Ninguna regla del dominio conoce PowerPoint, Ollama o
LibreOffice.
"""

from .dominio import Hallazgo, PlanVisual, Visual, cargar_plan, validar_plan

__all__ = ["Hallazgo", "PlanVisual", "Visual", "cargar_plan", "validar_plan"]
