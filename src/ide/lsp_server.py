"""
SafeAI CodeGuard Protocol - Language Server Protocol Implementation
Provides LSP support for IDE integration.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import re

from pygls.server import LanguageServer
from pygls.lsp.methods import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    INITIALIZE,
    SHUTDOWN,
    EXIT
)
from pygls.lsp.types import (
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
    Diagnostic,
    DiagnosticSeverity,
    Range,
    Position,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams
)

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


class DiagnosticSource(Enum):
    """Sources of diagnostic messages"""
    SAFETY = auto()
    COMPLIANCE = auto()
    BEHAVIOR = auto()
    VERIFICATION = auto()


@dataclass
class ServerState:
    """Server state information"""
    initialized: bool = False
    root_path: Optional[str] = None
    open_documents: Dict[str, str] = field(default_factory=dict)
    diagnostics_cache: Dict[str, List[Diagnostic]] = field(default_factory=dict)
    verification_results: Dict[str, List[VerificationResult]] = field(default_factory=dict)


class SACPLanguageServer(LanguageServer):
    """SACP Language Server implementation"""

    def __init__(self):
        super().__init__()
        self.state = ServerState()
        
        # Initialize safety systems
        self.safety_verifier = SafetyVerification(ComplianceLevel.STRICT)
        self.behavior_constraints = BehaviorConstraints()
        
        # Register command handlers
        self.command_handlers = {
            'sacp.verify': self.handle_verify_command,
            'sacp.checkCompliance': self.handle_compliance_command,
            'sacp.analyzeBehavior': self.handle_behavior_command
        }

    def setup_handlers(self):
        """Set up document and command handlers"""
        
        @self.feature(INITIALIZE)
        def initialize(params: InitializeParams) -> InitializeResult:
            """Initialize the language server"""
            self.state.initialized = True
            self.state.root_path = params.root_path
            
            capabilities = ServerCapabilities(
                text_document_sync=TextDocumentSyncKind.INCREMENTAL,
                diagnostic_provider={
                    'interFileDependencies': True,
                    'workspaceDiagnostics': True
                },
                code_action_provider=True,
                execute_command_provider={
                    'commands': list(self.command_handlers.keys())
                }
            )
            
            return InitializeResult(capabilities=capabilities)

        @self.feature(TEXT_DOCUMENT_DID_OPEN)
        def did_open(params: DidOpenTextDocumentParams):
            """Handle document open event"""
            document = params.text_document
            self.state.open_documents[document.uri] = document.text
            self._validate_document(document.uri, document.text)

        @self.feature(TEXT_DOCUMENT_DID_CHANGE)
        async def did_change(params: DidChangeTextDocumentParams):
            """Handle document change event"""
            document = params.text_document
            changes = params.content_changes
            
            # Apply changes to document
            current_text = self.state.open_documents.get(document.uri, "")
            for change in changes:
                if change.range:
                    # Apply incremental change
                    start_pos = self._offset_at_position(
                        current_text,
                        change.range.start
                    )
                    end_pos = self._offset_at_position(
                        current_text,
                        change.range.end
                    )
                    current_text = (
                        current_text[:start_pos] +
                        change.text +
                        current_text[end_pos:]
                    )
                else:
                    # Full text update
                    current_text = change.text
            
            self.state.open_documents[document.uri] = current_text
            await self._validate_document_async(document.uri, current_text)

        @self.feature(TEXT_DOCUMENT_DID_SAVE)
        def did_save(params: DidSaveTextDocumentParams):
            """Handle document save event"""
            document = params.text_document
            if document.uri in self.state.open_documents:
                self._validate_document(
                    document.uri,
                    self.state.open_documents[document.uri]
                )

    async def _validate_document_async(self, uri: str, content: str):
        """Validate document asynchronously"""
        try:
            # Create temporary file for validation
            temp_path = Path(uri).with_suffix('.py')
            temp_path.write_text(content)
            
            # Run safety verification
            properties = self._get_default_properties()
            results = self.safety_verifier.verify_codebase(
                str(temp_path.parent),
                properties
            )
            
            # Store results
            self.state.verification_results[uri] = results
            
            # Convert results to diagnostics
            diagnostics = self._convert_to_diagnostics(results)
            
            # Cache and publish diagnostics
            self.state.diagnostics_cache[uri] = diagnostics
            await self.publish_diagnostics(uri, diagnostics)
            
        except Exception as e:
            logging.error(f"Validation error: {str(e)}")

    def _validate_document(self, uri: str, content: str):
        """Validate document synchronously"""
        asyncio.create_task(self._validate_document_async(uri, content))

    def _convert_to_diagnostics(
        self,
        results: List[VerificationResult]
    ) -> List[Diagnostic]:
        """Convert verification results to LSP diagnostics"""
        diagnostics = []
        
        for result in results:
            if not result.success:
                for violation in result.violations:
                    diagnostic = Diagnostic(
                        range=self._get_violation_range(violation),
                        message=violation.get('message', str(violation)),
                        severity=self._get_violation_severity(violation),
                        source=f"SACP.{result.verification_type.name}",
                        code=violation.get('code'),
                        tags=self._get_violation_tags(violation)
                    )
                    diagnostics.append(diagnostic)
        
        return diagnostics

    def _get_violation_range(self, violation: Dict[str, Any]) -> Range:
        """Get the range for a violation"""
        if 'location' in violation:
            # Parse line number from location
            match = re.search(r'Line (\d+)', violation['location'])
            if match:
                line = int(match.group(1)) - 1
                return Range(
                    start=Position(line=line, character=0),
                    end=Position(line=line, character=80)
                )
        
        # Default to first line if no location
        return Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=80)
        )

    def _get_violation_severity(
        self,
        violation: Dict[str, Any]
    ) -> DiagnosticSeverity:
        """Get severity for a violation"""
        severity_map = {
            'CRITICAL': DiagnosticSeverity.Error,
            'HIGH': DiagnosticSeverity.Error,
            'MODERATE': DiagnosticSeverity.Warning,
            'LOW': DiagnosticSeverity.Information,
            'MINIMAL': DiagnosticSeverity.Hint
        }
        
        return severity_map.get(
            violation.get('severity', 'MODERATE'),
            DiagnosticSeverity.Warning
        )

    def _get_violation_tags(self, violation: Dict[str, Any]) -> List[int]:
        """Get diagnostic tags for a violation"""
        tags = []
        if 'deprecated' in violation.get('message', '').lower():
            tags.append(1)  # DiagnosticTag.Deprecated
        if 'unnecessary' in violation.get('message', '').lower():
            tags.append(2)  # DiagnosticTag.Unnecessary
        return tags

    def _get_default_properties(self) -> List[SafetyProperty]:
        """Get default safety properties for validation"""
        return [
            SafetyProperty(
                name="no_eval_exec",
                description="No use of eval() or exec()",
                property_type="invariant",
                expression="'eval' not in code and 'exec' not in code",
                severity="CRITICAL"
            ),
            SafetyProperty(
                name="no_shell_injection",
                description="No shell injection vulnerabilities",
                property_type="invariant",
                expression="'os.system' not in code",
                severity="CRITICAL"
            ),
            SafetyProperty(
                name="type_annotations",
                description="Functions should have type annotations",
                property_type="invariant",
                expression="all(hasattr(f, '__annotations__') for f in functions)",
                severity="WARNING"
            )
        ]

    def _offset_at_position(self, text: str, position: Position) -> int:
        """Convert LSP position to text offset"""
        lines = text.split('\n')
        offset = sum(len(line) + 1 for line in lines[:position.line])
        return offset + position.character

    async def handle_verify_command(self, params: Dict[str, Any]):
        """Handle verify command"""
        uri = params.get('uri')
        if uri and uri in self.state.open_documents:
            await self._validate_document_async(
                uri,
                self.state.open_documents[uri]
            )

    async def handle_compliance_command(self, params: Dict[str, Any]):
        """Handle compliance check command"""
        uri = params.get('uri')
        if uri and uri in self.state.open_documents:
            content = self.state.open_documents[uri]
            temp_path = Path(uri).with_suffix('.py')
            temp_path.write_text(content)
            
            result = self.safety_verifier.compliance_checker.check_compliance(
                str(temp_path)
            )
            
            diagnostics = self._convert_to_diagnostics([result])
            await self.publish_diagnostics(uri, diagnostics)

    async def handle_behavior_command(self, params: Dict[str, Any]):
        """Handle behavior analysis command"""
        uri = params.get('uri')
        if uri and uri in self.state.open_documents:
            content = self.state.open_documents[uri]
            
            # Create intent for analysis
            intent = self.behavior_constraints.create_intent(
                intent_type=IntentType.READ,
                description="Analyze file behavior",
                target_paths=[uri],
                required_permissions={'READ'},
                user_id="lsp_server",
                session_data={}
            )
            
            if intent:
                # Convert any violations to diagnostics
                diagnostics = []
                for ctx_type, ctx in intent.context.items():
                    if ctx.risk_level.value >= 3:  # HIGH or CRITICAL
                        diagnostic = Diagnostic(
                            range=Range(
                                start=Position(line=0, character=0),
                                end=Position(line=0, character=80)
                            ),
                            message=f"High risk behavior detected: {ctx.data}",
                            severity=DiagnosticSeverity.Warning,
                            source=f"SACP.Behavior.{ctx_type.name}"
                        )
                        diagnostics.append(diagnostic)
                
                await self.publish_diagnostics(uri, diagnostics)
