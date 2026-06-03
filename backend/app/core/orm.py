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
class User(Base): 
  __tablename__ = "users"

  user_id: Mapped[uuid.UUID] = mapped_column (
    UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
  )
  email: Mapped[str] = mapped_column(
    String(255), unique=True, nullable=False, index=True
  )
  hashed_password: Mapped[str] = mapped_column(
    String(255), nullable=False
  )
  display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
  role: Mapped[str] = mapped_column(
    Enum("admin", "editor", "reader", name="user_role"), nullable=False, default="reader"
  )
  is_active: Mapped[bool] = mapped_column(
    Boolean, nullable=False, default=True
  )
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  update_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  # ---- Revoked refresh token JTIs stored in Redis; model only stores last known ----
  refresh_jti: Mapped[str | None] = mapped_column(String(36), nullable=True)

  def __rep__(self) -> str: 
    return f"<User {self.display_name} - {self.email}  | role={self.role}"
