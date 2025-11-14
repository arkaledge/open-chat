# Enterprise AI Assistant Platform

A comprehensive open-source, self-hosted AI assistant platform that delivers production-grade conversational AI, RAG search, and multi-model orchestration while maintaining complete data sovereignty.

## Features

- 🤖 **Multi-Model Support**: OpenAI, Anthropic, Ollama, and more
- 🔒 **Enterprise Security**: SSO, RBAC, audit logging, PII detection
- 📚 **RAG System**: Document ingestion, vector search, hybrid retrieval
- 🌐 **Web Search**: Real-time search integration with Tavily
- 💬 **ChatGPT-like Interface**: Streaming responses, markdown rendering
- 🏢 **Multi-Tenancy**: Organizations, workspaces, team collaboration
- 📊 **Monitoring**: Prometheus, Grafana, OpenTelemetry
- 🔌 **Plugin System**: Extensible architecture for custom functionality
- 🚀 **Production-Ready**: Kubernetes deployment, high availability

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- (Optional) NVIDIA GPU for local model serving

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/open-chat.git
cd open-chat
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start infrastructure services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
cd backend
python -m alembic upgrade head
```

5. Start the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

6. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

7. Access the application:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/admin)

## Architecture

```
┌─────────────┐
│   Frontend  │ (React + TypeScript)
│  (Port 3000)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  API Gateway│ (FastAPI)
│  (Port 8000)│
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
   ┌───────┐ ┌───────┐ ┌────────┐ ┌────────┐
   │OpenAI │ │Claude │ │ Ollama │ │ Other  │
   └───────┘ └───────┘ └────────┘ └────────┘
       │
       ├──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
   ┌────────┐ ┌──────┐ ┌───────┐ ┌───────┐
   │Postgres│ │Redis │ │Qdrant │ │MinIO  │
   └────────┘ └──────┘ └───────┘ └───────┘
```

## Configuration

See [docs/configuration.md](docs/configuration.md) for detailed configuration options.

## Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
helm install open-chat ./helm/open-chat
```

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

## Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Deployment Guide](docs/deployment.md)
- [Plugin Development](docs/plugins.md)
- [Security](docs/security.md)

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
