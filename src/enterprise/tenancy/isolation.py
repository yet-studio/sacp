"""
SafeAI CodeGuard Protocol - Tenant Isolation
Implements resource isolation and access control between tenants.
"""

from typing import Dict, List, Optional, Set
from pathlib import Path
import asyncio
import aiofiles
import aiosqlite
from .tenant import TenantManager, Tenant

class ResourceIsolator:
    """Ensures strict resource isolation between tenants"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self._active_validations: Dict[str, Set[str]] = {}
        self._resource_locks: Dict[str, asyncio.Lock] = {}
    
    async def acquire_resource(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        amount: int = 1
    ) -> bool:
        """Acquire a resource for a tenant"""
        # Check quota
        if not await self.tenant_manager.check_tenant_quota(
            tenant_id, resource_type, amount
        ):
            return False
        
        # Get or create resource lock
        lock_key = f"{tenant_id}:{resource_type}:{resource_id}"
        if lock_key not in self._resource_locks:
            self._resource_locks[lock_key] = asyncio.Lock()
        
        # Acquire lock
        async with self._resource_locks[lock_key]:
            # Track resource usage
            if tenant_id not in self._active_validations:
                self._active_validations[tenant_id] = set()
            self._active_validations[tenant_id].add(resource_id)
            return True
    
    async def release_resource(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str
    ):
        """Release a previously acquired resource"""
        if tenant_id in self._active_validations:
            self._active_validations[tenant_id].discard(resource_id)
            
        # Clean up empty sets
        if not self._active_validations[tenant_id]:
            del self._active_validations[tenant_id]
    
    async def get_active_resources(
        self,
        tenant_id: str,
        resource_type: Optional[str] = None
    ) -> Set[str]:
        """Get active resources for a tenant"""
        return self._active_validations.get(tenant_id, set())

class StorageIsolator:
    """Manages isolated storage for each tenant"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
    
    async def get_tenant_path(
        self,
        tenant_id: str,
        subpath: Optional[str] = None
    ) -> Optional[Path]:
        """Get isolated path for tenant"""
        base_path = await self.tenant_manager.get_tenant_storage_path(tenant_id)
        if not base_path:
            return None
            
        if subpath:
            path = base_path / subpath
            path.parent.mkdir(parents=True, exist_ok=True)
            return path
        return base_path
    
    async def ensure_isolation(self, tenant_id: str, path: Path) -> bool:
        """Verify path is within tenant's isolated storage"""
        tenant_path = await self.tenant_manager.get_tenant_storage_path(
            tenant_id,
            create=False
        )
        if not tenant_path:
            return False
            
        try:
            # Resolve to absolute paths
            path = path.resolve()
            tenant_path = tenant_path.resolve()
            # Check if path is a child of tenant_path
            return str(path).startswith(str(tenant_path))
        except (ValueError, RuntimeError):
            return False
    
    async def get_storage_usage(self, tenant_id: str) -> int:
        """Get storage usage in MB for tenant"""
        tenant_path = await self.tenant_manager.get_tenant_storage_path(
            tenant_id,
            create=False
        )
        if not tenant_path or not tenant_path.exists():
            return 0
            
        total = 0
        for path in tenant_path.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        
        return total // (1024 * 1024)  # Convert to MB

class NetworkIsolator:
    """Controls network access and isolation between tenants"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self._active_connections: Dict[str, Set[str]] = {}
    
    async def can_access_endpoint(
        self,
        tenant_id: str,
        endpoint: str
    ) -> bool:
        """Check if tenant can access an endpoint"""
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
            
        # Check tenant's allowed features
        if "network" not in tenant.config.allowed_features:
            return False
            
        # Apply tenant-specific network rules
        rules = tenant.config.custom_settings.get("network_rules", {})
        allowed_endpoints = rules.get("allowed_endpoints", [])
        blocked_endpoints = rules.get("blocked_endpoints", [])
        
        if endpoint in blocked_endpoints:
            return False
            
        if allowed_endpoints and endpoint not in allowed_endpoints:
            return False
            
        return True
    
    async def track_connection(
        self,
        tenant_id: str,
        connection_id: str
    ):
        """Track an active network connection"""
        if tenant_id not in self._active_connections:
            self._active_connections[tenant_id] = set()
        self._active_connections[tenant_id].add(connection_id)
    
    async def release_connection(
        self,
        tenant_id: str,
        connection_id: str
    ):
        """Release a tracked connection"""
        if tenant_id in self._active_connections:
            self._active_connections[tenant_id].discard(connection_id)
            if not self._active_connections[tenant_id]:
                del self._active_connections[tenant_id]
    
    async def get_active_connections(
        self,
        tenant_id: str
    ) -> Set[str]:
        """Get active connections for a tenant"""
        return self._active_connections.get(tenant_id, set())
