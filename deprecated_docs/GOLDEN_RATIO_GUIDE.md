# Golden Ratio Visualization — Implementation Guide

## Overview

The golden ratio visualization endpoint has been implemented to provide users with an interactive visual analysis of their facial harmony relative to the golden ratio (φ = 1.618).

**Endpoint:** `POST /api/v1/analysis/analyze/golden/`

---

## Implementation Details

### Module: `facesyma_backend/facesyma_revize/golden_ratio.py`

**Features:**
- ✓ Analyzes facial measurements using the calculator module
- ✓ Calculates golden ratio conformance scores (0-100)
- ✓ Assigns letter grades (A+, A, A-, B+, B, B-, C+, C, D, F)
- ✓ Creates visual overlays on original photo with annotations
- ✓ Returns high-quality base64 PNG for frontend rendering
- ✓ Supports multi-language footer text (Turkish, English)
- ✓ KVKK-compliant: shows guidance on original photo without modification

### Key Functions

#### `analyze_golden_ratio(img_path, lang='tr', save_output=False)`
Main entry point that orchestrates the analysis.

**Returns:**
```json
{
  "score": 94.2,
  "grade": "A",
  "phi": 1.618,
  "features": {
    "measurements": {
      "eyes_distance": {"ratio": 1.618, "score": 98, "category": "golden"},
      "lip_width": {"ratio": 0.98, "score": 92, "category": "golden"}
    },
    "golden_ratios": [
      {"name": "Eye Spacing", "ratio": 1.618, "score": 98, "status": "golden"},
      {"name": "Lip Width", "ratio": 0.98, "score": 92, "status": "golden"}
    ]
  },
  "image_b64": "data:image/png;base64,iVBORw0KGgoA..."
}
```

#### Visual Overlay Components

The generated image includes:

1. **Title Bar (Dark background, 80px height)**
   - Golden Harmony Score display: "Golden Harmony: 94.2% A"

2. **Measurement Cards**
   - Shows up to 5 key measurements
   - Each card displays:
     - Measurement name (e.g., "Eye Spacing")
     - Calculated ratio (e.g., "1.62")
     - Score percentage (e.g., "98%")
     - Status indicator circle (green=golden, amber=adjustable)

3. **Footer Recommendation**
   - Dynamic text based on score
   - Language-aware (Turkish/English)
   - Provides actionable guidance

### Scoring System

**Golden Ratio Tolerance:** ±0.0618 (3.8% from 1.618)

- **95-100%** → A+ (Perfect harmony)
- **90-95%** → A (Excellent match)
- **85-90%** → A- (Very good)
- **80-85%** → B+ (Good)
- **75-80%** → B (Solid)
- **70-75%** → B- (Fair)
- **Below 70%** → C or lower

---

## Testing the Endpoint

### Prerequisites
- Backend service running: `docker-compose up -d backend`
- Test face image (JPG/PNG)

### 1. Basic Test with cURL

```bash
# Turkish (default)
curl -X POST http://localhost:8000/api/v1/analysis/analyze/golden/ \
  -F "image=@path/to/face_photo.jpg" \
  -F "lang=tr"

# English
curl -X POST http://localhost:8000/api/v1/analysis/analyze/golden/ \
  -F "image=@path/to/face_photo.jpg" \
  -F "lang=en"
```

### 2. Expected Response

```json
{
  "success": true,
  "data": {
    "score": 85.4,
    "grade": "B+",
    "phi": 1.618,
    "features": {...},
    "image_b64": "data:image/png;base64,..."
  }
}
```

### 3. Rendering the Visualization

The `image_b64` can be directly used in HTML:

```html
<img src="{image_b64}" alt="Golden Ratio Analysis" style="max-width: 100%;" />
```

Or save to disk:

```python
import base64
import io
from PIL import Image

img_b64 = response['data']['image_b64']
img_data = base64.b64decode(img_b64.split(',')[1])
img = Image.open(io.BytesIO(img_data))
img.save('golden_ratio_output.png')
```

---

## KVKK Compliance

✓ **Original Photo Protected:**
- No biometric modifications applied
- Guidance overlays drawn on top of original
- User's original photo remains unchanged
- Compliance: Can be shown to professional for follow-up

✓ **No Data Storage:**
- Visual guidance is for display only
- Original measurements not persisted
- Overlay annotations are transient

✓ **User Control:**
- User can choose to save/share the visualization
- No automatic storage of analysis results
- Transparent about what's being analyzed

---

## Customization Options

### Adjusting Colors

Edit `create_golden_overlay()` function in `golden_ratio.py`:

```python
# Premium purple (current)
color_golden = (139, 95, 191, 200)

# Change to other colors:
color_golden = (0, 128, 255, 200)    # Blue
color_golden = (255, 165, 0, 200)     # Orange
```

### Adding More Measurements

Edit `extract_golden_features()` to add more measurements:

```python
features['golden_ratios'].append({
    'name': 'New Measurement',
    'ratio': calculated_value,
    'score': calculate_score_from_ratio(calculated_value),
    'status': 'golden' or 'adjustable'
})
```

### Changing Languages

Update `get_footer_text()` for new languages:

```python
elif lang == 'de':  # German
    if score >= 95:
        return "✓ Ihre Gesichtsgeometrie zeigt perfekte goldene Schnitt-Harmonie."
```

---

## Frontend Integration

### React Component Example

```jsx
export function GoldenRatioAnalysis({ imageBase64, score, grade }) {
  return (
    <div className="golden-ratio-container">
      <img src={imageBase64} alt="Golden Ratio" className="analysis-image" />
      <div className="score-badge">
        <span className="score">{score.toFixed(1)}%</span>
        <span className="grade">{grade}</span>
      </div>
    </div>
  );
}
```

### Mobile Rendering

The base64 image is optimized for mobile:
- PNG format (lossless, crisp on screens)
- Responsive sizing (adapts to screen width)
- Touch-friendly overlay annotations

---

## Error Handling

If analysis fails, the endpoint returns:

```json
{
  "success": false,
  "detail": "Error message describing the issue"
}
```

Common errors:
- `"Could not load image"` → Invalid image format or corrupted file
- `"Analiz hatası: [error message]"` → Algorithm processing error
- `"Fotoğraf gerekli. (key: image)"` → Missing image parameter

---

## Performance Notes

- **Processing time:** 2-8 seconds per image (depends on face detection)
- **Image size:** Recommended 300x300 to 1920x1080 pixels
- **Output size:** Base64 image typically 50-200 KB
- **Memory:** Peak usage ~200 MB per request

---

## Next Steps

1. **Frontend Integration:** Add UI component to display visualization
2. **User Testing:** Collect feedback on visual design
3. **Refinement:** Adjust colors/layout based on user preferences
4. **Documentation:** Update mobile app docs with endpoint details
5. **Analytics:** Track visualization views and user engagement

---

## Testing Checklist

- [ ] Backend service running and healthy
- [ ] Endpoint responds to POST requests
- [ ] Image base64 decodes correctly
- [ ] Score calculation matches expected ranges
- [ ] Visual overlays render without distortion
- [ ] Footer text appears in correct language
- [ ] Multiple images analyzed successfully
- [ ] Error handling works for invalid images
