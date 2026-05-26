#!/usr/bin/env bash
# HPC Setup — Initialize PostgreSQL, Redis, and MinIO (first-time only)
# This script is idempotent — safe to re-run

set -euo pipefail
source "$(dirname "$0")/config.sh"

log_info "=== Termo Fácil HPC Setup ==="
log_info "Project root: $PROJECT_ROOT"
log_info "Data directory: $HPC_DATA_DIR"
log_info ""

# --- Step 1: Create directory skeleton ---
log_info "Creating directory structure..."
mkdir -p "$HPC_BIN_DIR" "$PG_DATA_DIR" "$REDIS_DATA_DIR" "$MINIO_DATA_DIR" "$HPC_LOGS_DIR"
log_ok "Directories ready"
echo ""

# --- Step 2: PostgreSQL ---
log_info "=== PostgreSQL ==="

if ! find_postgres; then
  log_info ""
  read -p "Install PostgreSQL via conda? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ! command -v conda &>/dev/null; then
      log_error "conda not found. Install conda or PostgreSQL manually."
      exit 1
    fi
    log_info "Installing PostgreSQL via conda..."
    conda install -y -c conda-forge postgresql
    if ! find_postgres; then
      log_error "PostgreSQL installation failed"
      exit 1
    fi
  else
    log_error "Cannot proceed without PostgreSQL. Install via conda or module system."
    exit 1
  fi
fi

log_ok "PostgreSQL found at: $PG_BIN_DIR"
echo ""

# --- Step 3: Initialize PostgreSQL cluster (idempotent) ---
if [ -f "$PG_DATA_DIR/PG_VERSION" ]; then
  log_info "PostgreSQL cluster already initialized, skipping initdb"
else
  log_info "Initializing PostgreSQL cluster in $PG_DATA_DIR..."
  "$PG_BIN_DIR/initdb" \
    -D "$PG_DATA_DIR" \
    --username=postgres \
    --auth=trust \
    --encoding=UTF8 \
    --locale=C \
    2>&1 | grep -v "^$" || true

  log_info "Configuring postgresql.conf for user-space operation..."
  cat >> "$PG_DATA_DIR/postgresql.conf" << CONFIG_EOF

# HPC user-space configuration
listen_addresses = '127.0.0.1'
port = $PG_PORT
unix_socket_directories = '$PG_DATA_DIR'
CONFIG_EOF

  log_ok "PostgreSQL cluster initialized"
fi
echo ""

# --- Step 4: Start PostgreSQL temporarily for setup ---
log_info "Starting PostgreSQL temporarily for initialization..."
"$PG_BIN_DIR/pg_ctl" -D "$PG_DATA_DIR" \
  -l "$HPC_LOGS_DIR/postgres.log" \
  start &>/dev/null || true

# Wait for PostgreSQL to be ready (up to 30 seconds)
for i in {1..30}; do
  if "$PG_BIN_DIR/pg_isready" -h 127.0.0.1 -p "$PG_PORT" -U postgres &>/dev/null; then
    log_ok "PostgreSQL is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    log_error "PostgreSQL failed to start. Check $HPC_LOGS_DIR/postgres.log"
    exit 1
  fi
  sleep 1
done
echo ""

# --- Step 5: Create database user and schema (idempotent) ---
PSQL="$PG_BIN_DIR/psql -h 127.0.0.1 -p $PG_PORT -U postgres"

log_info "Creating database user '$PG_USER' (if not exists)..."
$PSQL -tc "DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$PG_USER') THEN
    CREATE ROLE $PG_USER WITH LOGIN PASSWORD '$PG_PASSWORD';
  END IF;
END \$\$;" 2>&1 | grep -v "^$" || true
log_ok "User ready"

log_info "Creating database '$PG_DB' (if not exists)..."
if ! $PSQL -tc "SELECT 1 FROM pg_database WHERE datname='$PG_DB'" 2>/dev/null | grep -q 1; then
  $PSQL -c "CREATE DATABASE $PG_DB OWNER $PG_USER;" 2>&1 | grep -v "^$" || true
  log_ok "Database created"
else
  log_info "Database already exists"
fi
echo ""

