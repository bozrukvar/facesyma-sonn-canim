# GCP Deployment - Admin Panel Phase 4

## 📋 Pre-Deployment Checklist

- [x] Phase 4 views implemented (4 files)
- [x] URLs registered (12 endpoints)
- [x] MongoDB collections defined
- [ ] Environment variables configured
- [ ] Docker image rebuilt
- [ ] Deployed to GCP
- [ ] DNS configured
- [ ] Health check verified

---

## 🐳 Docker Rebuild

### Step 1: Build Backend Image

```bash
cd facesyma_backend
docker build -t facesyma-backend:latest .
```

**Dockerfile'da bulunan:**
- Python 3.10
- Django 4.2
- All requirements from requirements.txt
- Code from facesyma_backend/ (including new views)

### Step 2: Tag for GCP Registry

```bash
docker tag facesyma-backend:latest \
  gcr.io/your-gcp-project/facesyma-backend:latest
```

### Step 3: Push to Google Container Registry

```bash
docker push gcr.io/your-gcp-project/facesyma-backend:latest
```

---

## 🌐 Environment Variables (GCP)

Update `.env` in Cloud Run:

```env
# Django
DJANGO_SETTINGS_MODULE=facesyma_project.settings
DEBUG=False
ALLOWED_HOSTS=34.14.77.134,your-domain.com,*.compute.googleapis.com
DJANGO_SECRET_KEY=your-production-secret-key

# MongoDB Atlas
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/facesyma-backend?ssl=true

# JWT
JWT_SECRET=your-jwt-secret
JWT_ACCESS_EXP_HOURS=24

# Upload directory (GCS or local)
UPLOAD_TMP=/tmp/uploads

# Face Analysis Engine
FACESYMA_ENGINE_PATH=/app/facesyma_revize

# Google Cloud Storage (for backups/reports)
GCS_BUCKET_NAME=facesyma-backups
GCS_PROJECT_ID=your-gcp-project

# Email (for alerts)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=noreply@facesyma.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 🚀 Deploy to Cloud Run

### Option 1: gcloud CLI

```bash
gcloud run deploy facesyma-backend \
  --image gcr.io/your-gcp-project/facesyma-backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 3600 \
  --allow-unauthenticated \
  --env-vars-file .env.gcp
```

### Option 2: Cloud Console

1. Go to Cloud Run (console.cloud.google.com/run)
2. Click "Create Service"
3. Select image: `gcr.io/your-gcp-project/facesyma-backend:latest`
4. Configure:
   - Memory: 2GB
   - Timeout: 3600s
   - Environment variables: Copy from .env
5. Deploy

---

## 🔗 DNS Configuration (GCP)

### Current Status
- **Instance IP:** 34.14.77.134
- **Domain:** *.com (pending)
- **Issue:** DNS A record not configured

### Fix DNS

1. **Get Static IP** (if using Compute Engine):
```bash
gcloud compute addresses create facesyma-ip \
  --region us-central1
```

2. **Point Domain to IP** (in Domain Registrar):
```
A Record:
  Host: your-domain.com
  Points to: 34.14.77.134
  TTL: 300
```

3. **Configure Cloud Run Custom Domain**:
```bash
gcloud run services update-traffic facesyma-backend \
  --to-revisions LATEST=100 \
  --region us-central1

gcloud run domain-mappings create \
  --service facesyma-backend \
  --domain your-domain.com \
  --region us-central1
```

4. **Set up SSL** (Automatic via Cloud Run + Google-managed certs):
   - Cloud Run automatically provisions SSL certs for custom domains
   - Check status: `gcloud run domain-mappings describe your-domain.com`

---

## 🧪 Post-Deployment Tests

### 1. Health Check
```bash
curl https://your-domain.com/api/v1/admin/monitoring/health/
# Expected: {"success": true, "data": {...}}
```

### 2. Analytics Endpoint
```bash
curl https://your-domain.com/api/v1/admin/analytics/dashboard/
# Expected: 200 OK
```

### 3. Backup Endpoint
```bash
curl -X POST https://your-domain.com/api/v1/admin/backup/create/ \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "full"}'
# Expected: 200 OK
```

### 4. Logs
```bash
gcloud run logs read facesyma-backend --limit 50
# Check for errors
```

---

## 📈 Monitoring Setup

### 1. Cloud Monitoring Dashboard

```bash
# Create dashboard
gcloud monitoring dashboards create --config-from-file dashboard.json
```

### 2. Alert Policies

Create alerts for:
- Error rate > 1%
- Response time > 500ms
- Memory usage > 80%
- CPU usage > 75%

```bash
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Backend Error Rate Alert" \
  --condition-name="High Error Rate"
```

### 3. Log Aggregation

Setup Cloud Logging:
- Django logs → Cloud Logging
- Application errors → Error Reporting
- Custom metrics → Cloud Monitoring

---

## 🔐 Security Checklist

- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] DJANGO_SECRET_KEY is strong (32+ chars)
- [ ] MongoDB connection uses SSL
- [ ] JWT secret is strong
- [ ] Cloud SQL (if using) has VPC connector
- [ ] Service account has least-privilege IAM roles
- [ ] SSL certificate valid and auto-renews

---

## 📝 Backup Strategy (Phase 4)

### MongoDB Backup Automation

```bash
# Cloud Backup for MongoDB Atlas
gcloud compute backup-restore operations create \
  --backup-plan=facesyma-backup \
  --all-instances
```

### GCS Backup Storage

```bash
# Create bucket for backups
gsutil mb -c standard gs://facesyma-backups

# Set retention policy
gsutil retention set 30d gs://facesyma-backups

# Enable versioning
gsutil versioning set on gs://facesyma-backups
```

---

## 📊 Phase 4 Deployment Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Backend Code | ✅ Ready | 51 endpoints |
| Docker Image | ⏳ To Build | Build locally first |
| GCP Registry | ⏳ To Push | After build |
| Cloud Run | ⏳ To Deploy | Memory: 2GB |
| DNS | ⏳ To Config | A record + SSL cert |
| Monitoring | ⏳ To Setup | Dashboard + Alerts |
| Backups | ⏳ To Config | MongoDB + GCS |

---

## 🎯 Next Steps

1. **Build & Push Docker Image**
   ```bash
   cd facesyma_backend
   docker build -t facesyma-backend:latest .
   docker tag facesyma-backend:latest gcr.io/YOUR_PROJECT/facesyma-backend:latest
   docker push gcr.io/YOUR_PROJECT/facesyma-backend:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy facesyma-backend \
     --image gcr.io/YOUR_PROJECT/facesyma-backend:latest \
     --region us-central1 --memory 2Gi
   ```

3. **Configure DNS**
   - Point A record to Cloud Run IP
   - Set up custom domain in Cloud Run

4. **Verify Health**
   ```bash
   curl https://your-domain.com/api/v1/admin/monitoring/health/
   ```

---

**Status:** Ready for deployment ✅

**Estimated Time:** 20-30 minutes

**Success Criteria:**
- [ ] All 51 endpoints accessible (GET /api/v1/admin/analytics/dashboard/)
- [ ] Health check passes
- [ ] Logs visible in Cloud Logging
- [ ] Backups automated
- [ ] DNS resolves correctly
