# Monitoring Dashboard — Phase 2 Gamification ✅

**Date**: 2026-04-19  
**Status**: ✅ Complete  
**Impact**: **Real-time visibility into cache, performance, WebSocket, and system health**  

---

## Overview

The Monitoring Dashboard provides **real-time metrics and visualization** for all Phase 2 Gamification components:

- **Cache Performance** — Hit rate, memory usage, key counts
- **Leaderboard Performance** — Query latency (avg, P95, P99)
- **WebSocket Connections** — Active connections, connection rate
- **Trend Analysis** — Snapshot count, snapshot age, breakdown by type
- **System Health** — Redis, MongoDB, Scheduler status

### Key Features

✅ **Real-time Updates** — Auto-refresh every 5 seconds  
✅ **Beautiful Visualizations** — Charts, tables, progress bars  
✅ **Component Health** — Redis, MongoDB, Scheduler status  
✅ **Performance Metrics** — Latency percentiles, query breakdown  
✅ **System-wide View** — All Phase 2 metrics in one dashboard  

---

## Architecture

### Data Flow

```
Leaderboard Queries
  ↓
MetricsService.record_leaderboard_query()
  ├→ In-memory metrics store (for speed)
  └→ MongoDB metrics collection (for persistence)

API Requests
  ↓
GET /api/v1/admin/monitoring/gamification/dashboard
  ↓
MetricsService.get_dashboard_data()
  ├→ get_cache_statistics()
  ├→ get_leaderboard_performance()
  ├→ get_websocket_metrics()
  ├→ get_trend_metrics()
  └→ get_system_health()
  ↓
JSON Response

Browser (HTML Dashboard)
  ↓
fetch('/api/v1/admin/monitoring/gamification/dashboard')
  ↓
Auto-refresh every 5 seconds
  ↓
Update charts, tables, gauges
```

### API Endpoints

#### Complete Dashboard
```
GET /api/v1/admin/monitoring/gamification/dashboard
```
Returns aggregated metrics for all components.

**Response:**
```json
{
  "timestamp": "2026-04-19T14:35:00.000Z",
  "cache": {
    "total_queries": 523,
    "cache_hits": 485,
    "cache_misses": 38,
    "hit_rate_percent": 92.7,
    "redis_stats": {...}
  },
  "leaderboard_performance": {
    "total_queries": 150,
    "average_time_ms": 8.4,
    "p95_time_ms": 25.3,
    "p99_time_ms": 45.2,
    "by_type": {
      "global": {...},
      "trait": {...},
      "community": {...}
    }
  },
  "websocket": {
    "current_connections": 45,
    "connections_last_hour": 230,
    "peak_connections_today": 112
  },
  "trends": {
    "total_snapshots": 87,
    "latest_snapshot_age_hours": 0.3,
    "by_leaderboard_type": {
      "global": 3,
      "trait": 30,
      "community": 54
    },
    "retention_days": 90
  },
  "system_health": {
    "status": "healthy",
    "components": {
      "redis": "healthy",
      "mongodb": "healthy",
      "scheduler": "running"
    }
  }
}
```

#### Cache Statistics Only
```
GET /api/v1/admin/monitoring/gamification/cache
```

Returns:
- Hit rate percentage
- Total queries
- Memory usage (MB)
- Redis key counts by layer

#### Leaderboard Performance
```
GET /api/v1/admin/monitoring/gamification/performance
```

Returns:
- Average query time
- P95 and P99 latency
- Query breakdown by leaderboard type (global, trait, community)
- Min/max times per type

#### WebSocket Metrics
```
GET /api/v1/admin/monitoring/gamification/websocket
```

Returns:
- Current active connections
- Connections over last hour
- Peak connections today

#### Trend Analysis Metrics
```
GET /api/v1/admin/monitoring/gamification/trends
```

Returns:
- Total snapshots stored
- Latest snapshot age (hours)
- Snapshot breakdown by leaderboard type
- Retention policy (90 days)

#### System Health
```
GET /api/v1/admin/monitoring/gamification/health
```

Returns:
- Overall system status (healthy/degraded/error)
- Component status: Redis, MongoDB, Scheduler
- Recent error count

---

## HTML Dashboard

### Access

```
GET /api/v1/admin/gamification-dashboard/
```

Requires authentication. Returns interactive HTML dashboard with:
- Real-time metrics
- Auto-refresh toggle (5 second interval)
- Charts and visualizations
- Tables with detailed breakdown
- System health status

