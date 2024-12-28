"""
SafeAI CodeGuard Protocol - Access Control Framework
Implements the access control and permission management system.
"""

from enum import Enum, auto
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import re
from datetime import datetime, timedelta

from .protocol import SafetyLevel, AccessScope


class Permission(Enum):
    """Fine-grained permissions for AI operations"""
    READ = auto()           # Read file contents
    ANALYZE = auto()        # Analyze code (AST, patterns)
    SUGGEST = auto()        # Suggest changes
    MODIFY = auto()         # Make changes
    DELETE = auto()         # Delete files
    CREATE = auto()         # Create new files
    EXECUTE = auto()        # Execute code
    INSTALL = auto()        # Install dependencies


@dataclass
class AccessToken:
    """Represents a time-limited access token"""
    token_id: str
    permissions: Set[Permission]
    safety_level: SafetyLevel
    access_scope: AccessScope
    path_patterns: List[str]
    created_at: datetime
    expires_at: datetime
    owner: str
    is_revoked: bool = False


class AccessPolicy:
    """Defines access policies for different safety levels"""
    
    def __init__(self, safety_level: SafetyLevel):
        self.safety_level = safety_level
        self.permissions = self._get_default_permissions()
        self.excluded_patterns = self._get_excluded_patterns()
        
    def _get_default_permissions(self) -> Set[Permission]:
        """Get default permissions for the safety level"""
        if self.safety_level == SafetyLevel.READ_ONLY:
            return {Permission.READ, Permission.ANALYZE}
            
        if self.safety_level == SafetyLevel.SUGGEST_ONLY:
            return {Permission.READ, Permission.ANALYZE, Permission.SUGGEST}
            
        if self.safety_level == SafetyLevel.CONTROLLED:
            return {
                Permission.READ,
                Permission.ANALYZE,
                Permission.SUGGEST,
                Permission.MODIFY,
                Permission.CREATE
            }
            
        # FULL_ACCESS
        return set(Permission)
        
    def _get_excluded_patterns(self) -> List[str]:
        """Get patterns for files/paths that should be excluded"""
        return [
            r"\.git/.*",
            r"\.env.*",
            r".*_key.*",
            r".*password.*",
            r".*secret.*",
            r"\.ssh/.*",
            r".*\.pem$",
            r".*\.key$",
            r".*\.cert$",
            r".*\.credentials.*"
        ]


class AccessManager:
    """Manages access control and permissions"""
    
    def __init__(self):
        self.tokens: Dict[str, AccessToken] = {}
        self.policies: Dict[SafetyLevel, AccessPolicy] = {}
        self._init_policies()
        
    def _init_policies(self):
        """Initialize policies for all safety levels"""
        for level in SafetyLevel:
            self.policies[level] = AccessPolicy(level)
    
    def create_token(
        self,
        safety_level: SafetyLevel,
        access_scope: AccessScope,
        path_patterns: List[str],
        owner: str,
        duration: timedelta = timedelta(hours=1)
    ) -> AccessToken:
        """Create a new access token"""
        from uuid import uuid4
        
        now = datetime.now()
        token = AccessToken(
            token_id=str(uuid4()),
            permissions=self.policies[safety_level].permissions,
            safety_level=safety_level,
            access_scope=access_scope,
            path_patterns=path_patterns,
            created_at=now,
            expires_at=now + duration,
            owner=owner
        )
        
        self.tokens[token.token_id] = token
        return token
    
    def validate_access(
        self,
        token_id: str,
        required_permission: Permission,
        target_path: str
    ) -> bool:
        """Validate if a token has the required access"""
        if token_id not in self.tokens:
            return False
            
        token = self.tokens[token_id]
        
        # Check if token is valid
        if token.is_revoked or datetime.now() > token.expires_at:
            return False
            
        # Check permission
        if required_permission not in token.permissions:
            return False
            
        # Check path against excluded patterns
        excluded_patterns = self.policies[token.safety_level].excluded_patterns
        if any(re.match(pattern, target_path) for pattern in excluded_patterns):
            return False
            
        # Check path against token's allowed patterns
        if not any(re.match(pattern, target_path) for pattern in token.path_patterns):
            return False
            
        return True
    
    def revoke_token(self, token_id: str):
        """Revoke an access token"""
        if token_id in self.tokens:
            self.tokens[token_id].is_revoked = True
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        now = datetime.now()
        expired = [
            token_id
            for token_id, token in self.tokens.items()
            if now > token.expires_at
        ]
        for token_id in expired:
            del self.tokens[token_id]


class AccessMonitor:
    """Monitors and logs access attempts"""
    
    def __init__(self):
        self.access_log = []
        
    def log_access(
        self,
        token_id: str,
        permission: Permission,
        target_path: str,
        granted: bool,
        timestamp: Optional[datetime] = None
    ):
        """Log an access attempt"""
        log_entry = {
            'token_id': token_id,
            'permission': permission,
            'target_path': target_path,
            'granted': granted,
            'timestamp': timestamp or datetime.now()
        }
        self.access_log.append(log_entry)
    
    def get_access_history(
        self,
        token_id: Optional[str] = None,
        path_pattern: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Query access history with filters"""
        filtered_log = self.access_log
        
        if token_id:
            filtered_log = [
                entry for entry in filtered_log
                if entry['token_id'] == token_id
            ]
            
        if path_pattern:
            filtered_log = [
                entry for entry in filtered_log
                if re.match(path_pattern, entry['target_path'])
            ]
            
        if start_time:
            filtered_log = [
                entry for entry in filtered_log
                if entry['timestamp'] >= start_time
            ]
            
        if end_time:
            filtered_log = [
                entry for entry in filtered_log
                if entry['timestamp'] <= end_time
            ]
            
        return filtered_log
