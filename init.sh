#!/usr/bin/env bash
set -euo pipefail

# ─── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
section() { echo -e "\n${BLUE}━━━ $* ━━━${NC}"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── PATH: include common install locations for uv and bun ────────────────────
export PATH="$HOME/.bun/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# ─── Section 1: Auto-install uv and bun ───────────────────────────────────────
section "1. Checking & installing dependencies"

# ── uv ──
if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found — installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installs to ~/.local/bin or ~/.cargo/bin
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
    # Try sourcing the env script if it exists
    [ -f "$HOME/.local/bin/env" ] && source "$HOME/.local/bin/env"
    [ -f "$HOME/.cargo/env" ]     && source "$HOME/.cargo/env"
  fi
  command -v uv >/dev/null 2>&1 || error "uv installation failed. Please install manually: https://docs.astral.sh/uv"
  success "uv installed: $(uv --version)"
else
  success "uv: $(uv --version)"
fi

# ── bun ──
if ! command -v bun >/dev/null 2>&1; then
  warn "bun not found — installing..."
  curl -fsSL https://bun.sh/install | bash
  export PATH="$HOME/.bun/bin:$PATH"
  command -v bun >/dev/null 2>&1 || error "bun installation failed. Please install manually: https://bun.sh"
  success "bun installed: $(bun --version)"
else
  success "bun: $(bun --version)"
fi

# ── docker ──
command -v docker >/dev/null 2>&1 || error "docker not found. Install Docker Desktop: https://docker.com/get-started"
docker compose version >/dev/null 2>&1  || error "docker compose not found. Upgrade Docker Desktop to v2+."
# Check if Docker daemon is running; if not, try to start Docker Desktop (macOS)
if ! docker info >/dev/null 2>&1; then
  warn "Docker daemon not running — attempting to start Docker Desktop..."
  if [[ "$(uname)" == "Darwin" ]] && open -a Docker 2>/dev/null; then
    info "Waiting for Docker daemon to be ready (up to 60s)..."
    DOCKER_RETRIES=60
    until docker info >/dev/null 2>&1; do
      DOCKER_RETRIES=$((DOCKER_RETRIES - 1))
      [ $DOCKER_RETRIES -eq 0 ] && error "Docker daemon did not start in time. Please start Docker Desktop manually."
      printf '.'
      sleep 1
    done
    echo ""
    success "Docker daemon is ready"
  else
    error "Docker daemon is not running. Please start Docker Desktop and retry."
  fi
fi
success "docker: $(docker --version | awk '{print $3}' | tr -d ',')"

# ─── Section 2: Clear ports ────────────────────────────────────────────────────
section "2. Clearing ports"

# Stop existing Docker infrastructure first (prevents killing Docker's own proxy)
if docker info >/dev/null 2>&1 && \
   docker compose -f "$PROJECT_DIR/docker/docker-compose.yml" ps -q 2>/dev/null | grep -q .; then
  info "Stopping existing Docker containers..."
  docker compose -f "$PROJECT_DIR/docker/docker-compose.yml" down 2>/dev/null || true
  success "Docker containers stopped"
fi

kill_port() {
  local port=$1
  local label=${2:-"port $1"}
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    warn "Port $port in use (PIDs: $pids) — killing for $label..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 0.5
    success "Port $port cleared"
  else
    success "Port $port is free"
  fi
}

kill_port 5432 "PostgreSQL"
kill_port 6379 "Redis"
kill_port 6333 "Qdrant"
kill_port 9000 "MinIO"
kill_port 9001 "MinIO console"
kill_port 8000 "Backend API"
kill_port 3000 "Frontend"

# ─── Section 3: Environment configuration ─────────────────────────────────────
section "3. Environment configuration"

if [ ! -f "$PROJECT_DIR/.env" ]; then
  info "Copying .env.example → .env"
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  warn "Edit .env to set OPENAI_API_KEY (skip for Ollama mode)"
else
  success ".env already exists"
fi

# ─── Section 4: Install dependencies ──────────────────────────────────────────
section "4. Installing dependencies"

info "Installing backend dependencies (uv sync)..."
(cd "$PROJECT_DIR/backend" && uv sync --all-extras)
success "Backend dependencies installed"

info "Installing frontend dependencies (bun install)..."
(cd "$PROJECT_DIR/frontend" && bun install)
success "Frontend dependencies installed"

# ─── Section 5: Start Docker infrastructure ───────────────────────────────────
section "5. Starting Docker infrastructure"

info "Starting postgres, redis, qdrant, minio..."
docker compose -f "$PROJECT_DIR/docker/docker-compose.yml" up -d

# ── Wait for PostgreSQL ──
info "Waiting for PostgreSQL..."
RETRIES=60
until docker compose -f "$PROJECT_DIR/docker/docker-compose.yml" exec -T postgres \
    pg_isready -U postgres >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  [ $RETRIES -eq 0 ] && error "PostgreSQL did not become ready in time"
  printf '.'
  sleep 1
done
echo ""
success "PostgreSQL is ready"

# ── Wait for Redis ──
info "Waiting for Redis..."
RETRIES=30
until docker compose -f "$PROJECT_DIR/docker/docker-compose.yml" exec -T redis \
    redis-cli ping >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  [ $RETRIES -eq 0 ] && error "Redis did not become ready in time"
  printf '.'
  sleep 1
done
echo ""
success "Redis is ready"

# ─── Section 6: Database initialization ───────────────────────────────────────
section "6. Database initialization"

info "Running Alembic migrations..."
# Auto-generate initial migration if versions/ is empty
VERSIONS_DIR="$PROJECT_DIR/backend/alembic/versions"
if [ -d "$VERSIONS_DIR" ] && [ -z "$(ls -A "$VERSIONS_DIR" 2>/dev/null)" ]; then
  info "No migration files found — generating initial schema..."
  (cd "$PROJECT_DIR/backend" && uv run alembic revision --autogenerate -m "initial schema")
fi
(cd "$PROJECT_DIR/backend" && uv run alembic upgrade head)
success "Migrations applied"

info "Seeding database..."
(cd "$PROJECT_DIR/backend" && uv run python scripts/seed.py)
success "Seed complete"

# ─── Section 7: Start development servers ─────────────────────────────────────
section "7. Starting development servers"

# ── Backend ──
info "Starting backend (uvicorn --reload :8000)..."
(cd "$PROJECT_DIR/backend" && uv run uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

# ── Celery ──
info "Starting Celery worker..."
(cd "$PROJECT_DIR/backend" && uv run celery -A app.worker.celery_app worker --loglevel=info) &
CELERY_PID=$!

# ── Cleanup trap ──
cleanup() {
  echo ""
  info "Shutting down..."
  kill "$BACKEND_PID" "$CELERY_PID" 2>/dev/null || true
  info "Infrastructure still running. To stop: docker compose -f docker/docker-compose.yml down"
}
trap cleanup EXIT INT TERM

# ── Wait for backend to start ──
info "Waiting for backend API to be ready..."
RETRIES=20
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  if [ $RETRIES -eq 0 ]; then
    warn "Backend did not start in time — check logs above"
    break
  fi
  sleep 1
done
[ $RETRIES -gt 0 ] && success "Backend API is ready"

# ── Print ready banner ──
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Sisyphus Case Platform — Development Environment Ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Frontend   →  ${BLUE}http://localhost:3000${NC}"
echo -e "  Backend    →  ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs   →  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  MinIO UI   →  ${BLUE}http://localhost:9001${NC}  (minioadmin / minioadmin)"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all servers"
echo ""

# ── Start frontend (foreground, keeps script alive) ──
info "Starting frontend (bun dev :3000)..."
(cd "$PROJECT_DIR/frontend" && bun dev)
