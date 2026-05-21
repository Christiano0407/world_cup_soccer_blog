#!/bin/bash
# =============================================================
# FIFA World Cup Platform — Migration Runner
# =============================================================
# Executes all migration SQL files in order.
# Mount this script at /docker-entrypoint-initdb.d/ in the
# PostgreSQL container. Mount ./db/migrations/ at /migrations/.
#
# Usage (via docker-compose):
#   PostgreSQL executes this automatically on first boot.
#   To re-run: docker compose exec postgres bash /docker-entrypoint-initdb.d/01-run_migrations.sh
#
# Anti SQLi: All queries use parameterized execution in app code.
#            This script only runs DDL — no dynamic SQL.
# =============================================================
set -euo pipefail

MIGRATIONS_DIR="/migrations"

echo "============================================================"
echo "  FIFA World Cup Platform — Running Migrations"
echo "============================================================"

for f in "$MIGRATIONS_DIR"/*.sql; do
    echo "→ $(basename "$f") ..."
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"
    echo "  ✓ $(basename "$f") complete"
done

echo "============================================================"
echo "  All migrations applied successfully"
echo "============================================================"
