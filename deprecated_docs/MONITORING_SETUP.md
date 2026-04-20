# Monitoring & Alerting Setup Guide

## 📊 Local Monitoring Setup

### 1. Django Logging Configuration

Create `facesyma_backend/logging_config.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'admin_api': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/admin_api.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'json',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'admin_api': {
            'handlers': ['admin_api'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}
```

### 2. Enable in settings.py
```python
from logging_config import LOGGING

# settings.py'ye ekle
LOGGING = LOGGING
```

### 3. Create Log Directory
```bash
mkdir -p facesyma_backend/logs
```

---

## 🔔 Alert Rules Configuration

Create `facesyma_backend/alert_rules_init.py`:

```python
"""
Alert rules initialization
Run: python manage.py shell < alert_rules_init.py
"""
from pymongo import MongoClient
from django.conf import settings
from datetime import datetime

client = MongoClient(settings.MONGO_URI)
db = client['facesyma-backend']
alert_rules_col = db['alert_rules']

# Default alert rules
default_rules = [
    {
        'name': 'High Error Rate Alert',
        'condition': 'error_rate > 1%',
        'metric': 'error_rate',
        'threshold': 1.0,
        'severity': 'high',
        'enabled': True,
        'notification_channels': ['email', 'slack'],
        'created_at': datetime.utcnow()
    },
    {
        'name': 'High Response Time Alert',
        'condition': 'response_time_p95 > 500ms',
        'metric': 'response_time',
        'threshold': 500,
        'severity': 'medium',
        'enabled': True,
        'notification_channels': ['email'],
        'created_at': datetime.utcnow()
    },
    {
        'name': 'Low Uptime Alert',
        'condition': 'uptime < 99%',
        'metric': 'uptime',
        'threshold': 99.0,
        'severity': 'critical',
        'enabled': True,
        'notification_channels': ['email', 'slack', 'sms'],
        'created_at': datetime.utcnow()
    },
    {
        'name': 'High Memory Usage Alert',
        'condition': 'memory_usage > 80%',
        'metric': 'memory_usage',
        'threshold': 80.0,
        'severity': 'medium',
        'enabled': True,
        'notification_channels': ['slack'],
        'created_at': datetime.utcnow()
    },
    {
        'name': 'High CPU Usage Alert',
        'condition': 'cpu_usage > 75%',
        'metric': 'cpu_usage',
        'threshold': 75.0,
        'severity': 'medium',
        'enabled': True,
        'notification_channels': ['slack'],
        'created_at': datetime.utcnow()
    },
    {
        'name': 'Database Connection Pool Exhausted',
        'condition': 'db_connections > 95%',
        'metric': 'database_connections',
        'threshold': 95.0,
        'severity': 'critical',
        'enabled': True,
        'notification_channels': ['email', 'slack'],
        'created_at': datetime.utcnow()
    }
]

# Insert rules
for rule in default_rules:
    alert_rules_col.update_one(
        {'name': rule['name']},
        {'$set': rule},
        upsert=True
    )

print(f"✓ Inserted {len(default_rules)} alert rules")

# Create indexes
db['alert_rules'].create_index('enabled')
db['alert_history'].create_index('timestamp', expireAfterSeconds=7776000)  # 90 days
db['alert_history'].create_index('severity')

print("✓ Created indexes")
```

### Run Alert Rules Setup
```bash
python manage.py shell < alert_rules_init.py
```

---

## 📈 Monitoring Metrics Collection

Create `facesyma_backend/metrics_collector.py`:

```python
"""
Collect system metrics periodically
"""
import os
import psutil
import time
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings
import logging

log = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client['facesyma-backend']
        self.metrics_col = self.db['service_metrics']
    
    def collect(self, service_name='django'):
        """Collect current metrics"""
        try:
            process = psutil.Process(os.getpid())
            
            metrics = {
                'service': service_name,
                'timestamp': datetime.utcnow(),
                'cpu_usage': process.cpu_percent(interval=1),
                'memory_usage': process.memory_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'disk_usage': psutil.disk_usage('/').percent,
                'connections': len(process.connections()),
                'threads': process.num_threads()
            }
            
            self.metrics_col.insert_one(metrics)
            log.info(f"Collected metrics for {service_name}")
            return metrics
            
        except Exception as e:
            log.error(f"Error collecting metrics: {e}")
            return None

# Usage in Django settings
# Add to manage.py or use celery:
# from metrics_collector import MetricsCollector
# collector = MetricsCollector()
# collector.collect()
```

---

## 🚨 Alert Monitoring Script

