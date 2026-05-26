#!/usr/bin/env bash
# HPC Stop — Gracefully stop PostgreSQL, Redis, and MinIO

set -euo pipefail
source "$(dirname "$0")/config.sh"

log_info "=== Stopping Termo Fácil HPC Services ==="
echo ""

SOMETHING_STOPPED=0

# --- Stop MinIO ---
if [ -f "$MINIO_PID_FILE" ]; then
  MINIO_PID=$(cat "$MINIO_PID_FILE")
  if kill -0 "$MINIO_PID" 2>/dev/null; then
    log_info "Stopping MinIO (PID $MINIO_PID)..."
    kill -SIGTERM "$MINIO_PID" 2>/dev/null || true

    # Wait up to 10 seconds for clean exit
    for i in {1..10}; do
      if ! kill -0 "$MINIO_PID" 2>/dev/null; then
        log_ok "MinIO stopped gracefully"
        SOMETHING_STOPPED=1
        break
      fi
      sleep 1
    done

    # Force kill if still running
    if kill -0 "$MINIO_PID" 2>/dev/null; then
      log_warn "MinIO did not stop gracefully, forcing..."
      kill -SIGKILL "$MINIO_PID" 2>/dev/null || true
      log_ok "MinIO force-killed"
      SOMETHING_STOPPED=1
    fi
  else
    log_warn "MinIO PID file exists but process is not running"
  fi
  rm -f "$MINIO_PID_FILE"
else
  log_info "MinIO not running (no PID file)"
fi
echo ""

# --- Stop Redis ---
if [ -f "$REDIS_PID_FILE" ]; then
  REDIS_PID=$(cat "$REDIS_PID_FILE")
  if kill -0 "$REDIS_PID" 2>/dev/null; then
    log_info "Stopping Redis (PID $REDIS_PID)..."

    # Try graceful shutdown using redis-cli (locate it dynamically)
    REDIS_CLI=""
    for candidate in "$HPC_BIN_DIR/redis-cli" "${CONDA_PREFIX:-}/bin/redis-cli" /usr/bin/redis-cli /usr/local/bin/redis-cli; do
      if [ -x "$candidate" ] 2>/dev/null; then
        REDIS_CLI="$candidate"
        break
      fi
    done

    if [ -n "$REDIS_CLI" ]; then
      "$REDIS_CLI" -p "$REDIS_PORT" SHUTDOWN NOSAVE 2>/dev/null || true
    else
      kill -SIGTERM "$REDIS_PID" 2>/dev/null || true
    fi

    # Wait up to 10 seconds for clean exit
    for i in {1..10}; do
      if ! kill -0 "$REDIS_PID" 2>/dev/null; then
        log_ok "Redis stopped gracefully"
        SOMETHING_STOPPED=1
        break
      fi
      sleep 1
    done

    # Force kill if still running
    if kill -0 "$REDIS_PID" 2>/dev/null; then
      log_warn "Redis did not stop gracefully, forcing..."
      kill -SIGKILL "$REDIS_PID" 2>/dev/null || true
      log_ok "Redis force-killed"
      SOMETHING_STOPPED=1
    fi
  else
    log_warn "Redis PID file exists but process is not running"
  fi
  rm -f "$REDIS_PID_FILE"
else
  log_info "Redis not running (no PID file)"
fi
echo ""

# --- Stop PostgreSQL ---
if find_postgres 2>/dev/null; then
  if "$PG_BIN_DIR/pg_ctl" -D "$PG_DATA_DIR" status &>/dev/null; then
    log_info "Stopping PostgreSQL..."
    "$PG_BIN_DIR/pg_ctl" -D "$PG_DATA_DIR" stop -m fast &>/dev/null
    log_ok "PostgreSQL stopped"
    SOMETHING_STOPPED=1
  else
    log_info "PostgreSQL not running"
  fi
else
  log_info "PostgreSQL binaries not found"
fi
echo ""

if [ $SOMETHING_STOPPED -eq 1 ]; then
  log_ok "=== All Services Stopped ==="
else
  log_warn "No services were running"
fi
