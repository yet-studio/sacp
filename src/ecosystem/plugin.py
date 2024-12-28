"""
SafeAI CodeGuard Protocol - Plugin System
Provides a flexible plugin architecture for extending SACP functionality.
"""

import abc
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
import yaml

from src.verification.safety import SafetyProperty
from src.core.protocol import SafetyLevel


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = field(default_factory=list)
    entry_point: str = "plugin"
    config_schema: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)


class PluginInterface(abc.ABC):
    """Base interface for SACP plugins"""

    @abc.abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration"""
        pass

    @abc.abstractmethod
    def get_safety_properties(self) -> List[SafetyProperty]:
        """Get additional safety properties from plugin"""
        pass

    @abc.abstractmethod
    def get_compliance_rules(self) -> Dict[str, Any]:
        """Get additional compliance rules from plugin"""
        pass

    @abc.abstractmethod
    def get_behavior_validators(self) -> List[Callable]:
        """Get additional behavior validators from plugin"""
        pass

    @abc.abstractmethod
    def cleanup(self):
        """Clean up plugin resources"""
        pass


class PluginManager:
    """Manages SACP plugins"""

    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugin_dir = Path(plugin_dir) if plugin_dir else Path.home() / ".sacp" / "plugins"
        self.plugins: Dict[str, PluginInterface] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.logger = logging.getLogger("sacp.plugins")

    def discover_plugins(self) -> List[PluginMetadata]:
        """Discover available plugins"""
        discovered = []
        
        if not self.plugin_dir.exists():
            return discovered
        
        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue
            
            metadata_file = plugin_path / "plugin.yaml"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file) as f:
                    metadata = yaml.safe_load(f)
                
                plugin_metadata = PluginMetadata(
                    name=metadata["name"],
                    version=metadata["version"],
                    description=metadata.get("description", ""),
                    author=metadata.get("author", "unknown"),
                    dependencies=metadata.get("dependencies", []),
                    entry_point=metadata.get("entry_point", "plugin"),
                    config_schema=metadata.get("config_schema", {}),
                    capabilities=metadata.get("capabilities", [])
                )
                
                discovered.append(plugin_metadata)
                
            except Exception as e:
                self.logger.error(f"Error loading plugin metadata from {metadata_file}: {e}")
        
        return discovered

    def load_plugin(self, metadata: PluginMetadata, config: Dict[str, Any] = None) -> bool:
        """Load a plugin by its metadata"""
        try:
            # Add plugin directory to Python path
            plugin_path = self.plugin_dir / metadata.name
            if str(plugin_path) not in sys.path:
                sys.path.append(str(plugin_path))
            
            # Import plugin module
            module = importlib.import_module(metadata.entry_point)
            
            # Get plugin class
            plugin_class = getattr(module, "Plugin")
            
            # Validate plugin interface
            if not issubclass(plugin_class, PluginInterface):
                raise TypeError(
                    f"Plugin {metadata.name} does not implement PluginInterface"
                )
            
            # Initialize plugin
            plugin = plugin_class()
            if not plugin.initialize(config or {}):
                raise RuntimeError(
                    f"Failed to initialize plugin {metadata.name}"
                )
            
            # Store plugin and metadata
            self.plugins[metadata.name] = plugin
            self.metadata[metadata.name] = metadata
            
            self.logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading plugin {metadata.name}: {e}")
            return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin by name"""
        if name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[name]
            plugin.cleanup()
            
            del self.plugins[name]
            del self.metadata[name]
            
            self.logger.info(f"Unloaded plugin: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unloading plugin {name}: {e}")
            return False

    def get_plugin(self, name: str) -> Optional[PluginInterface]:
        """Get a loaded plugin by name"""
        return self.plugins.get(name)

    def get_all_safety_properties(self) -> List[SafetyProperty]:
        """Get safety properties from all plugins"""
        properties = []
        for plugin in self.plugins.values():
            try:
                properties.extend(plugin.get_safety_properties())
            except Exception as e:
                self.logger.error(f"Error getting safety properties from plugin: {e}")
        return properties

    def get_all_compliance_rules(self) -> Dict[str, Any]:
        """Get compliance rules from all plugins"""
        rules = {}
        for plugin in self.plugins.values():
            try:
                rules.update(plugin.get_compliance_rules())
            except Exception as e:
                self.logger.error(f"Error getting compliance rules from plugin: {e}")
        return rules

    def get_all_behavior_validators(self) -> List[Callable]:
        """Get behavior validators from all plugins"""
        validators = []
        for plugin in self.plugins.values():
            try:
                validators.extend(plugin.get_behavior_validators())
            except Exception as e:
                self.logger.error(f"Error getting behavior validators from plugin: {e}")
        return validators


class PackageManager:
    """Manages SACP packages and dependencies"""

    def __init__(self, package_dir: Optional[str] = None):
        self.package_dir = Path(package_dir) if package_dir else Path.home() / ".sacp" / "packages"
        self.installed_packages: Dict[str, str] = {}  # name -> version
        self.logger = logging.getLogger("sacp.packages")

    def install_package(self, name: str, version: Optional[str] = None) -> bool:
        """Install a package"""
        try:
            # TODO: Implement package installation from registry
            # For now, just create package directory
            package_path = self.package_dir / name
            package_path.mkdir(parents=True, exist_ok=True)
            
            self.installed_packages[name] = version or "latest"
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing package {name}: {e}")
            return False

    def uninstall_package(self, name: str) -> bool:
        """Uninstall a package"""
        try:
            package_path = self.package_dir / name
            if package_path.exists():
                import shutil
                shutil.rmtree(package_path)
            
            if name in self.installed_packages:
                del self.installed_packages[name]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error uninstalling package {name}: {e}")
            return False

    def update_package(self, name: str) -> bool:
        """Update a package to latest version"""
        try:
            # TODO: Implement package update from registry
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating package {name}: {e}")
            return False

    def list_packages(self) -> Dict[str, str]:
        """List installed packages"""
        return self.installed_packages.copy()

    def get_package_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get package information"""
        try:
            package_path = self.package_dir / name
            if not package_path.exists():
                return None
            
            info_file = package_path / "package.yaml"
            if not info_file.exists():
                return None
            
            with open(info_file) as f:
                return yaml.safe_load(f)
            
        except Exception as e:
            self.logger.error(f"Error getting package info for {name}: {e}")
            return None


class Registry:
    """SACP package and plugin registry"""

    def __init__(self, registry_url: Optional[str] = None):
        self.registry_url = registry_url or "https://registry.sacp.dev"
        self.logger = logging.getLogger("sacp.registry")

    def search_packages(self, query: str) -> List[Dict[str, Any]]:
        """Search for packages in registry"""
        try:
            # TODO: Implement registry API client
            return []
            
        except Exception as e:
            self.logger.error(f"Error searching packages: {e}")
            return []

    def get_package_versions(self, name: str) -> List[str]:
        """Get available versions for a package"""
        try:
            # TODO: Implement registry API client
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting package versions: {e}")
            return []

    def publish_package(self, package_path: str) -> bool:
        """Publish a package to registry"""
        try:
            # TODO: Implement registry API client
            return False
            
        except Exception as e:
            self.logger.error(f"Error publishing package: {e}")
            return False
