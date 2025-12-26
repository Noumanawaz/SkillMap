#!/bin/bash
# Script to push SkillMap AI to GitHub

echo "🚀 Setting up GitHub repository..."
echo ""
echo "📋 INSTRUCTIONS:"
echo "1. Go to https://github.com/new"
echo "2. Create a new repository (e.g., 'skillmap-ai')"
echo "3. DO NOT initialize with README, .gitignore, or license"
echo "4. Copy the repository URL (e.g., https://github.com/yourusername/skillmap-ai.git)"
echo ""
read -p "Enter your GitHub repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

echo ""
echo "📤 Adding remote and pushing to GitHub..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
git branch -M main
git push -u origin main

echo ""
echo "✅ Done! Your code is now on GitHub."
echo "🔗 Repository: $REPO_URL"
echo ""
echo "Next steps:"
echo "1. Go to Coolify"
echo "2. Create new resource → Docker Compose"
echo "3. Connect to: $REPO_URL"
echo "4. Add OPENAI_API_KEY environment variable"
echo "5. Deploy! 🎉"

