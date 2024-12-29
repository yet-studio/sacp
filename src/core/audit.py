"""
SafeAI CodeGuard Protocol - Audit Logging System
Implements comprehensive logging and monitoring of all AI operations.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path
import threading
from queue import Queue, Empty
import logging

from .protocol import SafetyLevel, AccessScope
from .access import Permission


class AuditEventType(Enum):
    """Types of events that can be audited"""
    SYSTEM_START = auto()
    SYSTEM_STOP = auto()
    CONFIG_CHANGE = auto()
    TOKEN_CREATED = auto()
    TOKEN_REVOKED = auto()
    TOKEN_EXPIRED = auto()
    ACCESS_GRANTED = auto()
    ACCESS_DENIED = auto()
    FILE_READ = auto()
    FILE_MODIFIED = auto()
    FILE_CREATED = auto()
    FILE_DELETED = auto()
    CODE_ANALYZED = auto()
    VALIDATION_SUCCESS = auto()
    VALIDATION_FAILURE = auto()
    EMERGENCY_STOP = auto()
    SECURITY_VIOLATION = auto()


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class AuditEvent:
    """Represents a single audit event"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    safety_level: SafetyLevel
    access_scope: AccessScope
    token_id: Optional[str]
    user_id: str
    resource_path: Optional[str]
    operation: Optional[Permission]
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    parent_event_id: Optional[str] = None


class AuditStore:
    """Handles persistent storage of audit events"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.current_file: Optional[Path] = None
        self.file_size_limit = 10 * 1024 * 1024  # 10MB
        self._init_storage()

    def _init_storage(self):
        """Initialize the storage directory structure"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._rotate_file_if_needed()

    def _rotate_file_if_needed(self, force: bool = False) -> bool:
        """Create a new log file if needed or forced
        Returns True if rotation occurred
        """
        if (
            force
            or not self.current_file
            or (self.current_file.exists() and self.current_file.stat().st_size >= self.file_size_limit)
        ):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Include microseconds
            self.current_file = self.base_path / f"audit_{timestamp}.jsonl"
            return True
        return False

    def store_event(self, event: AuditEvent):
        """Store a single audit event"""
        # Convert event to dict first to get accurate size
        event_dict = self._event_to_dict(event)
        event_size = len(json.dumps(event_dict))
        
        # Force rotation if event is too large or current file is near limit
        if (
            not self.current_file
            or event_size > self.file_size_limit / 2  # If event is more than half the limit
            or (self.current_file.exists() and 
                self.current_file.stat().st_size + event_size > self.file_size_limit)
        ):
            self._rotate_file_if_needed(force=True)
        
        with open(self.current_file, 'a') as f:
            json.dump(event_dict, f)
            f.write('\n')
            f.flush()  # Ensure immediate write

    def _event_to_dict(self, event: AuditEvent) -> Dict:
        """Convert AuditEvent to dictionary for storage"""
        return {
            'event_id': event.event_id,
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type.name,
            'severity': event.severity.name,
            'safety_level': event.safety_level.name,
            'access_scope': event.access_scope.name,
            'token_id': event.token_id,
            'user_id': event.user_id,
            'resource_path': event.resource_path,
            'operation': event.operation.name if event.operation else None,
            'details': event.details,
            'metadata': event.metadata,
            'parent_event_id': event.parent_event_id
        }

    def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        events = []
        
        # Get all audit files in chronological order
        audit_files = sorted(self.base_path.glob("audit_*.jsonl"))
        
        for file_path in audit_files:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        event_dict = json.loads(line.strip())
                        
                        # Apply filters
                        event_time = datetime.fromisoformat(event_dict['timestamp'])
                        if start_time and event_time < start_time:
                            continue
                        if end_time and event_time > end_time:
                            continue
                        if event_types and event_dict['event_type'] not in [t.name for t in event_types]:
                            continue
                        if user_id and event_dict['user_id'] != user_id:
                            continue
                        if severity and event_dict['severity'] != severity.name:
                            continue
                            
                        # Convert dict back to AuditEvent
                        event = AuditEvent(
                            event_id=event_dict['event_id'],
                            timestamp=event_time,
                            event_type=AuditEventType[event_dict['event_type']],
                            severity=AuditSeverity[event_dict['severity']],
                            safety_level=SafetyLevel[event_dict['safety_level']],
                            access_scope=AccessScope[event_dict['access_scope']],
                            token_id=event_dict['token_id'],
                            user_id=event_dict['user_id'],
                            resource_path=event_dict['resource_path'],
                            operation=Permission[event_dict['operation']] if event_dict['operation'] else None,
                            details=event_dict['details'],
                            metadata=event_dict['metadata'],
                            parent_event_id=event_dict['parent_event_id']
                        )
                        events.append(event)
                        
            except Exception as e:
                logging.error(f"Error reading audit file {file_path}: {str(e)}")
                
        return events


