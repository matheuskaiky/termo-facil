#!/usr/bin/env bash
# HPC Start — Start PostgreSQL, Redis, and MinIO as background services

set -euo pipefail
source "$(dirname "$0")/config.sh"

log_info "=== Starting Termo Fácil HPC Services ==="
echo ""

# --- Preflight checks ---
log_info "Verifying binaries and data..."
if ! find_postgres; then
  log_error "PostgreSQL not found. Run hpc/setup.sh first."
  exit 1
fi

if [ ! -x "$HPC_BIN_DIR/redis-server" ]; then
  log_error "redis-server not found at $HPC_BIN_DIR/redis-server. Run hpc/setup.sh first."
  exit 1
fi

if [ ! -x "$HPC_BIN_DIR/minio" ]; then
  log_error "minio not found at $HPC_BIN_DIR/minio. Run hpc/setup.sh first."
  exit 1
fi

if [ ! -f "$PG_DATA_DIR/PG_VERSION" ]; then
  log_error "PostgreSQL cluster not initialized. Run hpc/setup.sh first."
  exit 1
fi

log_ok "All binaries ready"
echo ""

# --- Start PostgreSQL ---
log_info "Starting PostgreSQL on port $PG_PORT..."

if "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$PG_PORT" -q 2>/dev/null; then
  log_info "PostgreSQL already running"
else
  if ! check_port_free "$PG_PORT"; then
    log_error "Port $PG_PORT is already in use!"
    exit 1
  fi

  "$PG_BIN_DIR/pg_ctl" -D "$PG_DATA_DIR" \
    -l "$HPC_LOGS_DIR/postgres.log" \
    start &>/dev/null || true

  # Wait for readiness (up to 15 seconds)
  for i in {1..15}; do
    if "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$PG_PORT" -q 2>/dev/null; then
      log_ok "PostgreSQL started (port $PG_PORT)"
      break
    fi
    if [ $i -eq 15 ]; then
      log_error "PostgreSQL failed to start. Check $HPC_LOGS_DIR/postgres.log"
      exit 1
    fi
    sleep 1
  done
fi
echo ""

# --- Start Redis ---
log_info "Starting Redis on port $REDIS_PORT..."

# Locate Redis binary — handle conda/multiple install locations
REDIS_BIN=""
if [ -x "$HPC_BIN_DIR/redis-server" ]; then
  REDIS_BIN="$HPC_BIN_DIR/redis-server"
elif [ -x "${CONDA_PREFIX:-}/bin/redis-server" ]; then
  REDIS_BIN="${CONDA_PREFIX}/bin/redis-server"
elif command -v redis-server &>/dev/null; then
  REDIS_BIN="$(command -v redis-server)"
fi

if [ -z "$REDIS_BIN" ]; then
  log_error "redis-server binary not found. Run hpc/setup.sh first."
  exit 1
fi

if [ -f "$REDIS_PID_FILE" ] && kill -0 "$(cat "$REDIS_PID_FILE")" 2>/dev/null; then
  log_info "Redis already running (PID $(cat "$REDIS_PID_FILE"))"
else
  if ! check_port_free "$REDIS_PORT"; then
    log_error "Port $REDIS_PORT is already in use!"
    exit 1
  fi

  mkdir -p "$(dirname "$REDIS_PID_FILE")"

  "$REDIS_BIN" \
    --port "$REDIS_PORT" \
    --daemonize yes \
    --pidfile "$REDIS_PID_FILE" \
    --logfile "$HPC_LOGS_DIR/redis.log" \
    --dir "$REDIS_DATA_DIR" \
    --appendonly yes \
    --appendfilename appendonly.aof > /dev/null 2>&1

  # Wait for readiness (up to 10 seconds) — use redis-cli from same location as redis-server
  REDIS_CLI="${REDIS_BIN%/*}/redis-cli"
  for i in {1..10}; do
    if "$REDIS_CLI" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
      log_ok "Redis started (port $REDIS_PORT)"
      break
    fi
    if [ $i -eq 10 ]; then
      log_error "Redis failed to start. Check $HPC_LOGS_DIR/redis.log"
      exit 1
    fi
    sleep 1
  done
fi
echo ""

# --- Start MinIO ---
log_info "Starting MinIO on port $MINIO_PORT (console $MINIO_CONSOLE_PORT)..."

if [ -f "$MINIO_PID_FILE" ] && kill -0 "$(cat "$MINIO_PID_FILE")" 2>/dev/null; then
  log_info "MinIO already running (PID $(cat "$MINIO_PID_FILE"))"
else
  if ! check_port_free "$MINIO_PORT"; then
    log_error "Port $MINIO_PORT is already in use!"
    exit 1
  fi

  if ! check_port_free "$MINIO_CONSOLE_PORT"; then
    log_error "Port $MINIO_CONSOLE_PORT is already in use!"
    exit 1
  fi

  export MINIO_ROOT_USER="$MINIO_ROOT_USER"
  export MINIO_ROOT_PASSWORD="$MINIO_ROOT_PASSWORD"

  nohup "$HPC_BIN_DIR/minio" server "$MINIO_DATA_DIR" \
    --address "127.0.0.1:$MINIO_PORT" \
    --console-address "127.0.0.1:$MINIO_CONSOLE_PORT" \
    > "$HPC_LOGS_DIR/minio.log" 2>&1 &
  MINIO_PID=$!
  echo "$MINIO_PID" > "$MINIO_PID_FILE"

  # Wait for readiness (up to 20 seconds)
  for i in {1..20}; do
    if curl -sf "http://127.0.0.1:$MINIO_PORT/minio/health/live" &>/dev/null; then
      log_ok "MinIO started (port $MINIO_PORT)"
      break
    fi
    if [ $i -eq 20 ]; then
      log_error "MinIO failed to start. Check $HPC_LOGS_DIR/minio.log"
      exit 1
    fi
    sleep 1
  done
fi
echo ""

# --- Summary ---
log_ok "=== All Services Running ==="
echo ""
echo "PostgreSQL   : 127.0.0.1:$PG_PORT  (db=$PG_DB, user=$PG_USER)"
echo "Redis        : 127.0.0.1:$REDIS_PORT"
echo "MinIO API    : http://127.0.0.1:$MINIO_PORT"
echo "MinIO Console: http://127.0.0.1:$MINIO_CONSOLE_PORT  (user: $MINIO_ROOT_USER)"
echo ""
echo "Next steps (each in a separate terminal, with .venv active):"
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
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:4200"
echo ""
echo "To stop all services, run: ./hpc/stop.sh"
