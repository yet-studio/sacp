"""
SafeAI CodeGuard Protocol - Behavior Analysis
Implements behavior analysis and risk assessment.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import ast
import logging

from .protocol import RiskLevel


class IntentType(Enum):
    """Types of AI system intents"""
    READ = 1
    WRITE = 2
    EXECUTE = 3
    ANALYZE = 4


class ContextType(Enum):
    """Types of code context"""
    CODE_CONTEXT = 1
    RUNTIME_CONTEXT = 2
    SYSTEM_CONTEXT = 3


class Intent:
    """Represents an AI system's intent"""
    
    def __init__(
        self,
        intent_type: IntentType,
        description: str,
        target_paths: List[str],
        required_permissions: set,
        user_id: str,
        session_data: Dict[str, Any]
    ):
        self.intent_type = intent_type
        self.description = description
        self.target_paths = target_paths
        self.required_permissions = required_permissions
        self.user_id = user_id
        self.session_data = session_data
        self.estimated_risk = self._calculate_risk()

    def _calculate_risk(self) -> RiskLevel:
        """Calculate risk level based on intent"""
        if self.intent_type == IntentType.EXECUTE:
            return RiskLevel.HIGH
        elif self.intent_type == IntentType.WRITE:
            return RiskLevel.MODERATE
        elif self.intent_type == IntentType.READ:
            return RiskLevel.LOW
        return RiskLevel.LOW


class CodeContext:
    """Represents code context for analysis"""
    
    def __init__(
        self,
        context_type: ContextType,
        code_path: str,
        ast_tree: Optional[ast.AST] = None
    ):
        self.context_type = context_type
        self.code_path = code_path
        self.ast_tree = ast_tree
        self.risk_level = self._analyze_risk()

    def _analyze_risk(self) -> RiskLevel:
        """Analyze risk level of code context"""
        if not self.ast_tree:
            return RiskLevel.LOW
            
        risk = RiskLevel.LOW
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in {'system', 'exec', 'eval'}:
                        return RiskLevel.HIGH
                    elif node.func.attr in {'write', 'open'}:
                        risk = RiskLevel.MODERATE
                elif isinstance(node.func, ast.Name):
                    if node.func.id in {'eval', 'exec'}:
                        return RiskLevel.HIGH
                    
        return risk


class ContextAnalyzer:
    """Analyzes code context for safety assessment"""
    
    def analyze_code_context(self, code_path: str) -> CodeContext:
        """Analyze code context from file"""
        try:
            with open(code_path, 'r') as f:
                code = f.read().strip()
            if not code:  # Handle empty files
                return CodeContext(
                    context_type=ContextType.CODE_CONTEXT,
                    code_path=code_path
                )
            tree = ast.parse(code)
            return CodeContext(
                context_type=ContextType.CODE_CONTEXT,
                code_path=code_path,
                ast_tree=tree
            )
        except (SyntaxError, IndentationError) as e:
            logging.error(f"Error analyzing code context: {str(e)}")
            # Return high risk context for invalid code
            ctx = CodeContext(
                context_type=ContextType.CODE_CONTEXT,
                code_path=code_path
            )
            ctx.risk_level = RiskLevel.HIGH
            return ctx
        except Exception as e:
            logging.error(f"Error analyzing code context: {str(e)}")
            return CodeContext(
                context_type=ContextType.CODE_CONTEXT,
                code_path=code_path
            )


class RiskLevel(Enum):
    """Risk levels for operations"""
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class BehaviorConstraints:
    """Enforces behavior constraints on AI system"""
    
    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.risk_threshold = RiskLevel.HIGH
        self.operation_history: List[Intent] = []

    def create_intent(
        self,
        intent_type: IntentType,
        description: str,
        target_paths: List[str],
        required_permissions: set,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> Optional[Intent]:
        """Create and validate an intent"""
        intent = Intent(
            intent_type=intent_type,
            description=description,
            target_paths=target_paths,
            required_permissions=required_permissions,
            user_id=user_id,
            session_data=session_data
        )
        
        if self._validate_intent(intent):
            self.operation_history.append(intent)
            return intent
        return None

    def _validate_intent(self, intent: Intent) -> bool:
        """Validate an intent against constraints"""
        # Check operation history for risk escalation
        if len(self.operation_history) > 0:
            recent_high_risk = sum(
                1 for op in self.operation_history[-5:]
                if op.estimated_risk >= RiskLevel.HIGH
            )
            if recent_high_risk >= 3:
                logging.warning("Too many recent high-risk operations")
                return False

        # Analyze code context for each target
        for path in intent.target_paths:
            context = self.context_analyzer.analyze_code_context(path)
            if context.risk_level >= RiskLevel.HIGH:
                logging.warning(f"High risk code context in {path}")
                return False

        return self.check_constraints(intent)

    def check_constraints(self, intent: Intent) -> bool:
        """Check if intent satisfies behavior constraints"""
        # Check session data for failed operations
        failed_ops = intent.session_data.get('failed_operations', 0)
        if failed_ops > 2:
            logging.warning("Too many failed operations in session")
            return False

        # Escalate risk for dangerous permissions
        if 'EXECUTE' in intent.required_permissions:
            if intent.estimated_risk >= RiskLevel.HIGH:
                logging.warning("High risk execution attempt")
                return False

        return True
