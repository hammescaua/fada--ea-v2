"""Features — engenharia de variáveis agroclimáticas a partir da série diária.

Conjunto parcimonioso e cientificamente defensável (ver ADR-0004): mede estresse
hídrico e térmico na janela reprodutiva da soja, mais a chuva total da safra.
"""

from app.domain.features.soybean import (
    SOYBEAN_FEATURE_NAMES,
    build_soybean_features,
    build_soybean_features_for_windows,
)

__all__ = [
    "build_soybean_features",
    "build_soybean_features_for_windows",
    "SOYBEAN_FEATURE_NAMES",
]
