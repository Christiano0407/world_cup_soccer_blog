"""
  SQLAlchemy ORM models for the FIFA World Cup platform.
  (Object Relational Mapping o Mapeo Objeto-Relacional) 
    - Su función principal es convertir los datos de los objetos en el lenguaje de programación a un formato adecuado para ser almacenado en una base de datos relacional (como MySQL o PostgreSQL).
    - [POO & DB] Técnica de programación que crea una capa de abstracción entre el código orientado a objetos y las bases de datos relacionales. 
"""  # noqa: E501

from __future__ import annotations

import uuid 
from datetime import UTC, datetime 

from sqlalchemy import (
  BigInteger,
  Boolean, 
  DateTime, 
  Enum, 
  Float, 
  ForeignKey, 
  Integer, 
  SmallInteger, 
  String, 
  Text, 
  UniqueConstraint, 
  func
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# === Declarative === 
class Base(DeclarativeBase):
  pass


# ─── === Auth === ─────────────────────────────────────────────────────────────────────
