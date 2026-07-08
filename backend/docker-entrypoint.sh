#!/bin/sh
set -e

DB_HOST="${DB_HOST:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-ai_collab}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

echo "Waiting for PostgreSQL at $DB_HOST..."
for i in $(seq 1 30); do
  if PGPASSWORD=postgres psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; then
    echo "PostgreSQL ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "WARNING: PostgreSQL not ready after 30s, continuing..."
  fi
  sleep 1
done

echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
for i in $(seq 1 30); do
  if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
    echo "Redis ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "WARNING: Redis not ready after 30s, continuing..."
  fi
  sleep 1
done

exec "$@"
