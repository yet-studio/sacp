# Compliance Monitoring Tutorial

Learn how to monitor and report on safety compliance using SACP's compliance features.

## Tutorial Overview

1. Basic Setup
2. Metrics Recording
3. Report Generation
4. Recommendations
5. Dashboard Usage

## 1. Basic Setup

```python
from sacp.enterprise.analytics import ComplianceAnalyzer
from sacp.enterprise.analytics.compliance import ComplianceMetrics

# Initialize analyzer
analyzer = ComplianceAnalyzer('analytics.db')

# Set tenant ID
tenant_id = 'my-company'
```

## 2. Metrics Recording

### Manual Recording
```python
# Create metrics
metrics = ComplianceMetrics(
    policy_violations=2,
    policy_adherence=0.95,
    risk_violations=1,
    safety_compliance=0.92,
    audit_score=0.88,
    resolution_time=4.5
)

# Record metrics
await analyzer.record_metrics(tenant_id, metrics)
```

### Automated Collection
```python
from sacp.enterprise.analytics.compliance import ComplianceCollector

# Create collector
collector = ComplianceCollector(
    analyzer=analyzer,
    tenant_id=tenant_id,
    interval=300  # 5 minutes
)

# Start collection
await collector.start()
```

## 3. Report Generation

### Basic Report
```python
# Generate report
report = await analyzer.generate_report(
    tenant_id,
    'monthly',
    start_time,
    end_time
)

print(f"ID: {report.id}")
print(f"Type: {report.report_type}")
print(f"Metrics: {report.metrics}")
```

### Custom Report
```python
# Configure report
await analyzer.configure_report(
    tenant_id,
    sections=[
        'violations',
        'trends',
        'recommendations'
    ],
    format='html'
)

# Generate custom report
report = await analyzer.generate_custom_report(
    tenant_id,
    start_time,
    end_time
)
```

## 4. Recommendations

### Get Recommendations
```python
# Get current recommendations
recommendations = await analyzer.get_recommendations(
    tenant_id,
    category='all'
)

for rec in recommendations:
    print(f"Category: {rec.category}")
    print(f"Priority: {rec.priority}")
    print(f"Description: {rec.description}")
```

### Implementation Tracking
```python
# Track implementation
await analyzer.track_recommendation(
    tenant_id,
    recommendation_id,
    status='in_progress',
    notes='Started implementation'
)

# Get implementation status
status = await analyzer.get_implementation_status(
    tenant_id,
    recommendation_id
)
```

## 5. Dashboard Usage

### Launch Dashboard
```python
# Create dashboard
app = analyzer.create_dashboard(tenant_id)

# Run server
app.run_server(port=8053)
```

### Dashboard Features

1. **Compliance Overview**
   - Policy adherence
   - Safety compliance
   - Audit scores

2. **Violation Tracking**
   - Active violations
   - Resolution times
   - Violation trends

3. **Recommendations**
   - Priority items
   - Implementation status
   - Impact assessment

4. **Analysis Tools**
   - Time range selection
   - Metric comparison
   - Trend analysis

## Best Practices

1. **Data Management**
   - Regular backups
   - Data validation
   - Audit trails

2. **Monitoring**
   - Real-time tracking
   - Alert thresholds
   - Response plans

3. **Reporting**
   - Clear metrics
   - Action items
   - Follow-up tasks

4. **Compliance**
   - Policy updates
   - Training records
   - Documentation

## Next Steps

- [Advanced Reporting Guide](reporting_guide.md)
- [Custom Dashboard Guide](dashboard_guide.md)
- [Policy Management Guide](policy_guide.md)
