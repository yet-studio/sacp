# Compliance Rules

## Overview

Compliance rules ensure code follows security best practices, coding standards, and safety guidelines. They complement safety properties by focusing on broader patterns and practices.

## Rule Categories

### 1. Security Rules

```yaml
security:
  - name: input_validation
    pattern: "validate_input\\(.*\\)"
    required: true
  - name: sql_injection
    pattern: "parameterized_query\\(.*\\)"
    required: true
```

### 2. Error Handling

```yaml
error_handling:
  - name: try_except
    pattern: "try:.*except.*:"
    required: true
  - name: logging
    pattern: "logger\\.(error|warning)\\(.*\\)"
    required: true
```

### 3. Resource Management

```yaml
resources:
  - name: file_handling
    pattern: "with open\\(.*\\) as .*:"
    required: true
  - name: connection_closing
    pattern: "close\\(\\)"
    required: true
```

## Rule Properties

- `name`: Rule identifier
- `pattern`: Regex pattern to match
- `required`: Must be present
- `forbidden`: Must not be present
- `message`: Custom message
- `severity`: Rule severity

## Custom Rules

Add custom rules in `sacp.yaml`:

```yaml
compliance:
  rules:
    custom_rules:
      - name: my_rule
        pattern: "custom_pattern"
        required: true
        message: "Custom rule message"
```

## Validation Process

1. Code Analysis
   - Pattern matching
   - AST analysis
   - Context awareness

2. Rule Application
   - Required patterns
   - Forbidden patterns
   - Context rules

3. Reporting
   - Rule violations
   - Suggestions
   - Documentation
