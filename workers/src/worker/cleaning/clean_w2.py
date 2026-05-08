"""
W2 — Clean Worker
=================
Responsibility: Read raw.* staging → validate → cast types → mark valid/invalid.
Rejected rows → raw.dead_letter with structured error codes.
 
Anti SQL-Injection: All queries use asyncpg $N parameterized execution.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from sqlalchemy.orm import Session

import asyncpg
import pandas as pd
import structlog

from worker.core.config import Settings

log = structlog.get_logger(__name__) # - Logs / History -Real Time - #