Create `monitor_alerts.py`:

```bash
#!/bin/bash
# Monitor alerts and health status

while true; do
    clear
    
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║            Facesyma Admin API - Health Monitor              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check Django health
    DJANGO_HEALTH=$(curl -s http://localhost:8000/api/v1/admin/monitoring/health/ | jq '.data.overall_status')
    echo "Django Health:  $DJANGO_HEALTH"
    
    # Check Error Rate
    ERROR_RATE=$(curl -s http://localhost:8000/api/v1/admin/monitoring/errors/ | jq '.data.error_rate')
    echo "Error Rate:     ${ERROR_RATE}%"
    
    # Check Response Time
    RESPONSE_TIME=$(curl -s http://localhost:8000/api/v1/admin/monitoring/response-time/ | jq '.data.p95_ms')
    echo "Response Time:  ${RESPONSE_TIME}ms"
    
    # Check Active Alerts
    ALERTS=$(curl -s http://localhost:8000/api/v1/admin/monitoring/alerts/ | jq '.data.active_alerts')
    echo "Active Alerts:  $ALERTS"
    
    echo ""
    echo "Last updated: $(date)"
    echo "Refresh: Ctrl+C to stop"
    echo ""
    
    sleep 10
done
```

Run:
```bash
chmod +x monitor_alerts.py
./monitor_alerts.py
```

---

## 📊 Monitoring Dashboard (Local)

Create `facesyma_backend/dashboard.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Facesyma Admin Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .dashboard { max-width: 1200px; margin: 0 auto; }
        .metric { 
            background: white; 
            padding: 20px; 
            margin: 10px 0; 
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric h3 { margin: 0 0 10px 0; }
        .metric-value { font-size: 32px; font-weight: bold; color: #2196F3; }
        .metric.warning { border-left: 4px solid #ff9800; }
        .metric.error { border-left: 4px solid #f44336; }
        .metric.success { border-left: 4px solid #4caf50; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>Facesyma Admin Dashboard</h1>
        
        <div class="grid">
            <div class="metric success">
                <h3>Healthy Services</h3>
                <div class="metric-value" id="healthy">4</div>
            </div>
            
            <div class="metric">
                <h3>Error Rate</h3>
                <div class="metric-value" id="error-rate">0.02%</div>
            </div>
            
            <div class="metric">
                <h3>Avg Response Time</h3>
                <div class="metric-value" id="response-time">245ms</div>
            </div>
            
            <div class="metric">
                <h3>Active Alerts</h3>
                <div class="metric-value" id="alerts">2</div>
            </div>
            
            <div class="metric">
                <h3>Uptime</h3>
                <div class="metric-value" id="uptime">99.9%</div>
            </div>
            
            <div class="metric">
                <h3>Total Requests</h3>
                <div class="metric-value" id="requests">45,234</div>
            </div>
        </div>
    </div>
    
    <script>
        // Refresh every 10 seconds
        setInterval(() => {
            fetch('/api/v1/admin/monitoring/health/')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('healthy').textContent = 
                        data.data.services ? Object.keys(data.data.services).length : 0;
                });
        }, 10000);
    </script>
</body>
</html>
```

Serve it:
```bash
python manage.py runserver
# Visit: http://localhost:8000/dashboard.html
```

---

## ✅ Local Monitoring Checklist

- [ ] Logging configured and files created
- [ ] Alert rules initialized in MongoDB
- [ ] Metrics collector running
- [ ] Health endpoints responding
- [ ] Error tracking working
- [ ] Uptime metrics calculating
- [ ] Response times tracked
- [ ] Dashboard loading

---

## 🔍 Health Check Commands

```bash
# Check all services health
curl http://localhost:8000/api/v1/admin/monitoring/health/ | jq

# Check error rate
curl http://localhost:8000/api/v1/admin/monitoring/errors/ | jq '.data.error_rate'

# Check uptime
curl http://localhost:8000/api/v1/admin/monitoring/uptime/ | jq '.data.uptime_percentage'

# Check active alerts
curl http://localhost:8000/api/v1/admin/monitoring/alerts/ | jq '.data'

# Check logs
curl http://localhost:8000/api/v1/admin/monitoring/logs/ | jq '.data.total_logs'
```

---

## 📋 Monitoring Success Criteria

✅ All services healthy  
✅ Error rate < 0.1%  
✅ Response time p95 < 500ms  
✅ Uptime > 99.5%  
✅ Active alerts properly triggered  
✅ Logs centralized  
✅ Metrics collected  

---

**Status:** Ready for local testing ✅
