"""Catalog — catálogo de produtos (insumos). Contexto de suporte/referência.

Sem preços dinâmicos nesta fase — apenas estrutura (ADR-0011).
"""

from app.domain.catalog.product import Product, ProductCategory

__all__ = ["Product", "ProductCategory"]
