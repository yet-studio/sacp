"""
SafeAI CodeGuard Protocol - Database Models
SQLAlchemy models for data persistence.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Enum,
    Text,
    Boolean
)
import enum

from .database import Base


class AlertLevel(enum.Enum):
    """Alert severity levels"""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


class SafetyMetric(Base):
    """Safety-related metrics"""
    __tablename__ = 'safety_metrics'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    timestamp = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    meta_data = Column(
        JSON,
        default=dict,
        nullable=False
    )


class SafetyAlert(Base):
    """Safety alerts and notifications"""
    __tablename__ = 'safety_alerts'
    
    id = Column(Integer, primary_key=True)
    level = Column(Enum(AlertLevel), nullable=False)
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(
        JSON,
        default=dict,
        nullable=False
    )
    timestamp = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)


class SystemHealth(Base):
    """System health status"""
    __tablename__ = 'system_health'
    
    id = Column(Integer, primary_key=True)
    healthy = Column(Boolean, nullable=False)
    checks = Column(
        JSON,
        default=dict,
        nullable=False
    )
    metrics = Column(
        JSON,
        default=dict,
        nullable=False
    )
    timestamp = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )


class OperationLog(Base):
    """Operation audit log"""
    __tablename__ = 'operation_logs'
    
    id = Column(Integer, primary_key=True)
    operation_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    user = Column(String(100), nullable=False)
    details = Column(
        JSON,
        default=dict,
        nullable=False
    )
    impact_score = Column(Float, nullable=False)
    started_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    completed_at = Column(DateTime)
    error_message = Column(Text)


class ResourceUsage(Base):
    """Resource usage metrics"""
    __tablename__ = 'resource_usage'
    
    id = Column(Integer, primary_key=True)
    cpu_percent = Column(Float, nullable=False)
    memory_mb = Column(Float, nullable=False)
    disk_mb = Column(Float, nullable=False)
    network_bytes = Column(Integer, nullable=False)
    timestamp = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    meta_data = Column(
        JSON,
        default=dict,
        nullable=False
    )
