"""
SafeAI CodeGuard Protocol - Safety Constraints
Defines and enforces safety constraints for AI operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
import re
import psutil
import z3


class SafetyConstraint(ABC):
    """Base class for all safety constraints"""
    
    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validates if operation meets safety constraints"""
        pass
    
    @abstractmethod
    def enforce(self, context: Dict[str, Any]) -> None:
        """Enforces safety constraints on operation"""
        pass


@dataclass
class ResourceConstraint(SafetyConstraint):
    """Enforces resource usage constraints"""
    max_memory_mb: int
    max_cpu_percent: float
    max_disk_mb: int
    check_interval_ms: int = 100
    
    def __post_init__(self):
        self.process = psutil.Process()
        self.last_check = datetime.now()
        self.violations = []
    
    def validate(self, context: Dict[str, Any], force: bool = False) -> bool:
        """Validates resource usage"""
        current_time = datetime.now()
        
        # Only check at specified intervals unless forced
        if not force and (current_time - self.last_check).total_seconds() * 1000 < self.check_interval_ms:
            return True
        
        self.last_check = current_time
        
        # Check memory usage
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        if memory_mb > self.max_memory_mb:
            self.violations.append({
                'type': 'memory',
                'value': memory_mb,
                'limit': self.max_memory_mb,
                'timestamp': current_time
            })
            return False
        
        # Check CPU usage
        cpu_percent = self.process.cpu_percent()
        if cpu_percent > self.max_cpu_percent:
            self.violations.append({
                'type': 'cpu',
                'value': cpu_percent,
                'limit': self.max_cpu_percent,
                'timestamp': current_time
            })
            return False
        
        # Check disk usage
        disk_usage = sum(
            getattr(f, 'size', 0) 
            for f in context.get('modified_files', [])
        )
        if disk_usage > self.max_disk_mb * 1024 * 1024:
            self.violations.append({
                'type': 'disk',
                'value': disk_usage / (1024 * 1024),
                'limit': self.max_disk_mb,
                'timestamp': current_time
            })
            return False
        
        return True
    
    def enforce(self, context: Dict[str, Any]) -> None:
        """Enforces resource constraints by raising ResourceError if violated"""
        if not self.validate(context, force=True):
            latest_violation = self.violations[-1] if self.violations else None
            if latest_violation:
                msg = f"Resource limit exceeded: {latest_violation['type']} usage {latest_violation['value']:.2f} > {latest_violation['limit']}"
            else:
                msg = "Resource constraint violated"
            raise ResourceError(msg)


@dataclass
class OperationConstraint(SafetyConstraint):
    """Enforces operation safety constraints"""
    max_operations_per_minute: int
    max_file_size_mb: int
    restricted_patterns: Set[str]
    allowed_operations: Set[str]
    max_impact_score: float = 0.8
    
    def __post_init__(self):
        self.operation_history = []
        self.impact_calculator = z3.Solver()
    
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validates operation safety"""
        operation = context['operation']
        current_time = datetime.now()
        
        # Clean old history
        self.operation_history = [
            op for op in self.operation_history
            if current_time - op['timestamp'] <= timedelta(minutes=1)
        ]
        
        # Check operation rate
        if len(self.operation_history) >= self.max_operations_per_minute:
            return False
        
        # Check operation type
        if operation['type'] not in self.allowed_operations:
            return False
        
        # Check file size
        if operation.get('file_size', 0) > self.max_file_size_mb * 1024 * 1024:
            return False
        
        # Check restricted patterns
        content = operation.get('content', '')
        for pattern in self.restricted_patterns:
            if re.search(pattern, content):
                return False
        
        # Calculate impact score
        impact_score = self._calculate_impact(operation)
        if impact_score > self.max_impact_score:
            return False
        
        # Record operation
        self.operation_history.append({
            'operation': operation,
            'timestamp': current_time,
            'impact_score': impact_score
        })
        
        return True
    
    def enforce(self, context: Dict[str, Any]) -> None:
        """Enforces operation constraints"""
        if not self.validate(context):
            raise OperationError(
                "Operation violates safety constraints"
            )
    
    def _calculate_impact(self, operation: Dict[str, Any]) -> float:
        """Calculates operation impact score using Z3 solver"""
        # Reset solver for new calculation
        self.impact_calculator.reset()
        
        impact = z3.Real('impact')
        
        # Add basic constraints
        self.impact_calculator.add(impact >= 0)
        self.impact_calculator.add(impact <= 1)
        
        # Factor in operation type
        type_weights = {
            'read': 0.1,
            'write': 0.6,
            'delete': 0.9,
            'modify': 0.7
        }
        type_impact = type_weights.get(operation['type'], 0.5)
        self.impact_calculator.add(impact >= type_impact * 0.8)
        
        # Factor in file importance
        if 'file_path' in operation:
            if 'test' in operation['file_path']:
                self.impact_calculator.add(impact <= 0.6)
            if 'core' in operation['file_path']:
                self.impact_calculator.add(impact >= 0.4)
        
        # Factor in content size
        content_size = len(operation.get('content', ''))
        if content_size > 1000:
            self.impact_calculator.add(impact >= 0.3)
        
        # Solve constraints
        if self.impact_calculator.check() == z3.sat:
            model = self.impact_calculator.model()
            # Convert Z3 decimal to float
            decimal_str = str(model[impact].as_decimal(6)).rstrip('?')
            return float(decimal_str)
        
        return 1.0  # Maximum impact if cannot determine


@dataclass
class AccessConstraint(SafetyConstraint):
    """Enforces access control constraints"""
    allowed_paths: Set[str]
    restricted_paths: Set[str]
    required_permissions: Dict[str, Set[str]]
    max_scope: str = 'directory'
    
    def validate(self, context: Dict[str, Any]) -> bool:
        """Validates access control"""
        operation = context['operation']
        user = context.get('user', {})
        
        # Check path restrictions
        path = operation.get('file_path', '')
        
        # Deny if path is restricted
        if any(path.startswith(r) for r in self.restricted_paths):
            return False
        
        # Allow only if path is in allowed paths
        if not any(path.startswith(a) for a in self.allowed_paths):
            return False
        
        # Check permissions
        required = self.required_permissions.get(operation['type'], set())
        if not required.issubset(user.get('permissions', set())):
            return False
        
        # Check scope
        if self.max_scope == 'file' and '/' in path:
            return False
        if self.max_scope == 'directory' and '../' in path:
            return False
        
        return True
    
    def enforce(self, context: Dict[str, Any]) -> None:
        """Enforces access constraints"""
        if not self.validate(context):
            raise AccessError(
                "Operation violates access constraints"
            )


class ResourceError(Exception):
    """Raised when resource constraints are violated"""
    pass


class OperationError(Exception):
    """Raised when operation constraints are violated"""
    pass


class AccessError(Exception):
    """Raised when access constraints are violated"""
    pass