# --- Step 6: Apply database schema (guarded against re-application) ---
log_info "Applying database schema..."
SCHEMA_COUNT=$($PSQL -d "$PG_DB" -tAc \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='delegacia'" 2>/dev/null || echo 0)

if [ "$SCHEMA_COUNT" -eq 0 ]; then
  log_info "Applying SQL schema from arquivos-projeto/modelo_bd.sql..."
  if $PSQL -d "$PG_DB" -f "$PROJECT_ROOT/arquivos-projeto/modelo_bd.sql" 2>&1 | tail -5; then
    log_ok "Schema applied"
  else
    log_error "Schema application failed"
    "$PG_BIN_DIR/pg_ctl" -D "$PG_DATA_DIR" stop 2>/dev/null || true
    exit 1
  fi
else
  log_info "Schema already applied, skipping"
fi
echo ""

# --- Step 7: Run Python seed script (idempotent) ---
log_info "Running database seed script..."
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
  log_info "Virtual environment activated"
fi

(
  cd "$PROJECT_ROOT/backend"
  if python scripts/seed_db.py 2>&1 | tail -10; then
    log_ok "Database seeded"
  else
    log_error "Seed script failed"
    exit 1
  fi
)
echo ""

# --- Step 8: Stop temporary PostgreSQL ---
log_info "Stopping PostgreSQL (will restart with hpc/start.sh)..."
"$PG_BIN_DIR/pg_ctl" -D "$PG_DATA_DIR" stop 2>/dev/null || true
log_ok "PostgreSQL stopped"
echo ""

# --- Step 9: Redis (locate or compile) ---
log_info "=== Redis ==="
if [ -x "$HPC_BIN_DIR/redis-server" ]; then
  log_info "Redis binary already present"
elif command -v redis-server &>/dev/null; then
  log_info "redis-server found in PATH, creating symlink..."
  ln -sf "$(command -v redis-server)" "$HPC_BIN_DIR/redis-server"
  ln -sf "$(command -v redis-cli)" "$HPC_BIN_DIR/redis-cli" || true
  log_ok "Redis linked"
elif command -v conda &>/dev/null; then
  log_info "Installing Redis via conda..."
  conda install -y -c conda-forge redis
  CONDA_REDIS="$(conda run -n base which redis-server)"
  ln -sf "$CONDA_REDIS" "$HPC_BIN_DIR/redis-server"
  CONDA_CLI="$(conda run -n base which redis-cli)" || true
  ln -sf "$CONDA_CLI" "$HPC_BIN_DIR/redis-cli" || true
  log_ok "Redis installed via conda"
else
  log_info "Compiling Redis from source (no sudo required)..."
  REDIS_VERSION="7.2.4"
  REDIS_SRC="$HPC_DATA_DIR/redis-src"

  if [ ! -d "$REDIS_SRC" ]; then
    curl -fsSL "https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz" -o /tmp/redis.tar.gz
    tar xzf /tmp/redis.tar.gz -C "$HPC_DATA_DIR/"
    mv "$HPC_DATA_DIR/redis-${REDIS_VERSION}" "$REDIS_SRC"
  fi

  make -C "$REDIS_SRC" -j"$(nproc)" &>/dev/null
  cp "$REDIS_SRC/src/redis-server" "$HPC_BIN_DIR/"
  cp "$REDIS_SRC/src/redis-cli" "$HPC_BIN_DIR/"
  log_ok "Redis compiled and installed to $HPC_BIN_DIR"
fi
echo ""

# --- Step 10: MinIO (download standalone binary) ---
log_info "=== MinIO ==="
if [ -x "$HPC_BIN_DIR/minio" ]; then
  log_info "MinIO binary already present"
else
  log_info "Downloading MinIO binary..."
  curl -fsSL "https://dl.min.io/server/minio/release/linux-amd64/minio" \
    -o "$HPC_BIN_DIR/minio"
  chmod +x "$HPC_BIN_DIR/minio"
  log_ok "MinIO downloaded and ready"
fi
echo ""

# --- Final summary ---
log_ok "=== Setup Complete ==="
echo ""
echo "Next step:"
echo "  ./hpc/start.sh"
echo ""
echo "Then run (each in a separate terminal, with .venv active):"
echo "  uvicorn app.main:app --reload --app-dir backend"
echo "  cd backend && celery -A app.core.celery_app worker --loglevel=info -P solo"
echo "  cd frontend && npm run start"
echo ""
echo "Note: Ollama must be installed separately (see CLAUDE.md)"
