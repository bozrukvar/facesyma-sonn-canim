# Pre-Deployment Checklist
**GCP'ye geçmeden kontrol listesi**

---

## ✅ STEP 1: TESTS (RUN_TESTS.md)

### Local Django Server Başlat
```bash
cd facesyma_backend
python manage.py runserver 0.0.0.0:8000
```

### Test Case'leri Çalıştır
```bash
# Ayrı terminal'de:
python manage.py test test_admin_api_integration.AdminAPIIntegrationTest -v 2
```

**Beklenen Sonuç:**
```
Ran 42 tests in X.XXXs
OK
```

### Endpoint Validation
```bash
bash validate_admin_endpoints.sh
```

**Beklenen Sonuç:**
```
Total:      51  │  Success:    51  │  Failed:      0
✓ ALL ENDPOINTS WORKING
```

### Test Checklist
- [ ] Django sunucusu başladı
- [ ] MongoDB bağlandı
- [ ] 42 test case geçti
- [ ] 51 endpoint'in tamamı çalışıyor
- [ ] Hata logları yok
- [ ] Response time < 500ms

---

## 📊 STEP 2: MONITORING SETUP (MONITORING_SETUP.md)

### Logging Konfigürasyonu
```bash
# Create logs directory
mkdir -p facesyma_backend/logs

# Check logging_config.py exists
ls facesyma_backend/logging_config.py
```

### Alert Rules Initialize Et
```bash
python manage.py shell < alert_rules_init.py
```

**Verify:**
```bash
curl http://localhost:8000/api/v1/admin/alerts/config/ | jq '.data.total_rules'
# Expected: 6 (default rules)
```

### Health Check
```bash
curl http://localhost:8000/api/v1/admin/monitoring/health/ | jq
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "services": {
      "django": { "status": "healthy", "response_time_ms": 145 },
      "mongodb": { "status": "healthy" },
      ...
    }
  }
}
```

### Error Rate Check
```bash
curl http://localhost:8000/api/v1/admin/monitoring/errors/ | jq '.data'
```

**Expected:**
```json
{
  "error_rate": 0.02,
  "total_errors": 1,
  "top_errors": []
}
```

### Uptime Tracking
```bash
curl http://localhost:8000/api/v1/admin/monitoring/uptime/ | jq '.data'
```

### Metrics Collection
```bash
curl http://localhost:8000/api/v1/admin/health/services/ | jq '.data.metrics'
```

### Monitoring Checklist
- [ ] Logging configured
- [ ] Alert rules initialized (6 rules)
- [ ] Health endpoint responding
- [ ] Error tracking working
- [ ] Uptime calculation working
- [ ] Response times tracked
- [ ] Metrics collecting
- [ ] No critical errors in logs

---

## 🌐 STEP 3: DNS CONFIGURATION (DNS_SETUP.md)

### 3.1 Domain Registrar Setup
- [ ] Domain registrar'a erişim sağlandı
- [ ] A record oluşturuldu:
  ```
  Type: A
  Name: @
  Value: 34.14.77.134
  TTL: 300
  ```
- [ ] DNS propagation beklendi (5-30 min)

### 3.2 DNS Propagation Verify
```bash
nslookup facesyma.com
# or
dig facesyma.com

# Expected:
# facesyma.com.    300    IN    A    34.14.77.134
```

Online: https://www.whatsmydns.net/

- [ ] DNS A record propagated globally

### 3.3 GCP Instance Setup
```bash
# SSH into instance
gcloud compute ssh facesyma-backend --zone us-central1-a

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

- [ ] Docker installed
- [ ] Docker Compose installed

### 3.4 SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx

sudo certbot certonly --standalone -d facesyma.com
# Fill in email for renewal notifications

# Test renewal
sudo certbot renew --dry-run
```

- [ ] Let's Encrypt certificate generated
- [ ] Renewal test passed

### 3.5 Nginx Configuration
```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/facesyma
# Copy from DNS_SETUP.md

# Enable site
sudo ln -s /etc/nginx/sites-available/facesyma /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl restart nginx
```

- [ ] Nginx configured
- [ ] Syntax test passed
- [ ] Nginx restarted

