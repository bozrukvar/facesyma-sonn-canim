# Similarity Module: Phase 1 Integration Plan

**Feature:** "5 Benzeriniz" (Celebrity, Historical, Object, Plant, Animal)  
**Status:** Planning Phase  
**Target:** Phase 1 (integrate into current deployment)  
**Timeline:** 3-4 days implementation  
**Top Results:** 3 per category (optimized for engagement)

---

## 🎯 Overview

Single module showing user 5 different "matches":
1. **Celebrity** - Who do you look like (famous public figures)
2. **Historical** - Historical leader/figure you resemble
3. **Object** - What luxury item/everyday object matches your style
4. **Plant/Flower** - What plant/flower matches your aesthetic
5. **Animal** - What animal matches your personality/appearance

---

## 📊 Data Sources

### ✅ Source Strategy

| Category | Primary | Backup | Compliance |
|----------|---------|--------|-----------|
| **Celebrity** | Wikimedia CC0 | IMDb public | Public domain only |
| **Historical** | Wikimedia CC0 | Wikipedia public | Pre-1928 (auto-public) |
| **Objects** | Unsplash CC0 | Pexels public | Free creative commons |
| **Plants** | Wikimedia CC0 | Botanical databases | Public domain only |
| **Animals** | Wikimedia CC0 | Unsplash wildlife | CC0/public domain |

### Database Size (Phase 1)

```
Initial Launch (Month 1):
├─ Celebrities:       100 entries
├─ Historical:        100 entries
├─ Objects:           80 entries (curated luxury + everyday)
├─ Plants:            80 entries
└─ Animals:           80 entries
Total:               440 database entries

Each entry includes:
├─ Name/Title
├─ Image (CC0/public domain URL)
├─ Sıfat tags (from 201 sıfat system)
├─ Category traits
├─ Embeddings for matching
└─ Metadata

Expansion (Month 2-3):
└─ Expand to 1000+ total entries
```

---

## 🏗️ Architecture

### 1. New Collections (MongoDB)

```javascript
// similarities_celebrities
{
  _id: ObjectId,
  name: "Angelina Jolie",
  category: "celebrity",
  image_url: "https://commons.wikimedia.org/...",
  wikimedia_id: "...",
  sifatlar: ["Güzel", "Cesur", "Karismati", "Entellektüel"],
  face_embedding: Float32Array[512],  // From face recognition model
  birth_year: 1975,
  style_type: ["Elegant", "Minimalist"],
  description_tr: "Hollywood'un en etkili oyunlarından...",
  description_en: "One of Hollywood's most influential...",
  created_at: timestamp,
  similarity_score: 0.95  // For caching user results
}

// similarities_historical
{
  _id: ObjectId,
  name: "Cleopatra",
  era: "Ancient Egypt",
  image_url: "https://commons.wikimedia.org/...",
  sifatlar: ["Lider", "Güçlü", "Akıllı", "Karizmatik"],
  traits: ["Leadership", "Intelligence", "Political Power"],
  birth_year: 69,
  death_year: 30,
  description_tr: "Mısır'ın son etkin pharaonu...",
  public_domain: true
}

// similarities_objects
{
  _id: ObjectId,
  name: "Hermès Leather Bag",
  category: "object",
  subcategory: "luxury_fashion",
  image_url: "https://unsplash.com/...",
  style_traits: ["Sophisticated", "Elegant", "Timeless", "Luxury"],
  elegance_score: 95,
  vibe: ["Professional", "Refined", "Minimalist"],
  price_range: "Luxury",
  description_tr: "Klasik ve zarafet sembolü...",
  color_options: ["Black", "Brown", "Bordeaux"]
}

// similarities_plants
{
  _id: ObjectId,
  name: "Rose",
  latin_name: "Rosa",
  color: "Red",
  image_url: "https://commons.wikimedia.org/...",
  aesthetic_traits: ["Beautiful", "Delicate", "Romantic", "Passionate"],
  sifatlar: ["Güzel", "Duyarlı", "Romantik"],
  meanings: ["Love", "Passion", "Beauty"],
  season: ["Year-round"],
  description_tr: "Güzellik ve aşkın sembolü...",
  matched_traits: ["Romantic", "Delicate", "Powerful"]
}

// similarities_animals
{
  _id: ObjectId,
  name: "Panther",
  scientific_name: "Panthera pardus",
  image_url: "https://commons.wikimedia.org/...",
  behavioral_traits: ["Graceful", "Powerful", "Independent", "Stealthy"],
  sifatlar: ["Güçlü", "Zarif", "Bağımsız", "Gizemli"],
  physical_traits: ["Dark", "Sleek", "Muscular"],
  habitat: "Africa, Asia",
  description_tr: "Güç ve zarafetin mükemmel kombinasyonu...",
  matched_personality: ["Strong", "Independent", "Mysterious"]
}

// user_similarities (results cache)
{
  _id: ObjectId,
  user_id: 123,
  analyzed_at: timestamp,
  face_id: "user_123_face_embedding",
  results: {
    celebrities: [
      {
        rank: 1,
        name: "Angelina Jolie",
        score: 0.95,
        image_url: "...",
        match_reason: "Facial features + Personality traits match"
      },
      {...}
    ],
    historical: [{...}],
    objects: [{...}],
    plants: [{...}],
    animals: [{...}]
  },
  validity: "30 days"  // Cache for 30 days
}
```

