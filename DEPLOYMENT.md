# Deployment Guide for Coolify

This guide will help you deploy SkillMap AI to Coolify with a single-click deployment.

## Prerequisites

1. A GitHub repository with your code
2. A Coolify instance set up
3. OpenAI API key (for AI features)

## Quick Deployment Steps

### 1. Push to GitHub

Make sure all files are committed and pushed to your GitHub repository:

```bash
git add .
git commit -m "Add Docker deployment files"
git push origin main
```

### 2. Setup in Coolify

1. **Create New Resource** in Coolify
2. **Select "Docker Compose"** as the deployment type
3. **Connect GitHub Repository**:
   - Authorize Coolify to access your GitHub
   - Select your repository
   - Select the branch (usually `main` or `master`)

4. **Configure Environment Variables**:
   Click on "Environment Variables" and add:
   
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   DATABASE_URL=postgresql://user:password@postgres:5432/skillmap
   ```
   
   **Note**: For production, it's recommended to use PostgreSQL. Coolify can create a PostgreSQL database for you.

5. **Deploy**:
   - Coolify will automatically detect the `docker-compose.yml` file
   - Click "Deploy" and wait for the build to complete

### 3. Database Setup (PostgreSQL Recommended)

If using PostgreSQL:

1. In Coolify, create a PostgreSQL database service
2. Note the connection details
3. Update `DATABASE_URL` in your environment variables:
   ```
   DATABASE_URL=postgresql://user:password@postgres-service:5432/skillmap
   ```

### 4. Access Your Application

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

Simply push new changes to GitHub, and Coolify will automatically:
1. Pull the latest code
2. Rebuild Docker images
3. Redeploy the services

## Health Checks

Both services include health checks:
- Backend: `http://backend:8000/health`
- Frontend: Nginx serves static files

## Support

For issues specific to:
- **Coolify**: Check [Coolify Documentation](https://coolify.io/docs)
- **Application**: Check application logs in Coolify dashboard

