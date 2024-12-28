# Quick Start Guide

## Initialize Project

Create a new SACP project:

```bash
sacp init my-project
cd my-project
```

This creates:
- `sacp.yaml`: Configuration file
- `.sacp/`: Project directory

## Basic Configuration

Edit `sacp.yaml`:

```yaml
project:
  name: my-project
  version: 1.0.0

safety:
  level: standard
  properties:
    - name: no_eval
      severity: critical
    - name: input_validation
      severity: high

compliance:
  rules:
    - security_best_practices
    - error_handling
```

## First Verification

1. Create a Python file:

```python
# main.py
def process_data(data):
    return data.upper()
```

2. Run verification:

```bash
sacp verify main.py
```

## Using the IDE Extension

1. Open project in VSCode/JetBrains
2. Enable SACP extension
3. See real-time safety checks

## Next Steps

- Review [Configuration](configuration.md)
- Explore safety properties
- Add custom rules
