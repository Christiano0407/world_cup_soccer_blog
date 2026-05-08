"""
workers/utils/helpers.py
  - Funciones utilitarias puras (sin efectos secundarios, sin dependencias externas).
  - Fáciles de testear unitariamente.
"""
# Regular Expressions # 
import re 
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

# === Convierte strings comunes de booleano a bool. Retorna None si ambiguo. ===
def parse_bool(value:str | None ) -> bool | None: 
  """Convierte strings comunes de booleano a bool. Retorna None si ambiguo."""
  if value is None:
    return None
  normalized = str(value).strip().upper()
  if normalized in { "TRUE", "1", "YES", "SI", "S", "Y" }: 
    return True
  if normalized in { "FALSE", "0", "NO", "N" }: 
    return False
  return None

# === Convierte string a Decimal. Maneja comas como separador decimal. Retorna None si el valor es vacío o inválido. === #  # noqa: E501 === #
def parse_decimal(value:str | None, *, field: str = "") -> Decimal | None:
  """ 
    - Convierte string a Decimal. Maneja comas como separador decimal. Retorna None si el valor es vacío o inválido.
  """  # noqa: E501
  if value is None or str(value).strip() == "":
    return None
  cleaned = str(value).strip().replace(",", ".")
  try:
    return Decimal(cleaned)
  except InvalidOperation:
    return None



# === Convierte string a int. Retorna None si inválido. === #
def parse_int(value:str | None) -> int | None:
  """Convierte string a int. Retorna None si inválido"""
  if value is None or str(value).strip() == "":
    return None
  try: 
    return int(str(value).strip())
  except ValueError:
    return None

# === Intenta parsear fecha en múltiples formatos comunes. Retorna None si no puede parsear. === #
def parse_date(value:str | None) -> date | None:
  """Intenta parsear fecha en múltiples formatos comunes. Retorna None si no puede parsear"""
  if value is None or str(value).strip() == "":
    return None
  format = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"]
  clean = str(value).strip()
  for fmt in format:
    try:
        return datetime.strptime(clean, fmt).date()
    except ValueError:
      continue
  return None


# === Normaliza SKU (Valor único): strip + uppercase. Retorna None si vacío. === #
def normalize_unique_sku(value: str | None) -> str | None: 
 """Normaliza SKU (Valor único): strip + uppercase. Retorna None si vacío."""
 if value is None: 
   return None
 result = str(value).strip().upper()
 return result or None
 

# === Strip de espacios. Opcionalmente trunca al max_length. === #
def normalize_text(value:str | None, *, max_length: int | None = None) -> str | None:
  """Strip de espacios. Opcionalmente trunca al max_length."""
  if value is None:
    return None
  result = str(value).strip()
  if not result:
    return None
  if max_length is not None:
    result = result[:max_length]
  return result


# === Genera un slug URL-friendly a partir de un texto. === #


# === Retorna el momento actual en UTC (timezone-aware). === #


# === Genera una clave S3 con timestamp para evitar colisiones. Ejemplo: products/20240115_143022_productos.csv === #  # noqa: E501 === #
