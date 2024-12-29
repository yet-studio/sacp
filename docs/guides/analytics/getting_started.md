# Getting Started with Analytics

This guide will help you set up and start using SACP's analytics features.

## Prerequisites

- Python 3.8+
- SQLite
- SACP core installation

## Installation

1. Install analytics dependencies:
   ```bash
   pip install -r requirements-analytics.txt
   ```

2. Verify installation:
   ```python
   from sacp.enterprise.analytics import (
       BehaviorAnalyzer,
       RiskAnalyzer,
       TrendAnalyzer,
       ComplianceAnalyzer
   )
   ```

## Quick Demo

Run the included demo:
```bash
python -m src.enterprise.analytics.examples.run_demo_dashboard
```

This will:
1. Generate example data
2. Launch interactive dashboards
3. Open them in your browser

## Basic Setup

```python
# Initialize analyzers
behavior = BehaviorAnalyzer('analytics.db')
risk = RiskAnalyzer('analytics.db')
trends = TrendAnalyzer('analytics.db')
compliance = ComplianceAnalyzer('analytics.db')

# Create tenant
tenant_id = 'my-company'

# Launch dashboards
behavior.create_dashboard(tenant_id).run_server(port=8050)
risk.create_dashboard(tenant_id).run_server(port=8051)
trends.create_dashboard(tenant_id).run_server(port=8052)
compliance.create_dashboard(tenant_id).run_server(port=8053)
```

## Next Steps

- [Behavior Monitoring Tutorial](behavior_tutorial.md)
- [Risk Assessment Guide](risk_tutorial.md)
- [Trend Analysis Walkthrough](trends_tutorial.md)
- [Compliance Setup](compliance_tutorial.md)
