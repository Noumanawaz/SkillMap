# 🚀 Quick Start - Build and Deploy

## Step 1: Build and Push Images to Docker Hub

```bash
# Make sure you're logged into Docker Hub
docker login

# Build and push both images
./build-and-push.sh
```

This will create:
- `nomi2k4/skillmap-backend:latest`
- `nomi2k4/skillmap-frontend:latest`

## Step 2: Deploy to Coolify

1. Go to Coolify → Create New Resource
2. Select **"Docker Compose Empty"** (under Docker Based)
3. Paste the contents of `docker-compose.yml`
4. Add environment variable: `OPENAI_API_KEY=sk-your-key`
5. Click Deploy! 🎉

## That's it!

Your app will be live in minutes. No build time in Coolify since images are pre-built!

---

## Optional: Auto-Build with GitHub Actions

1. Go to GitHub → Settings → Secrets → Actions
2. Add secrets:
   - `DOCKER_USERNAME`: `nomi2k4`
   - `DOCKER_PASSWORD`: Your Docker Hub password/token
3. Push to GitHub - images build automatically on every push!

