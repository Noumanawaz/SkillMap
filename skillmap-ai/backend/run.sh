#!/bin/bash
# Quick start script for SkillMap AI backend

echo "🚀 Starting SkillMap AI Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env and add your OPENAI_API_KEY"
        echo "   Then run this script again."
        exit 1
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if virtualenv exists
if [ ! -d .venv ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtualenv
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check for OpenAI API key
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set in .env"
    echo "   The system will use fallback heuristics instead of AI."
fi

# Run the server
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