class AuditLogger:
    """Main audit logging interface"""
    
    def __init__(self, store: AuditStore):
        self.store = store
        self.event_queue: Queue = Queue()
        self.should_stop = False
        self._start_worker()

    def _start_worker(self):
        """Start the background worker thread"""
        self.worker_thread = threading.Thread(target=self._process_events)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _process_events(self):
        """Background worker to process events"""
        while not self.should_stop:
            try:
                event = self.event_queue.get(timeout=1.0)
                self.store.store_event(event)
                self.event_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing event: {str(e)}")

    def stop(self):
        """Stop the audit logger"""
        self.should_stop = True
        self.worker_thread.join()

    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        safety_level: SafetyLevel,
        access_scope: AccessScope,
        user_id: str,
        token_id: Optional[str] = None,
        resource_path: Optional[str] = None,
        operation: Optional[Permission] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_event_id: Optional[str] = None
    ):
        """Log an audit event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            safety_level=safety_level,
            access_scope=access_scope,
            token_id=token_id,
            user_id=user_id,
            resource_path=resource_path,
            operation=operation,
            details=details or {},
            metadata=metadata or {},
            parent_event_id=parent_event_id
        )
        self.event_queue.put(event)

    def _generate_event_id(self) -> str:
        """Generate a unique event ID"""
        timestamp = datetime.now().isoformat()
        random = str(hash(timestamp + str(threading.get_ident())))
        return hashlib.sha256(f"{timestamp}{random}".encode()).hexdigest()[:16]


class AuditAnalyzer:
    """Analyzes audit logs for patterns and anomalies"""
    
    def __init__(self, store: AuditStore):
        self.store = store

    def get_activity_summary(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate activity summary for a time period"""
        events = self.store.query_events(start_time=start_time, end_time=end_time)
        
        return {
            'total_events': len(events),
            'by_type': self._count_by_field(events, 'event_type'),
            'by_severity': self._count_by_field(events, 'severity'),
            'by_user': self._count_by_field(events, 'user_id'),
            'access_denied_rate': self._calculate_denial_rate(events),
            'validation_failure_rate': self._calculate_validation_failure_rate(events)
        }

    def detect_anomalies(
        self,
        window: timedelta = timedelta(hours=1)
    ) -> List[Dict[str, Any]]:
        """Detect potential security anomalies"""
        end_time = datetime.now()
        start_time = end_time - window
        events = self.store.query_events(start_time=start_time, end_time=end_time)
        
        anomalies = []
        
        # Check for high denial rates
        denial_rate = self._calculate_denial_rate(events)
        if denial_rate > 0.2:  # More than 20% denials
            anomalies.append({
                'type': 'high_denial_rate',
                'value': denial_rate,
                'threshold': 0.2
            })
        
        # Check for repeated security violations
        violations = [e for e in events if e.event_type == AuditEventType.SECURITY_VIOLATION]
        if len(violations) > 5:  # More than 5 violations in window
            anomalies.append({
                'type': 'repeated_violations',
                'count': len(violations),
                'threshold': 5
            })
        
        return anomalies

    def _count_by_field(
        self,
        events: List[AuditEvent],
        field: str
    ) -> Dict[str, int]:
        """Count events by a specific field"""
        counts: Dict[str, int] = {}
        for event in events:
            value = getattr(event, field)
            if isinstance(value, Enum):
                value = value.name
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _calculate_denial_rate(self, events: List[AuditEvent]) -> float:
        """Calculate the rate of access denials"""
        access_events = [
            e for e in events
            if e.event_type in (AuditEventType.ACCESS_GRANTED, AuditEventType.ACCESS_DENIED)
        ]
        if not access_events:
            return 0.0
        
        denials = sum(1 for e in access_events if e.event_type == AuditEventType.ACCESS_DENIED)
        return denials / len(access_events)

    def _calculate_validation_failure_rate(self, events: List[AuditEvent]) -> float:
        """Calculate the rate of validation failures"""
        validation_events = [
            e for e in events
            if e.event_type in (AuditEventType.VALIDATION_SUCCESS, AuditEventType.VALIDATION_FAILURE)
        ]
        if not validation_events:
            return 0.0
        
        failures = sum(1 for e in validation_events if e.event_type == AuditEventType.VALIDATION_FAILURE)
        return failures / len(validation_events)
