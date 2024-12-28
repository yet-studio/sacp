"""
SafeAI CodeGuard Protocol - Custom Safety Policies
Implements customizable safety policies and rules for enterprise teams.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum, auto
import json
import yaml
from pathlib import Path

class PolicyScope(Enum):
    """Scope of policy application"""
    GLOBAL = auto()      # Applies to all teams
    TEAM = auto()        # Applies to specific team
    PROJECT = auto()     # Applies to specific project
    REPOSITORY = auto()  # Applies to specific repository

class PolicyPriority(Enum):
    """Priority levels for policy enforcement"""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class SafetyRule:
    """Individual safety rule within a policy"""
    id: str
    name: str
    description: str
    pattern: str
    scope: PolicyScope
    priority: PolicyPriority
    is_blocking: bool = True
    custom_validator: Optional[Callable] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class SafetyPolicy:
    """Collection of safety rules"""
    id: str
    name: str
    description: str
    rules: Dict[str, SafetyRule] = field(default_factory=dict)
    scope: PolicyScope = PolicyScope.GLOBAL
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)

class PolicyManager:
    """Manages custom safety policies"""
    
    def __init__(self, policy_dir: Optional[str] = None):
        self.policy_dir = Path(policy_dir) if policy_dir else Path.home() / ".sacp" / "policies"
        self.policies: Dict[str, SafetyPolicy] = {}
        self.policy_dir.mkdir(parents=True, exist_ok=True)
    
    def create_policy(self, name: str, description: str, scope: PolicyScope) -> SafetyPolicy:
        """Create a new safety policy"""
        policy_id = name.lower().replace(" ", "_")
        policy = SafetyPolicy(
            id=policy_id,
            name=name,
            description=description,
            scope=scope
        )
        self.policies[policy_id] = policy
        return policy
    
    def add_rule(self, policy_id: str, rule: SafetyRule) -> bool:
        """Add a rule to a policy"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        policy.rules[rule.id] = rule
        return True
    
    def remove_rule(self, policy_id: str, rule_id: str) -> bool:
        """Remove a rule from a policy"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        if rule_id in policy.rules:
            del policy.rules[rule_id]
            return True
        return False
    
    def save_policy(self, policy_id: str) -> bool:
        """Save policy to file"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        policy_file = self.policy_dir / f"{policy_id}.yaml"
        
        try:
            policy_dict = {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "scope": policy.scope.name,
                "enabled": policy.enabled,
                "metadata": policy.metadata,
                "rules": {
                    rule.id: {
                        "name": rule.name,
                        "description": rule.description,
                        "pattern": rule.pattern,
                        "scope": rule.scope.name,
                        "priority": rule.priority.name,
                        "is_blocking": rule.is_blocking,
                        "metadata": rule.metadata
                    }
                    for rule in policy.rules.values()
                }
            }
            
            with open(policy_file, "w") as f:
                yaml.safe_dump(policy_dict, f)
            return True
            
        except Exception as e:
            return False
    
    def load_policy(self, policy_id: str) -> Optional[SafetyPolicy]:
        """Load policy from file"""
        policy_file = self.policy_dir / f"{policy_id}.yaml"
        
        if not policy_file.exists():
            return None
        
        try:
            with open(policy_file) as f:
                policy_dict = yaml.safe_load(f)
            
            policy = SafetyPolicy(
                id=policy_dict["id"],
                name=policy_dict["name"],
                description=policy_dict["description"],
                scope=PolicyScope[policy_dict["scope"]],
                enabled=policy_dict["enabled"],
                metadata=policy_dict["metadata"]
            )
            
            for rule_id, rule_dict in policy_dict["rules"].items():
                rule = SafetyRule(
                    id=rule_id,
                    name=rule_dict["name"],
                    description=rule_dict["description"],
                    pattern=rule_dict["pattern"],
                    scope=PolicyScope[rule_dict["scope"]],
                    priority=PolicyPriority[rule_dict["priority"]],
                    is_blocking=rule_dict["is_blocking"],
                    metadata=rule_dict["metadata"]
                )
                policy.rules[rule_id] = rule
            
            self.policies[policy_id] = policy
            return policy
            
        except Exception as e:
            return None
    
    def validate_against_policy(self, policy_id: str, content: str) -> List[Dict]:
        """Validate content against a policy's rules"""
        if policy_id not in self.policies:
            return []
        
        policy = self.policies[policy_id]
        violations = []
        
        for rule in policy.rules.values():
            if rule.custom_validator:
                # Use custom validation function
                if not rule.custom_validator(content):
                    violations.append({
                        "rule_id": rule.id,
                        "name": rule.name,
                        "priority": rule.priority.name,
                        "is_blocking": rule.is_blocking
                    })
            else:
                # Use pattern matching
                import re
                if re.search(rule.pattern, content):
                    violations.append({
                        "rule_id": rule.id,
                        "name": rule.name,
                        "priority": rule.priority.name,
                        "is_blocking": rule.is_blocking
                    })
        
        return violations
