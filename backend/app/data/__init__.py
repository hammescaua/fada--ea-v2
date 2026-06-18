"""Data platform — conectores de fontes externas e ingestão.

Separa 'obter dado' de 'servir dado'. Conectores têm cache em disco (reprodutível,
re-executável offline) e degradam de forma graciosa quando a fonte está indisponível.
"""
