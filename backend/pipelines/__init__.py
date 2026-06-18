"""Pipelines de ingestão e treino (offline).

Dependem do extra ``ml`` (pandas/sklearn/xgboost/mlflow). Não fazem parte do
runtime da API — produzem os artefatos versionados em ``data/features`` e
``data/models`` que a API consome.
"""
