"""
SafeAI CodeGuard Protocol - Command Line Interface
Main CLI implementation.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional
import json
import yaml

from ..core.protocol import ComplianceLevel, SafetyLevel
from ..analyzers.static import SecurityAnalyzer
from ..verification.safety import SafetyVerification


class OutputFormat(str):
    """Output format options"""
    TEXT = 'text'
    JSON = 'json'
    YAML = 'yaml'


class CommandLineInterface:
    """Command line interface for SACP"""

    def __init__(self):
        self.parser = self._create_parser()
        self.security_analyzer = SecurityAnalyzer()
        self.safety_verification = SafetyVerification()

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
        init_parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'json', 'yaml'],
            default='text',
            help='Output format'
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
            '--config',
            type=str,
            help='Path to config file'
        )
        verify_parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'json', 'yaml'],
            default='text',
            help='Output format'
        )
        
        # Check command
        check_parser = subparsers.add_parser(
            'check',
            help='Check code against rules'
        )
        check_parser.add_argument(
            'path',
            type=str,
            help='Path to check'
        )
        check_parser.add_argument(
            '--rules',
            type=str,
            help='Path to rules file'
        )
        check_parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'json', 'yaml'],
            default='text',
            help='Output format'
        )
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Analyze code behavior'
        )
        analyze_parser.add_argument(
            'path',
            type=str,
            help='Path to analyze'
        )
        analyze_parser.add_argument(
            '--context',
            type=str,
            help='Path to context file'
        )
        analyze_parser.add_argument(
            '--format',
            type=str,
            choices=['text', 'json', 'yaml'],
            default='text',
            help='Output format'
        )
        
        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with arguments"""
        if args is None:
            args = sys.argv[1:]
            
        try:
            parsed_args = self.parser.parse_args(args)
            
            if parsed_args.command == 'init':
                return self._handle_init(parsed_args)
            elif parsed_args.command == 'verify':
                return self._handle_verify(parsed_args)
            elif parsed_args.command == 'check':
                return self._handle_check(parsed_args)
            elif parsed_args.command == 'analyze':
                return self._handle_analyze(parsed_args)
            else:
                self.parser.print_help()
                return 1
                
        except argparse.ArgumentError as e:
            logging.error(f"Argument error: {str(e)}")
            return 1
        except SystemExit as e:
            # Convert argparse's sys.exit(2) to return code 1
            return 1 if e.code == 2 else e.code
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
            
        self._output(f"Initialized SACP in {project_path}", args)
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
        
        self._output_results(results, args)
        return 0 if results.passed else 1

    def _handle_check(self, args) -> int:
        """Handle check command"""
        path = Path(args.path).resolve()
        if not path.exists():
            logging.error(f"Path does not exist: {path}")
            return 1
            
        # Load rules
        rules = {}
        if args.rules:
            rules_path = Path(args.rules).resolve()
            if not rules_path.exists():
                logging.error(f"Rules file does not exist: {rules_path}")
                return 1
                
            with open(rules_path) as f:
                rules = yaml.safe_load(f)
        
        # Run checks
        results = self.security_analyzer.analyze_file(
            str(path),
            rules=rules
        )
        
        self._output_results(results, args)
        # Return 1 if any high severity issues found
        return 0 if not results else 1

    def _handle_analyze(self, args) -> int:
        """Handle analyze command"""
        path = Path(args.path).resolve()
        if not path.exists():
            logging.error(f"Path does not exist: {path}")
            return 1
            
        # Load context
        context = {}
        if args.context:
            context_path = Path(args.context).resolve()
            if not context_path.exists():
                logging.error(f"Context file does not exist: {context_path}")
                return 1
                
            with open(context_path) as f:
                context = yaml.safe_load(f)
        
        # Run analysis
        results = self.security_analyzer.analyze_file(str(path))
        
        self._output_results(results, args)
        return 0

    def _output(self, message: str, args):
        """Output message in specified format"""
        if args.format == OutputFormat.JSON:
            print(json.dumps({'message': message}))
        elif args.format == OutputFormat.YAML:
            print(yaml.safe_dump({'message': message}))
        else:
            print(message)

    def _output_results(self, results, args):
        """Output results in specified format"""
        if isinstance(results, list):
            # Convert list of results to dict format
            results_dict = {
                'results': [
                    {
                        'severity': str(r.severity),
                        'message': str(r.message) if hasattr(r, 'message') else '',
                        'file': str(r.file) if hasattr(r, 'file') else '',
                        'line': r.line if hasattr(r, 'line') else None,
                        'details': r.details if hasattr(r, 'details') else {}
                    }
                    for r in results
                ]
            }
            
            if args.format == OutputFormat.JSON:
                print(json.dumps(results_dict, indent=2))
            elif args.format == OutputFormat.YAML:
                print(yaml.safe_dump(results_dict))
            else:
                self._print_results(results)
        else:
            # Handle single result object with to_dict method
            if args.format == OutputFormat.JSON:
                print(json.dumps(results.to_dict(), indent=2))
            elif args.format == OutputFormat.YAML:
                print(yaml.safe_dump(results.to_dict()))
            else:
                self._print_results(results)

    def _print_results(self, results):
        """Print results in text format"""
        print("\nResults:")
        print("-" * 50)
        
        if isinstance(results, list):
            # Print list of results
            for result in results:
                print(f"\n- Severity: {result.severity}")
                if hasattr(result, 'message'):
                    print(f"  Message: {result.message}")
                if hasattr(result, 'file'):
                    print(f"  File: {result.file}")
                if hasattr(result, 'line'):
                    print(f"  Line: {result.line}")
                if hasattr(result, 'details'):
                    print(f"  Details: {result.details}")
        else:
            # Print single result object
            if hasattr(results, 'passed'):
                print(f"Status: {'PASSED' if results.passed else 'FAILED'}")
                
            if hasattr(results, 'violations'):
                if results.violations:
                    print("\nViolations:")
                    for violation in results.violations:
                        print(f"\n- {violation.rule_name}")
                        print(f"  Severity: {violation.severity}")
                        print(f"  Location: {violation.file_path}:{violation.line_number}")
                        print(f"  Description: {violation.description}")
                        
            if hasattr(results, 'warnings'):
                if results.warnings:
                    print("\nWarnings:")
                    for warning in results.warnings:
                        print(f"- {warning}")


def main():
    """Main entry point"""
    cli = CommandLineInterface()
    sys.exit(cli.run())
