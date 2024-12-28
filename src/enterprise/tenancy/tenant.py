"""
SafeAI CodeGuard Protocol - Multi-Tenancy Core
Implements core tenant management and isolation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
import uuid
from pathlib import Path
import json
import asyncio
import aiofiles
import aiosqlite

@dataclass
class TenantQuota:
    """Resource quotas for a tenant"""
    max_users: int
    max_projects: int
    max_storage_mb: int
    max_concurrent_validations: int
    custom_limits: Dict[str, int] = field(default_factory=dict)

@dataclass
class TenantConfig:
    """Tenant-specific configuration"""
    safety_level: str
    allowed_features: Set[str]
    validation_rules: List[Dict]
    custom_settings: Dict = field(default_factory=dict)

@dataclass
class Tenant:
    """Represents a tenant in the system"""
    id: str
    name: str
    created_at: datetime
    quota: TenantQuota
    config: TenantConfig
    status: str = "active"
    metadata: Dict = field(default_factory=dict)

class TenantManager:
    """Manages tenant lifecycle and isolation"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "tenants.db"
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    quota BLOB NOT NULL,
                    config BLOB NOT NULL,
                    metadata BLOB
                );
                
                CREATE INDEX IF NOT EXISTS idx_tenants_status 
                ON tenants(status);
            """)
        finally:
            conn.close()
    
    async def create_tenant(
        self,
        name: str,
        quota: TenantQuota,
        config: TenantConfig,
        metadata: Optional[Dict] = None
    ) -> Tenant:
        """Create a new tenant"""
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=name,
            created_at=datetime.now(),
            quota=quota,
            config=config,
            metadata=metadata or {}
        )
        
        # Create tenant directory
        tenant_dir = self.data_dir / tenant.id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # Store in database
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO tenants
                (id, name, created_at, status, quota, config, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tenant.id,
                tenant.name,
                tenant.created_at.isoformat(),
                tenant.status,
                json.dumps(tenant.quota.__dict__),
                json.dumps(tenant.config.__dict__),
                json.dumps(tenant.metadata)
            ))
            await db.commit()
        
        return tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT * FROM tenants WHERE id = ?",
                (tenant_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return Tenant(
                        id=row[0],
                        name=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        status=row[3],
                        quota=TenantQuota(**json.loads(row[4])),
                        config=TenantConfig(**json.loads(row[5])),
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
        return None
    
    async def update_tenant_config(
        self,
        tenant_id: str,
        config: TenantConfig
    ) -> bool:
        """Update tenant configuration"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE tenants 
                SET config = ?
                WHERE id = ?
            """, (
                json.dumps(config.__dict__),
                tenant_id
            ))
            await db.commit()
            return True
    
    async def update_tenant_quota(
        self,
        tenant_id: str,
        quota: TenantQuota
    ) -> bool:
        """Update tenant quota"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE tenants 
                SET quota = ?
                WHERE id = ?
            """, (
                json.dumps(quota.__dict__),
                tenant_id
            ))
            await db.commit()
            return True
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Deactivate a tenant"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE tenants 
                SET status = 'inactive'
                WHERE id = ?
            """, (tenant_id,))
            await db.commit()
            return True
    
    async def get_tenant_storage_path(
        self,
        tenant_id: str,
        create: bool = True
    ) -> Optional[Path]:
        """Get tenant's isolated storage path"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        path = self.data_dir / tenant_id
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path
    
    async def check_tenant_quota(
        self,
        tenant_id: str,
        resource: str,
        amount: int = 1
    ) -> bool:
        """Check if operation is within tenant's quota"""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Get current usage
        usage = await self._get_resource_usage(tenant_id, resource)
        
        # Check against quota
        if resource == "users":
            return usage + amount <= tenant.quota.max_users
        elif resource == "projects":
            return usage + amount <= tenant.quota.max_projects
        elif resource == "storage":
            return usage + amount <= tenant.quota.max_storage_mb
        elif resource == "validations":
            return usage + amount <= tenant.quota.max_concurrent_validations
        elif resource in tenant.quota.custom_limits:
            return usage + amount <= tenant.quota.custom_limits[resource]
        
        return False
    
    async def _get_resource_usage(
        self,
        tenant_id: str,
        resource: str
    ) -> int:
        """Get current resource usage for a tenant"""
        # This is a placeholder implementation
        # In a real system, you would track actual usage
        return 0
