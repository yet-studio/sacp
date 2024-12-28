# SACP Ecosystem Documentation

## Overview

The SACP ecosystem provides a flexible and extensible platform for AI safety and verification. This document describes the key components and how to use them.

## Package Management

SACP uses a package management system to distribute and manage safety components, rules, and plugins.

### Installing Packages

```bash
sacp package install <package-name>
sacp package install <package-name>@<version>
```

### Managing Packages

```bash
sacp package list
sacp package update <package-name>
sacp package uninstall <package-name>
```

### Creating Packages

1. Create a new package directory:
```bash
sacp package init my-package
```

2. Edit the package metadata in `package.yaml`:
```yaml
name: my-package
version: 1.0.0
description: My SACP package
author: Your Name
dependencies:
  - sacp-core>=1.0.0
```

3. Build and publish:
```bash
sacp package build
sacp package publish
```

## Plugin System

The plugin system allows extending SACP with custom safety rules, compliance checks, and behavior validators.

### Creating Plugins

1. Create a new plugin:
```python
from sacp.ecosystem.plugin import PluginInterface, SafetyProperty

class MyPlugin(PluginInterface):
    def initialize(self, config):
        self.config = config
        return True
    
    def get_safety_properties(self):
        return [
            SafetyProperty(
                name="my_rule",
                description="Custom safety rule",
                property_type="invariant",
                expression="my_condition == True",
                severity="HIGH"
            )
        ]
    
    def get_compliance_rules(self):
        return {
            "my_rule": {
                "description": "Custom compliance rule",
                "pattern": r"unsafe_pattern"
            }
        }
    
    def get_behavior_validators(self):
        def validator(context):
            return context.get("safe", False)
        return [validator]
    
    def cleanup(self):
        pass
```

2. Create plugin metadata in `plugin.yaml`:
```yaml
name: my-plugin
version: 1.0.0
description: My SACP plugin
author: Your Name
entry_point: plugin.MyPlugin
capabilities:
  - safety
  - compliance
  - behavior
```

### Using Plugins

```python
from sacp.ecosystem.plugin import PluginManager

# Initialize plugin manager
manager = PluginManager()

# Discover plugins
plugins = manager.discover_plugins()

# Load plugin
manager.load_plugin(plugins[0])

# Get aggregated safety properties
properties = manager.get_all_safety_properties()
```

## Contributing

We welcome contributions to the SACP ecosystem! Here's how you can contribute:

1. **Submit Packages**: Create and share reusable safety components
2. **Develop Plugins**: Extend SACP with new capabilities
3. **Improve Documentation**: Help others understand and use SACP
4. **Report Issues**: Help us improve by reporting bugs and suggesting features

## Community Guidelines

1. **Code Quality**
   - Follow PEP 8 style guide
   - Write clear documentation
   - Include tests for new features

2. **Safety First**
   - Prioritize safety in all contributions
   - Document safety implications
   - Include safety tests

3. **Collaboration**
   - Be respectful and professional
   - Follow the code of conduct
   - Help others learn and improve

## Support

- GitHub Issues: Report bugs and request features
- Documentation: [docs.sacp.dev](https://docs.sacp.dev)
- Community Forum: [community.sacp.dev](https://community.sacp.dev)
- Email: support@sacp.dev
