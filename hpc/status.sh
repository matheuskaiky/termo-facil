#!/usr/bin/env bash
# HPC Status — Show running/stopped state of all services

set -euo pipefail
source "$(dirname "$0")/config.sh"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  Termo Fácil — HPC Service Status                       ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# --- PostgreSQL status ---
PG_OK=0
if find_postgres 2>/dev/null && "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$PG_PORT" -q 2>/dev/null; then
  log_ok "PostgreSQL      RUNNING"
  echo "               127.0.0.1:$PG_PORT  db=$PG_DB  user=$PG_USER"
  echo "               psql postgresql://$PG_USER:***@127.0.0.1:$PG_PORT/$PG_DB"
  PG_OK=1
else
  log_error "PostgreSQL      STOPPED"
  if ! find_postgres 2>/dev/null; then
    echo "               [pg_ctl not found — run hpc/setup.sh first]"
  else
    echo "               [run hpc/start.sh to start]"
  fi
fi
echo ""

# --- Redis status ---
REDIS_OK=0
if [ -x "$HPC_BIN_DIR/redis-cli" ] || command -v redis-cli &>/dev/null; then
  REDIS_CLI="${HPC_BIN_DIR}/redis-cli"
  [ -x "$REDIS_CLI" ] || REDIS_CLI=$(command -v redis-cli)
  if $REDIS_CLI -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
    log_ok "Redis           RUNNING"
    echo "               127.0.0.1:$REDIS_PORT"
    echo "               redis-cli -p $REDIS_PORT"
    REDIS_OK=1
  else
    log_error "Redis           STOPPED"
    echo "               [run hpc/start.sh to start]"
  fi
else
  log_error "Redis           STOPPED"
  echo "               [redis-cli not found — run hpc/setup.sh first]"
fi
echo ""

# --- MinIO status ---
MINIO_OK=0
if curl -sf "http://127.0.0.1:$MINIO_PORT/minio/health/live" &>/dev/null 2>&1; then
  log_ok "MinIO           RUNNING"
  echo "               API:     http://127.0.0.1:$MINIO_PORT"
  echo "               Console: http://127.0.0.1:$MINIO_CONSOLE_PORT"
  echo "               User: $MINIO_ROOT_USER  Password: $MINIO_ROOT_PASSWORD"
  MINIO_OK=1
else
  log_error "MinIO           STOPPED"
  echo "               [run hpc/start.sh to start]"
fi
echo ""

# --- Summary ---
TOTAL_OK=$((PG_OK + REDIS_OK + MINIO_OK))
if [ $TOTAL_OK -eq 3 ]; then
  log_ok "All infrastructure services are UP"
elif [ $TOTAL_OK -eq 0 ]; then
  log_error "All infrastructure services are DOWN"
else
  log_warn "$TOTAL_OK/3 services are running"
fi
echo ""

echo "Logs directory: $HPC_LOGS_DIR"
echo "  postgres.log  redis.log  minio.log"
echo ""

echo "Application services (start manually, from project root with .venv active):"
echo ""
echo "  # Terminal 1 — Backend API"
echo "  uvicorn app.main:app --reload --app-dir backend"
echo ""
echo "  # Terminal 2 — Celery Worker"
echo "  cd backend && celery -A app.core.celery_app worker --loglevel=info -P solo"
echo ""
echo "  # Terminal 3 — Frontend"
echo "  cd frontend && npm run start"
echo ""
echo "  # Terminal 4 — Ollama (if not already running)"
echo "  ollama serve"
echo ""
