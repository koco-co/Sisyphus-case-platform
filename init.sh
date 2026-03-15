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
COMPOSE_PROJECT_FILE="$PROJECT_DIR/.compose-project-name"

# ─── PATH: include common install locations for uv and bun ────────────────────
export PATH="$HOME/.bun/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# ─── Docker helper functions ──────────────────────────────────────────────────

# Check if Docker daemon is responsive
is_docker_ready() {
  docker info >/dev/null 2>&1
}

# Wait for Docker daemon to be ready (with retries)
wait_for_docker() {
  local max_retries=${1:-60}
  local retry_interval=${2:-1}

  if is_docker_ready; then
    return 0
  fi

  warn "Docker daemon not responding — waiting..."
  local count=0
  until is_docker_ready; do
    count=$((count + 1))
    if [ $count -ge $max_retries ]; then
      return 1
    fi
    printf '.'
    sleep $retry_interval
  done
  echo ""
  return 0
}

# Ensure Docker daemon is running (start if needed on macOS)
ensure_docker_running() {
  if is_docker_ready; then
    return 0
  fi

  warn "Docker daemon not running — attempting to start Docker Desktop..."

  # Try to start Docker Desktop on macOS
  if [[ "$(uname)" == "Darwin" ]]; then
    if open -a Docker 2>/dev/null; then
      info "Waiting for Docker daemon to be ready (up to 90s)..."
      if wait_for_docker 90 1; then
        success "Docker daemon is ready"
        return 0
      fi
    fi
  fi

  # Try to start Docker service on Linux
  if [[ "$(uname)" == "Linux" ]]; then
    if command -v systemctl >/dev/null 2>&1; then
      sudo systemctl start docker 2>/dev/null || true
      if wait_for_docker 30 1; then
        success "Docker daemon is ready"
        return 0
      fi
    fi
  fi

  error "Docker daemon is not running. Please start Docker Desktop manually and retry."
}

# Pull Docker image with retry
pull_docker_image() {
  local image=$1
  local max_retries=${2:-3}
  local retry=0

  while [ $retry -lt $max_retries ]; do
    if docker pull "$image" 2>/dev/null; then
      return 0
    fi
    retry=$((retry + 1))
    if [ $retry -lt $max_retries ]; then
      warn "Failed to pull $image, retrying ($retry/$max_retries)..."
      sleep 2
    fi
  done
  return 1
}

# Docker compose up with retry
docker_compose_up() {
  local project_name=$1
  local compose_file=$2
  local max_retries=${3:-3}
  local retry=0

  while [ $retry -lt $max_retries ]; do
    # Verify Docker is still responsive before each attempt
    if ! is_docker_ready; then
      warn "Docker daemon became unresponsive, waiting..."
      if ! wait_for_docker 30 1; then
        error "Docker daemon is not responding. Please check Docker Desktop."
      fi
    fi

    if docker compose -p "$project_name" -f "$compose_file" up -d 2>&1; then
      return 0
    fi

    retry=$((retry + 1))
    if [ $retry -lt $max_retries ]; then
      warn "docker compose up failed, retrying ($retry/$max_retries) in 3 seconds..."
      sleep 3
    fi
  done
  return 1
}

# ─── Section 1: Auto-install uv and bun ───────────────────────────────────────
section "1. Checking & installing dependencies"

# ── uv ──
if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found — installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv >/dev/null 2>&1; then
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
docker compose version >/dev/null 2>&1 || error "docker compose not found. Upgrade Docker Desktop to v2+."

# Initial Docker check
ensure_docker_running
success "docker: $(docker --version | awk '{print $3}' | tr -d ',')"

# ─── Section 2: Clear ports ────────────────────────────────────────────────────
section "2. Clearing ports"

# Ensure Docker is still responsive before operations
ensure_docker_running

# Stop previous run's compose project (if any)
if [ -f "$COMPOSE_PROJECT_FILE" ]; then
  OLD_PROJECT=$(cat "$COMPOSE_PROJECT_FILE" 2>/dev/null)
  if [ -n "$OLD_PROJECT" ]; then
    info "Stopping previous Docker Compose project..."
    docker compose -p "$OLD_PROJECT" -f "$PROJECT_DIR/docker/docker-compose.yml" down 2>/dev/null || true
    success "Previous containers stopped (or already gone)"
  fi
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