### 2. Indexes (For Performance)

```javascript
// For matching queries
db.similarities_celebrities.createIndex({ sifatlar: 1 })
db.similarities_historical.createIndex({ sifatlar: 1 })
db.similarities_objects.createIndex({ style_traits: 1 })
db.similarities_plants.createIndex({ aesthetic_traits: 1 })
db.similarities_animals.createIndex({ behavioral_traits: 1 })

// For caching
db.user_similarities.createIndex({ user_id: 1 }, { unique: true })
db.user_similarities.createIndex({ analyzed_at: 1 })

// TTL index - auto-delete old results after 30 days
db.user_similarities.createIndex(
  { analyzed_at: 1 },
  { expireAfterSeconds: 2592000 }
)
```

---

## 🔄 Matching Algorithm

### Phase 1 Approach: Trait-Based + Embeddings

```python
class SimilarityMatcher:
    
    def match_user_to_similarities(self, user_profile, user_face_embedding):
        """
        Match user to all 5 categories
        
        Input:
        - user_profile: Dict with sıfatlar, personality traits
        - user_face_embedding: Float32Array[512] from face model
        
        Output:
        - results: Dict with top 3 matches per category
        """
        
        results = {
            'celebrities': self._match_celebrities(user_profile, user_face_embedding),
            'historical': self._match_historical(user_profile),
            'objects': self._match_objects(user_profile),
            'plants': self._match_plants(user_profile),
            'animals': self._match_animals(user_profile)
        }
        
        return results
    
    def _match_celebrities(self, user_profile, user_face_embedding):
        """
        Match celebrities: 60% face similarity + 40% sıfat overlap
        """
        # 1. Face embedding similarity (cosine distance)
        face_similarities = []
        for celeb in celebrities_db.find():
            face_score = cosine_similarity(user_face_embedding, celeb['face_embedding'])
            face_similarities.append((celeb, face_score))
        
        # 2. Sıfat overlap (Jaccard similarity)
        sifat_similarities = []
        for celeb, face_score in face_similarities:
            sifat_overlap = len(set(user_profile['sifatlar']) & set(celeb['sifatlar']))
            sifat_score = sifat_overlap / max(len(user_profile['sifatlar']), len(celeb['sifatlar']))
            
            # Combined score: 60% face + 40% sıfat
            combined_score = (face_score * 0.6) + (sifat_score * 0.4)
            sifat_similarities.append((celeb, combined_score))
        
        # 3. Return top 3
        top_3 = sorted(sifat_similarities, key=lambda x: x[1], reverse=True)[:3]
        
        return [
            {
                'rank': i+1,
                'name': match[0]['name'],
                'score': round(match[1] * 100, 1),
                'image_url': match[0]['image_url'],
                'sifatlar': match[0]['sifatlar'][:5],  # Top 5 sıfats
                'match_reason': f"Yüz benzerliği + {len(set(user_profile['sifatlar']) & set(match[0]['sifatlar']))} ortak sıfat"
            }
            for i, match in enumerate(top_3)
        ]
    
    def _match_historical(self, user_profile):
        """
        Match historical: 100% sıfat overlap (no face data)
        """
        sifat_similarities = []
        for figure in historical_db.find():
            overlap = len(set(user_profile['sifatlar']) & set(figure['sifatlar']))
            score = overlap / max(len(user_profile['sifatlar']), len(figure['sifatlar']))
            sifat_similarities.append((figure, score))
        
        top_3 = sorted(sifat_similarities, key=lambda x: x[1], reverse=True)[:3]
        
        return [
            {
                'rank': i+1,
                'name': match[0]['name'],
                'era': match[0]['era'],
                'score': round(match[1] * 100, 1),
                'image_url': match[0]['image_url'],
                'sifatlar': match[0]['sifatlar'][:5],
                'description': match[0][f'description_{lang}']
            }
            for i, match in enumerate(top_3)
        ]
    
    def _match_objects(self, user_profile):
        """
        Match objects: Style + elegance + vibe alignment
        """
        # Extract style traits from user profile
        user_style = self._extract_style_traits(user_profile)
        
        style_similarities = []
        for obj in objects_db.find():
            # Calculate overlap with user style
            overlap = len(set(user_style) & set(obj['style_traits']))
            style_score = overlap / max(len(user_style), len(obj['style_traits']))
            
            # Elegance bonus if user has elegant traits
            elegance_bonus = 0.1 if 'Zarafet' in user_profile['sifatlar'] else 0
            
            combined_score = (style_score * 0.7) + (obj['elegance_score'] / 100 * 0.3) + elegance_bonus
            style_similarities.append((obj, combined_score))
        
        top_3 = sorted(style_similarities, key=lambda x: x[1], reverse=True)[:3]
        
        return [
            {
                'rank': i+1,
                'name': match[0]['name'],
                'score': round(match[1] * 100, 1),
                'image_url': match[0]['image_url'],
                'style_traits': match[0]['style_traits'][:4],
                'elegance_score': match[0]['elegance_score']
            }
            for i, match in enumerate(top_3)
        ]
    
    def _match_plants(self, user_profile):
        """
        Match plants: Aesthetic traits + sıfat alignment
        """
        aesthetic_similarities = []
        for plant in plants_db.find():
            sifat_overlap = len(set(user_profile['sifatlar']) & set(plant['sifatlar']))
            sifat_score = sifat_overlap / max(len(user_profile['sifatlar']), len(plant['sifatlar']))
            
            aesthetic_similarities.append((plant, sifat_score))
        
        top_3 = sorted(aesthetic_similarities, key=lambda x: x[1], reverse=True)[:3]
        
        return [
            {
                'rank': i+1,
                'name': match[0]['name'],
                'score': round(match[1] * 100, 1),
                'image_url': match[0]['image_url'],
                'aesthetic_traits': match[0]['aesthetic_traits'][:4],
                'color': match[0].get('color', 'Natural'),
                'meaning': match[0]['meanings'][0] if match[0]['meanings'] else 'Nature'
            }
            for i, match in enumerate(top_3)
        ]
    
    def _match_animals(self, user_profile):
        """
        Match animals: Behavioral + personality traits
        """
        behavior_similarities = []
        for animal in animals_db.find():
            behavior_overlap = len(set(user_profile['sifatlar']) & set(animal['sifatlar']))
            behavior_score = behavior_overlap / max(len(user_profile['sifatlar']), len(animal['sifatlar']))
            
            behavior_similarities.append((animal, behavior_score))
        
        top_3 = sorted(behavior_similarities, key=lambda x: x[1], reverse=True)[:3]
        
        return [
            {
                'rank': i+1,
                'name': match[0]['name'],
                'score': round(match[1] * 100, 1),
                'image_url': match[0]['image_url'],
                'behavioral_traits': match[0]['behavioral_traits'][:4],
                'habitat': match[0]['habitat']
            }
            for i, match in enumerate(top_3)
        ]

# Helper methods
def _extract_style_traits(self, user_profile):
    """Extract style traits from user sıfatlar"""
    style_mapping = {
        'Zarafet': 'Elegant',
        'Saflık': 'Minimalist',
        'Lüks': 'Luxury',
        'Doğallık': 'Natural',
        # ... etc
    }
    return [style_mapping.get(s, s) for s in user_profile['sifatlar'] if s in style_mapping]
```

