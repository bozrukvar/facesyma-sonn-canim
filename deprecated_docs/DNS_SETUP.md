# DNS & SSL Configuration Guide

## 🌐 Current Status

```
Domain:         facesyma.com (pending)
IP Address:     34.14.77.134 (GCP Compute Engine)
SSL:            Not configured
DNS Records:    Not configured
Status:         ⏳ Paused at DNS setup
```

---

## 📋 Pre-DNS Checklist

Before configuring DNS, verify:

- [x] GCP Compute Engine instance created (34.14.77.134)
- [x] Django backend running on port 8000
- [x] All 51 API endpoints responding
- [x] FastAPI Chat Service running
- [x] Coach Service running
- [x] MongoDB Atlas connected
- [ ] Domain registrar access
- [ ] Cloud Run service deployed (after tests pass)

---

## 🔧 Step 1: Configure Domain Registrar

### A. Get your Domain Registrar

Where did you register `facesyma.com`?
- GoDaddy?
- Namecheap?
- Google Domains?
- Other?

### B. Add A Record

Go to your domain registrar's DNS settings:

```
Type:     A
Name:     @ (or leave blank)
Value:    34.14.77.134
TTL:      300 (or lowest available)
```

**Note:** Changes can take 5-30 minutes to propagate globally.

### C. Verify DNS Propagation

```bash
# Check if A record is set
nslookup facesyma.com
# or
dig facesyma.com

# Expected output:
# facesyma.com.    300    IN    A    34.14.77.134
```

Online tool: https://www.whatsmydns.net/

---

## 🐳 Step 2: Configure Docker on GCP Instance

SSH into your instance:

```bash
gcloud compute ssh facesyma-backend --zone us-central1-a
```

### Install Docker

```bash
# Update system
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
```

### Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 🔒 Step 3: SSL Certificate Setup

### Option A: Self-Signed Certificate (Development)

```bash
sudo mkdir -p /etc/nginx/ssl

# Generate certificate (valid for 365 days)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/private.key \
  -out /etc/nginx/ssl/certificate.crt

# Fill in the prompts:
# Country: TR
# State: Istanbul
# City: Istanbul
# Organization: Facesyma
# Common Name: facesyma.com
```

### Option B: Let's Encrypt (Free, Auto-Renewing)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d facesyma.com

# Certificate location:
# /etc/letsencrypt/live/facesyma.com/fullchain.pem
# /etc/letsencrypt/live/facesyma.com/privkey.pem

# Auto-renew
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 🌐 Step 4: Nginx Configuration

Create `/etc/nginx/sites-available/facesyma`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name facesyma.com www.facesyma.com;
    
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name facesyma.com www.facesyma.com;
    
    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/facesyma.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/facesyma.com/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy settings
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API endpoints
    location /api/v1/admin/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # Chat Service (FastAPI)
    location /api/v1/chat/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/facesyma /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🐳 Step 5: Deploy with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: facesyma-backend:latest
    container_name: facesyma-backend
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=facesyma_project.settings
      - DEBUG=False
      - ALLOWED_HOSTS=facesyma.com,www.facesyma.com,localhost,127.0.0.1,34.14.77.134
      - MONGO_URI=${MONGO_URI}
      - JWT_SECRET=${JWT_SECRET}
      - FACESYMA_ENGINE_PATH=/app/facesyma_revize
    volumes:
      - ./logs:/app/logs
      - ./uploads:/tmp/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/admin/monitoring/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - facesyma-net

  chat-service:
    image: facesyma-chat:latest
    container_name: facesyma-chat
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - MONGO_URI=${MONGO_URI}
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - facesyma-net

  coach-service:
    image: facesyma-coach:latest
    container_name: facesyma-coach
    ports:
      - "8002:8002"
    environment:
      - MONGO_URI=${MONGO_URI}
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - facesyma-net

  nginx:
    image: nginx:alpine
    container_name: facesyma-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/nginx/sites-available/facesyma:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - backend
      - chat-service
      - coach-service
    restart: unless-stopped
    networks:
      - facesyma-net

networks:
  facesyma-net:
    driver: bridge
```

Deploy:

```bash
# Build images
docker build -t facesyma-backend:latest facesyma_backend/
docker build -t facesyma-chat:latest facesyma_ai/chat_service/
docker build -t facesyma-coach:latest facesyma_coach/

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

---

## ✅ Step 6: Verify Configuration

### Test DNS
```bash
nslookup facesyma.com
# Should resolve to: 34.14.77.134
```

### Test HTTPS
```bash
curl -I https://facesyma.com/api/v1/admin/monitoring/health/
# Should return: HTTP/2 200
```

### Test Endpoints
```bash
# Test via domain
curl https://facesyma.com/api/v1/admin/analytics/dashboard/ | jq

# Test specific endpoint
curl https://facesyma.com/api/v1/admin/monitoring/health/ | jq '.data'

# All 51 endpoints should be accessible
```

### Check SSL Certificate
```bash
curl -I https://facesyma.com

# Should show:
# HTTP/2 200
# Strict-Transport-Security: max-age=31536000
```

Online tool: https://www.sslshowcase.com/

---

## 🔄 SSL Auto-Renewal

If using Let's Encrypt:

```bash
# Test renewal
sudo certbot renew --dry-run

# Manual renew
sudo certbot renew

# Check renewal schedule
sudo systemctl status certbot.timer
```

---

## 📊 DNS Configuration Checklist

- [ ] Domain registrar accessed
- [ ] A record created (@ → 34.14.77.134)
- [ ] DNS propagation verified (nslookup/dig)
- [ ] SSL certificate generated
- [ ] Nginx configured
- [ ] Docker services deployed
- [ ] HTTPS working
- [ ] Health check responding
- [ ] All endpoints accessible via domain
- [ ] Security headers present

---

## 🐛 Troubleshooting

### DNS Not Resolving
```bash
# Clear DNS cache
sudo systemctl restart systemd-resolved

# Check again
nslookup facesyma.com
```

### SSL Certificate Not Found
```bash
# Check certificate location
ls -la /etc/letsencrypt/live/facesyma.com/

# Ensure Nginx can read it
sudo chown -R www-data:www-data /etc/letsencrypt
```

### Nginx Not Reloading
```bash
# Check syntax
sudo nginx -t

# Reload
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

### Port 443 in Use
```bash
# Find process using port 443
sudo lsof -i :443

# Kill if needed
sudo kill -9 <PID>
```

---

## 📝 Summary

**After completing all steps:**

1. ✅ Domain resolves to 34.14.77.134
2. ✅ HTTPS working with valid certificate
3. ✅ All 51 API endpoints accessible
4. ✅ Nginx reverse proxy active
5. ✅ Docker services running
6. ✅ Health checks passing
7. ✅ SSL auto-renewing
8. ✅ Security headers present

**Then:** Ready for GCP Cloud Run migration

---

**Next:** Deploy to GCP Cloud Run for auto-scaling 🚀
