# Facesyma Test Module

Multi-language psychometric testing system with AI interpretation.

## Features

- **6 Test Types**
  - Personality (Big Five)
  - Career Aptitude
  - HR / Work Style
  - Skills Assessment
  - Vocational (Holland RIASEC)
  - Relationship & Emotional Intelligence

- **18 Languages** (Turkish, English, German, Russian, Arabic, Spanish, Korean, Japanese, Chinese, Hindi, French, Portuguese, Bengali, Indonesian, Urdu, Italian, Vietnamese, Polish)

- **Likert 1-5 Scale** with reverse-scored items

- **AI Interpretation** via Ollama + orca-mini model

- **MongoDB Storage** (isolated database)

- **JWT Authentication** (shared with other services)

## API Endpoints

### Get Test Types
```bash
GET /test/types
```

Response: List of 6 test types with metadata

### Start a Test
```bash
POST /test/start
Content-Type: application/json

{
  "test_type": "personality",
  "lang": "tr"
}
```

Response: Session ID + 20 questions with scale labels

### Submit Test Answers
```bash
POST /test/submit
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "session_id": "uuid",
  "test_type": "personality",
  "lang": "tr",
  "answers": [
    {"q_id": "P001", "score": 4},
    {"q_id": "P002", "score": 3},
    ...
  ]
}
```

Response: Scored results + AI interpretation

### Get User's Test History
```bash
GET /test/results/{uid}
Authorization: Bearer {jwt_token}
```

Response: List of user's past test results

### Get PDF Download URL
```bash
GET /test/pdf/{result_id}
```

Response: GCS signed URL (TODO: PDF generation)

### Supported Languages
```bash
GET /test/languages
```

Response: 18 language codes and names

### Health Check
```bash
GET /test/health
```

Response: Service status

## Deployment

### Docker Build
```bash
docker build -t facesyma_test:latest .
```

### Docker Run
```bash
docker run -p 8004:8004 \
  -e OLLAMA_URL=http://ollama:11434 \
  -e MONGO_URI=mongodb+srv://... \
  -e JWT_SECRET=your-secret \
  facesyma_test:latest
```

### Database Setup
```bash
python migration/setup_test_db.py
```

## Configuration

Environment variables (.env):
```
OLLAMA_URL=http://ollama:11434
MONGO_URI=mongodb+srv://...
JWT_SECRET=facesyma-jwt-secret-key
```

## Question Banks

6 JSON files in `questions/` directory:
- `personality_questions.json` (20 questions, Big Five)
- `career_questions.json` (20 questions, 6 domains)
- `hr_questions.json` (20 questions, 5 domains)
- `skills_questions.json` (20 questions, 5 domains)
- `vocation_questions.json` (20 questions, Holland RIASEC)
- `relationship_questions.json` (20 questions, 4 subscales)

Each file includes:
- 20 questions with unique IDs
- Domain/subscale mappings
- Reverse-scored flags
- Translations in 18 languages
- Likert scale labels in 18 languages

## Scoring System

Domain score calculation:
1. For each domain, sum answers (1-5 scale)
2. Reverse-scored items: 6 - score
3. Calculate average: sum / question_count
4. Convert to 0-100: ((avg - 1) / 4) × 100

Interpretation levels:
- 0-39: Low
- 40-69: Moderate
- 70-100: High

## AI Interpretation

Ollama integration:
- Model: orca-mini
- Endpoint: `/api/generate`
- Generates natural language summary of test results
- Stored with each test result in MongoDB

## Database Schema

### test_sessions
```json
{
  "_id": "uuid",
  "user_id": 12345,
  "test_type": "personality",
  "lang": "tr",
  "status": "in_progress|completed",
  "created_at": "ISO8601"
}
```

### test_results
```json
{
  "_id": "uuid",
  "user_id": 12345,
  "session_id": "uuid",
  "test_type": "personality",
  "lang": "tr",
  "answers": [{"q_id": "P001", "score": 4}, ...],
  "domain_scores": {"openness": 78, "conscientiousness": 65, ...},
  "ai_interpretation": "Natural language summary...",
  "pdf_url": "https://...",
  "created_at": "ISO8601"
}
```

## Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
uvicorn api.test_api:app --reload --port 8004
```

### Test API
```bash
curl http://localhost:8004/test/health
```

## TODO

- [ ] PDF generation (reportlab)
- [ ] Google Cloud Storage integration
- [ ] Batch test creation for organizations
- [ ] Test result analytics dashboard
- [ ] Export results to CSV/Excel
