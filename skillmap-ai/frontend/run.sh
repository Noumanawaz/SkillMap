#!/bin/bash
# Quick start script for SkillMap AI frontend

echo "🚀 Starting SkillMap AI Frontend..."

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "📥 Installing dependencies..."
    npm install
fi

# Run the dev server
echo "✅ Starting Vite dev server on http://localhost:5173"
echo ""
npm run dev

