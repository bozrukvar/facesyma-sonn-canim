# Deployment Checklist — Phase 2A: AI Chat Service

**Status:** ✅ **READY FOR PRODUCTION**  
**Last Updated:** 2026-04-10  
**Estimated Time to Deploy:** 30 minutes

---

## ✅ Pre-Deployment Checklist

### Prerequisites
- [ ] Anthropic API key obtained from https://console.anthropic.com
- [ ] MongoDB connection string ready (Atlas or local)
- [ ] Python 3.11+ installed
- [ ] pip package manager working
- [ ] Port 8002 available (no other service running)

### Environment Setup
```bash
cd facesyma_ai
cp .env.example .env
# Edit .env with:
# - ANTHROPIC_API_KEY=sk-ant-...
# - MONGO_URI=mongodb://...
# - JWT_SECRET=change-this
```

- [ ] .env file created with all required variables
- [ ] ANTHROPIC_API_KEY is valid (test: `curl https://api.anthropic.com/v1/models`)
- [ ] MONGO_URI is accessible (test: `mongosh "your-connection-string"`)
- [ ] JWT_SECRET changed from default

---

## 📦 Installation Checklist

```bash
# Install dependencies
pip install -r requirements.txt
```

- [ ] All dependencies installed without errors
- [ ] Verify: `python -c "import fastapi, anthropic, pymongo, jwt; print('✅ All imports OK')"`
- [ ] requirements.txt matches current versions:
  - fastapi==0.115.0
  - uvicorn==0.30.6
  - anthropic==0.40.0
  - pymongo==4.7.2
  - PyJWT==2.9.0
  - pydantic==2.9.0

---

## 🚀 Startup Checklist

### Start the Service
```bash
python -m uvicorn chat_service.main:app \
  --host 0.0.0.0 \
  --port 8002 \
  --reload
```

- [ ] Service starts without errors
- [ ] Listens on `http://0.0.0.0:8002`
- [ ] No port conflicts (check with: `lsof -i :8002`)
- [ ] FastAPI documentation available at `http://localhost:8002/docs`

### Initial Health Checks (In Another Terminal)
```bash
# Check 1: Health endpoint
curl http://localhost:8002/health
# Expected: {"status": "ok"}
```

- [ ] Health endpoint returns 200 OK
- [ ] Response is valid JSON
- [ ] Service responds within 1 second

```bash
# Check 2: Languages endpoint
curl http://localhost:8002/languages
# Expected: {"languages": ["tr", "en", "de", ..., "pl"]}
```

- [ ] Languages endpoint returns 200 OK
- [ ] All 18 languages listed
- [ ] Can parse response as JSON

---

## 🧪 Functional Testing Checklist

### Test 1: Start Conversation (Turkish)
```bash
curl -X POST http://localhost:8002/chat/start \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_result": {
      "sifatlar": ["Güvenli", "Yaratıcı"],
      "moduls": {"kariyer": 85}
    },
    "lang": "tr",
    "first_message": "Kariyer potansiyelim nedir?"
  }'
```

- [ ] Request succeeds (200 OK)
- [ ] Response includes `conversation_id`
- [ ] Response includes `assistant_message` (non-empty)
- [ ] Response includes `lang: "tr"`
- [ ] Claude API was called (logs show token usage)
- [ ] Response saved to MongoDB

### Test 2: Send Message
```bash
# Using conversation_id from Test 1:
curl -X POST http://localhost:8002/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_...",
    "message": "Sanat alanında nasılım?",
    "lang": "tr"
  }'
```

- [ ] Request succeeds (200 OK)
- [ ] Response includes `assistant_message`
- [ ] Response includes `usage` with token counts
- [ ] Message is saved to conversation history
- [ ] Response is contextual (references previous analysis)

### Test 3: Multi-Language (English & German)
```bash
# English
curl -X POST http://localhost:8002/chat/start \
  -H "Content-Type: application/json" \
  -d '{"analysis_result": {...}, "lang": "en"}'

# German
curl -X POST http://localhost:8002/chat/start \
  -H "Content-Type: application/json" \
  -d '{"analysis_result": {...}, "lang": "de"}'
```

- [ ] English conversation starts successfully
- [ ] German conversation starts successfully
- [ ] Arabic works (if testing: `"lang": "ar"`)
- [ ] All responses are in the requested language
- [ ] No language mixing in responses

### Test 4: Run Full Test Suite
```bash
python test_ai_chat.py
```

- [ ] All 7 tests pass
- [ ] Health check: ✅
- [ ] Languages: ✅
- [ ] Start conversation: ✅
- [ ] Send message: ✅
- [ ] Language variations: ✅
- [ ] Error handling: ✅
- [ ] Performance: ✅

---

## 📊 Monitoring & Validation

### Check Application Logs
- [ ] No ERROR level logs (only INFO/WARNING acceptable)
- [ ] Token usage logged for each request
- [ ] MongoDB write operations confirmed
- [ ] Claude API calls successful (no 429 rate limit errors)

### Check MongoDB
```bash
# Connect to MongoDB
mongosh "your-connection-string"

# List conversations
use facesyma-backend
db.ai_conversations.find().limit(3)

# Verify structure
db.ai_conversations.findOne()
```

