"""
Example SACP Plugin: Safety Checker
Demonstrates a basic safety checking plugin implementation.
"""

from typing import Dict, List, Any, Callable
from src.ecosystem.plugin import PluginInterface, SafetyProperty
from src.verification.safety import SafetyLevel


class SafetyCheckerPlugin(PluginInterface):
    """Example plugin that implements basic safety checks"""

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration"""
        self.config = config
        self.severity_threshold = config.get('severity_threshold', 'LOW')
        return True

    def get_safety_properties(self) -> List[SafetyProperty]:
        """Define safety properties for common vulnerabilities"""
        return [
            SafetyProperty(
                name="no_eval",
                description="Prevents use of eval() function",
                property_type="invariant",
                expression="'eval(' not in code",
                severity="CRITICAL"
            ),
            SafetyProperty(
                name="no_exec",
                description="Prevents use of exec() function",
                property_type="invariant",
                expression="'exec(' not in code",
                severity="CRITICAL"
            ),
            SafetyProperty(
                name="no_shell_injection",
                description="Prevents shell injection vulnerabilities",
                property_type="invariant",
                expression="not any(cmd in code for cmd in ['os.system', 'subprocess.call', 'subprocess.run'])",
                severity="HIGH"
            ),
            SafetyProperty(
                name="no_unsafe_pickle",
                description="Prevents unsafe pickle usage",
                property_type="invariant",
                expression="'pickle.loads' not in code or 'safe_pickle' in code",
                severity="HIGH"
            )
        ]

    def get_compliance_rules(self) -> Dict[str, Any]:
        """Define compliance rules for code safety"""
        return {
            "input_validation": {
                "description": "Ensure input validation is present",
                "pattern": r"validate_input\(|input_validator\.|@validate_input"
            },
            "safe_file_operations": {
                "description": "Use safe file operations",
                "pattern": r"safe_open\(|PathLib\.Path|with\s+open\("
            },
            "proper_error_handling": {
                "description": "Ensure proper error handling",
                "pattern": r"try:.+except\s+\w+:"
            }
        }

    def get_behavior_validators(self) -> List[Callable]:
        """Define behavior validators for runtime checks"""
        def validate_input_handling(context: Dict[str, Any]) -> bool:
            """Validate proper input handling"""
            if 'input_data' not in context:
                return True
            return all(
                isinstance(value, (str, int, float, bool))
                for value in context['input_data'].values()
            )

        def validate_resource_usage(context: Dict[str, Any]) -> bool:
            """Validate resource usage limits"""
            limits = self.config.get('resource_limits', {})
            usage = context.get('resource_usage', {})
            
            return all(
                usage.get(resource, 0) <= limit
                for resource, limit in limits.items()
            )

        return [validate_input_handling, validate_resource_usage]

    def cleanup(self):
        """Clean up any resources used by the plugin"""
        pass
