# Getting Started with OpenChat

This guide will help you get OpenChat up and running on your local machine.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)
- (Optional) NVIDIA GPU with CUDA support for local model serving

## Quick Start with Docker Compose

The fastest way to get started is using Docker Compose:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/openchat.git
cd openchat
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required for most functionality
SECRET_KEY=your-random-secret-key
JWT_SECRET=your-random-jwt-secret

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional features
TAVILY_API_KEY=...  # For web search
```

### 3. Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This will:
- Generate random secrets
- Start infrastructure services (PostgreSQL, Redis, MinIO, Qdrant)
- Install dependencies
- Run database migrations

### 4. Start the Application

**Option A: Using Docker Compose (Recommended)**

```bash
docker-compose up -d
```

**Option B: Local Development**

Terminal 1 (Backend):
```bash
cd backend
uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)

## First Steps

### 1. Create an Account

1. Navigate to http://localhost:3000
2. Click "Sign up"
3. Enter your email, name, and password
4. You'll be automatically logged in

### 2. Start Chatting

1. Select a model from the dropdown (GPT-4o, Claude 3.5 Sonnet, or Llama 3.1)
2. Type your message in the input box
3. Press Enter or click the send button
4. Watch as the AI streams its response in real-time

### 3. Enable Advanced Features

#### RAG (Retrieval-Augmented Generation)

1. Upload documents via the document management interface
2. Toggle "RAG" before sending a message
3. The AI will search your documents and provide grounded answers

#### Web Search

1. Toggle "Web Search" before sending a message
2. The AI will search the web for current information
3. Responses will include citations to web sources

### 4. Using Ollama for Local Models

If you have a GPU and want to run models locally:

```bash
# Pull a model
docker exec openchat-ollama ollama pull llama3.1:8b

# The model will now be available in the dropdown
```

## Configuration

### Backend Configuration

Edit `backend/.env` or set environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `QDRANT_URL`: Qdrant vector database URL
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)

### Frontend Configuration

Edit `frontend/.env.local`:

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## Troubleshooting

### Services Won't Start

Check Docker logs:
```bash
docker-compose logs -f
```

### Database Connection Issues

Ensure PostgreSQL is running and accessible:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### API Key Issues

Verify your API keys are correctly set in `.env`:
```bash
cat .env | grep API_KEY
```

### Port Conflicts

If ports are already in use, modify the port mappings in `docker-compose.yml`.

## Next Steps

- Read the [Architecture Overview](docs/architecture.md)
- Explore [API Documentation](docs/api.md)
- Learn about [Deployment](docs/deployment.md)
- Develop [Custom Plugins](docs/plugins.md)

## Getting Help

- GitHub Issues: https://github.com/yourusername/openchat/issues
- Documentation: https://docs.openchat.ai
- Community Discord: https://discord.gg/openchat
