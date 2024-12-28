# Safety Properties

## Overview

Safety properties in SACP define constraints and rules that code must follow to be considered safe. They help prevent common vulnerabilities and ensure AI safety guidelines are met.

## Property Types

### 1. Invariants

Static rules that must always be true:

```yaml
name: no_eval
description: Prevents use of eval()
type: invariant
expression: "'eval(' not in code"
severity: CRITICAL
```

### 2. Runtime Checks

Dynamic rules checked during execution:

```yaml
name: memory_limit
description: Memory usage limit
type: runtime
expression: "memory_usage < MAX_MEMORY"
severity: HIGH
```

### 3. Behavioral Properties

Complex patterns of behavior:

```yaml
name: rate_limiting
description: API rate limiting
type: behavioral
expression: "call_frequency <= MAX_RATE"
severity: MEDIUM
```

## Severity Levels

- `CRITICAL`: Must be fixed immediately
- `HIGH`: Should be fixed soon
- `MEDIUM`: Should be reviewed
- `LOW`: Best practice suggestions

## Custom Properties

Create custom properties in `sacp.yaml`:

```yaml
safety:
  properties:
    - name: custom_rule
      description: Custom safety rule
      type: invariant
      expression: "custom_condition == True"
      severity: HIGH
```

## Best Practices

1. Start with standard properties
2. Add custom properties gradually
3. Review and adjust severity levels
4. Document property rationale
5. Test properties thoroughly
