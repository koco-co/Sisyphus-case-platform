#!/usr/bin/env bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
section() { echo -e "\n${BLUE}━━━ $* ━━━${NC}"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

section "1. Checking dependencies"

command -v uv     >/dev/null 2>&1 || error "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
command -v bun    >/dev/null 2>&1 || error "bun not found. Install: curl -fsSL https://bun.sh/install | bash"
command -v docker >/dev/null 2>&1 || error "docker not found. Install Docker Desktop from https://docker.com"
docker compose version >/dev/null 2>&1 || error "docker compose not found. Upgrade Docker Desktop."

info "uv:     $(uv --version)"
info "bun:    $(bun --version)"
info "docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"

section "2. Port availability check"

for port in 5432 6379 6333 9000 8000 3000; do
  if lsof -i :"$port" >/dev/null 2>&1; then
    warn "Port $port is already in use — may cause conflicts"
  fi
done

section "3. Environment configuration"

if [ ! -f "$PROJECT_DIR/.env" ]; then
  info "Copying .env.example → .env"
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  warn "Please edit .env to set OPENAI_API_KEY (optional if using Ollama)"
else
  info ".env already exists, skipping copy"
fi

section "4. Installing dependencies"

info "Installing backend dependencies..."
cd "$PROJECT_DIR/backend" && uv sync --all-extras

info "Installing frontend dependencies..."
cd "$PROJECT_DIR/frontend" && bun install

section "5. Starting Docker infrastructure"

info "Starting postgres, redis, qdrant, minio..."
cd "$PROJECT_DIR"
docker compose -f docker/docker-compose.yml up -d

info "Waiting for PostgreSQL to be ready..."
RETRIES=30
until docker compose -f docker/docker-compose.yml exec -T postgres pg_isready -U postgres >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  if [ $RETRIES -eq 0 ]; then
    error "PostgreSQL did not become ready in time"
  fi
  sleep 1
done
info "PostgreSQL is ready"

info "Waiting for Redis to be ready..."
RETRIES=15
until docker compose -f docker/docker-compose.yml exec -T redis redis-cli ping >/dev/null 2>&1; do
  RETRIES=$((RETRIES - 1))
  [ $RETRIES -eq 0 ] && error "Redis did not become ready in time"
  sleep 1
done
info "Redis is ready"

section "6. Database initialization"

info "Running Alembic migrations..."
cd "$PROJECT_DIR/backend" && uv run alembic upgrade head

info "Seeding database..."
cd "$PROJECT_DIR/backend" && uv run python scripts/seed.py

section "7. Starting development servers"

info "Starting backend (uvicorn) in background..."
cd "$PROJECT_DIR/backend"
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

info "Starting Celery worker in background..."
uv run celery -A app.worker.celery_app worker --loglevel=info &
CELERY_PID=$!

# Cleanup on exit
cleanup() {
  echo ""
  info "Shutting down..."
  kill "$BACKEND_PID" "$CELERY_PID" 2>/dev/null || true
  info "Done. Run 'docker compose -f docker/docker-compose.yml down' to stop infrastructure."
}
trap cleanup EXIT INT TERM

# Wait for backend to start
sleep 2

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Sisyphus Case Platform — Dev Environment Ready${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "  Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  MinIO:     ${BLUE}http://localhost:9001${NC}  (minioadmin / minioadmin)"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

info "Starting frontend (Ctrl+C to stop all servers)..."
cd "$PROJECT_DIR/frontend" && bun dev