# ─── Run command with timeout (portable, no GNU timeout) ──────────────────────
run_with_timeout() {
  local timeout_sec=$1
  shift
  "$@" & local pid=$!
  local i=0
  while kill -0 "$pid" 2>/dev/null && [ $i -lt "$timeout_sec" ]; do
    sleep 1
    i=$((i + 1))
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
    return 124
  fi
  wait "$pid"
  return $?
}

# ─── Section 4: Install dependencies ──────────────────────────────────────────
section "4. Installing dependencies"

info "Installing backend dependencies (uv sync)..."
(cd "$PROJECT_DIR/backend" && uv sync --all-extras)
success "Backend dependencies installed"

info "Installing frontend dependencies (bun install)..."
BUN_INSTALL_OK=0
if [ -n "${BUN_REGISTRY:-}" ]; then
  (cd "$PROJECT_DIR/frontend" && bun config set registry "$BUN_REGISTRY" && bun install) && BUN_INSTALL_OK=1
else
  (cd "$PROJECT_DIR/frontend" && run_with_timeout 120 bun install) && BUN_INSTALL_OK=1
fi
if [ "$BUN_INSTALL_OK" -eq 0 ]; then
  warn "bun install timed out or failed — retrying with npmmirror registry..."
  (cd "$PROJECT_DIR/frontend" && bun config set registry https://registry.npmmirror.com && bun install) || error "Frontend install failed. Run: cd frontend && bun install"
fi
success "Frontend dependencies installed"

# ─── Section 5: Start Docker infrastructure ───────────────────────────────────
section "5. Starting Docker infrastructure"

# Re-verify Docker is responsive before starting containers
ensure_docker_running

# Pre-pull images to avoid timeout during compose up
info "Pre-pulling Docker images (this may take a moment on first run)..."
IMAGES=("postgres:16-alpine" "redis:7-alpine" "qdrant/qdrant:latest" "minio/minio:latest")
for img in "${IMAGES[@]}"; do
  if ! docker image inspect "$img" >/dev/null 2>&1; then
    info "Pulling $img..."
    if ! pull_docker_image "$img" 3; then
      warn "Failed to pull $img, will retry during compose up"
    fi
  else
    success "$img already exists locally"
  fi
done

# Use a new project name every run
COMPOSE_PROJECT_NAME="sisyphus_$(date +%s)_$$"
echo "$COMPOSE_PROJECT_NAME" > "$COMPOSE_PROJECT_FILE"

info "Starting postgres, redis, qdrant, minio (project: $COMPOSE_PROJECT_NAME)..."

# Docker compose up with retry mechanism
if ! docker_compose_up "$COMPOSE_PROJECT_NAME" "$PROJECT_DIR/docker/docker-compose.yml" 3; then
  error "Failed to start Docker containers after 3 attempts. Check Docker logs for details."
fi

success "Docker containers started"

# ── Wait for PostgreSQL ──
info "Waiting for PostgreSQL..."
RETRIES=60
until docker compose -p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker/docker-compose.yml" exec -T postgres \
    pg_isready -U postgres >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  if [ $RETRIES -eq 0 ]; then
    # Show container logs for debugging
    warn "PostgreSQL container logs:"
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker/docker-compose.yml" logs postgres --tail=20 2>&1 | sed 's/^/  /'
    error "PostgreSQL did not become ready in time"
  fi
  printf '.'
  sleep 1
done
echo ""
success "PostgreSQL is ready"

# ── Wait for Redis ──
info "Waiting for Redis..."
RETRIES=30
until docker compose -p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker/docker-compose.yml" exec -T redis \
    redis-cli ping >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  if [ $RETRIES -eq 0 ]; then
    warn "Redis container logs:"
    docker compose -p "$COMPOSE_PROJECT_NAME" -f "$PROJECT_DIR/docker/docker-compose.yml" logs redis --tail=10 2>&1 | sed 's/^/  /'
    error "Redis did not become ready in time"
  fi
  printf '.'
  sleep 1
done
echo ""
success "Redis is ready"

# ─── Section 6: Database initialization ───────────────────────────────────────
section "6. Database initialization"

info "Running Alembic migrations..."
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
  info "Infrastructure still running. To stop: docker compose -p $COMPOSE_PROJECT_NAME -f docker/docker-compose.yml down"
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
