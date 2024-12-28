"""
Example SACP Plugin: Behavior Monitor
Demonstrates runtime behavior monitoring capabilities.
"""

from typing import Dict, List, Any, Callable
import time
import psutil
from src.ecosystem.plugin import PluginInterface, SafetyProperty


class BehaviorMonitorPlugin(PluginInterface):
    """Example plugin that monitors runtime behavior"""

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration"""
        self.config = config
        self.start_time = time.time()
        self.process = psutil.Process()
        return True

    def get_safety_properties(self) -> List[SafetyProperty]:
        """Define safety properties for runtime behavior"""
        return [
            SafetyProperty(
                name="resource_usage",
                description="Monitor resource usage",
                property_type="runtime",
                expression="memory_percent < 80 and cpu_percent < 90",
                severity="HIGH"
            ),
            SafetyProperty(
                name="execution_time",
                description="Monitor execution time",
                property_type="runtime",
                expression="execution_time < max_execution_time",
                severity="MEDIUM"
            )
        ]

    def get_compliance_rules(self) -> Dict[str, Any]:
        """Define compliance rules for runtime behavior"""
        return {
            "resource_logging": {
                "description": "Ensure resource usage logging",
                "pattern": r"log_resource_usage\(|ResourceMonitor\."
            },
            "performance_tracking": {
                "description": "Track performance metrics",
                "pattern": r"track_performance\(|PerformanceTracker\."
            }
        }

    def get_behavior_validators(self) -> List[Callable]:
        """Define behavior validators for runtime monitoring"""
        def validate_memory_usage(context: Dict[str, Any]) -> bool:
            """Validate memory usage is within limits"""
            memory_percent = self.process.memory_percent()
            memory_limit = self.config.get('memory_limit_percent', 80)
            
            context['memory_percent'] = memory_percent
            return memory_percent < memory_limit

        def validate_cpu_usage(context: Dict[str, Any]) -> bool:
            """Validate CPU usage is within limits"""
            cpu_percent = self.process.cpu_percent()
            cpu_limit = self.config.get('cpu_limit_percent', 90)
            
            context['cpu_percent'] = cpu_percent
            return cpu_percent < cpu_limit

        def validate_execution_time(context: Dict[str, Any]) -> bool:
            """Validate execution time is within limits"""
            current_time = time.time()
            execution_time = current_time - self.start_time
            max_time = self.config.get('max_execution_time', 300)  # 5 minutes
            
            context['execution_time'] = execution_time
            context['max_execution_time'] = max_time
            return execution_time < max_time

        return [
            validate_memory_usage,
            validate_cpu_usage,
            validate_execution_time
        ]

    def cleanup(self):
        """Clean up monitoring resources"""
        pass