---

## 🔌 API Endpoint

### New Endpoint

```bash
POST /api/v1/analysis/analyze/similarity/
Content-Type: multipart/form-data

Parameters:
  image: <file>           # User's photo
  lang: "tr" or "en"     # Language for descriptions
  use_cache: true        # Use cached results if available (optional)

Response:
{
  "success": true,
  "data": {
    "celebrities": [
      {
        "rank": 1,
        "name": "Angelina Jolie",
        "score": 95,  # Percentage (0-100)
        "image_url": "https://commons.wikimedia.org/...",
        "sifatlar": ["Güzel", "Cesur", "Karizmatik"],
        "match_reason": "Yüz benzerliği + 3 ortak sıfat"
      },
      {
        "rank": 2,
        "name": "Natalie Portman",
        "score": 88,
        "image_url": "...",
        "sifatlar": ["Zarafet", "Inteligent"],
        "match_reason": "2 ortak sıfat"
      },
      {
        "rank": 3,
        "name": "Audrey Hepburn",
        "score": 82,
        "image_url": "...",
        "sifatlar": ["Zarafet", "Stil"],
        "match_reason": "Stil ve zarafet benzerliği"
      }
    ],
    "historical": [
      {
        "rank": 1,
        "name": "Cleopatra",
        "era": "Ancient Egypt",
        "score": 89,
        "image_url": "...",
        "sifatlar": ["Lider", "Güçlü", "Akıllı"],
        "description": "Mısır'ın son etkin pharaonu..."
      },
      {...},
      {...}
    ],
    "objects": [
      {
        "rank": 1,
        "name": "Hermès Leather Bag",
        "score": 87,
        "image_url": "...",
        "style_traits": ["Sophisticated", "Elegant", "Timeless"],
        "elegance_score": 95
      },
      {...},
      {...}
    ],
    "plants": [
      {
        "rank": 1,
        "name": "Rose",
        "score": 85,
        "image_url": "...",
        "aesthetic_traits": ["Beautiful", "Romantic"],
        "color": "Red",
        "meaning": "Love & Passion"
      },
      {...},
      {...}
    ],
    "animals": [
      {
        "rank": 1,
        "name": "Panther",
        "score": 92,
        "image_url": "...",
        "behavioral_traits": ["Graceful", "Powerful", "Independent"],
        "habitat": "Africa, Asia"
      },
      {...},
      {...}
    ],
    "summary": "You're like Angelina Jolie with the elegance of a rose and the grace of a panther! Your style matches a Hermès bag, and your leadership qualities remind us of Cleopatra."
  }
}
```

