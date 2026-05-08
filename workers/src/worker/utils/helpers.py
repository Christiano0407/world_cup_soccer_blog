"""
workers/utils/helpers.py
  - Funciones utilitarias puras (sin efectos secundarios, sin dependencias externas).
  - Fáciles de testear unitariamente.
"""
# Regular Expressions # 
import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation


# ─────────────────────────────────────────────────────────────────────────────
# PARSERS BOOLEAN
# ─────────────────────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────────────────────
# PARSERS NUMÉRICO
# ─────────────────────────────────────────────────────────────────────────────

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

def parse_attendance(value: str | None) -> int | None:
  """
    - Parser específico para el campo attendance del CSV FIFA.
 
    - El CSV usa punto como separador de miles (notación europea):
        "590.549"  → 590549
        "1.045.246" → 1045246
        "363.000"  → 363000
 
    - También maneja enteros normales: "4444" → 4444
    - Retorna None si vacío o no parseable.
    """
  if value is None or str(value).strip() == "": 
    return None
  cleaned = str(value).strip().replace(",", ".").replace(",", ".")
  try: 
    result = int(cleaned)
    # Sanity check: asistencia razonable (0 a 200.000 por partido)
    return result if result >= 0 else None
  except ValueError:
    return None


# ─────────────────────────────────────────────────────────────────────────────
# PARSERS DE FECHA Y TIEMPO
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZADORES DE TEXTO
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# GENERADORES Y UTILIDADES
# ─────────────────────────────────────────────────────────────────────────────

# === Genera un slug URL-friendly a partir de un texto. === #
def slugify(text: str) -> str:
    """Genera un slug URL-friendly a partir de un texto."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return re.sub(r"^-+|-+$", "", text)


# === Retorna el momento actual en UTC (timezone-aware). === #
def now_utc() -> datetime:
  return datetime.now(UTC)


# === Genera una clave S3 con timestamp para evitar colisiones. Ejemplo: products/20240115_143022_productos.csv === #  # noqa: E501 === #
def format_s3_key(prefix:str, filename: str, *, ts:datetime | None = None) -> str:
  """
    Genera una clave S3 con timestamp para evitar colisiones.
    Ejemplo: products/20240115_143022_productos.csv
  """
  ts = ts or now_utc()
  timestamp = ts.strftime("%Y%m%d_%H%M%S")
  return f"{prefix}/{timestamp}_{filename}"