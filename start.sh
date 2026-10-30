#!/usr/bin/env bash
# Starts the API (port 8001) and the web app (port 5173) together. Stop both with Ctrl+C.
#   ./start.sh            run
#   ./start.sh --test     run the backend tests instead
set -e
cd "$(dirname "$0")"

# ---- backend setup (first run only) ----
if [ ! -d backend/.venv ]; then
  echo "Setting up the backend (first run)..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env from the example. Add your NVIDIA keys there to turn on voice, translation and help."
fi

if [ "$1" = "--test" ]; then
  cd backend && .venv/bin/python -m pytest -q
  exit $?
fi

# ---- frontend setup (first run only) ----
if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend packages (first run)..."
  (cd frontend && npm install --silent)
fi

# ---- ports must be free ----
for p in 8001 5173; do
  if lsof -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $p is already in use (an old server is probably still running)."
    echo "Free both ports, then run this again:"
    echo "  lsof -tiTCP:8001 -sTCP:LISTEN | xargs kill; lsof -tiTCP:5173 -sTCP:LISTEN | xargs kill"
    exit 1
  fi
done

cleanup() { kill $API_PID $WEB_PID 2>/dev/null || true; }
trap cleanup EXIT INT TERM

echo "API  -> http://localhost:8001/health"
(cd backend && .venv/bin/python -m uvicorn app.main:app --port 8001) &
API_PID=$!

echo "Web  -> http://localhost:5173"
(cd frontend && npm run dev -- --host 127.0.0.1) &
WEB_PID=$!

wait
