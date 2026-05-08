"""
workers/pipeline/validators/schemas.py
  - Pydantic v2 models para validar cada fila del CSV.
  - RawProductRow  → datos tal como llegan del CSV (todo strings)
  - CleanProductRow → datos después de validación y casteo
"""

from __future__ import annotations

import re
from datetime import date 
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator

from worker.core.config import Settings