### 3.6 Docker Services Deploy
```bash
# Create docker-compose.yml (from DNS_SETUP.md)

# Build images
docker build -t facesyma-backend:latest facesyma_backend/

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

- [ ] Docker Compose created
- [ ] Backend image built
- [ ] Services started
- [ ] No errors in logs

### 3.7 Verification
```bash
# Test HTTPS
curl -I https://facesyma.com/api/v1/admin/monitoring/health/
# Should return: HTTP/2 200

# Test health endpoint
curl https://facesyma.com/api/v1/admin/monitoring/health/ | jq

# Check SSL certificate
curl -I https://facesyma.com
```

- [ ] HTTPS working
- [ ] Health endpoint accessible
- [ ] SSL certificate valid
- [ ] Security headers present (HSTS, X-Frame-Options, etc.)

### DNS Configuration Checklist
- [ ] Domain A record configured
- [ ] DNS propagation verified
- [ ] Docker installed on GCP
- [ ] SSL certificate generated
- [ ] Nginx configured
- [ ] Services deployed
- [ ] HTTPS working
- [ ] All endpoints accessible via domain

---

## 📋 FINAL VERIFICATION

### API Health via Domain
```bash
# All major endpoint'leri test et

# Analytics
curl https://facesyma.com/api/v1/admin/analytics/dashboard/ | jq '.success'

# Payment
curl https://facesyma.com/api/v1/admin/payments/transactions/ | jq '.success'

# Monitoring
curl https://facesyma.com/api/v1/admin/monitoring/health/ | jq '.data.overall_status'

# Backup
curl https://facesyma.com/api/v1/admin/backup/status/ | jq '.success'

# Logging
curl https://facesyma.com/api/v1/admin/logs/aggregated/ | jq '.success'

# Alerts
curl https://facesyma.com/api/v1/admin/alerts/config/ | jq '.success'

# Reports
curl https://facesyma.com/api/v1/admin/reports/history/ | jq '.success'
```

**Expected:** Tüm endpoints `"success": true` döndürmelidir

### Performance Check
```bash
# Response time
time curl https://facesyma.com/api/v1/admin/monitoring/health/
# Expected: < 500ms

# Error rate
curl https://facesyma.com/api/v1/admin/monitoring/errors/ | jq '.data.error_rate'
# Expected: < 0.1%

# Uptime
curl https://facesyma.com/api/v1/admin/monitoring/uptime/ | jq '.data.uptime_percentage'
# Expected: > 99%
```

### Security Check
```bash
# Check SSL grade
curl -I https://facesyma.com
# Should show:
# Strict-Transport-Security
# X-Content-Type-Options
# X-Frame-Options
# X-XSS-Protection

# SSL Labs test (online)
# https://www.ssllabs.com/ssltest/analyze.html?d=facesyma.com
```

### Log Check
```bash
# Check for errors
docker-compose logs backend | grep ERROR
# Should be none or minimal

# Check MongoDB connection
docker-compose logs backend | grep "MongoDB"
# Should show successful connection
```

### Final Verification Checklist
- [ ] All 51 endpoints responding via HTTPS
- [ ] Response time < 500ms
- [ ] Error rate < 0.1%
- [ ] Uptime > 99%
- [ ] SSL certificate valid
- [ ] Security headers present
- [ ] No critical errors in logs
- [ ] MongoDB connected
- [ ] Health checks passing
- [ ] Monitoring collecting data

---

## ✅ APPROVED FOR GCP DEPLOYMENT

Tüm checklistler tamamlandığında:

```
✓ Tests: 42/42 passed
✓ Monitoring: 6+ rules active
✓ DNS: Propagated globally
✓ SSL: Valid certificate
✓ Endpoints: 51/51 accessible
✓ Performance: Healthy metrics
✓ Security: All headers present
✓ Logs: Clean, no errors
```

**THEN:** GCP Cloud Run'a deploy et

---

## 🚀 NEXT: GCP Deployment

When all checks pass:
1. Push Docker images to Google Container Registry
2. Deploy to Cloud Run
3. Configure auto-scaling (100+ concurrent users)
4. Setup Cloud Monitoring dashboards
5. Enable Cloud Logging
6. Configure backup to GCS
7. Done! ✅

---

**Status:** Ready for pre-deployment tests ✅

**Timeline:** 
- Tests: 15 minutes
- Monitoring setup: 20 minutes
- DNS configuration: 30-60 minutes
- Verification: 15 minutes
- **Total: ~2 hours before GCP deployment**
