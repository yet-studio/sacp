# Behavior Analytics Tutorial

Learn how to monitor and analyze AI system behavior using SACP's behavior analytics.

## Tutorial Overview

1. Basic Setup
2. Recording Metrics
3. Pattern Analysis
4. Dashboard Usage
5. Alert Configuration

## 1. Basic Setup

```python
from sacp.enterprise.analytics import BehaviorAnalyzer
from sacp.enterprise.analytics.behavior import BehaviorMetrics

# Initialize analyzer
analyzer = BehaviorAnalyzer('analytics.db')

# Set tenant ID
tenant_id = 'my-company'
```

## 2. Recording Metrics

### Manual Recording
```python
# Create metrics
metrics = BehaviorMetrics(
    request_count=100,
    modification_rate=0.15,
    error_rate=0.02,
    avg_response_time=0.2,
    resource_usage={
        'cpu': 0.5,
        'memory': 0.4,
        'disk': 0.3
    },
    safety_violations=1,
    risk_score=0.2
)

# Record metrics
await analyzer.record_metrics(tenant_id, metrics)
```

### Automated Recording
```python
from sacp.enterprise.analytics.behavior import MetricsCollector

# Create collector
collector = MetricsCollector(
    analyzer=analyzer,
    tenant_id=tenant_id,
    interval=60  # seconds
)

# Start collection
await collector.start()
```

## 3. Pattern Analysis

### Analyzing Behavior
```python
# Get recent patterns
patterns = await analyzer.analyze_patterns(
    tenant_id,
    hours=24
)

# Check for anomalies
anomalies = await analyzer.detect_anomalies(
    tenant_id,
    sensitivity=0.95
)

# Correlate patterns
correlations = await analyzer.correlate_patterns(
    tenant_id,
    metrics=['error_rate', 'response_time']
)
```

### Using LSTM Predictions
```python
# Get behavior predictions
predictions = await analyzer.predict_behavior(
    tenant_id,
    hours_ahead=24
)

# Check prediction confidence
for pred in predictions:
    print(f"Time: {pred.timestamp}")
    print(f"Predicted: {pred.value}")
    print(f"Confidence: {pred.confidence}")
```

## 4. Dashboard Usage

### Launch Dashboard
```python
# Create dashboard
app = analyzer.create_dashboard(tenant_id)

# Run server
app.run_server(port=8050)
```

### Dashboard Features

1. **Request Monitor**
   - View request volume
   - Track error rates
   - Monitor response times

2. **Resource Usage**
   - CPU utilization
   - Memory usage
   - Disk activity

3. **Safety Metrics**
   - Violation counts
   - Risk scores
   - Pattern alerts

4. **Analysis Tools**
   - Time range selection
   - Metric correlation
   - Pattern highlighting

## 5. Alert Configuration

### Setting Up Alerts
```python
# Configure alert thresholds
await analyzer.configure_alerts(
    tenant_id,
    thresholds={
        'error_rate': 0.05,
        'response_time': 1.0,
        'risk_score': 0.7
    }
)

# Add alert handler
async def handle_alert(alert):
    print(f"Alert: {alert.message}")
    print(f"Severity: {alert.severity}")
    print(f"Metrics: {alert.metrics}")

analyzer.add_alert_handler(handle_alert)
```

### Alert Types

1. **Threshold Alerts**
   - Metric value exceeds threshold
   - Sustained high values
   - Rapid changes

2. **Pattern Alerts**
   - Unusual patterns
   - Trend changes
   - Correlation shifts

3. **Prediction Alerts**
   - High-risk predictions
   - Confidence changes
   - Pattern divergence

## Best Practices

1. **Data Collection**
   - Regular intervals
   - Complete metrics
   - Consistent format

2. **Analysis**
   - Multiple timeframes
   - Context awareness
   - Pattern validation

3. **Alerting**
   - Appropriate thresholds
   - Clear messages
   - Action items

4. **Dashboard Use**
   - Regular monitoring
   - Pattern investigation
   - Alert response

## Next Steps

- [Risk Assessment Tutorial](risk_tutorial.md)
- [Advanced Pattern Analysis](patterns_guide.md)
- [Alert Configuration Guide](alerts_guide.md)
