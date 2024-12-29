"""
SafeAI CodeGuard Protocol - Cross-Tenant Policies
Implements policy management and enforcement across tenants.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import aiosqlite
from .tenant import TenantManager, Tenant

@dataclass
class PolicyRule:
    """Represents a policy rule"""
    id: str
    name: str
    description: str
    resource_type: str
    action: str
    conditions: Dict
    priority: int = 0
    enabled: bool = True

@dataclass
class Policy:
    """Represents a complete policy"""
    id: str
    name: str
    description: str
    rules: List[PolicyRule]
    scope: str  # global, tenant-group, tenant
    scope_ids: Set[str]
    created_at: datetime
    updated_at: datetime
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)

class PolicyManager:
    """Manages cross-tenant policies"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self.db_path = tenant_manager.db_path.parent / "policies.db"
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS policies (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    scope TEXT NOT NULL,
                    scope_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    metadata BLOB
                );
                
                CREATE TABLE IF NOT EXISTS policy_rules (
                    id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    resource_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    conditions BLOB NOT NULL,
                    priority INTEGER NOT NULL,
                    enabled INTEGER NOT NULL,
                    FOREIGN KEY (policy_id) REFERENCES policies(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_policies_scope 
                ON policies(scope, enabled);
                
                CREATE INDEX IF NOT EXISTS idx_policy_rules_policy 
                ON policy_rules(policy_id, enabled);
            """)
        finally:
            conn.close()
    
    async def create_policy(
        self,
        name: str,
        description: str,
        scope: str,
        scope_ids: Set[str],
        rules: List[PolicyRule],
        metadata: Optional[Dict] = None
    ) -> Policy:
        """Create a new policy"""
        now = datetime.now()
        policy = Policy(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            scope=scope,
            scope_ids=scope_ids,
            rules=rules,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Insert policy
            await db.execute("""
                INSERT INTO policies
                (id, name, description, scope, scope_ids, 
                created_at, updated_at, enabled, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                policy.id,
                policy.name,
                policy.description,
                policy.scope,
                json.dumps(list(policy.scope_ids)),
                policy.created_at.isoformat(),
                policy.updated_at.isoformat(),
                policy.enabled,
                json.dumps(policy.metadata)
            ))
            
            # Insert rules
            for rule in policy.rules:
                await db.execute("""
                    INSERT INTO policy_rules
                    (id, policy_id, name, description,
                    resource_type, action, conditions,
                    priority, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.id,
                    policy.id,
                    rule.name,
                    rule.description,
                    rule.resource_type,
                    rule.action,
                    json.dumps(rule.conditions),
                    rule.priority,
                    rule.enabled
                ))
            
            await db.commit()
        
        return policy
    
    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get policy by ID"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Get policy
            async with db.execute(
                "SELECT * FROM policies WHERE id = ?",
                (policy_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                # Get rules
                async with db.execute(
                    "SELECT * FROM policy_rules WHERE policy_id = ?",
                    (policy_id,)
                ) as rule_cursor:
                    rules = []
                    async for rule_row in rule_cursor:
                        rules.append(PolicyRule(
                            id=rule_row[0],
                            name=rule_row[2],
                            description=rule_row[3],
                            resource_type=rule_row[4],
                            action=rule_row[5],
                            conditions=json.loads(rule_row[6]),
                            priority=rule_row[7],
                            enabled=bool(rule_row[8])
                        ))
                
                return Policy(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    scope=row[3],
                    scope_ids=set(json.loads(row[4])),
                    created_at=datetime.fromisoformat(row[5]),
                    updated_at=datetime.fromisoformat(row[6]),
                    enabled=bool(row[7]),
                    metadata=json.loads(row[8]) if row[8] else {},
                    rules=rules
                )
    
    async def get_applicable_policies(
        self,
        tenant_id: str,
        resource_type: Optional[str] = None
    ) -> List[Policy]:
        """Get policies applicable to a tenant"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            query = """
                SELECT DISTINCT p.* 
                FROM policies p
                LEFT JOIN policy_rules pr ON p.id = pr.policy_id
                WHERE p.enabled = 1
                AND (
                    p.scope = 'global'
                    OR (p.scope = 'tenant' AND p.scope_ids LIKE ?)
                )
            """
            params = [f"%{tenant_id}%"]
            
            if resource_type:
                query += " AND pr.resource_type = ?"
                params.append(resource_type)
            
            policies = []
            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    policy = await self.get_policy(row[0])
                    if policy:
                        policies.append(policy)
            
            return policies
    
    async def evaluate_policies(
        self,
        tenant_id: str,
        resource_type: str,
        context: Dict
    ) -> List[str]:
        """Evaluate policies and return required actions"""
        policies = await self.get_applicable_policies(tenant_id, resource_type)
        actions = set()
        
        for policy in policies:
            for rule in sorted(
                policy.rules,
                key=lambda r: r.priority,
                reverse=True
            ):
                if not rule.enabled:
                    continue
                    
                if rule.resource_type != resource_type:
                    continue
                    
                if self._evaluate_conditions(rule.conditions, context):
                    actions.add(rule.action)
        
        return sorted(actions)
    
    def _evaluate_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Evaluate rule conditions against context"""
        # Simple condition evaluator - extend as needed
        for key, expected in conditions.items():
            if key not in context:
                return False
            if context[key] != expected:
                return False
        return True
