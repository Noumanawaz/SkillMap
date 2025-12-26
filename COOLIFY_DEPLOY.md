# 🚀 Coolify Deployment - Quick Start

Deploy SkillMap AI to Coolify in 3 simple steps!

## Step 1: Push to GitHub

```bash
git add .
git commit -m "Add Docker deployment configuration"
git push origin main
```

## Step 2: Setup in Coolify

1. **Go to Coolify Dashboard** → Create New Resource
2. **Select "Docker Compose"**
3. **Connect GitHub**:
   - Authorize Coolify
   - Select your repository
   - Select branch (usually `main`)
4. **Add Environment Variables**:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
   (Optional: `DATABASE_URL` for PostgreSQL)
5. **Click Deploy** 🎉

## Step 3: Done!

Coolify will automatically:
- ✅ Build Docker images
- ✅ Start both services (backend + frontend)
- ✅ Set up networking
- ✅ Enable health checks

Your app will be live at your Coolify domain!

---

## 📋 What Gets Deployed?

- **Backend**: FastAPI on port 8000 (internal)
- **Frontend**: Nginx on port 80 (public)
- **Database**: SQLite by default (or PostgreSQL if configured)

## 🔧 Environment Variables

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key

**Optional:**
- `DATABASE_URL` - PostgreSQL connection (recommended for production)
- `OPENAI_MODEL` - Model to use (default: `gpt-3.5-turbo`)
- `VECTOR_DB_BACKEND` - Vector DB backend (default: `in_memory`)

## 📚 More Details

See `DEPLOYMENT.md` for detailed documentation.

