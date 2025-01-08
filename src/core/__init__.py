"""
SafeAI CodeGuard Protocol - Core Module
"""

from .protocol import (
    SafetyLevel,
    AccessScope,
    SafetyConstraints,
    ProtocolConfig,
    EmergencyStop,
    ProtocolManager
)

from .safety.validator import SafetyValidator

__version__ = '0.1.0'
