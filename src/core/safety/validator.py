#!/usr/bin/env python3
"""
SACP Safety Validator Module
Implements validation rules and safety checks for the protocol
"""

from typing import Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ValidationResult(NamedTuple):
    """Result of a validation check"""
    valid: bool
    message: Optional[str] = None

@dataclass
class ValidationConfig:
    """Configuration for validation rules"""
    max_file_size: int = 1024 * 1024  # 1MB
    allowed_extensions: set = None
    restricted_paths: set = None

class SafetyValidator:
    """Implements safety validation rules"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.config.allowed_extensions = self.config.allowed_extensions or {'.py', '.txt', '.md'}
        self.config.restricted_paths = self.config.restricted_paths or {'/etc/passwd', '/etc/shadow', '/usr/bin', '/var/log'}
        self.constraints = []
        logger.info("Initialized SafetyValidator")

    def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate operation context against safety rules
        
        Args:
            context: Dictionary containing operation details
                    Required keys: 'operation', 'file'
        Returns:
            ValidationResult: Result of validation with message if invalid
        """
        try:
            # Basic validation
            if not self._validate_basic(context):
                return ValidationResult(False, "Failed basic validation")

            # File validation
            if not self._validate_file(context):
                return ValidationResult(False, "Failed file validation")

            # Operation validation
            if not self._validate_operation(context):
                return ValidationResult(False, "Failed operation validation")

            return ValidationResult(True)

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return ValidationResult(False, f"Validation error: {str(e)}")

    def _validate_basic(self, context: Dict[str, Any]) -> bool:
        """Basic context validation"""
        required_keys = {'operation', 'file'}
        return all(key in context for key in required_keys)

    def _validate_file(self, context: Dict[str, Any]) -> bool:
        """Validate file-related constraints"""
        file_path = context.get('file', '')
        
        logger.debug("Validating file path: %s", file_path)
        logger.debug(f"File path details: {file_path}")
        
        # Check file extension
        if not any(file_path.endswith(ext) for ext in self.config.allowed_extensions):
            logger.warning(f"Invalid file extension: {file_path}")
            return False
            
        # Check restricted paths
        if any(file_path.startswith(path) for path in self.config.restricted_paths):
            logger.warning(f"Access to restricted path: {file_path}")
            return False
            
        return True

    def _validate_operation(self, context: Dict[str, Any]) -> bool:
        """Validate operation-specific rules"""
        operation = context.get('operation', {})
        logger.debug("Validating operation: %s", operation)
        logger.debug(f"Context details: {context}")
        logger.debug(f"Operation details: {operation}")
        
        # Get operation type
        op_type = operation.get('type')
        if not op_type:
            logger.warning("Missing operation type")
            return False
            
        # Validate operation type
        allowed_operations = {'read', 'write', 'delete', 'move'}
        if op_type not in allowed_operations:
            logger.warning(f"Invalid operation type: {op_type}")
            return False
            
        # Validate operation content
        content = operation.get('content', '')
        unsafe_patterns = {'eval', 'exec', 'subprocess', 'os.system'}
        if any(pattern in content for pattern in unsafe_patterns):
            logger.warning(f"Found unsafe pattern in content: {content}")
            return False
            
        return True

    def add_constraint(self, constraint):
        # Method to add a constraint for validation
        logger.info(f"Adding constraint: {constraint}")
        logger.debug(f"Adding constraint: {constraint}")
        self.constraints.append(constraint)
