# Core API Reference

## Safety Module

```python
from sacp.core.safety import SafetyProperty, verify_safety

# Create safety property
property = SafetyProperty(
    name="no_eval",
    description="Prevent eval usage",
    property_type="invariant",
    expression="'eval(' not in code",
    severity="CRITICAL"
)

# Verify code safety
result = verify_safety("my_code.py", [property])
```

## Compliance Module

```python
from sacp.core.compliance import ComplianceRule, check_compliance

# Create compliance rule
rule = ComplianceRule(
    name="input_validation",
    pattern=r"validate_input\(.*\)",
    required=True
)

# Check compliance
result = check_compliance("my_code.py", [rule])
```

## Behavior Module

```python
from sacp.core.behavior import BehaviorAnalyzer

# Create analyzer
analyzer = BehaviorAnalyzer()

# Monitor behavior
with analyzer.monitor() as monitor:
    # Your code here
    results = monitor.get_results()
```

## Protocol Module

```python
from sacp.core.protocol import SafetyLevel, Protocol

# Create protocol
protocol = Protocol(
    name="my_protocol",
    safety_level=SafetyLevel.HIGH
)

# Apply protocol
result = protocol.apply("my_code.py")
```

## Utility Functions

```python
from sacp.core.utils import (
    load_config,
    save_results,
    format_output
)

# Load configuration
config = load_config("sacp.yaml")

# Save results
save_results(results, "report.json")

# Format output
formatted = format_output(results, format="text")
```
