"""Decisions — camada de apoio à decisão DETERMINÍSTICA e explicável.

Não produz score único (falsa precisão) nem prescrição agronômica. Produz:
- atenção por FLAGS nomeadas e gated (cada uma com evidência, N, efeito, confiança);
- ranking multi-critério (uma dimensão por vez).
FADA aponta ONDE olhar, não O QUE fazer (ADR-0016). Sem LLM.
"""

from app.domain.decisions.model import AttentionFlag, FieldAttention, FieldDecisionInput
from app.domain.decisions.engine import attention_level, evaluate, rankings

__all__ = [
    "FieldDecisionInput",
    "AttentionFlag",
    "FieldAttention",
    "evaluate",
    "attention_level",
    "rankings",
]
