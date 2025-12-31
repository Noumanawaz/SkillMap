# SkillMap AI - Cognitive Workforce Development Platform

A production-ready AI system for strategic workforce planning and personalized learning, powered by OpenAI GPT-3.5 and cognitive modeling.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API Key (get one at https://platform.openai.com/api-keys)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd skillmap-ai/backend
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and add your OpenAI API key:**
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

4. **Run the backend:**
   ```bash
   ./run.sh
   # Or manually:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at: http://localhost:8000
   API docs: http://localhost:8000/docs

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd skillmap-ai/frontend
   ```

2. **Install dependencies and run:**
   ```bash
   ./run.sh
   # Or manually:
   npm install
   npm run dev
   ```

   Frontend will be available at: http://localhost:5173

## 🎯 Features

### ✅ Fully Implemented

- **Real LLM Integration**: Uses OpenAI GPT-3.5 for:
  - Strategic goal extraction from documents
  - Automatic skill inference from goals
  - On-demand learning content generation

- **Cognitive Profiling**: IRT-based (Item Response Theory) ability estimation per skill

- **Skill Gap Analysis**: 
  - Scalar gap calculation (target vs current)
  - Vector similarity-based gap index
  - Team and individual analysis

- **Personalized Learning Paths**:
  - AI-generated micro-lessons when content doesn't exist
  - Difficulty adaptation based on cognitive profile
  - Time-aware prioritization

- **Modern Frontend**:
  - Beautiful, responsive UI
  - Real-time error handling
  - Gap explorer, learning cockpit, goal management

## 📋 API Endpoints

### Strategy
- `GET /v1/strategy/goals` - List all strategic goals
- `POST /v1/strategy/goals` - Create a strategic goal
- `PUT /v1/strategy/goals/{goal_id}` - Update a strategic goal
- `DELETE /v1/strategy/goals/{goal_id}` - Delete a strategic goal

### Skills
- `POST /v1/skills` - Create skill in ontology
- `GET /v1/skills` - List all skills
- `POST /v1/skills/match` - Find similar skills via embeddings

### Profiles
- `GET /v1/profiles/{employee_id}` - Get employee profile
- `POST /v1/profiles/{employee_id}/cognitive-update` - Update IRT profile with assessments
- `GET /v1/profiles/{employee_id}/cognitive-summary` - Get cognitive profile summary

### Gaps
- `GET /v1/gaps/by-goal/{goal_id}/employee/{employee_id}` - Individual gap analysis
- `GET /v1/gaps/by-goal/{goal_id}/team/{manager_id}` - Team gap analysis

### Learning
- `POST /v1/learning-path` - Generate personalized learning path (generates content on-demand)

## 🏗️ Architecture

### Backend (FastAPI)
- **Skill Extraction Service**: LLM-based skill inference from goals
- **LLM Service**: Centralized OpenAI client for all AI operations
- **Cognitive Service**: IRT-based learner modeling
- **Gap Engine**: Scalar + vector similarity gap computation
- **Recommender**: Personalized path generation with on-demand content creation
- **Vector Store**: Abstracted interface (in-memory by default, supports Pinecone/Weaviate)

### Frontend (React + Vite)
- **Goal Management**: Create and manage strategic goals
- **Skill Gap Explorer**: Analyze gaps with visual indicators
- **Employee Learning Cockpit**: Generate and view personalized paths

## 🔧 Configuration

Edit `backend/.env`:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7
DATABASE_URL=sqlite:///./skillmap.db  # or PostgreSQL
```

## 📊 Database

By default, uses SQLite (`skillmap.db`) for easy setup. For production, use PostgreSQL:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/skillmap
```

Run migrations (when Alembic is configured):
```bash
alembic upgrade head
```

## 🧪 Testing

```bash
cd backend
pytest tests/
```

## 🎨 Frontend Development

The frontend uses:
- React 18
- TypeScript
- Vite
- Modern CSS (no framework, clean and fast)

## 🔐 Security & Ethics

- **Decision Support Only**: SkillMap AI provides recommendations, not autonomous HR decisions
- **Transparency**: All cognitive profiles and recommendations are explainable
- **Privacy**: Employee data is stored securely; API keys in `.env` (never commit)
- **Bias Mitigation**: Regular audits recommended for demographic fairness

## 📝 Example Workflow

1. **Create Goals**: Add strategic goals via Goal Management page
2. **Create Employee**: Add employee profile via Employee Management page
3. **Update Cognitive Profile**: Submit assessments → IRT updates ability estimates
4. **Analyze Gaps**: View gap analysis for employee vs goal
5. **Generate Learning Path**: AI creates personalized path, generating content on-demand

## 🚧 Future Enhancements

- Multi-source skill inference (code repos, documents, reviews)
- Predictive readiness modeling
- Team-level interventions
- Advanced IRT (MIRT, CAT)
- Production vector DB integration (Pinecone/Weaviate)

## 📄 License

MIT

## 🙏 Credits

Built with:
- FastAPI
- OpenAI GPT-3.5
- SentenceTransformers
- React + Vite
- SQLAlchemy
