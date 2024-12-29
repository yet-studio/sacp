"""
SafeAI CodeGuard Protocol - Command Line Interface
Provides CLI commands for interacting with the SACP system.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional
import json

from ..core.protocol import ComplianceLevel, SafetyLevel
from ..analyzers.static import SecurityAnalyzer
from ..verification.safety import SafetyVerification
from ..control.dynamic import DynamicControl


class CommandLineInterface:
    """Command line interface for SACP"""

    def __init__(self):
        self.parser = self._create_parser()
        self.security_analyzer = SecurityAnalyzer()
        self.safety_verification = SafetyVerification()
        self.dynamic_control = DynamicControl()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description='SafeAI CodeGuard Protocol CLI'
        )
        
        subparsers = parser.add_subparsers(dest='command')
        
        # Init command
        init_parser = subparsers.add_parser(
            'init',
            help='Initialize SACP for a project'
        )
        init_parser.add_argument(
            '--path',
            type=str,
            default='.',
            help='Project path'
        )
        init_parser.add_argument(
            '--safety-level',
            type=str,
            choices=[level.name for level in SafetyLevel],
            default=SafetyLevel.CONTROLLED.name,
            help='Safety level'
        )
        
        # Verify command
        verify_parser = subparsers.add_parser(
            'verify',
            help='Verify code safety'
        )
        verify_parser.add_argument(
            'path',
            type=str,
            help='Path to verify'
        )
        verify_parser.add_argument(
            '--compliance-level',
            type=str,
            choices=[level.name for level in ComplianceLevel],
            default=ComplianceLevel.STANDARD.name,
            help='Compliance level'
        )
        verify_parser.add_argument(
            '--output',
            type=str,
            choices=['text', 'json'],
            default='text',
            help='Output format'
        )
        
        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with arguments"""
        if args is None:
            args = sys.argv[1:]
            
        parsed_args = self.parser.parse_args(args)
        
        try:
            if parsed_args.command == 'init':
                return self._handle_init(parsed_args)
            elif parsed_args.command == 'verify':
                return self._handle_verify(parsed_args)
            else:
                self.parser.print_help()
                return 1
                
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return 1

    def _handle_init(self, args) -> int:
        """Handle init command"""
        project_path = Path(args.path).resolve()
        if not project_path.exists():
            logging.error(f"Project path does not exist: {project_path}")
            return 1
            
        safety_level = SafetyLevel[args.safety_level]
        
        # Create config file
        config = {
            'safety_level': safety_level.name,
            'initialized_at': str(project_path),
            'version': '1.0.0'
        }
        
        config_path = project_path / '.sacp.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"Initialized SACP in {project_path}")
        return 0

    def _handle_verify(self, args) -> int:
        """Handle verify command"""
        path = Path(args.path).resolve()
        if not path.exists():
            logging.error(f"Path does not exist: {path}")
            return 1
            
        compliance_level = ComplianceLevel[args.compliance_level]
        
        # Run verification
        results = self.safety_verification.verify(
            str(path),
            compliance_level=compliance_level
        )
        
        # Format output
        if args.output == 'json':
            print(json.dumps(results.to_dict(), indent=2))
        else:
            self._print_verification_results(results)
            
        return 0 if results.passed else 1

    def _print_verification_results(self, results):
        """Print verification results in text format"""
        print("\nVerification Results:")
        print("-" * 50)
        print(f"Status: {'PASSED' if results.passed else 'FAILED'}")
        print(f"Compliance Level: {results.compliance_level.name}")
        
        if results.violations:
            print("\nViolations:")
            for violation in results.violations:
                print(f"\n- {violation.rule_name}")
                print(f"  Severity: {violation.severity}")
                print(f"  Location: {violation.file_path}:{violation.line_number}")
                print(f"  Description: {violation.description}")
                
        if results.warnings:
            print("\nWarnings:")
            for warning in results.warnings:
                print(f"- {warning}")


def main():
    """Main entry point"""
    cli = CommandLineInterface()
    sys.exit(cli.run())
