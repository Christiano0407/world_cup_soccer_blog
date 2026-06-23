from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import factory

from app.schemas.schemas import (
    AdminUserOut,
    HeadToHeadOut,
    MatchListOut,
    MatchOut,
    Paginated,
    PlayerAppearanceOut,
    PlayerCareerOut,
    TeamOut,
    TeamStatsOut,
    TopScorerOut,
    TournamentListOut,
    TournamentOut,
    UserOut,
)


class UserOutFactory(factory.Factory):
    class Meta:
        model = UserOut

    user_id = factory.LazyFunction(uuid.uuid4)
    email = factory.Faker("email")
    display_name = factory.Faker("name")
    role = "reader"
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    update_at = factory.LazyFunction(lambda: datetime.now(UTC))


class AdminUserOutFactory(factory.Factory):
    class Meta:
        model = AdminUserOut

    user_id = factory.LazyFunction(uuid.uuid4)
    email = factory.Faker("email")
    display_name = factory.Faker("name")
    role = "admin"
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    update_at = factory.LazyFunction(lambda: datetime.now(UTC))


class TeamOutFactory(factory.Factory):
    class Meta:
        model = TeamOut

    team_id = factory.Sequence(lambda n: n + 1)
    initials = factory.Iterator(["ARG", "BRA", "GER", "FRA", "ITA"])
    name = factory.Faker("word")
    confederation = "CONMEBOL"
    fifa_code = factory.SelfAttribute("initials")
    active = True


class TeamStatsOutFactory(factory.Factory):
    class Meta:
        model = TeamStatsOut

    initials = "ARG"
    name = "Argentina"
    confederation = "CONMEBOL"
    tournaments_played = 10
    titles = 3
    runner_ups = 2
    total_matches = 50
    wins = 30
    draws = 10
    losses = 10
    goals_scored = 90
    goals_conceded = 40
    goal_difference = 50
    win_rate_pct = 60.0


class TournamentOutFactory(factory.Factory):
    class Meta:
        model = TournamentOut

    tournament_id = factory.Sequence(lambda n: n + 1)
    year = factory.Iterator([1930, 1934, 1938, 1950, 1954])
    host_country = factory.Faker("country")
    winner = "Argentina"
    runners_up = "France"
    third_place = "Germany"
    fourth_place = "Brazil"
    goals_scored = 100
    qualified_teams = 16
    matches_played = 50
    attendance_total = 1000000
    avg_goals_per_match = 2.5


class TournamentListOutFactory(factory.Factory):
    class Meta:
        model = TournamentListOut

    tournament_id = factory.Sequence(lambda n: n + 1)
    year = factory.Iterator([1930, 1934, 1938])
    host_country = factory.Faker("country")
    winner = "Argentina"
    goals_scored = 100
    matches_played = 50


class MatchOutFactory(factory.Factory):
    class Meta:
        model = MatchOut

    match_id = factory.Sequence(lambda n: n + 1)
    tournament_id = 1
    year = 2022
    stage = "Final"
    match_datetime = factory.LazyFunction(lambda: datetime.now(UTC))
    stadium = "Lusail Stadium"
    city = "Lusail"
    home_team_initials = "ARG"
    away_team_initials = "FRA"
    home_team_name = "Argentina"
    away_team_name = "France"
    home_goals = 3
    away_goals = 3
    ht_home_goals = 2
    ht_away_goals = 0
    win_conditions = "Argentina wins 4-2 on penalties"
    attendance = 88966
    referee = "Szymon Marciniak"


class MatchListOutFactory(factory.Factory):
    class Meta:
        model = MatchListOut

    match_id = factory.Sequence(lambda n: n + 1)
    year = 2022
    stage = "Group Stage"
    match_datetime = factory.LazyFunction(lambda: datetime.now(UTC))
    home_team_initials = "ARG"
    away_team_initials = "KSA"
    home_goals = 1
    away_goals = 2


class PlayerAppearanceOutFactory(factory.Factory):
    class Meta:
        model = PlayerAppearanceOut

    player_match_id = factory.Sequence(lambda n: n + 1)
    match_id = 1
    team_initials = "ARG"
    coach_name = "Lionel Scaloni"
    lineup_type = "S"
    shirt_number = 10
    player_name = "Lionel Messi"
    position = "FW"
    event_code = "G"


class TopScorerOutFactory(factory.Factory):
    class Meta:
        model = TopScorerOut

    player_name = "Lionel Messi"
    team_initials = "ARG"
    goals = 8
    own_goals = 0
    matches_played = 7
    first_wc = 2006
    last_wc = 2022
    editions = 5


class PlayerCareerOutFactory(factory.Factory):
    class Meta:
        model = PlayerCareerOut

    player_name = "Lionel Messi"
    team_initials = "ARG"
    total_appearances = 26
    starts = 24
    substitutions = 2
    goals = 13
    yellow_cards = 0
    red_cards = 0
    editions = [2006, 2010, 2014, 2018, 2022]


class HeadToHeadOutFactory(factory.Factory):
    class Meta:
        model = HeadToHeadOut

    team_a = "ARG"
    team_b = "FRA"
    total_matches = 4
    team_a_wins = 2
    team_b_wins = 1
    draws = 1
    team_a_goals = 7
    team_b_goals = 6
    first_encounter = 1930
    last_encounter = 2022


def build_paginated(items: list, total: int | None = None, page: int = 1, page_size: int = 20) -> Paginated[Any]:
    total = total or len(items)
    pages = -(-total // page_size)
    return Paginated(items=items, total=total, page=page, page_size=page_size, pages=pages)
