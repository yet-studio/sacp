"""
SafeAI CodeGuard Protocol - Enterprise Access Management
Implements fine-grained access control for enterprise teams.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union
from enum import Enum, auto
from datetime import datetime, timedelta
import uuid
import jwt
from pathlib import Path

class AccessLevel(Enum):
    """Access levels for resources"""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    OWNER = 4

class ResourceType(Enum):
    """Types of resources"""
    FILE = auto()
    DIRECTORY = auto()
    PROJECT = auto()
    TEAM = auto()
    POLICY = auto()
    REPORT = auto()

@dataclass
class AccessToken:
    """JWT-based access token"""
    token_id: str
    user_id: str
    teams: List[str]
    scopes: Dict[str, AccessLevel]
    issued_at: datetime
    expires_at: datetime
    metadata: Dict = field(default_factory=dict)

@dataclass
class AccessPolicy:
    """Access control policy"""
    id: str
    name: str
    description: str
    resource_type: ResourceType
    required_level: AccessLevel
    team_overrides: Dict[str, AccessLevel] = field(default_factory=dict)
    user_overrides: Dict[str, AccessLevel] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

class AccessManager:
    """Manages access control for enterprise resources"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.policies: Dict[str, AccessPolicy] = {}
        self.tokens: Dict[str, AccessToken] = {}
    
    def create_token(
        self,
        user_id: str,
        teams: List[str],
        scopes: Dict[str, AccessLevel],
        duration: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """Create a new access token"""
        try:
            now = datetime.utcnow()
            token_id = str(uuid.uuid4())
            
            token = AccessToken(
                token_id=token_id,
                user_id=user_id,
                teams=teams,
                scopes=scopes,
                issued_at=now,
                expires_at=now + duration
            )
            
            payload = {
                "token_id": token.token_id,
                "user_id": token.user_id,
                "teams": token.teams,
                "scopes": {k: v.value for k, v in token.scopes.items()},
                "iat": int(token.issued_at.timestamp()),
                "exp": int(token.expires_at.timestamp())
            }
            
            jwt_token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            self.tokens[token_id] = token
            
            return jwt_token
            
        except Exception as e:
            return None
    
    def validate_token(self, jwt_token: str) -> Optional[AccessToken]:
        """Validate and decode an access token"""
        try:
            payload = jwt.decode(jwt_token, self.secret_key, algorithms=["HS256"])
            token_id = payload["token_id"]
            
            if token_id not in self.tokens:
                return None
            
            token = self.tokens[token_id]
            now = datetime.utcnow()
            
            if now > token.expires_at:
                del self.tokens[token_id]
                return None
            
            return token
            
        except jwt.InvalidTokenError:
            return None
    
    def create_policy(
        self,
        name: str,
        description: str,
        resource_type: ResourceType,
        required_level: AccessLevel
    ) -> AccessPolicy:
        """Create a new access policy"""
        policy_id = str(uuid.uuid4())
        policy = AccessPolicy(
            id=policy_id,
            name=name,
            description=description,
            resource_type=resource_type,
            required_level=required_level
        )
        self.policies[policy_id] = policy
        return policy
    
    def add_team_override(
        self,
        policy_id: str,
        team_id: str,
        access_level: AccessLevel
    ) -> bool:
        """Add team-specific access override"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        policy.team_overrides[team_id] = access_level
        return True
    
    def add_user_override(
        self,
        policy_id: str,
        user_id: str,
        access_level: AccessLevel
    ) -> bool:
        """Add user-specific access override"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        policy.user_overrides[user_id] = access_level
        return True
    
    def check_access(
        self,
        token: AccessToken,
        resource_type: ResourceType,
        resource_id: str
    ) -> AccessLevel:
        """Check access level for a resource"""
        # Check user-specific overrides
        for policy in self.policies.values():
            if policy.resource_type == resource_type:
                if token.user_id in policy.user_overrides:
                    return policy.user_overrides[token.user_id]
        
        # Check team-specific overrides
        max_team_access = AccessLevel.NONE
        for team_id in token.teams:
            for policy in self.policies.values():
                if policy.resource_type == resource_type:
                    if team_id in policy.team_overrides:
                        team_access = policy.team_overrides[team_id]
                        if team_access.value > max_team_access.value:
                            max_team_access = team_access
        
        if max_team_access != AccessLevel.NONE:
            return max_team_access
        
        # Check scope-based access
        scope_key = f"{resource_type.name.lower()}:{resource_id}"
        return token.scopes.get(scope_key, AccessLevel.NONE)