### Features

#### Cards
1. **Cache Performance** — Hit rate gauge, memory usage
2. **Leaderboard Performance** — Query latency metrics
3. **WebSocket Connections** — Active connection count
4. **Trend Analysis** — Snapshot statistics
5. **System Health** — Component status checks

#### Charts
- **Query Performance Trend** — Bar chart showing average/min/max times by leaderboard type

#### Tables
1. **Snapshot Breakdown** — Snapshots by leaderboard type
2. **Performance by Type** — Query counts, latency by global/trait/community

#### Controls
- **Refresh Now** — Manual refresh
- **Auto-refresh Toggle** — Enable/disable 5-second auto-refresh
- **Status Indicator** — Green/yellow/red based on system health

---

## Implementation

### Metrics Collection Service

**File**: `admin_api/services/metrics_service.py`

```python
class MetricsService:
    # Record metrics
    MetricsService.record_leaderboard_query(
        leaderboard_type="global",
        query_time_ms=8.5,
        cache_hit=True,
        entries_returned=100
    )
    
    MetricsService.record_websocket_connection(connected=True)
    
    # Retrieve metrics
    stats = MetricsService.get_cache_statistics()
    perf = MetricsService.get_leaderboard_performance()
    ws = MetricsService.get_websocket_metrics()
    trends = MetricsService.get_trend_metrics()
    health = MetricsService.get_system_health()
    
    # Complete dashboard
    dashboard = MetricsService.get_dashboard_data()
```

### Recording Metrics

Integrate into leaderboard queries to track performance:

```python
import time
from admin_api.services.metrics_service import MetricsService

def get_global_leaderboard(...):
    start_time = time.time()
    cache_hit = False
    
    # Check cache
    cached = redis_get(cache_key)
    if cached:
        cache_hit = True
        entries = json.loads(cached)
    else:
        # Query database
        entries = list(users_col.find(...))
    
    elapsed_ms = (time.time() - start_time) * 1000
    
    # Record metric
    MetricsService.record_leaderboard_query(
        leaderboard_type="global",
        query_time_ms=elapsed_ms,
        cache_hit=cache_hit,
        entries_returned=len(entries)
    )
    
    return entries
```

### WebSocket Integration

Track connections:

```python
from admin_api.services.metrics_service import MetricsService

class LeaderboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        MetricsService.record_websocket_connection(connected=True)
        await self.accept()
    
    async def disconnect(self, close_code):
        MetricsService.record_websocket_connection(connected=False)
```

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `admin_api/services/metrics_service.py` | ✅ Created | Metrics collection |
| `admin_api/views/monitoring_gamification_views.py` | ✅ Created | API endpoints |
| `admin_api/views/dashboard_html_views.py` | ✅ Created | HTML dashboard view |
| `admin_api/templates/gamification_dashboard.html` | ✅ Created | Dashboard UI |
| `admin_api/urls.py` | ✅ Modified | Added 7 routes |

---

## Testing the Dashboard

### 1. Access Dashboard

```bash
# In browser (requires login)
http://localhost:8000/api/v1/admin/gamification-dashboard/

# Or view API data
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/admin/monitoring/gamification/dashboard/ | jq
```

### 2. Verify Metrics Collection

```bash
# Award coins (triggers leaderboard query)
curl -X POST http://localhost:8000/api/v1/coins/add/ \
  -H "Authorization: Bearer <token>" \
  -d '{"user_id": 123, "amount": 100}'

# Check metrics
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/admin/monitoring/gamification/performance/ | jq .leaderboard_performance.total_queries

# Should show incremented query count
```

### 3. Check System Health

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/admin/monitoring/gamification/health/ | jq

# Output:
# {
#   "status": "healthy",
#   "components": {
#     "redis": "healthy",
#     "mongodb": "healthy",
#     "scheduler": "running"
#   }
# }
```

### 4. Load Test WebSocket

```bash
# While connected users trigger leaderboard updates
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/admin/monitoring/gamification/websocket/ | jq

