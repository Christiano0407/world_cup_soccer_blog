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


class Team(Base): 
  __tablename__ = "teams"

  team_id: Mapped[int] = mapped_column(
    Integer, primary_key=True, autoincrement=True
  )
  initials: Mapped[str] = mapped_column(
    String(3), unique=True, nullable=False, index=True
  )
  name: Mapped[str] = mapped_column(
    String(100), nullable=False
  )
  confederation: Mapped[str | None] = mapped_column(
    String(20), nullable=True
  )
  fifa_code: Mapped[str | None] = mapped_column(
    String(3), nullable=True
  )
  active: Mapped[bool] = mapped_column(
    Boolean, nullable=False, default=True
  )
  home_matches: Mapped[list[Match]] = relationship (
    "Match", foreign_keys="Match.home_team_initials", back_populates="home_team"
  )
  away_matches: Mapped[list[Match]] = relationship (
    "Match", foreign_keys="Match.away_team_initials", back_populates="away_team"
  )

  def __rep__(self) -> str: 
    return f"<Team {self.initials}"
  

class Tournaments(Base): 
  __tablename__ = "tournaments"
  __table_args__ = (UniqueConstraint("year", name="uq_tournament_year"), )
  
  tournament_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  year: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
  host_country: Mapped[str] = mapped_column(String(100), nullable=False)
  winner: Mapped[str] = mapped_column(String(100), nullable=False)
  runners_up: Mapped[str] = mapped_column(String(100), nullable=False)
  third_place: Mapped[str | None] = mapped_column(String(100), nullable=True)
  fourth_place: Mapped[str | None] = mapped_column(String(100), nullable=True)
  goals_scored: Mapped[int] = mapped_column(Integer, nullable=False)
  qualified_teams: Mapped[int] = mapped_column(SmallInteger, nullable=False)
  matches_played: Mapped[int] = mapped_column(SmallInteger, nullable=False)
  attendance_total: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

  matches: Mapped[list[Match]] = relationship("Match", back_populates="tournament")

  @property
  def svg_goals_per_match(self) -> float | None: 
    if self.matches_played: 
      return round(self.goals_scored / self.matches_played, 2)
    return None
  
  def __rep__(self) -> str: 
      return f"<Tournament Year: {self.year} | Winner: {self.winner}"

class Match(Base): 
  __tablename__ = "matches"
  
  match_id: Mapped[int] = mapped_column(Integer, primary_key=True)
  tournament_id: Mapped[int] = mapped_column(
    Integer, ForeignKey("tournaments.tournament_id", ondelete="RESTRICT"), nullable=False
  )
  year: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
  stage: Mapped[int] = mapped_column(String(50), nullable=False)
  match_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
  stadium: Mapped[str | None] = mapped_column(String(100), nullable=True)
  city: Mapped[str | None] = mapped_column(String(100), nullable=True)
  home_team_initials: Mapped[str] = mapped_column(
    String(3), ForeignKey("teams.initials", ondelete="RESTRICT"), nullable=False
  )
  away_team_initials: Mapped[str] = mapped_column(
    String(3), ForeignKey("teams.initials", ondelete="RESTRICT"), nullable=False
  )
  home_goals: Mapped[int] = mapped_column(SmallInteger, nullable=False)
  away_goals: Mapped[int] = mapped_column(SmallInteger, nullable=False)
  ht_home_goals: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
  ht_away_goals: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
  win_conditions: Mapped[str | None] = mapped_column(String(50), nullable=True)
  attendance: Mapped[int | None] = mapped_column(Integer, nullable=True)
  referee: Mapped[str | None] = mapped_column(String(100), nullable=True)

  tournament: Mapped[Tournaments] = relationship("Tournaments", back_populates="matches")
  home_team: Mapped[Team] = relationship(
    "Team", foreign_keys=[home_team_initials], back_populates="home_matches"
  )
  away_team: Mapped[Team] = relationship(
    "Team", foreign_keys=[away_team_initials], back_populates="away_matches"
  )
  player_appearances: Mapped[list[PlayerAppearance]] = relationship(
    "PlayerAppearance", back_populates="matches"
  )

  def __repr__(self) -> str:
    return f"<Match {self.year} {self.home_team_initials} Vs {self.away_team_initials}>"


class PlayerAppearance(Base): 
  __tablename__ = "player_appearance"
  
  player_match_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
  match_id: Mapped[int] = mapped_column(
    Integer, ForeignKey("Matches.match_id", ondelete="CASCADE"), nullable=False, 
    index=True
  )
  team_initials: Mapped[str] = mapped_column(String(3), nullable=False)
  coach_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
  lineup_type: Mapped[str] = mapped_column(
    Enum("S", "N", name="lineup_type"), nullable=False, comment="S=titular, N=suplente"
  )
  shirt_number: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
  player_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
  position: Mapped[str | None] = mapped_column(
    Enum("GK", "DF","MF", "FW", name="position_type"), nullable=True
  )
  event_code: Mapped[str | None] = mapped_column(
    String(5), nullable=True, comment="G=gol, y=Amarilla, r=Roja, OG=propia",
  )
  match: Mapped[Match] = relationship("Match", back_populates="player_appearances")

  def __repr__(self) -> str:
    return f"<PlayerAppearances {self.player_name} | match={self.match_id}"


class EtlRun(Base):
  __tablename__ = "etl_runs"
  pass


class DeadLetter(Base): 
  __tablename__ = "dead_letters"
  pass


class AuditLog(Base): 
  __tablename__ = "audit_logs"
  pass