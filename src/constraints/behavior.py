"""
SafeAI CodeGuard Protocol - AI Behavior Constraints
Implements context-aware safety rules, permission controls, and intent validation.
"""

import re
import ast
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
import json
from pathlib import Path
import threading
from collections import deque


class ContextType(Enum):
    """Types of context that influence AI behavior"""
    CODE_CONTEXT = auto()      # Code structure and dependencies
    RUNTIME_CONTEXT = auto()   # Runtime environment and state
    USER_CONTEXT = auto()      # User interactions and preferences
    SYSTEM_CONTEXT = auto()    # System state and resources
    SECURITY_CONTEXT = auto()  # Security and permissions


class IntentType(Enum):
    """Types of AI operation intents"""
    READ = auto()          # Reading or analyzing code
    SUGGEST = auto()       # Suggesting changes
    MODIFY = auto()        # Modifying code
    EXECUTE = auto()       # Executing commands
    INSTALL = auto()       # Installing dependencies


class RiskLevel(Enum):
    """Risk levels for AI operations"""
    MINIMAL = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class OperationContext:
    """Context information for an AI operation"""
    context_type: ContextType
    timestamp: datetime
    data: Dict[str, Any]
    risk_level: RiskLevel
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intent:
    """Represents the intended action of the AI"""
    intent_type: IntentType
    description: str
    target_paths: List[str]
    required_permissions: Set[str]
    estimated_risk: RiskLevel
    context: Dict[ContextType, OperationContext]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextAnalyzer:
    """Analyzes and maintains operation context"""

    def __init__(self):
        self.context_history: Dict[ContextType, deque] = {
            ct: deque(maxlen=1000) for ct in ContextType
        }
        self.context_lock = threading.Lock()

    def analyze_code_context(self, file_path: str) -> OperationContext:
        """Analyze code structure and dependencies"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                tree = ast.parse(content)
                
                # Analyze imports and dependencies
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        imports.append(ast.unparse(node))
                
                # Analyze code complexity
                complexity = {
                    'lines': len(content.splitlines()),
                    'functions': len([n for n in ast.walk(tree) 
                                   if isinstance(n, ast.FunctionDef)]),
                    'classes': len([n for n in ast.walk(tree)
                                  if isinstance(n, ast.ClassDef)])
                }
                
                context = OperationContext(
                    context_type=ContextType.CODE_CONTEXT,
                    timestamp=datetime.now(),
                    data={
                        'imports': imports,
                        'complexity': complexity,
                        'file_path': file_path
                    },
                    risk_level=self._assess_code_risk(complexity, imports)
                )
                
                with self.context_lock:
                    self.context_history[ContextType.CODE_CONTEXT].append(context)
                
                return context
                
        except Exception as e:
            logging.error(f"Error analyzing code context: {str(e)}")
            return self._create_error_context(ContextType.CODE_CONTEXT)

    def analyze_runtime_context(self) -> OperationContext:
        """Analyze runtime environment state"""
        import sys
        import os
        
        context = OperationContext(
            context_type=ContextType.RUNTIME_CONTEXT,
            timestamp=datetime.now(),
            data={
                'python_version': sys.version,
                'platform': sys.platform,
                'env_vars': dict(os.environ),
                'cwd': os.getcwd()
            },
            risk_level=RiskLevel.LOW
        )
        
        with self.context_lock:
            self.context_history[ContextType.RUNTIME_CONTEXT].append(context)
        
        return context

    def analyze_user_context(
        self,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> OperationContext:
        """Analyze user interaction patterns"""
        context = OperationContext(
            context_type=ContextType.USER_CONTEXT,
            timestamp=datetime.now(),
            data={
                'user_id': user_id,
                'session_data': session_data,
                'interaction_count': len(self.context_history[ContextType.USER_CONTEXT])
            },
            risk_level=self._assess_user_risk(user_id, session_data)
        )
        
        with self.context_lock:
            self.context_history[ContextType.USER_CONTEXT].append(context)
        
        return context

    def analyze_system_context(self) -> OperationContext:
        """Analyze system state"""
        import psutil
        
        context = OperationContext(
            context_type=ContextType.SYSTEM_CONTEXT,
            timestamp=datetime.now(),
            data={
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'open_files': len(psutil.Process().open_files())
            },
            risk_level=self._assess_system_risk()
        )
        
        with self.context_lock:
            self.context_history[ContextType.SYSTEM_CONTEXT].append(context)
        
        return context

    def analyze_security_context(
        self,
        permissions: Set[str],
        security_level: str
    ) -> OperationContext:
        """Analyze security state and permissions"""
        context = OperationContext(
            context_type=ContextType.SECURITY_CONTEXT,
            timestamp=datetime.now(),
            data={
                'permissions': list(permissions),
                'security_level': security_level,
                'recent_violations': self._count_recent_violations()
            },
            risk_level=self._assess_security_risk(permissions, security_level)
        )
        
        with self.context_lock:
            self.context_history[ContextType.SECURITY_CONTEXT].append(context)
        
        return context

    def _assess_code_risk(
        self,
        complexity: Dict[str, int],
        imports: List[str]
    ) -> RiskLevel:
        """Assess risk level based on code complexity and imports"""
        risk_score = 0
        
        # Complexity factors
        if complexity['lines'] > 1000:
            risk_score += 1
        if complexity['functions'] > 50:
            risk_score += 1
        if complexity['classes'] > 20:
            risk_score += 1
        
        # Risky imports
        risky_modules = {'os', 'sys', 'subprocess', 'eval', 'exec'}
        if any(any(m in imp for m in risky_modules) for imp in imports):
            risk_score += 2
        
        return RiskLevel(min(risk_score, 4))

    def _assess_user_risk(
        self,
        user_id: str,
        session_data: Dict[str, Any]
    ) -> RiskLevel:
        """Assess risk level based on user behavior"""
        risk_score = 0
        
        # Check rapid operations
        recent_ops = len([
            c for c in self.context_history[ContextType.USER_CONTEXT]
            if (datetime.now() - c.timestamp).seconds < 60
        ])
        if recent_ops > 30:  # More than 30 operations per minute
            risk_score += 2
        
        # Check failed operations
        if session_data.get('failed_operations', 0) > 5:
            risk_score += 1
        
        return RiskLevel(min(risk_score, 4))

    def _assess_system_risk(self) -> RiskLevel:
        """Assess risk level based on system state"""
        import psutil
        
        risk_score = 0
        
        # Resource usage
        if psutil.cpu_percent() > 80:
            risk_score += 1
        if psutil.virtual_memory().percent > 80:
            risk_score += 1
        if psutil.disk_usage('/').percent > 90:
            risk_score += 2
        
        return RiskLevel(min(risk_score, 4))

    def _assess_security_risk(
        self,
        permissions: Set[str],
        security_level: str
    ) -> RiskLevel:
        """Assess risk level based on security context"""
        risk_score = 0
        
        # High-risk permissions
        high_risk_perms = {'EXECUTE', 'MODIFY_SYSTEM', 'INSTALL'}
        if any(p in high_risk_perms for p in permissions):
            risk_score += 2
        
        # Security level
        if security_level == 'LOW':
            risk_score += 1
        elif security_level == 'MINIMAL':
            risk_score += 2
        
        return RiskLevel(min(risk_score, 4))

    def _count_recent_violations(self) -> int:
        """Count security violations in the last hour"""
        hour_ago = datetime.now() - timedelta(hours=1)
        return len([
            c for c in self.context_history[ContextType.SECURITY_CONTEXT]
            if c.timestamp > hour_ago and c.risk_level >= RiskLevel.HIGH
        ])

    def _create_error_context(self, context_type: ContextType) -> OperationContext:
        """Create an error context when analysis fails"""
        return OperationContext(
            context_type=context_type,
            timestamp=datetime.now(),
            data={'error': 'Analysis failed'},
            risk_level=RiskLevel.HIGH
        )


class IntentValidator:
    """Validates AI operation intents"""

    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.validators: Dict[IntentType, List[Callable]] = {
            intent_type: [] for intent_type in IntentType
        }

    def register_validator(
        self,
        intent_type: IntentType,
        validator: Callable[[Intent], bool]
    ):
        """Register a custom validator for an intent type"""
        self.validators[intent_type].append(validator)

    def validate_intent(self, intent: Intent) -> bool:
        """Validate an operation intent"""
        # Check basic requirements
        if not self._validate_basic_requirements(intent):
            return False
        
        # Check risk level
        if not self._validate_risk_level(intent):
            return False
        
        # Run custom validators
        for validator in self.validators[intent.intent_type]:
            if not validator(intent):
                return False
        
        return True

    def _validate_basic_requirements(self, intent: Intent) -> bool:
        """Validate basic intent requirements"""
        try:
            # Check for required context
            required_contexts = {
                IntentType.READ: {ContextType.CODE_CONTEXT},
                IntentType.SUGGEST: {ContextType.CODE_CONTEXT, ContextType.USER_CONTEXT},
                IntentType.MODIFY: {
                    ContextType.CODE_CONTEXT,
                    ContextType.USER_CONTEXT,
                    ContextType.SECURITY_CONTEXT
                },
                IntentType.EXECUTE: {
                    ContextType.RUNTIME_CONTEXT,
                    ContextType.SECURITY_CONTEXT,
                    ContextType.SYSTEM_CONTEXT
                },
                IntentType.INSTALL: {
                    ContextType.RUNTIME_CONTEXT,
                    ContextType.SECURITY_CONTEXT
                }
            }
            
            if not all(ct in intent.context for ct in required_contexts[intent.intent_type]):
                logging.warning(f"Missing required context for {intent.intent_type}")
                return False
            
            # Validate target paths
            if not self._validate_paths(intent.target_paths):
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating basic requirements: {str(e)}")
            return False

    def _validate_risk_level(self, intent: Intent) -> bool:
        """Validate intent risk level"""
        # Calculate combined risk from context
        context_risks = [ctx.risk_level.value for ctx in intent.context.values()]
        max_context_risk = max(context_risks) if context_risks else 0
        
        # Intent type base risks
        base_risks = {
            IntentType.READ: 0,
            IntentType.SUGGEST: 1,
            IntentType.MODIFY: 2,
            IntentType.EXECUTE: 3,
            IntentType.INSTALL: 3
        }
        
        # Calculate total risk
        total_risk = max(base_risks[intent.intent_type], max_context_risk)
        
        # Check if estimated risk matches calculated risk
        if intent.estimated_risk.value < total_risk:
            logging.warning(
                f"Underestimated risk for {intent.intent_type}: "
                f"estimated={intent.estimated_risk.value}, actual={total_risk}"
            )
            return False
        
        return True

    def _validate_paths(self, paths: List[str]) -> bool:
        """Validate target paths"""
        for path in paths:
            try:
                path = Path(path)
                
                # Check if path exists
                if not path.exists():
                    logging.warning(f"Path does not exist: {path}")
                    return False
                
                # Check for suspicious patterns
                suspicious_patterns = [
                    r'/etc/',
                    r'/usr/',
                    r'/bin/',
                    r'/sbin/',
                    r'/dev/',
                    r'/proc/',
                    r'/sys/',
                    r'\.\./',  # Parent directory
                    r'~/'      # Home directory
                ]
                
                if any(re.search(pattern, str(path)) for pattern in suspicious_patterns):
                    logging.warning(f"Suspicious path pattern detected: {path}")
                    return False
                
            except Exception as e:
                logging.error(f"Error validating path {path}: {str(e)}")
                return False
        
        return True


class BehaviorConstraints:
    """Main system for enforcing AI behavior constraints"""

    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.intent_validator = IntentValidator()
        self.operation_history: List[Intent] = []
        self.history_lock = threading.Lock()

    def create_intent(
        self,
        intent_type: IntentType,
        description: str,
        target_paths: List[str],
        required_permissions: Set[str],
        user_id: str,
        session_data: Dict[str, Any]
    ) -> Optional[Intent]:
        """Create and validate an operation intent"""
        try:
            # Gather all context
            context = {}
            
            # Code context (if applicable)
            if target_paths and intent_type in {IntentType.READ, IntentType.SUGGEST, IntentType.MODIFY}:
                context[ContextType.CODE_CONTEXT] = self.context_analyzer.analyze_code_context(target_paths[0])
            
            # Runtime context
            if intent_type in {IntentType.EXECUTE, IntentType.INSTALL}:
                context[ContextType.RUNTIME_CONTEXT] = self.context_analyzer.analyze_runtime_context()
            
            # User context
            context[ContextType.USER_CONTEXT] = self.context_analyzer.analyze_user_context(
                user_id, session_data
            )
            
            # System context
            if intent_type in {IntentType.EXECUTE, IntentType.MODIFY}:
                context[ContextType.SYSTEM_CONTEXT] = self.context_analyzer.analyze_system_context()
            
            # Security context
            if required_permissions:
                context[ContextType.SECURITY_CONTEXT] = self.context_analyzer.analyze_security_context(
                    required_permissions,
                    self._determine_security_level(intent_type, required_permissions)
                )
            
            # Calculate estimated risk
            estimated_risk = self._estimate_risk(
                intent_type, context, required_permissions
            )
            
            # Create intent
            intent = Intent(
                intent_type=intent_type,
                description=description,
                target_paths=target_paths,
                required_permissions=required_permissions,
                estimated_risk=estimated_risk,
                context=context
            )
            
            # Validate intent
            if not self.intent_validator.validate_intent(intent):
                logging.warning(f"Intent validation failed for {intent_type}")
                return None
            
            # Record in history
            with self.history_lock:
                self.operation_history.append(intent)
            
            return intent
            
        except Exception as e:
            logging.error(f"Error creating intent: {str(e)}")
            return None

    def _determine_security_level(
        self,
        intent_type: IntentType,
        permissions: Set[str]
    ) -> str:
        """Determine security level based on intent and permissions"""
        if intent_type in {IntentType.EXECUTE, IntentType.INSTALL}:
            return 'HIGH'
        if 'MODIFY' in permissions:
            return 'MODERATE'
        if 'READ' in permissions:
            return 'LOW'
        return 'MINIMAL'

    def _estimate_risk(
        self,
        intent_type: IntentType,
        context: Dict[ContextType, OperationContext],
        permissions: Set[str]
    ) -> RiskLevel:
        """Estimate risk level for an operation"""
        risk_score = 0
        
        # Base risk from intent type
        base_risks = {
            IntentType.READ: 0,
            IntentType.SUGGEST: 1,
            IntentType.MODIFY: 2,
            IntentType.EXECUTE: 3,
            IntentType.INSTALL: 3
        }
        risk_score += base_risks[intent_type]
        
        # Risk from context
        if context.get(ContextType.CODE_CONTEXT):
            risk_score = max(risk_score, context[ContextType.CODE_CONTEXT].risk_level.value)
        
        if context.get(ContextType.SECURITY_CONTEXT):
            risk_score = max(risk_score, context[ContextType.SECURITY_CONTEXT].risk_level.value)
        
        # Risk from permissions
        high_risk_perms = {'EXECUTE', 'MODIFY_SYSTEM', 'INSTALL'}
        if any(p in high_risk_perms for p in permissions):
            risk_score += 1
        
        return RiskLevel(min(risk_score, 4))

    def get_operation_history(
        self,
        minutes: int = 60,
        intent_types: Optional[Set[IntentType]] = None
    ) -> List[Intent]:
        """Get operation history filtered by time and intent type"""
        with self.history_lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            return [
                intent for intent in self.operation_history
                if (intent_types is None or intent.intent_type in intent_types) and
                any(ctx.timestamp > cutoff for ctx in intent.context.values())
            ]
