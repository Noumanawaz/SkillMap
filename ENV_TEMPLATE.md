# Environment Variables Template

Copy these variables to your Coolify environment settings:

```bash
# Database Configuration
# For production, use PostgreSQL: postgresql://user:password@host:5432/dbname
# For development, SQLite is fine: sqlite:///./skillmap.db
DATABASE_URL=sqlite:///./skillmap.db

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Vector Database (optional)
VECTOR_DB_BACKEND=in_memory
# If using Pinecone:
# PINECONE_API_KEY=your-pinecone-key
# PINECONE_ENVIRONMENT=your-environment
# If using Weaviate:
# WEAVIATE_URL=http://weaviate:8080

# Frontend API URL (leave empty for production, nginx will proxy)
VITE_API_URL=
```

## Required Variables for Coolify

**Minimum required:**
- `OPENAI_API_KEY` - Your OpenAI API key

**Recommended for production:**
- `DATABASE_URL` - PostgreSQL connection string (create a PostgreSQL service in Coolify first)

