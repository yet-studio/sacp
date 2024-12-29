"""
SafeAI CodeGuard Protocol - Tenant Customization
Implements tenant-specific customization capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import json
import aiosqlite
from pathlib import Path
import yaml
from .tenant import TenantManager, Tenant

@dataclass
class ValidationWorkflow:
    """Custom validation workflow configuration"""
    id: str
    name: str
    steps: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    timeout: int = 3600
    retries: int = 3
    enabled: bool = True

@dataclass
class SafetyRules:
    """Tenant-specific safety rules"""
    allowed_actions: Set[str]
    blocked_patterns: Set[str]
    required_approvals: int
    auto_rollback: bool
    custom_rules: List[Dict[str, Any]]

@dataclass
class UIPreferences:
    """Tenant UI customization"""
    theme: str
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    shortcuts: Dict[str, str]
    custom_css: Optional[str] = None

@dataclass
class IntegrationSettings:
    """Tenant integration preferences"""
    enabled_integrations: Set[str]
    webhooks: List[Dict[str, Any]]
    api_keys: Dict[str, str]
    custom_endpoints: Dict[str, str]

class CustomizationManager:
    """Manages tenant-specific customizations"""
    
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
        self.db_path = tenant_manager.db_path.parent / "customizations.db"
        self._ensure_db()
        
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    config BLOB NOT NULL,
                    enabled INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                );
                
                CREATE TABLE IF NOT EXISTS safety_rules (
                    tenant_id TEXT PRIMARY KEY,
                    rules BLOB NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                );
                
                CREATE TABLE IF NOT EXISTS ui_preferences (
                    tenant_id TEXT PRIMARY KEY,
                    preferences BLOB NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                );
                
                CREATE TABLE IF NOT EXISTS integration_settings (
                    tenant_id TEXT PRIMARY KEY,
                    settings BLOB NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                );
            """)
        finally:
            conn.close()
    
    async def create_workflow(
        self,
        tenant_id: str,
        name: str,
        steps: List[Dict[str, Any]],
        conditions: Dict[str, Any],
        actions: Dict[str, Any],
        timeout: int = 3600,
        retries: int = 3
    ) -> ValidationWorkflow:
        """Create a custom validation workflow"""
        workflow = ValidationWorkflow(
            id=str(uuid.uuid4()),
            name=name,
            steps=steps,
            conditions=conditions,
            actions=actions,
            timeout=timeout,
            retries=retries
        )
        
        now = datetime.now().isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO workflows
                (id, tenant_id, name, config, enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow.id,
                tenant_id,
                workflow.name,
                json.dumps(workflow.__dict__),
                workflow.enabled,
                now,
                now
            ))
            await db.commit()
        
        return workflow
    
    async def set_safety_rules(
        self,
        tenant_id: str,
        rules: SafetyRules
    ):
        """Set tenant-specific safety rules"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT OR REPLACE INTO safety_rules
                (tenant_id, rules, updated_at)
                VALUES (?, ?, ?)
            """, (
                tenant_id,
                json.dumps(rules.__dict__),
                now
            ))
            await db.commit()
    
    async def set_ui_preferences(
        self,
        tenant_id: str,
        preferences: UIPreferences
    ):
        """Set tenant UI preferences"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT OR REPLACE INTO ui_preferences
                (tenant_id, preferences, updated_at)
                VALUES (?, ?, ?)
            """, (
                tenant_id,
                json.dumps(preferences.__dict__),
                now
            ))
            await db.commit()
    
    async def set_integration_settings(
        self,
        tenant_id: str,
        settings: IntegrationSettings
    ):
        """Set tenant integration settings"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT OR REPLACE INTO integration_settings
                (tenant_id, settings, updated_at)
                VALUES (?, ?, ?)
            """, (
                tenant_id,
                json.dumps(settings.__dict__),
                now
            ))
            await db.commit()
    
    async def get_workflow(
        self,
        workflow_id: str
    ) -> Optional[ValidationWorkflow]:
        """Get workflow by ID"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT config FROM workflows WHERE id = ?",
                (workflow_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return ValidationWorkflow(**json.loads(row[0]))
        return None
    
    async def get_tenant_workflows(
        self,
        tenant_id: str,
        enabled_only: bool = True
    ) -> List[ValidationWorkflow]:
        """Get all workflows for a tenant"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            query = """
                SELECT config 
                FROM workflows 
                WHERE tenant_id = ?
            """
            if enabled_only:
                query += " AND enabled = 1"
                
            async with db.execute(query, (tenant_id,)) as cursor:
                workflows = []
                async for row in cursor:
                    workflows.append(
                        ValidationWorkflow(**json.loads(row[0]))
                    )
                return workflows
    
    async def get_safety_rules(
        self,
        tenant_id: str
    ) -> Optional[SafetyRules]:
        """Get tenant safety rules"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT rules FROM safety_rules WHERE tenant_id = ?",
                (tenant_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return SafetyRules(**json.loads(row[0]))
        return None
    
    async def get_ui_preferences(
        self,
        tenant_id: str
    ) -> Optional[UIPreferences]:
        """Get tenant UI preferences"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT preferences FROM ui_preferences WHERE tenant_id = ?",
                (tenant_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return UIPreferences(**json.loads(row[0]))
        return None
    
    async def get_integration_settings(
        self,
        tenant_id: str
    ) -> Optional[IntegrationSettings]:
        """Get tenant integration settings"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute(
                "SELECT settings FROM integration_settings WHERE tenant_id = ?",
                (tenant_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return IntegrationSettings(**json.loads(row[0]))
        return None
    
    async def export_tenant_config(
        self,
        tenant_id: str,
        output_path: Path
    ):
        """Export all tenant customizations to YAML"""
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
            
        config = {
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "created_at": tenant.created_at.isoformat()
            },
            "workflows": [
                w.__dict__ for w in 
                await self.get_tenant_workflows(tenant_id, enabled_only=False)
            ],
            "safety_rules": (
                await self.get_safety_rules(tenant_id)
            ).__dict__ if await self.get_safety_rules(tenant_id) else None,
            "ui_preferences": (
                await self.get_ui_preferences(tenant_id)
            ).__dict__ if await self.get_ui_preferences(tenant_id) else None,
            "integration_settings": (
                await self.get_integration_settings(tenant_id)
            ).__dict__ if await self.get_integration_settings(tenant_id) else None
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml.dump(config, sort_keys=False))
    
    async def import_tenant_config(
        self,
        tenant_id: str,
        config_path: Path
    ):
        """Import tenant customizations from YAML"""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        config = yaml.safe_load(config_path.read_text())
        
        # Import workflows
        if "workflows" in config:
            for workflow_data in config["workflows"]:
                await self.create_workflow(
                    tenant_id=tenant_id,
                    name=workflow_data["name"],
                    steps=workflow_data["steps"],
                    conditions=workflow_data["conditions"],
                    actions=workflow_data["actions"],
                    timeout=workflow_data.get("timeout", 3600),
                    retries=workflow_data.get("retries", 3)
                )
        
        # Import safety rules
        if "safety_rules" in config and config["safety_rules"]:
            await self.set_safety_rules(
                tenant_id,
                SafetyRules(**config["safety_rules"])
            )
        
        # Import UI preferences
        if "ui_preferences" in config and config["ui_preferences"]:
            await self.set_ui_preferences(
                tenant_id,
                UIPreferences(**config["ui_preferences"])
            )
        
        # Import integration settings
        if "integration_settings" in config and config["integration_settings"]:
            await self.set_integration_settings(
                tenant_id,
                IntegrationSettings(**config["integration_settings"])
            )
