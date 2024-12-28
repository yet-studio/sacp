"""
SafeAI CodeGuard Protocol - Configuration Parser
Handles parsing and validation of SACP protocol configuration files.
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from .protocol import SafetyLevel, AccessScope, SafetyConstraints


class ConfigError(Exception):
    """Base class for configuration errors"""
    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails"""
    pass


class ConfigParser:
    """Parses and validates SACP protocol configuration"""
    
    REQUIRED_FIELDS = ['version', 'safety_level', 'access_scope']
    SUPPORTED_VERSIONS = ['1.0']
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.config: Dict[str, Any] = {}

    def load_from_file(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from a YAML file"""
        if config_path:
            self.config_path = Path(config_path)
        
        if not self.config_path or not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")
            
        try:
            with open(self.config_path, 'r') as f:
                content = f.read()
                if '@sacp-protocol:' not in content:
                    raise ConfigError("Missing @sacp-protocol declaration")
                    
                # Remove the @sacp-protocol prefix and parse YAML
                yaml_content = content.split('@sacp-protocol:', 1)[1]
                self.config = yaml.safe_load(yaml_content)
                
            self.validate()
            return self.config
            
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML: {str(e)}")

    def load_from_string(self, config_str: str) -> Dict[str, Any]:
        """Load configuration from a string"""
        try:
            if '@sacp-protocol:' not in config_str:
                raise ConfigError("Missing @sacp-protocol declaration")
                
            # Remove the @sacp-protocol prefix and parse YAML
            yaml_content = config_str.split('@sacp-protocol:', 1)[1]
            self.config = yaml.safe_load(yaml_content)
            
            self.validate()
            return self.config
            
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML: {str(e)}")

    def validate(self) -> None:
        """Validate the configuration"""
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in self.config:
                raise ConfigValidationError(f"Missing required field: {field}")

        # Validate version
        if self.config['version'] not in self.SUPPORTED_VERSIONS:
            raise ConfigValidationError(
                f"Unsupported version: {self.config['version']}. "
                f"Supported versions: {self.SUPPORTED_VERSIONS}"
            )

        # Validate safety level
        try:
            SafetyLevel[self.config['safety_level']]
        except KeyError:
            raise ConfigValidationError(
                f"Invalid safety_level: {self.config['safety_level']}. "
                f"Valid values: {[level.name for level in SafetyLevel]}"
            )

        # Validate access scope
        try:
            AccessScope[self.config['access_scope']]
        except KeyError:
            raise ConfigValidationError(
                f"Invalid access_scope: {self.config['access_scope']}. "
                f"Valid values: {[scope.name for scope in AccessScope]}"
            )

        # Validate constraints if present
        if 'constraints' in self.config:
            self._validate_constraints(self.config['constraints'])

    def _validate_constraints(self, constraints: Dict[str, Any]) -> None:
        """Validate constraint values"""
        if 'max_file_size' in constraints:
            if not isinstance(constraints['max_file_size'], int) or constraints['max_file_size'] <= 0:
                raise ConfigValidationError("max_file_size must be a positive integer")

        if 'max_changes_per_session' in constraints:
            if not isinstance(constraints['max_changes_per_session'], int) or constraints['max_changes_per_session'] <= 0:
                raise ConfigValidationError("max_changes_per_session must be a positive integer")

        if 'require_human_review' in constraints:
            if not isinstance(constraints['require_human_review'], bool):
                raise ConfigValidationError("require_human_review must be a boolean")

    def get_protocol_config(self) -> 'ProtocolConfig':
        """Convert parsed config to ProtocolConfig object"""
        from datetime import datetime
        import uuid
        
        constraints = SafetyConstraints(
            max_file_size=self.config.get('constraints', {}).get('max_file_size', 1024 * 1024),
            max_changes_per_session=self.config.get('constraints', {}).get('max_changes_per_session', 50),
            require_human_review=self.config.get('constraints', {}).get('require_human_review', True)
        )
        
        return ProtocolConfig(
            safety_level=SafetyLevel[self.config['safety_level']],
            access_scope=AccessScope[self.config['access_scope']],
            constraints=constraints,
            session_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            owner="system"  # This should be configurable
        )
