# 🚀 Coolify Deployment - Quick Start

Deploy SkillMap AI to Coolify using pre-built Docker images!

## Step 1: Build and Push Docker Images

**Option A: Manual Build**
```bash
# Login to Docker Hub
docker login

# Build and push images
./build-and-push.sh
```

**Option B: Automatic Build (GitHub Actions)**
1. Set GitHub Secrets: `DOCKER_USERNAME` and `DOCKER_PASSWORD`
2. Push to GitHub - images build automatically!

## Step 2: Setup in Coolify

1. **Go to Coolify Dashboard** → Create New Resource
2. **Select "Docker Compose Empty"** (under Docker Based section)
3. **Paste docker-compose.yml**:
   - The file is already configured with images: `nomi2k4/skillmap-backend:latest` and `nomi2k4/skillmap-frontend:latest`
4. **Add Environment Variables**:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
   (Optional: `DATABASE_URL` for PostgreSQL)
5. **Click Deploy** 🎉

## Step 3: Done!

Coolify will:
- ✅ Pull pre-built Docker images (no build time!)
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