# Should show current_connections > 0
```

---

## Metrics Reference

### Cache Statistics

| Metric | Range | Target | Notes |
|--------|-------|--------|-------|
| Hit Rate | 0–100% | >90% | Higher = better caching |
| Memory Used | 0–512 MB | <400 MB | Includes all cache layers |
| Total Queries | 0–∞ | 100+ | Tracked since service start |

### Leaderboard Performance

| Metric | Range | Target | Notes |
|--------|-------|--------|-------|
| Avg Query Time | 0–∞ ms | <10 ms | With cache hits |
| P95 Latency | 0–∞ ms | <50 ms | 95th percentile |
| P99 Latency | 0–∞ ms | <100 ms | 99th percentile |

### WebSocket

| Metric | Range | Target | Notes |
|--------|-------|--------|-------|
| Current Connections | 0–∞ | Depends on load | Real-time count |
| Connections/hour | 0–∞ | 100+ | Churn rate indicator |
| Peak/day | 0–∞ | Depends on load | Capacity planning |

### Trends

| Metric | Target | Notes |
|--------|--------|-------|
| Total Snapshots | 87+ | 3 daily × 30 days = 90 snapshots |
| Snapshot Age | <1 hour | Latest snapshot should be recent |
| Retention | 90 days | Auto-purge older snapshots |

### System Health

| Component | Healthy | Degraded | Error |
|-----------|---------|----------|-------|
| Redis | "healthy" | N/A | "unavailable" or error msg |
| MongoDB | "healthy" | N/A | "unavailable" or error msg |
| Scheduler | "running" | N/A | "stopped" or error msg |

---

## Alerts & Monitoring

### Auto-Alert Conditions

Set up alerts for:

1. **Cache Hit Rate < 80%** → Investigate cache invalidation frequency
2. **P95 Latency > 100ms** → Database performance degradation
3. **WebSocket Connections = 0** → Check Channels health
4. **Latest Snapshot Age > 24 hours** → Scheduler not running
5. **System Health ≠ "healthy"** → Check Redis/MongoDB/Scheduler

### Example Alert Setup (Using Prometheus)

```yaml
# Prometheus rules
- alert: LowCacheHitRate
  expr: gamification_cache_hit_rate < 0.8
  for: 10m
  annotations:
    summary: "Cache hit rate below 80%"

- alert: HighLeaderboardLatency
  expr: gamification_leaderboard_p95_ms > 100
  for: 5m
  annotations:
    summary: "Leaderboard queries slow (P95 > 100ms)"

- alert: NoWebSocketConnections
  expr: gamification_websocket_connections == 0
  for: 5m
  annotations:
    summary: "No active WebSocket connections"
```

---

## Performance Optimization Tips

### Improve Cache Hit Rate
```python
# Increase TTL from 5 min → 10 min
LEADERBOARD_CACHE_TTL = 600  # 10 minutes

# Or reduce cache invalidation frequency
# (Only clear cache on significant changes, not every coin award)
```

### Reduce Latency
```python
# Add index on frequently queried fields
db.appfaceapi_myuser.createIndex({"total_coins_earned": -1})
db.appfaceapi_myuser.createIndex({"top_sifats": 1})

# Monitor MongoDB query plans
db.appfaceapi_myuser.find(...).explain("executionStats")
```

### Scale WebSocket
```python
# Increase Redis Channels capacity
CHANNEL_LAYERS = {
    'default': {
        'CONFIG': {
            'capacity': 3000,  # Was 1500
        }
    }
}
```

---

## Dashboard Customization

### Add New Metric Card

1. Create API endpoint in `monitoring_gamification_views.py`
2. Add route in `admin_api/urls.py`
3. Add card in `gamification_dashboard.html`:

```html
<div class="card">
    <div class="card-title">📊 New Metric</div>
    <div class="metric">
        <div class="metric-label">Custom Metric</div>
        <div class="metric-value"><span id="custom-value">0</span></div>
    </div>
</div>
```

4. Add JavaScript function to populate:

```javascript
function updateCustomMetrics(data) {
    const value = data.custom || 0;
    document.getElementById('custom-value').textContent = value;
}
```

5. Call in `refreshDashboard()`:

```javascript
updateCustomMetrics(data);
```

---

## Summary

**Monitoring Dashboard provides:**

✅ **Real-time visibility** — Auto-refresh every 5 seconds  
✅ **Comprehensive metrics** — Cache, performance, WebSocket, trends, health  
✅ **Beautiful UI** — Dark mode, responsive charts, status indicators  
✅ **Production-ready** — Error handling, authentication, monitoring  
✅ **Extensible** — Easy to add new metrics and alerts  

Ready for deployment and operational monitoring of Phase 2 Gamification.
