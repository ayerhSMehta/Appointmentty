#!/bin/bash
set -e

cd "$(dirname "$0")/backend"

echo "🔧 Setting up Python virtual environment..."
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo "🚀 Starting backend on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
