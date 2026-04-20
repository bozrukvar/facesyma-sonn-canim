# Facesyma — Docker Deployment Guide

## 📋 Overview

This guide explains how to deploy Facesyma using Docker. All three backend services (Django, AI Chat, Coach) run in separate containers orchestrated by Docker Compose with Nginx as a reverse proxy.

### Services
- **Backend (Django)** — Port 8000: User auth, face analysis, admin panel
- **AI Chat (FastAPI)** — Port 8002: AI conversation service
- **Coach (FastAPI)** — Port 8003: Life coaching modules
- **Nginx** — Port 80: Reverse proxy to all services

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- `.env` files configured (see below)

### Deploy

```bash
# 1. Navigate to project root
cd facesyma-sonn-canim

# 2. Build all containers
docker-compose build

# 3. Start all services
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Verify health
curl http://localhost/api/v1/admin/users/stats/
curl http://localhost/v1/chat/analyze
curl http://localhost/coach/modules
```

That's it! All services are now running.

---

## 🔧 Configuration

### .env Files

Each service has a `.env` file that must be configured before deployment:

#### `facesyma_backend/.env`
```
DJANGO_SECRET_KEY=your-secret-key
MONGO_URI=your-mongodb-uri
JWT_SECRET=your-jwt-secret
GOOGLE_CLIENT_ID=your-google-oauth-id
```

#### `facesyma_ai/.env`
```
ANTHROPIC_API_KEY=your-anthropic-key
MONGO_URI=your-mongodb-uri
JWT_SECRET=your-jwt-secret
```

#### `facesyma_coach/.env`
```
MONGO_URI=your-mongodb-uri
JWT_SECRET=your-jwt-secret
```

**All .env files are pre-created with placeholder values. Update them with real credentials before production deployment.**

---

## 📁 Deployment Files

### Core Files Created
- `docker-compose.yml` — Orchestrates all containers
- `nginx.conf` — Reverse proxy configuration
- `facesyma_coach/Dockerfile` — Coach service container definition
- `facesyma_backend/.dockerignore` — Build optimization
- `facesyma_ai/.dockerignore` — Build optimization
- `facesyma_coach/.dockerignore` — Build optimization
- `.github/workflows/deploy.yml` — CI/CD pipeline (optional)

### Existing Files Used
- `facesyma_backend/Dockerfile` — Already existed
- `facesyma_ai/Dockerfile` — Already existed
- `facesyma_backend/requirements.txt` — Python dependencies
- `facesyma_ai/requirements.txt` — Python dependencies
- `facesyma_coach/requirements.txt` — Python dependencies

---

## 🧪 Testing Deployment

### Health Checks
```bash
# All services should return 200 OK
curl http://localhost/health
```

### API Endpoints
```bash
# Django Admin
curl http://localhost/api/v1/admin/users/stats/

# AI Chat
curl -X POST http://localhost/v1/chat/analyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_result":{"emotion":"happy"},"lang":"tr"}'

# Coach
curl http://localhost/coach/modules
```

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f ai_chat
docker-compose logs -f coach
docker-compose logs -f nginx
```

---

## 🛑 Stopping Services

```bash
# Stop all containers (data persists)
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 🔄 Updating Services

```bash
# Rebuild and restart a specific service
docker-compose up -d --build backend

# Update all services
docker-compose pull
docker-compose up -d --build
```

---

## 📊 Monitoring

### Container Status
```bash
docker-compose ps
```

### Resource Usage
```bash
docker stats
```

### Database Connection
```bash
# All services use MongoDB Atlas (cloud-based)
# No local database container needed
# Connection string in .env files
```

---

## 🌍 Production Deployment

### On VPS/Server

1. **Copy project to server:**
   ```bash
   scp -r facesyma-sonn-canim user@server:/home/facesyma/
   ```

2. **SSH into server:**
   ```bash
   ssh user@server
   cd /home/facesyma/facesyma-sonn-canim
   ```

3. **Update .env files with production secrets:**
   ```bash
   nano facesyma_backend/.env
   nano facesyma_ai/.env
   nano facesyma_coach/.env
   ```

4. **Deploy:**
   ```bash
   docker-compose up -d
   ```

5. **Verify:**
   ```bash
   curl http://your-server-ip/api/v1/admin/users/stats/
   ```

### With SSL/HTTPS

Update `nginx.conf`:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of config
}
```

Or use Let's Encrypt with Certbot:
```bash
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly -d yourdomain.com
```

---

## 🚨 Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use
```bash
# Check what's using the port
lsof -i :8000  # or :8002, :8003, :80

# Kill the process
kill -9 <PID>
```

### MongoDB connection error
- Verify `.env` files have correct `MONGO_URI`
- Check MongoDB Atlas network access list
- Ensure internet connectivity

### Nginx 502 Bad Gateway
- Check if backend services are running: `docker-compose ps`
- Verify service hostnames in `nginx.conf`
- Check backend logs: `docker-compose logs backend`

---

## 📝 Environment Variables Reference

### Backend
| Variable | Purpose | Example |
|----------|---------|---------|
| `DJANGO_SECRET_KEY` | Django secret | `django-insecure-xxx` |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed domains | `localhost,api.example.com` |
| `MONGO_URI` | Database URL | `mongodb+srv://...` |
| `JWT_SECRET` | JWT signing key | `jwt-secret-xxx` |

### AI Chat & Coach
| Variable | Purpose | Example |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-xxx` |
| `MONGO_URI` | Database URL | `mongodb+srv://...` |
| `JWT_SECRET` | JWT signing key | `jwt-secret-xxx` |

---

## 🔐 Security Notes

1. **Never commit .env files** — They contain secrets
2. **Use strong secrets** — Generate random keys for production
3. **Network access** — Configure firewall rules appropriately
4. **HTTPS/SSL** — Use in production
5. **MongoDB** — Whitelist server IP in Atlas network access

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify .env files
3. Ensure all services are running: `docker-compose ps`
4. Test individual endpoints with curl

---

## 🎯 Next Steps

After successful deployment:
1. Set up CI/CD pipeline (`.github/workflows/deploy.yml`)
2. Configure domain name and SSL certificate
3. Set up monitoring and alerting
4. Create backup strategy for databases
5. Document any customizations