---

## 📱 UI Component

```
┌────────────────────────────────────────┐
│         KİŞİYE BENZEYEN 5               │
├────────────────────────────────────────┤
│                                        │
│ 🎬 ÜNLÜ                               │
│ ┌──────────────────────────────────┐  │
│ │ 1. Angelina Jolie       ☆ 95%    │  │
│ │    [Foto] Güzel • Cesur          │  │
│ │                                  │  │
│ │ 2. Natalie Portman      ☆ 88%    │  │
│ │    [Foto] Zarafet • Entellektüel │  │
│ │                                  │  │
│ │ 3. Audrey Hepburn       ☆ 82%    │  │
│ │    [Foto] Stil • Zarafet        │  │
│ └──────────────────────────────────┘  │
│                                        │
│ 📜 TARİHİ ŞAHSIYETLER                 │
│ ┌──────────────────────────────────┐  │
│ │ 1. Cleopatra (Mısır)    ☆ 89%    │  │
│ │    [Foto] Lider • Güçlü          │  │
│ └──────────────────────────────────┘  │
│                                        │
│ 🎨 EŞYA/STİL                          │
│ ┌──────────────────────────────────┐  │
│ │ 1. Hermès Bag           ☆ 87%    │  │
│ │    [Foto] Sofistike • Zarafet    │  │
│ └──────────────────────────────────┘  │
│                                        │
│ 🌸 ÇIÇEK/BİTKİ                       │
│ ┌──────────────────────────────────┐  │
│ │ 1. Red Rose             ☆ 85%    │  │
│ │    [Foto] Güzel • Romantik       │  │
│ └──────────────────────────────────┘  │
│                                        │
│ 🦁 HAYVAN                             │
│ ┌──────────────────────────────────┐  │
│ │ 1. Panther              ☆ 92%    │  │
│ │    [Foto] Güçlü • Zarif          │  │
│ └──────────────────────────────────┘  │
│                                        │
│ "Angelina Jolie'nin güzelliği ile     │
│  Cleopatra'nın liderliği taşıyorsun.  │
│  Zarafet ve güç mükemmel uyum!" 🎉   │
│                                        │
│ [💬 Paylaş] [❤️ Kaydet] [📊 Detay]   │
│                                        │
└────────────────────────────────────────┘
```

