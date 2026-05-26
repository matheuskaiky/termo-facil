#!/usr/bin/env bash
# HPC Configuration — shared variables and utilities
# Sourced by all other hpc scripts

set -euo pipefail

# Resolve absolute paths (work from any directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Directory layout
HPC_BIN_DIR="$SCRIPT_DIR/bin"
HPC_DATA_DIR="$SCRIPT_DIR/.data"
HPC_LOGS_DIR="$SCRIPT_DIR/logs"

# Per-service data directories
PG_DATA_DIR="$HPC_DATA_DIR/postgres"
REDIS_DATA_DIR="$HPC_DATA_DIR/redis"
MINIO_DATA_DIR="$HPC_DATA_DIR/minio"

# PID files for process management
REDIS_PID_FILE="$HPC_DATA_DIR/redis/redis.pid"
MINIO_PID_FILE="$HPC_DATA_DIR/minio/minio.pid"

# Credentials — MUST match backend/.env exactly
PG_USER="termo_user"
PG_PASSWORD="termo_password"
PG_DB="termo_facil"
PG_PORT="5432"

REDIS_PORT="6379"

MINIO_PORT="9000"
MINIO_CONSOLE_PORT="9001"
MINIO_ROOT_USER="admin"
MINIO_ROOT_PASSWORD="adminpassword"

# PostgreSQL binary directory (set by find_postgres)
PG_BIN_DIR=""

# Logging with colors (graceful degradation if not a terminal)
log_info() {
  echo "[INFO] $*" >&2
}

log_ok() {
  if [ -t 2 ]; then
    echo -e "\033[0;32m[OK]\033[0m $*" >&2
  else
    echo "[OK] $*" >&2
  fi
}

log_warn() {
  if [ -t 2 ]; then
    echo -e "\033[0;33m[WARN]\033[0m $*" >&2
  else
    echo "[WARN] $*" >&2
  fi
}

log_error() {
  if [ -t 2 ]; then
    echo -e "\033[0;31m[ERROR]\033[0m $*" >&2
  else
    echo "[ERROR] $*" >&2
  fi
}

# Find PostgreSQL binaries
find_postgres() {
  # Try 1: Check if initdb is in PATH
  if command -v initdb &>/dev/null; then
    PG_BIN_DIR="$(dirname "$(command -v initdb)")"
    log_info "PostgreSQL found in PATH: $PG_BIN_DIR"
    return 0
  fi

  # Try 2: Check conda
  if command -v conda &>/dev/null; then
    CONDA_PG_BIN="$(conda run -n base which initdb 2>/dev/null)" || true
    if [ -n "$CONDA_PG_BIN" ]; then
      PG_BIN_DIR="$(dirname "$CONDA_PG_BIN")"
      log_info "PostgreSQL found via conda: $PG_BIN_DIR"
      return 0
    fi
  fi

  # Try 3: Check Environment Modules (common on HPC)
  if command -v module &>/dev/null || [ -f /etc/profile.d/modules.sh ]; then
    source /etc/profile.d/modules.sh 2>/dev/null || true
    if command -v module &>/dev/null; then
      module load postgresql 2>/dev/null || true
      if command -v initdb &>/dev/null; then
        PG_BIN_DIR="$(dirname "$(command -v initdb)")"
        log_info "PostgreSQL loaded via modules: $PG_BIN_DIR"
        return 0
      fi
    fi
  fi

  log_error "PostgreSQL binaries (initdb/pg_ctl) not found"
  cat >&2 << 'EOF'

Install PostgreSQL via one of these methods:
  1. conda: conda install -c conda-forge postgresql
  2. module: module load postgresql (then re-run this script)
  3. Manual: compile from source or download precompiled binary

EOF
  return 1
}

# Find Redis binary
find_redis() {
  # Try PATH first
  if command -v redis-server &>/dev/null; then
    echo "$(command -v redis-server)"
    return 0
  fi

  # Try HPC bin directory
  if [ -x "$HPC_BIN_DIR/redis-server" ]; then
    echo "$HPC_BIN_DIR/redis-server"
    return 0
  fi

  # Try conda
  if command -v conda &>/dev/null; then
    CONDA_REDIS="$(conda run -n base which redis-server 2>/dev/null)" || true
    if [ -n "$CONDA_REDIS" ]; then
      echo "$CONDA_REDIS"
      return 0
    fi
  fi

  log_error "redis-server not found. Run hpc/setup.sh to compile/install it."
  return 1
}

# Check if a port is free (uses ss or netstat)
check_port_free() {
  local PORT=$1
  if command -v ss &>/dev/null; then
    ! ss -tlnp 2>/dev/null | grep -q ":$PORT " && return 0
  elif command -v netstat &>/dev/null; then
    ! netstat -tlnp 2>/dev/null | grep -q ":$PORT " && return 0
  else
    # Fallback: try to connect
    ! timeout 1 bash -c "echo > /dev/tcp/127.0.0.1/$PORT" 2>/dev/null && return 0
  fi
  return 1
}
