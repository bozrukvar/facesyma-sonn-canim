# Facesyma Docker Deployment Guide

## Build Status: ✅ Complete (2026-04-13 20:00 UTC+3)

All 6 services successfully deployed and running.

### Running Services

| Service | Port | Status | Image Size |
|---------|------|--------|------------|
| Nginx | 80 | healthy | ~10MB |
| Django Admin | 8000 | healthy | 3.27GB |
| AI Chat | 8002 | healthy | 160MB |
| Coach API | 8003 | healthy | 174MB |
| Test Module | 8004 | healthy | 210MB |
| Ollama LLM | 11434 | starting | ~1.2GB |

### Quick Commands

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f [SERVICE]

# Stop services
docker-compose down
```

### API Testing

```bash
# Health check
curl http://localhost/health

# Admin stats
curl http://localhost:8000/api/v1/admin/users/stats/

# Chat service
curl http://localhost:8002/health

# Coach API
curl http://localhost:8003/health
```

### Resource Usage

- Backend: 200-300MB RAM
- AI Chat: 150-200MB RAM
- Coach: 100-150MB RAM
- Test: 100-150MB RAM
- Ollama: 2-4GB RAM
- Total: 3-5GB RAM

### Configuration

Each service uses `.env` files:
- facesyma_backend/.env
- facesyma_ai/.env
- facesyma_coach/.env
- facesyma_test/.env

All configured with MongoDB Atlas and JWT authentication.

### Network Architecture

Services communicate via `facesyma_network` bridge:
- backend:8000 (Django)
- ai_chat:8002 (FastAPI)
- coach:8003 (FastAPI)
- test:8004 (FastAPI)
- ollama:11434 (Ollama)

External access through Nginx on port 80.

