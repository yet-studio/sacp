# Safety Trends

The safety trends component analyzes long-term safety patterns and forecasts future trends.

## Features

### 1. Time Series Analysis
- Prophet forecasting
- Seasonal decomposition
- Trend classification
- Pattern correlation

### 2. Trend Metrics

```python
@dataclass
class TrendMetrics:
    safety_violations: int
    risk_level: float
    incident_count: int
    recovery_time: float
    mitigation_effectiveness: float
    compliance_rate: float
```

### 3. Analysis Types
- Trend detection
- Seasonality analysis
- Anomaly detection
- Cross-correlation

### 4. Dashboard

![Trends Dashboard](../images/trends_dashboard.png)

Components:
- Trend forecasts
- Seasonal patterns
- Anomaly highlights
- Correlation matrix
- Metric breakdowns

## Usage

```python
from sacp.enterprise.analytics import TrendAnalyzer

# Initialize
analyzer = TrendAnalyzer('analytics.db')

# Record metrics
metrics = TrendMetrics(
    safety_violations=5,
    risk_level=0.3,
    incident_count=2,
    recovery_time=4.5,
    mitigation_effectiveness=0.8,
    compliance_rate=0.9
)
await analyzer.record_metrics('tenant-1', metrics)

# Analyze trends
trends = await analyzer.analyze_trends(
    'tenant-1',
    start_time,
    end_time
)

# Create dashboard
app = analyzer.create_dashboard('tenant-1')
app.run_server(port=8052)
```

## Analysis Methods

### 1. Prophet
- Time series forecasting
- Multiple seasonality
- Holiday effects
- Trend changepoints

### 2. Seasonal Decomposition
- Trend component
- Seasonal component
- Residual analysis
- Pattern extraction

### 3. Anomaly Detection
- Statistical methods
- Pattern-based
- Threshold analysis
- Confidence scoring

## Configuration

```python
{
    "prophet": {
        "changepoint_prior_scale": 0.05,
        "seasonality_prior_scale": 10,
        "holidays_prior_scale": 10,
        "mcmc_samples": 0
    },
    "decomposition": {
        "period": 24,
        "model": "additive",
        "extrapolate_trend": 1
    },
    "anomaly": {
        "window_size": 24,
        "contamination": 0.1,
        "method": "statistical"
    }
}
```

## Best Practices

1. **Data Collection**:
   - Consistent intervals
   - Complete time series
   - Quality validation

2. **Analysis**:
   - Appropriate timeframes
   - Multiple methods
   - Context awareness

3. **Forecasting**:
   - Confidence intervals
   - Model validation
   - Regular updates

4. **Visualization**:
   - Clear trends
   - Interactive exploration
   - Meaningful annotations
