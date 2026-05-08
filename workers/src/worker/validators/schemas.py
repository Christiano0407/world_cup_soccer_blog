"""
workers/pipeline/validators/schemas.py
  - Pydantic v2 models para validar cada fila del CSV.
  - RawProductRow  → datos tal como llegan del CSV (todo strings)
  - CleanProductRow → datos después de validación y casteo
"""