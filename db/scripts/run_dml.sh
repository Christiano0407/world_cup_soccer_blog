#!/bin/bash
# =============================================================
# FIFA World Cup Platform — DML Runner
# =============================================================
# Executes DML seed/insert files after migrations.
# Mount this script at /docker-entrypoint-initdb.d/ AFTER
# run_migrations.sh (01-* runs before 02-*).
#
# Anti SQLi: DML files only contain static SQL — no dynamic input.
# =============================================================
set -euo pipefail

DML_DIR="/dml"

echo "============================================================"
echo "  FIFA World Cup Platform — Running DML Seeds"
echo "============================================================"

for f in "$DML_DIR"/*.sql; do
    echo "→ $(basename "$f") ..."
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"
    echo "  ✓ $(basename "$f") complete"
done

echo "============================================================"
echo "  All DML applied successfully"
echo "============================================================"
