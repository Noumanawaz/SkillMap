# Deployment Guide for Coolify

This guide will help you deploy SkillMap AI to Coolify using pre-built Docker images.

## Prerequisites

1. Docker Hub account (username: `nomi2k4`)
2. A Coolify instance set up
3. OpenAI API key (for AI features)

## Quick Deployment Steps

### Option 1: Build and Push Images Manually

1. **Build and push Docker images to Docker Hub:**

```bash
# Make sure you're logged into Docker Hub
docker login

# Run the build script
./build-and-push.sh
```

This will build and push both backend and frontend images to `nomi2k4/skillmap-backend:latest` and `nomi2k4/skillmap-frontend:latest`.

### Option 2: Automatic Builds with GitHub Actions

1. **Set up GitHub Secrets:**
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `DOCKER_USERNAME`: `nomi2k4`
     - `DOCKER_PASSWORD`: Your Docker Hub password or access token

2. **Push to GitHub:**
   - The GitHub Actions workflow will automatically build and push images on every push to `main` branch

### 3. Deploy in Coolify

1. **Create New Resource** in Coolify
2. **Select "Docker Compose Empty"** (under Docker Based section)
3. **Paste your docker-compose.yml:**
   - The file is already configured to use pre-built images: `nomi2k4/skillmap-backend:latest` and `nomi2k4/skillmap-frontend:latest`

4. **Configure Environment Variables:**
   Click on "Environment Variables" and add:
   
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   DATABASE_URL=postgresql://user:password@postgres:5432/skillmap
   ```
   
   **Note**: For production, it's recommended to use PostgreSQL. Coolify can create a PostgreSQL database for you.

5. **Deploy**:
   - Click "Deploy" and wait for the services to start
   - No build time needed since images are pre-built!

### 4. Database Setup (PostgreSQL Recommended)

If using PostgreSQL:

1. In Coolify, create a PostgreSQL database service
2. Note the connection details
3. Update `DATABASE_URL` in your environment variables:
   ```
   DATABASE_URL=postgresql://user:password@postgres-service:5432/skillmap
   ```

### 5. Access Your Application

Once deployed:
- Frontend will be available at your Coolify domain (port 80)
- Backend API will be available at the same domain (proxied through nginx)
- API docs available at: `https://your-domain.com/docs`

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key for AI features |
| `DATABASE_URL` | No | `sqlite:///./skillmap.db` | Database connection string |
| `OPENAI_MODEL` | No | `gpt-3.5-turbo` | OpenAI model to use |
| `VECTOR_DB_BACKEND` | No | `in_memory` | Vector database backend |

## Architecture

The deployment uses Docker Compose with two services:

- **Backend**: FastAPI application on port 8000
- **Frontend**: Nginx serving React build, proxying API requests to backend

## Troubleshooting

### Build Fails

- Check that all files are committed to GitHub
- Verify Dockerfile paths are correct
- Check Coolify logs for specific errors

### Backend Not Starting

- Verify `OPENAI_API_KEY` is set correctly
- Check database connection if using PostgreSQL
- Review backend logs in Coolify

### Frontend Shows Blank Page

- Check browser console for errors
- Verify nginx is proxying correctly
- Ensure backend is healthy (check `/health` endpoint)

### Database Issues

- For SQLite: Ensure volume mount is working
- For PostgreSQL: Verify connection string and network connectivity

## Updating the Application

### Manual Update:
1. Make your code changes
2. Build and push new images: `./build-and-push.sh`
3. In Coolify, restart the services or pull the latest images

### Automatic Update (with GitHub Actions):
1. Push changes to GitHub
2. GitHub Actions automatically builds and pushes new images
3. In Coolify, restart services to pull the latest images
4. (Optional) Set up Coolify webhooks to auto-restart on image updates

## Health Checks

Both services include health checks:
- Backend: `http://backend:8000/health`
- Frontend: Nginx serves static files

## Support

For issues specific to:
- **Coolify**: Check [Coolify Documentation](https://coolify.io/docs)
- **Application**: Check application logs in Coolify dashboard

