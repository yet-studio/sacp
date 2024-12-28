# SACP Protocol Syntax Specification

## Overview
The SafeAI CodeGuard Protocol (SACP) uses a declarative syntax to define safety constraints and behaviors for AI coding assistants. This document specifies the protocol's syntax and usage.

## Protocol Declaration

### Basic Structure
```yaml
@sacp-protocol:
  version: "1.0"
  safety_level: READ_ONLY | SUGGEST_ONLY | CONTROLLED | FULL_ACCESS
  access_scope: SINGLE_FILE | DIRECTORY | PROJECT | WORKSPACE
  constraints:
    max_file_size: <size_in_bytes>
    max_changes_per_session: <number>
    require_human_review: true | false
```

### Example
```yaml
@sacp-protocol:
  version: "1.0"
  safety_level: CONTROLLED
  access_scope: PROJECT
  constraints:
    max_file_size: 1048576  # 1MB
    max_changes_per_session: 50
    require_human_review: true
```

## Safety Levels

### READ_ONLY
- AI can only read and analyze code
- No modifications allowed
- Example:
```yaml
@sacp-protocol:
  safety_level: READ_ONLY
  access_scope: PROJECT
```

### SUGGEST_ONLY
- AI can suggest changes in markdown/diff format
- No direct modifications
- Example:
```yaml
@sacp-protocol:
  safety_level: SUGGEST_ONLY
  access_scope: SINGLE_FILE
  constraints:
    require_human_review: true
```

### CONTROLLED
- AI can modify with strict validation
- All changes logged and validated
- Example:
```yaml
@sacp-protocol:
  safety_level: CONTROLLED
  access_scope: DIRECTORY
  constraints:
    max_changes_per_session: 20
    require_human_review: true
```

### FULL_ACCESS
- Advanced mode with comprehensive logging
- Suitable for trusted environments
- Example:
```yaml
@sacp-protocol:
  safety_level: FULL_ACCESS
  access_scope: WORKSPACE
  constraints:
    max_changes_per_session: 100
    require_human_review: false
```

## Access Scopes

### SINGLE_FILE
- Limits AI access to one file
- Example:
```yaml
access_scope: SINGLE_FILE
target_file: "./src/main.py"
```

### DIRECTORY
- Limits AI access to specific directory
- Example:
```yaml
access_scope: DIRECTORY
target_directory: "./src"
allowed_extensions: [".py", ".js", ".ts"]
```

### PROJECT
- Allows AI access to entire project
- Example:
```yaml
access_scope: PROJECT
excluded_paths: ["./tests", "./docs"]
```

### WORKSPACE
- Allows AI access to multiple projects
- Example:
```yaml
access_scope: WORKSPACE
allowed_projects: ["project1", "project2"]
```

## Constraints

### File Size Constraints
```yaml
constraints:
  max_file_size: 1048576  # 1MB
  max_total_size: 10485760  # 10MB
```

### Change Constraints
```yaml
constraints:
  max_changes_per_session: 50
  max_changes_per_file: 10
  max_files_per_session: 5
```

### Review Constraints
```yaml
constraints:
  require_human_review: true
  review_threshold: "medium"  # low, medium, high
  auto_approve_tests: true
```

## Emergency Stop

### Trigger Conditions
```yaml
emergency_stop:
  triggers:
    - type: "rate_limit"
      threshold: 10
      window_seconds: 60
    - type: "error_rate"
      threshold: 0.2
      window_changes: 20
```

### Recovery Actions
```yaml
emergency_stop:
  recovery:
    auto_rollback: true
    notification_channels: ["slack", "email"]
    require_manual_reset: true
```

## Validation Rules

### Syntax Validation
```yaml
validation:
  syntax:
    enabled: true
    strict_mode: true
```

### Security Patterns
```yaml
validation:
  security_patterns:
    - pattern: "(?i)(password|secret|key)\\s*=\\s*[\"'][^\"']+[\"']"
      severity: "high"
    - pattern: "(?i)execute\\s*\\(\\s*[\"'][^\"']*\\%s[^\"']*[\"']"
      severity: "critical"
```

### Custom Rules
```yaml
validation:
  custom_rules:
    - name: "max_function_length"
      rule: "function_lines <= 50"
      severity: "warning"
```

## Audit Logging

### Log Configuration
```yaml
audit:
  enabled: true
  log_level: "info"  # debug, info, warn, error
  retention_days: 30
```

### Event Types
```yaml
audit:
  events:
    - "file_access"
    - "code_modification"
    - "validation_failure"
    - "emergency_stop"
```

## Integration Examples

### VSCode Integration
```yaml
@sacp-protocol:
  version: "1.0"
  safety_level: CONTROLLED
  access_scope: PROJECT
  ide_integration:
    editor: "vscode"
    features:
      - "inline_suggestions"
      - "validation_highlights"
      - "quick_fixes"
```

### CI/CD Pipeline
```yaml
@sacp-protocol:
  version: "1.0"
  safety_level: CONTROLLED
  access_scope: PROJECT
  ci_integration:
    validate_pr: true
    block_on_violation: true
    report_format: "github_checks"
```