---

## 🗂️ Implementation Steps

### Phase 1: Setup (Day 1-2)

```
1. Create 5 new MongoDB collections
   └─ similarities_celebrities (100 entries)
   └─ similarities_historical (100 entries)
   └─ similarities_objects (80 entries)
   └─ similarities_plants (80 entries)
   └─ similarities_animals (80 entries)
   └─ user_similarities (results cache)

2. Populate data from Wikimedia Commons API
   └─ Fetch CC0 images + metadata
   └─ Generate face embeddings for celebrities
   └─ Tag with sıfatlar

3. Create Python module: similarity_matcher.py
   └─ SimilarityMatcher class
   └─ Matching algorithms
   └─ Cache management
```

### Phase 2: API (Day 2-3)

```
1. Create new view: SimilarityAnalyzeView
   └─ File upload handling
   └─ Image processing
   └─ Call similarity matcher
   └─ Cache results

2. Add URL route
   └─ POST /api/v1/analysis/analyze/similarity/

3. Integration with existing analysis
   └─ Call after face analysis completes
   └─ Add to history
```

### Phase 3: Testing (Day 3)

```
1. Write tests
   └─ Matching algorithm accuracy
   └─ API endpoint functionality
   └─ Cache behavior
   └─ Error handling

2. Test with real images
   └─ Verify top-3 matches make sense
   └─ Check scoring logic
```

### Phase 4: Deployment (Day 4)

```
1. Build and deploy to Docker
2. Verify all endpoints working
3. Monitor performance
4. Update documentation
```

---

## 📦 Data Seeding Strategy

### Option 1: Wikimedia API + Manual Curation (Recommended)

```python
# Pseudo-code for data population

# 1. Fetch from Wikimedia Commons
def seed_celebrities():
    """
    Query Wikimedia Commons for CC0 celebrity photos
    """
    celebrities = [
        {
            "name": "Angelina Jolie",
            "wikimedia_file": "Angelina_Jolie_2019.jpg",
            "sifatlar": ["Güzel", "Cesur", "Karizmatik", "Entellektüel"],
            "url": fetch_from_wikimedia("Angelina Jolie"),
            "face_embedding": generate_embedding("url")
        },
        # ... 100 total
    ]
    db.similarities_celebrities.insert_many(celebrities)

# 2. Historical figures (all public domain pre-1928)
def seed_historical():
    figures = [
        {
            "name": "Cleopatra",
            "era": "Ancient Egypt",
            "sifatlar": ["Lider", "Güçlü", "Akıllı", "Karizmatik"],
            "birth_year": 69,
            "death_year": 30,
            "url": fetch_from_wikimedia("Cleopatra")
        },
        # ... 100 total
    ]
    db.similarities_historical.insert_many(figures)

# 3. Objects (curated + Unsplash CC0)
def seed_objects():
    objects = [
        {
            "name": "Hermès Leather Bag",
            "category": "luxury_fashion",
            "style_traits": ["Sophisticated", "Elegant", "Timeless"],
            "elegance_score": 95,
            "url": fetch_from_unsplash("hermes bag")
        },
        # ... 80 total (mix of luxury + everyday)
    ]
    db.similarities_objects.insert_many(objects)

# 4. Plants (Wikimedia botanical)
def seed_plants():
    plants = [
        {
            "name": "Rose",
            "latin_name": "Rosa",
            "color": "Red",
            "sifatlar": ["Güzel", "Duyarlı", "Romantik"],
            "url": fetch_from_wikimedia("Rose flower")
        },
        # ... 80 total
    ]
    db.similarities_plants.insert_many(plants)

# 5. Animals (Wikimedia wildlife)
def seed_animals():
    animals = [
        {
            "name": "Panther",
            "scientific_name": "Panthera pardus",
            "sifatlar": ["Güçlü", "Zarif", "Bağımsız"],
            "behavioral_traits": ["Graceful", "Powerful", "Stealthy"],
            "url": fetch_from_wikimedia("Panther wildlife")
        },
        # ... 80 total
    ]
    db.similarities_animals.insert_many(animals)
```

