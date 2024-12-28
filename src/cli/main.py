"""
SafeAI CodeGuard Protocol - Command Line Interface
Provides CLI tools for code verification, compliance checking, and behavior analysis.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum, auto
import yaml

from src.verification.safety import (
    SafetyVerification,
    SafetyProperty,
    ComplianceLevel,
    VerificationResult
)
from src.constraints.behavior import (
    BehaviorConstraints,
    IntentType,
    ContextType
)
from src.core.protocol import SafetyLevel


class OutputFormat(Enum):
    """Output format options"""
    TEXT = auto()
    JSON = auto()
    YAML = auto()


class CommandLineInterface:
    """Main CLI class for SACP"""

    def __init__(self):
        self.safety_verifier = SafetyVerification(ComplianceLevel.STANDARD)
        self.behavior_constraints = BehaviorConstraints()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger("sacp-cli")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
        )
        
        logger.addHandler(handler)
        return logger

    def run(self, args: List[str]) -> int:
        """Run the CLI with given arguments"""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            if parsed_args.command == "verify":
                return self._handle_verify(parsed_args)
            elif parsed_args.command == "check":
                return self._handle_check(parsed_args)
            elif parsed_args.command == "analyze":
                return self._handle_analyze(parsed_args)
            elif parsed_args.command == "init":
                return self._handle_init(parsed_args)
            else:
                self.logger.error(f"Unknown command: {parsed_args.command}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="SafeAI CodeGuard Protocol CLI"
        )
        
        parser.add_argument(
            "--format",
            choices=["text", "json", "yaml"],
            default="text",
            help="Output format"
        )
        
        subparsers = parser.add_subparsers(dest="command", required=True)
        
        # Verify command
        verify_parser = subparsers.add_parser(
            "verify",
            help="Verify code safety"
        )
        verify_parser.add_argument(
            "path",
            type=str,
            help="Path to file or directory to verify"
        )
        verify_parser.add_argument(
            "--config",
            type=str,
            help="Path to configuration file"
        )
        verify_parser.add_argument(
            "--level",
            choices=["minimal", "standard", "strict", "critical"],
            default="standard",
            help="Verification level"
        )
        
        # Check command
        check_parser = subparsers.add_parser(
            "check",
            help="Check code compliance"
        )
        check_parser.add_argument(
            "path",
            type=str,
            help="Path to file or directory to check"
        )
        check_parser.add_argument(
            "--rules",
            type=str,
            help="Path to custom rules file"
        )
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            "analyze",
            help="Analyze AI behavior"
        )
        analyze_parser.add_argument(
            "path",
            type=str,
            help="Path to file or directory to analyze"
        )
        analyze_parser.add_argument(
            "--context",
            type=str,
            help="Path to context file"
        )
        
        # Init command
        init_parser = subparsers.add_parser(
            "init",
            help="Initialize SACP configuration"
        )
        init_parser.add_argument(
            "--dir",
            type=str,
            default=".",
            help="Directory to initialize"
        )
        
        return parser

    def _handle_verify(self, args: argparse.Namespace) -> int:
        """Handle verify command"""
        path = Path(args.path)
        if not path.exists():
            self.logger.error(f"Path does not exist: {path}")
            return 1
        
        # Load configuration
        config = self._load_config(args.config) if args.config else {}
        
        # Get properties from config
        properties = self._get_properties_from_config(config)
        
        # Run verification
        results = self.safety_verifier.verify_codebase(
            str(path),
            properties,
            coverage_threshold=config.get("coverage_threshold", 80.0)
        )
        
        # Output results
        self._output_results(results, args.format)
        
        # Return 1 if any verification failed
        return 1 if any(not r.success for r in results) else 0

    def _handle_check(self, args: argparse.Namespace) -> int:
        """Handle check command"""
        path = Path(args.path)
        if not path.exists():
            self.logger.error(f"Path does not exist: {path}")
            return 1
        
        # Load custom rules
        custom_rules = None
        if args.rules:
            rules_path = Path(args.rules)
            if not rules_path.exists():
                self.logger.error(f"Rules file does not exist: {rules_path}")
                return 1
            with open(rules_path) as f:
                custom_rules = yaml.safe_load(f)
        
        # Run compliance check
        result = self.safety_verifier.compliance_checker.check_compliance(
            str(path),
            custom_rules
        )
        
        # Output results
        self._output_results([result], args.format)
        
        return 1 if not result.success else 0

    def _handle_analyze(self, args: argparse.Namespace) -> int:
        """Handle analyze command"""
        path = Path(args.path)
        if not path.exists():
            self.logger.error(f"Path does not exist: {path}")
            return 1
        
        # Load context
        context = None
        if args.context:
            context_path = Path(args.context)
            if not context_path.exists():
                self.logger.error(f"Context file does not exist: {context_path}")
                return 1
            with open(context_path) as f:
                context = yaml.safe_load(f)
        
        # Create intent for analysis
        intent = self.behavior_constraints.create_intent(
            intent_type=IntentType.READ,
            description="CLI behavior analysis",
            target_paths=[str(path)],
            required_permissions={"READ"},
            user_id="cli",
            session_data=context or {}
        )
        
        if not intent:
            self.logger.error("Failed to create analysis intent")
            return 1
        
        # Output results
        self._output_results([intent.validation_result], args.format)
        
        return 1 if not intent.is_valid else 0

    def _handle_init(self, args: argparse.Namespace) -> int:
        """Handle init command"""
        dir_path = Path(args.dir)
        if not dir_path.exists():
            self.logger.error(f"Directory does not exist: {dir_path}")
            return 1
        
        # Create default configuration
        config = {
            "version": "1.0.0",
            "compliance_level": "standard",
            "coverage_threshold": 80.0,
            "properties": [
                {
                    "name": "no_eval_exec",
                    "description": "No use of eval() or exec()",
                    "property_type": "invariant",
                    "expression": "'eval' not in code and 'exec' not in code",
                    "severity": "CRITICAL"
                }
            ],
            "custom_rules": {
                "no_shell_injection": {
                    "description": "No shell injection vulnerabilities",
                    "pattern": r"os\.system\(|subprocess\.call\("
                }
            }
        }
        
        # Write configuration file
        config_path = dir_path / "sacp.yaml"
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f, sort_keys=False)
        
        self.logger.info(f"Created configuration file: {config_path}")
        return 0

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _get_properties_from_config(
        self,
        config: Dict[str, Any]
    ) -> List[SafetyProperty]:
        """Get safety properties from configuration"""
        properties = []
        
        for prop_data in config.get("properties", []):
            properties.append(
                SafetyProperty(
                    name=prop_data["name"],
                    description=prop_data["description"],
                    property_type=prop_data["property_type"],
                    expression=prop_data["expression"],
                    severity=prop_data["severity"]
                )
            )
        
        return properties

    def _output_results(
        self,
        results: List[VerificationResult],
        format_type: str
    ):
        """Output results in specified format"""
        if format_type == "json":
            self._output_json(results)
        elif format_type == "yaml":
            self._output_yaml(results)
        else:
            self._output_text(results)

    def _output_json(self, results: List[VerificationResult]):
        """Output results in JSON format"""
        output = []
        for result in results:
            output.append({
                "type": result.verification_type.name,
                "success": result.success,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "violations": result.violations
            })
        
        json.dump(output, sys.stdout, indent=2)
        sys.stdout.write("\n")

    def _output_yaml(self, results: List[VerificationResult]):
        """Output results in YAML format"""
        output = []
        for result in results:
            output.append({
                "type": result.verification_type.name,
                "success": result.success,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "violations": result.violations
            })
        
        yaml.safe_dump(output, sys.stdout, sort_keys=False)

    def _output_text(self, results: List[VerificationResult]):
        """Output results in text format"""
        for result in results:
            print(f"Type: {result.verification_type.name}")
            print(f"Success: {result.success}")
            print(f"Timestamp: {result.timestamp}")
            print("Details:")
            for key, value in result.details.items():
                print(f"  {key}: {value}")
            
            if result.violations:
                print("Violations:")
                for violation in result.violations:
                    print(f"  - {violation}")
            print()


def main():
    """Main entry point"""
    cli = CommandLineInterface()
    sys.exit(cli.run(sys.argv[1:]))


if __name__ == "__main__":
    main()
