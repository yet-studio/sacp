# Risk Assessment Tutorial

Learn how to use SACP's predictive risk assessment features for AI safety.

## Tutorial Overview

1. Basic Setup
2. Risk Metrics
3. Model Training
4. Predictions
5. Dashboard Usage

## 1. Basic Setup

```python
from sacp.enterprise.analytics import RiskAnalyzer
from sacp.enterprise.analytics.risk import RiskMetrics

# Initialize analyzer
analyzer = RiskAnalyzer('analytics.db')

# Set tenant ID
tenant_id = 'my-company'
```

## 2. Risk Metrics

### Recording Metrics
```python
# Create metrics
metrics = RiskMetrics(
    safety_score=0.85,
    reliability_score=0.90,
    compliance_score=0.95,
    vulnerability_score=0.15,
    impact_score=0.30,
    probability_score=0.20
)

# Record metrics
await analyzer.record_metrics(tenant_id, metrics)
```

### Automated Collection
```python
from sacp.enterprise.analytics.risk import RiskCollector

# Create collector
collector = RiskCollector(
    analyzer=analyzer,
    tenant_id=tenant_id,
    interval=300  # 5 minutes
)

# Start collection
await collector.start()
```

## 3. Model Training

### Random Forest
```python
# Train model
await analyzer.train_random_forest(
    tenant_id,
    features=[
        'safety_score',
        'reliability_score',
        'compliance_score'
    ],
    target='risk_level'
)

# Get feature importance
importance = analyzer.get_feature_importance()
```

### Gradient Boosting
```python
# Train model
await analyzer.train_gradient_boost(
    tenant_id,
    learning_rate=0.1,
    n_estimators=100
)

# Validate model
score = await analyzer.validate_model('gradient_boost')
```

### Deep Learning
```python
# Configure model
await analyzer.configure_deep_learning(
    layers=[64, 32, 16],
    dropout=0.3,
    activation='relu'
)

# Train model
await analyzer.train_deep_learning(
    tenant_id,
    epochs=100,
    batch_size=32
)
```

## 4. Predictions

### Single Predictions
```python
# Get risk prediction
prediction = await analyzer.predict_risk(
    tenant_id,
    metrics=current_metrics
)

print(f"Risk Level: {prediction.risk_level}")
print(f"Confidence: {prediction.confidence}")
print(f"Factors: {prediction.factors}")
```

### Batch Predictions
```python
# Get multiple predictions
predictions = await analyzer.predict_batch(
    tenant_id,
    metric_list=metrics_batch
)

for pred in predictions:
    print(f"Time: {pred.timestamp}")
    print(f"Risk: {pred.risk_level}")
```

### Mitigation Suggestions
```python
# Get risk mitigation suggestions
suggestions = await analyzer.get_mitigations(
    tenant_id,
    risk_level=prediction.risk_level,
    factors=prediction.factors
)

for suggestion in suggestions:
    print(f"Action: {suggestion.action}")
    print(f"Impact: {suggestion.impact}")
    print(f"Priority: {suggestion.priority}")
```

## 5. Dashboard Usage

### Launch Dashboard
```python
# Create dashboard
app = analyzer.create_dashboard(tenant_id)

# Run server
app.run_server(port=8051)
```

### Dashboard Features

1. **Risk Overview**
   - Current risk level
   - Risk trends
   - Factor breakdown

2. **Model Insights**
   - Prediction confidence
   - Feature importance
   - Model performance

3. **Mitigation Tools**
   - Suggested actions
   - Impact analysis
   - Priority ranking

4. **Analysis Tools**
   - Time range selection
   - Factor correlation
   - Trend analysis

## Best Practices

1. **Data Quality**
   - Regular updates
   - Complete metrics
   - Validated data

2. **Model Management**
   - Regular retraining
   - Performance monitoring
   - Version control

3. **Predictions**
   - Context awareness
   - Confidence checking
   - Factor analysis

4. **Mitigation**
   - Clear actions
   - Impact assessment
   - Follow-up tracking

## Next Steps

- [Trend Analysis Tutorial](trends_tutorial.md)
- [Model Configuration Guide](models_guide.md)
- [Risk Factor Analysis](factors_guide.md)
