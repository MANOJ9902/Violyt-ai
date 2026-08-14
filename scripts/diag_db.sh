#!/bin/bash
# Postgres connection headroom, quiet about the collation warning.
PSQL="sudo docker exec violyt-deploy-postgres-1 psql -U violyt -d violyt -tAX -q"
echo -n "max_connections: "
$PSQL -c "SHOW max_connections;" 2>/dev/null | grep -E '^[0-9]+$'
echo -n "reserved_superuser: "
$PSQL -c "SHOW superuser_reserved_connections;" 2>/dev/null | grep -E '^[0-9]+$'
echo -n "in_use_now: "
$PSQL -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | grep -E '^[0-9]+$'
echo "by_application:"
$PSQL -c "SELECT coalesce(application_name,'?')||' '||count(*) FROM pg_stat_activity GROUP BY 1 ORDER BY 2 DESC;" 2>/dev/null | grep -vE '^\s*$'
