# Safety Trend Analysis Tutorial

Learn how to analyze and forecast safety trends using SACP's trend analysis features.

## Tutorial Overview

1. Basic Setup
2. Recording Trends
3. Analysis Methods
4. Forecasting
5. Dashboard Usage

## 1. Basic Setup

```python
from sacp.enterprise.analytics import TrendAnalyzer
from sacp.enterprise.analytics.trends import TrendMetrics

# Initialize analyzer
analyzer = TrendAnalyzer('analytics.db')

# Set tenant ID
tenant_id = 'my-company'
```

## 2. Recording Trends

### Manual Recording
```python
# Create metrics
metrics = TrendMetrics(
    safety_violations=5,
    risk_level=0.3,
    incident_count=2,
    recovery_time=4.5,
    mitigation_effectiveness=0.8,
    compliance_rate=0.9
)

# Record metrics
await analyzer.record_metrics(tenant_id, metrics)
```

### Automated Collection
```python
from sacp.enterprise.analytics.trends import TrendCollector

# Create collector
collector = TrendCollector(
    analyzer=analyzer,
    tenant_id=tenant_id,
    interval=3600  # hourly
)

# Start collection
await collector.start()
```

## 3. Analysis Methods

### Seasonal Decomposition
```python
# Decompose trend
decomposition = await analyzer.decompose_trend(
    tenant_id,
    metric='safety_violations',
    period=24  # hours
)

print("Trend:", decomposition.trend)
print("Seasonal:", decomposition.seasonal)
print("Residual:", decomposition.residual)
```

### Pattern Detection
```python
# Detect patterns
patterns = await analyzer.detect_patterns(
    tenant_id,
    metrics=['risk_level', 'incident_count'],
    window=168  # 1 week
)

for pattern in patterns:
    print(f"Type: {pattern.type}")
    print(f"Strength: {pattern.strength}")
    print(f"Duration: {pattern.duration}")
```

### Correlation Analysis
```python
# Analyze correlations
correlations = await analyzer.analyze_correlations(
    tenant_id,
    metrics=[
        'safety_violations',
        'risk_level',
        'recovery_time'
    ]
)

# View correlation matrix
print(correlations.matrix)
print(correlations.significance)
```

## 4. Forecasting

### Prophet Forecasting
```python
# Create forecast
forecast = await analyzer.forecast_trend(
    tenant_id,
    metric='safety_violations',
    days_ahead=30
)

for pred in forecast:
    print(f"Date: {pred.date}")
    print(f"Value: {pred.value}")
    print(f"Lower: {pred.lower}")
    print(f"Upper: {pred.upper}")
```

### Custom Forecasting
```python
# Configure custom model
await analyzer.configure_forecast(
    changepoint_prior_scale=0.05,
    seasonality_prior_scale=10,
    holidays_prior_scale=10
)

# Generate forecast
forecast = await analyzer.custom_forecast(
    tenant_id,
    metric='risk_level',
    days_ahead=30
)
```

## 5. Dashboard Usage

### Launch Dashboard
```python
# Create dashboard
app = analyzer.create_dashboard(tenant_id)

# Run server
app.run_server(port=8052)
```

### Dashboard Features

1. **Trend Overview**
   - Safety metrics
   - Risk patterns
   - Incident tracking

2. **Analysis Tools**
   - Decomposition view
   - Pattern detection
   - Correlation matrix

3. **Forecasting**
   - Trend predictions
   - Confidence intervals
   - Seasonal patterns

4. **Interactive Tools**
   - Time range selection
   - Metric comparison
   - Pattern highlighting

## Best Practices

1. **Data Collection**
   - Regular intervals
   - Complete metrics
   - Quality validation

2. **Analysis**
   - Multiple timeframes
   - Context awareness
   - Pattern validation

3. **Forecasting**
   - Model validation
   - Regular updates
   - Confidence tracking

4. **Visualization**
   - Clear trends
   - Pattern highlights
   - Interactive tools

## Next Steps

- [Compliance Tutorial](compliance_tutorial.md)
- [Advanced Forecasting Guide](forecasting_guide.md)
- [Pattern Analysis Guide](patterns_guide.md)