- [ ] Conversations table exists in facesyma-backend
- [ ] Documents have correct structure:
  - `_id`: ObjectId
  - `user_id`: number or null
  - `conversation_id`: string
  - `messages`: array of objects
  - `analysis`: object
  - `lang`: string
  - `created_at`: date
  - `updated_at`: date
- [ ] At least 1 document from testing exists
- [ ] No corrupted/incomplete records

### Check API Response Times
- [ ] `/health` responds in <100ms
- [ ] `/languages` responds in <100ms
- [ ] `/chat/start` responds in 2-5 seconds (Claude API latency)
- [ ] `/chat/message` responds in 2-5 seconds
- [ ] No timeout errors (>20 seconds)

---

## 🔐 Security Checklist

### Authentication
- [ ] JWT token validation implemented
- [ ] Expired tokens rejected
- [ ] Invalid tokens rejected
- [ ] Optional auth for public endpoints (health, languages)
- [ ] Test with invalid token:
```bash
curl -H "Authorization: Bearer invalid.token.here" \
  http://localhost:8002/chat/history
# Should return 401 or 403
```

### Data Protection
- [ ] Conversations stored in encrypted MongoDB
- [ ] API key not logged in plain text
- [ ] JWT secret changed from default
- [ ] No sensitive data in error messages
- [ ] CORS configured appropriately

### Rate Limiting (Optional but Recommended)
- [ ] Consider implementing for production:
  - Max 30 requests/minute per IP
  - Max 100 tokens/minute per user
- [ ] Monitor for abuse patterns

---

## 🔄 Integration Checklist

### Django Backend Integration
- [ ] AI Chat service listens on port 8002
- [ ] Django backend can call `/chat/start` endpoint
- [ ] Django backend can call `/chat/message` endpoint
- [ ] JWT tokens from Django work with AI Chat service
- [ ] Test from Django:
```python
# In Django shell:
import requests
import os
token = "your-jwt-token-from-login"
response = requests.post('http://localhost:8002/chat/start', 
  headers={'Authorization': f'Bearer {token}'},
  json={'analysis_result': {...}, 'lang': 'tr'})
print(response.json())
```

- [ ] Conversation IDs returned can be stored in Django models
- [ ] Chat history can be retrieved by user_id

### Mobile App Integration (Future)
- [ ] API endpoints documented for mobile team
- [ ] React Native service class created
- [ ] CORS headers allow mobile domain
- [ ] Authentication flow works with app tokens

---

## 📋 Documentation Checklist

- [ ] PHASE_2A_AI_CHAT.md created with:
  - Quick start guide
  - API endpoint reference
  - Authentication details
  - Multi-language support docs
  - Integration examples
  - Troubleshooting guide

- [ ] test_ai_chat.py created with comprehensive tests

- [ ] Deployment checklist (this document) completed

- [ ] API documentation accessible at `/docs`

- [ ] README.md updated with Phase 2A status

---

## 🚨 Rollback Plan (If Needed)

If deployment fails:

```bash
# 1. Stop the service
# Kill the uvicorn process or Ctrl+C

# 2. Check logs for errors
tail -f /var/log/facesyma-ai.log

# 3. Verify environment variables
cat .env

# 4. Reinstall dependencies
pip install --upgrade -r requirements.txt

# 5. Clear MongoDB conversations (if corrupted)
# USE WITH CAUTION - only if data is bad:
# mongosh > use facesyma-backend
#          > db.ai_conversations.deleteMany({})

# 6. Restart service
python -m uvicorn chat_service.main:app --port 8002
```

- [ ] Rollback plan understood
- [ ] Know how to stop service quickly
- [ ] Know how to check logs
- [ ] Backup MongoDB before production deployment

---

## ✅ Final Sign-Off

### Review Checklist
- [ ] All prerequisites met
- [ ] All installation steps completed
- [ ] All functional tests passed
- [ ] All monitoring checks done
- [ ] Security requirements satisfied
- [ ] Integration points verified
- [ ] Documentation complete
- [ ] Rollback plan understood

### Approval
- [ ] Developer reviewed and tested: _______________
- [ ] Date: _______________
- [ ] Ready for production: ✅ / ❌

---

## 📞 Support & Next Steps

### If Any Tests Fail:
1. Check logs: `tail -f /var/log/facesyma-ai.log`
2. Verify .env: `cat .env | grep -v "^#"`
3. Test Claude API: `python -c "import anthropic; print(anthropic.__version__)"`
4. Check MongoDB: `mongosh "your-connection-string"`
5. See PHASE_2A_AI_CHAT.md for troubleshooting

### Next Phase:
- Phase 2B: Fine-tuned Llama (optional)
- Phase 3: Coach API (life coaching modules)
- Phase 4: Mobile app integration

### Support Resources:
- FastAPI docs: https://fastapi.tiangolo.com
- Anthropic docs: https://docs.anthropic.com
- MongoDB docs: https://docs.mongodb.com
- uvicorn docs: https://www.uvicorn.org

---

**Status:** ✅ Phase 2A Ready for Deployment  
**Command to Start:** `python -m uvicorn chat_service.main:app --host 0.0.0.0 --port 8002`

