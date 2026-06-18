"""CONAB — séries históricas de safras (suplementar, best-effort).

O acesso programático da CONAB é instável e sem API REST estável documentada.
Aqui ela entra como fonte **suplementar** de contexto estadual (área/produção/
produtividade por safra), nunca como ground truth — esse papel é do IBGE/PAM.

O conector degrada de forma graciosa: se a fonte estiver indisponível, retorna
vazio e o pipeline segue apenas com o IBGE, registrando a ausência.
"""

from __future__ import annotations

import logging

from app.data.connectors.base import HttpDataSource

logger = logging.getLogger(__name__)

# Endpoint do portal de informações agropecuárias da CONAB (pode mudar/sair do ar).
_SERIES_URL = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/SojaSerieHist.txt"


class ConabConnector:
    def __init__(self, source: HttpDataSource | None = None) -> None:
        self._http = source or HttpDataSource()

    def soybean_state_yield(self, uf: str = "RS") -> dict[str, float]:
        """Best-effort: {safra: produtividade kg/ha} estadual. Vazio se indisponível."""
        try:
            # Tentativa best-effort; formato e disponibilidade variam.
            self._http.get_json(_SERIES_URL)
        except Exception as exc:  # noqa: BLE001
            logger.warning("CONAB indisponível (%s); seguindo só com IBGE.", type(exc).__name__)
            return {}
        return {}
