#!/bin/bash
set -e

# Remove any Railway-custom config parameters not recognized by standard postgres
if [ -f "$PGDATA/postgresql.conf" ]; then
    sed -i '/autovacuum_worker_slots/d' "$PGDATA/postgresql.conf"
fi

exec docker-entrypoint.sh postgres "$@"