### Option 2: Data File

Create `similarity_data.json` with all entries, then bulk import.

---

## 🎨 Why Top 3?

```
✅ Mobile-friendly (no excessive scrolling)
✅ Better UX (most relevant matches highlighted)
✅ Faster load time (fewer embeddings to compute)
✅ Higher engagement (top 3 already compelling)
✅ Better for sharing (cleaner output)
✅ Easier to display side-by-side

vs. Top 5:
❌ More clutter on mobile
❌ Slower computation
❌ Less relevant 5th match
✅ But: More options if needed
```

**Decision: TOP 3** - Best balance of speed, UX, relevance.

---

## 🔄 Integration Points

### Into Existing Analysis

```python
# In analysis_api/views.py AnalyzeBaseView

def post(self, request):
    # ... existing analysis code ...
    
    # NEW: Similarity analysis
    try:
        from facesyma_revize.similarity_matcher import SimilarityMatcher
        matcher = SimilarityMatcher()
        similarity_results = matcher.match_user_to_similarities(
            user_profile=character_analysis['sifatlar'],
            user_face_embedding=face_embedding
        )
        result['similarity'] = similarity_results
    except Exception as e:
        # Graceful fallback
        log.warning(f"Similarity matching failed: {e}")
        result['similarity'] = None
    
    return result
```

### Response Structure

```json
{
  "success": true,
  "data": {
    "character_analysis": {...},
    "similarity": {
      "celebrities": [...],
      "historical": [...],
      "objects": [...],
      "plants": [...],
      "animals": [...]
    }
  }
}
```

---

## 📊 Performance Considerations

### Caching Strategy

```python
# Cache user results for 30 days
# If same user submits new photo, clear old cache

db.user_similarities.create_index(
    { "analyzed_at": 1 },
    { expireAfterSeconds: 2592000 }  # 30 days
)

# On new analysis:
old_results = db.user_similarities.find_one({'user_id': user_id})
if old_results:
    db.user_similarities.delete_one({'user_id': user_id})
```

### Computation Cost

```
Per request:
- Face embedding: ~200ms (reuse from existing analysis)
- Celebrity matching: ~50ms (100 entries, cosine similarity)
- Historical matching: ~30ms (100 entries, sıfat overlap)
- Object matching: ~20ms (80 entries)
- Plant matching: ~20ms (80 entries)
- Animal matching: ~20ms (80 entries)
─────────────────────────────────
TOTAL: ~340ms (acceptable)

With caching: 0ms (instant return)
```

---

## 📋 Development Checklist

- [ ] Design data schemas
- [ ] Create MongoDB collections (6 total)
- [ ] Seed initial data (440 entries)
- [ ] Write SimilarityMatcher class
- [ ] Implement matching algorithms
- [ ] Create API endpoint
- [ ] Write 15+ test cases
- [ ] Integrate with existing analysis
- [ ] Performance testing
- [ ] Update documentation
- [ ] Deploy to Docker
- [ ] Monitor results

---

## 🚀 Timeline

```
Day 1: Database setup + data seeding
Day 2: Matching algorithm + API
Day 3: Testing + optimization
Day 4: Integration + deployment
```

Expected completion: **4 days**

---

## 💰 Value Add

### User Engagement
- ✅ Novel, shareable feature
- ✅ Fun factor (people love this kind of analysis)
- ✅ Instagram-worthy results

### Product
- ✅ Differentiator from competitors
- ✅ Deeper personality analysis
- ✅ Cross-category insights

### Monetization
- Premium: Detailed similarity reports
- Premium: Historical deep-dives
- Social: Sharing triggers network growth

---

## ✅ Ready to Start?

**This plan:**
- ✅ KVKK/GDPR compliant (only public domain sources)
- ✅ Integrated into Phase 1
- ✅ Performance optimized (340ms/request)
- ✅ Top 3 per category (best UX)
- ✅ 440 initial entries (sufficient for launch)
- ✅ Expandable to 1000+ later

**Should we start implementation?**

