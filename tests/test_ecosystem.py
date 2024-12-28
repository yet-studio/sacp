"""
Tests for the SACP ecosystem components
"""

import unittest
import tempfile
from pathlib import Path
import yaml
from typing import List, Dict, Any, Callable

from src.ecosystem.plugin import (
    PluginManager,
    PackageManager,
    Registry,
    PluginInterface,
    PluginMetadata,
    SafetyProperty
)


class TestPlugin(PluginInterface):
    """Test plugin implementation"""
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        return True

    def get_safety_properties(self) -> List[SafetyProperty]:
        return [
            SafetyProperty(
                name="test_property",
                description="Test safety property",
                property_type="invariant",
                expression="True",
                severity="LOW"
            )
        ]

    def get_compliance_rules(self) -> Dict[str, Any]:
        return {
            "test_rule": {
                "description": "Test compliance rule",
                "pattern": r"test"
            }
        }

    def get_behavior_validators(self) -> List[Callable]:
        def validator(context: Dict[str, Any]) -> bool:
            return True
        return [validator]

    def cleanup(self):
        pass


class TestPluginSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_dir = Path(self.temp_dir) / "plugins"
        self.plugin_dir.mkdir()
        self.plugin_manager = PluginManager(str(self.plugin_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_plugin(self, name: str) -> PluginMetadata:
        """Create a test plugin directory and metadata"""
        plugin_dir = self.plugin_dir / name
        plugin_dir.mkdir()
        
        # Create plugin metadata
        metadata = {
            "name": name,
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "dependencies": [],
            "entry_point": "plugin",
            "capabilities": ["safety", "compliance", "behavior"]
        }
        
        with open(plugin_dir / "plugin.yaml", "w") as f:
            yaml.safe_dump(metadata, f)
        
        # Create plugin module
        with open(plugin_dir / "plugin.py", "w") as f:
            f.write("""
from src.ecosystem.plugin import PluginInterface, SafetyProperty
from typing import Dict, List, Any, Callable

class Plugin(PluginInterface):
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
        
    def get_safety_properties(self) -> List[SafetyProperty]:
        return []
        
    def get_compliance_rules(self) -> Dict[str, Any]:
        return {}
        
    def get_behavior_validators(self) -> List[Callable]:
        return []
        
    def cleanup(self):
        pass
""")
        
        return PluginMetadata(**metadata)

    def test_plugin_discovery(self):
        # Create test plugins
        plugin1 = self.create_test_plugin("plugin1")
        plugin2 = self.create_test_plugin("plugin2")
        
        # Discover plugins
        discovered = self.plugin_manager.discover_plugins()
        
        self.assertEqual(len(discovered), 2)
        self.assertEqual(discovered[0].name, "plugin1")
        self.assertEqual(discovered[1].name, "plugin2")

    def test_plugin_loading(self):
        # Create and load test plugin
        metadata = self.create_test_plugin("test_plugin")
        success = self.plugin_manager.load_plugin(metadata)
        
        self.assertTrue(success)
        self.assertIn("test_plugin", self.plugin_manager.plugins)
        
        # Test plugin functionality
        plugin = self.plugin_manager.get_plugin("test_plugin")
        self.assertIsNotNone(plugin)
        
        # Unload plugin
        success = self.plugin_manager.unload_plugin("test_plugin")
        self.assertTrue(success)
        self.assertNotIn("test_plugin", self.plugin_manager.plugins)

    def test_plugin_aggregation(self):
        # Create test plugin with actual implementations
        plugin_dir = self.plugin_dir / "test_plugin"
        plugin_dir.mkdir()
        
        # Create plugin metadata
        metadata = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author"
        }
        
        with open(plugin_dir / "plugin.yaml", "w") as f:
            yaml.safe_dump(metadata, f)
        
        # Create plugin module with TestPlugin implementation
        with open(plugin_dir / "plugin.py", "w") as f:
            f.write("""
from src.ecosystem.plugin import PluginInterface, SafetyProperty
from typing import Dict, List, Any, Callable

class Plugin(PluginInterface):
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
        
    def get_safety_properties(self) -> List[SafetyProperty]:
        return [
            SafetyProperty(
                name="test_property",
                description="Test safety property",
                property_type="invariant",
                expression="True",
                severity="LOW"
            )
        ]
        
    def get_compliance_rules(self) -> Dict[str, Any]:
        return {
            "test_rule": {
                "description": "Test compliance rule",
                "pattern": r"test"
            }
        }
        
    def get_behavior_validators(self) -> List[Callable]:
        def validator(context: Dict[str, Any]) -> bool:
            return True
        return [validator]
        
    def cleanup(self):
        pass
""")
        
        # Load plugin
        plugin_metadata = PluginMetadata(**metadata)
        self.plugin_manager.load_plugin(plugin_metadata)
        
        # Test aggregation methods
        properties = self.plugin_manager.get_all_safety_properties()
        self.assertEqual(len(properties), 1)
        self.assertEqual(properties[0].name, "test_property")
        
        rules = self.plugin_manager.get_all_compliance_rules()
        self.assertIn("test_rule", rules)
        
        validators = self.plugin_manager.get_all_behavior_validators()
        self.assertEqual(len(validators), 1)


class TestPackageManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.package_dir = Path(self.temp_dir) / "packages"
        self.package_manager = PackageManager(str(self.package_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_package_installation(self):
        # Test package installation
        success = self.package_manager.install_package("test-package", "1.0.0")
        self.assertTrue(success)
        
        # Check if package is listed
        packages = self.package_manager.list_packages()
        self.assertIn("test-package", packages)
        self.assertEqual(packages["test-package"], "1.0.0")
        
        # Test package uninstallation
        success = self.package_manager.uninstall_package("test-package")
        self.assertTrue(success)
        self.assertNotIn("test-package", self.package_manager.list_packages())

    def test_package_info(self):
        # Install package
        self.package_manager.install_package("test-package")
        
        # Create package info
        package_info = {
            "name": "test-package",
            "version": "1.0.0",
            "description": "Test package"
        }
        
        package_dir = self.package_dir / "test-package"
        with open(package_dir / "package.yaml", "w") as f:
            yaml.safe_dump(package_info, f)
        
        # Get package info
        info = self.package_manager.get_package_info("test-package")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "test-package")
        self.assertEqual(info["version"], "1.0.0")


class TestRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = Registry("http://test-registry.sacp.dev")

    def test_registry_operations(self):
        # Test package search
        results = self.registry.search_packages("test")
        self.assertEqual(len(results), 0)  # No results yet
        
        # Test version listing
        versions = self.registry.get_package_versions("test-package")
        self.assertEqual(len(versions), 0)  # No versions yet
        
        # Test package publishing
        success = self.registry.publish_package("test-package")
        self.assertFalse(success)  # Not implemented yet


if __name__ == "__main__":
    unittest.main()
