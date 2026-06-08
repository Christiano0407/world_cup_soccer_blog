"""
  Now let me create the service layer and route handlers | 
    - Lógica & Reglas de Negocio ((Business Layer) de tu módulo de autenticación.)
    - Authentication service — register, login, refresh, password change.
  ## ============================================================================ ##
  La capa Service contiene las reglas de negocio.
    - No le importa HTTP.
    - No le importa FastAPI.
    - No le importa Swagger. 
    - No le importa JSON.
    - Su única responsabilidad es:
      Tomar datos
          ↓
          Aplicar reglas de negocio
          ↓
          Usar BD
          ↓
          Usar Redis
          ↓
          Usar JWT
          ↓
          Devolver resultados
  ## ============================================================================== ##
"""  # noqa: E501

from __future__ import annotations

import uuid
from datetime import UTC, datetime