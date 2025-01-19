#!/usr/bin/env python3
"""
SACP Core Protocol Module
Defines the core safety and communication protocols for the system
"""

from enum import Enum, IntEnum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    """Safety levels for protocol operations"""
    READ_ONLY = "READ_ONLY"
    SUGGEST_ONLY = "SUGGEST_ONLY"
    CONTROLLED = "CONTROLLED"
    RESTRICTED = "RESTRICTED"
    FULL_ACCESS = "FULL_ACCESS"

class ComplianceLevel(Enum):
    """Compliance levels for protocol operations"""
    LOW = "LOW"         # Minimal compliance checks
    MEDIUM = "MEDIUM"   # Moderate compliance checks
    HIGH = "HIGH"       # Strict compliance checks
    FULL = "FULL"       # Full compliance with all checks
    STANDARD = "STANDARD"  # Standard compliance checks
    STRICT = "STRICT"

class AccessScope(IntEnum):
    """Access scope levels for protocol operations"""
    NONE = 0
    FILE = 1
    PROJECT = 2
    WORKSPACE = 3
    SYSTEM = 4

    def __lt__(self, other):
        if not isinstance(other, AccessScope):
            return NotImplemented
        return int(self) < int(other)

    def __le__(self, other):
        if not isinstance(other, AccessScope):
            return NotImplemented
        return int(self) <= int(other)

    def __gt__(self, other):
        if not isinstance(other, AccessScope):
            return NotImplemented
        return int(self) > int(other)

    def __ge__(self, other):
        if not isinstance(other, AccessScope):
            return NotImplemented
        return int(self) >= int(other)

@dataclass
class ProtocolConfig:
    """Configuration for protocol behavior"""
    max_retries: int = 3
    timeout_seconds: int = 30
    validate_all: bool = True

@dataclass
class SafetyConstraints:
    """Safety constraints for protocol operations"""
    max_file_size: int = 1024 * 1024  # 1MB default
    allowed_extensions: set = None
    restricted_paths: set = None
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = {'.py', '.txt', '.md'}
        if self.restricted_paths is None:
            self.restricted_paths = {'/etc', '/usr', '/var'}

class EmergencyStop:
    """Emergency stop mechanism for critical operations"""
    def __init__(self):
        self._active = False
        self._reason = None
        logger.info("Emergency stop mechanism initialized")

    @property
    def is_active(self) -> bool:
        return self._active

    def activate(self, reason: str = None) -> None:
        self._active = True
        self._reason = reason
        logger.warning(f"Emergency stop activated: {reason}")

    def deactivate(self) -> None:
        self._active = False
        self._reason = None
        logger.info("Emergency stop deactivated")

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "reason": self._reason
        }

class SafetyProtocol:
    """Core protocol implementation for safety-critical operations"""
    
    def __init__(self, safety_level: str = "READ_ONLY", config: Optional[ProtocolConfig] = None):
        self.safety_level = SafetyLevel(safety_level)
        self.config = config or ProtocolConfig()
        self._operation_history: List[Dict[str, Any]] = []
        logger.info(f"Initialized SafetyProtocol with level: {safety_level}")

    def validate_change(self, change: Dict[str, Any]) -> bool:
        """
        Validate if a change is allowed under current safety level
        
        Args:
            change: Dictionary containing change details
                   Required keys: 'type', 'file'
        Returns:
            bool: True if change is allowed, False otherwise
        """
        try:
            operation_type = change.get("type", "")
            
            if self.safety_level == SafetyLevel.READ_ONLY:
                return operation_type == "read"
                
            if self.safety_level == SafetyLevel.RESTRICTED:
                return operation_type in ["read", "log"]
                
            # FULL_ACCESS level
            return True
            
        except Exception as e:
            logger.error(f"Error validating change: {str(e)}")
            return False

    def log_change(self, change: Dict[str, Any]) -> bool:
        """
        Log a change attempt to operation history
        
        Args:
            change: Dictionary containing change details
        Returns:
            bool: True if logging successful, False otherwise
        """
        try:
            self._operation_history.append({
                "change": change,
                "safety_level": self.safety_level.value,
                "validated": self.validate_change(change)
            })
            logger.info(f"Logged change: {change}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging change: {str(e)}")
            return False

    def get_history(self) -> List[Dict[str, Any]]:
        """Return operation history"""
        return self._operation_history

    def reset_history(self) -> None:
        """Clear operation history"""
        self._operation_history = []
        logger.info("Operation history cleared")

class ProtocolManager:
    """Manager class for handling protocol operations and safety measures"""
    def __init__(self, config: Optional[ProtocolConfig] = None):
        self.config = config or ProtocolConfig()
        self.safety_protocol = SafetyProtocol(safety_level="RESTRICTED", config=self.config)
        self.emergency_stop = EmergencyStop()
        self._active_protocols: Dict[str, Any] = {}
        logger.info("Protocol Manager initialized")

    def register_protocol(self, name: str, protocol: Any) -> bool:
        """Register a new protocol"""
        try:
            if name in self._active_protocols:
                logger.warning(f"Protocol {name} already registered")
                return False
            self._active_protocols[name] = protocol
            logger.info(f"Protocol {name} registered successfully")
            return True
        except Exception as e:
            logger.error(f"Error registering protocol {name}: {str(e)}")
            return False

    def unregister_protocol(self, name: str) -> bool:
        """Unregister a protocol"""
        try:
            if name not in self._active_protocols:
                logger.warning(f"Protocol {name} not found")
                return False
            del self._active_protocols[name]
            logger.info(f"Protocol {name} unregistered successfully")
            return True
        except Exception as e:
            logger.error(f"Error unregistering protocol {name}: {str(e)}")
            return False

    def get_protocol(self, name: str) -> Optional[Any]:
        """Get a registered protocol by name"""
        return self._active_protocols.get(name)

    def list_protocols(self) -> List[str]:
        """List all registered protocols"""
        return list(self._active_protocols.keys())

    def emergency_shutdown(self, reason: str = "Emergency shutdown initiated") -> None:
        """Initiate emergency shutdown of all protocols"""
        self.emergency_stop.activate(reason)
        logger.critical(f"Emergency shutdown initiated: {reason}")
        # Additional shutdown logic can be added here
