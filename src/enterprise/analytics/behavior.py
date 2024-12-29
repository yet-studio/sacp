"""
SafeAI CodeGuard Protocol - AI Behavior Analytics
Analyzes and tracks AI behavior patterns and anomalies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid
import sqlite3
import aiosqlite
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

@dataclass
class BehaviorMetrics:
    """Metrics for AI behavior analysis"""
    request_count: int
    modification_rate: float
    error_rate: float
    avg_response_time: float
    resource_usage: Dict[str, float]
    safety_violations: int
    risk_score: float

@dataclass
class BehaviorPattern:
    """Detected behavior pattern"""
    id: str
    name: str
    description: str
    indicators: Dict[str, Any]
    severity: str
    frequency: float
    first_seen: datetime
    last_seen: datetime
    related_patterns: List[str] = field(default_factory=list)

class BehaviorAnalyzer:
    """Analyzes AI behavior patterns"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scaler = StandardScaler()
        self.detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.sequence_model = self._build_sequence_model()
        self._ensure_db()
    
    def _build_sequence_model(self) -> Sequential:
        """Build LSTM model for sequence prediction"""
        model = Sequential([
            LSTM(64, input_shape=(24, 6), return_sequences=True),
            LSTM(32),
            Dense(6, activation='sigmoid')
        ])
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse'
        )
        return model
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS behavior_metrics (
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    metrics BLOB NOT NULL,
                    PRIMARY KEY (timestamp, tenant_id)
                );
                
                CREATE TABLE IF NOT EXISTS behavior_patterns (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    indicators BLOB NOT NULL,
                    severity TEXT NOT NULL,
                    frequency REAL NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    related_patterns TEXT
                );
                
                CREATE TABLE IF NOT EXISTS pattern_correlations (
                    pattern_id_1 TEXT NOT NULL,
                    pattern_id_2 TEXT NOT NULL,
                    correlation_type TEXT NOT NULL,
                    correlation_strength REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    PRIMARY KEY (pattern_id_1, pattern_id_2)
                );
                
                CREATE TABLE IF NOT EXISTS realtime_alerts (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    details BLOB NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_tenant 
                ON behavior_metrics(tenant_id, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_patterns_tenant 
                ON behavior_patterns(tenant_id, severity);
                
                CREATE INDEX IF NOT EXISTS idx_correlations
                ON pattern_correlations(pattern_id_1, correlation_type);
                
                CREATE INDEX IF NOT EXISTS idx_alerts_tenant
                ON realtime_alerts(tenant_id, timestamp);
            """)
        finally:
            conn.close()
    
    async def record_metrics(
        self,
        tenant_id: str,
        metrics: BehaviorMetrics
    ):
        """Record behavior metrics"""
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO behavior_metrics
                (timestamp, tenant_id, metrics)
                VALUES (?, ?, ?)
            """, (
                now,
                tenant_id,
                json.dumps(metrics.__dict__)
            ))
            await db.commit()
    
    async def detect_anomalies(
        self,
        tenant_id: str,
        window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Detect behavioral anomalies"""
        # Get recent metrics
        since = datetime.now() - timedelta(hours=window_hours)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT metrics 
                FROM behavior_metrics 
                WHERE tenant_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (tenant_id, since.isoformat())) as cursor:
                metrics = []
                async for row in cursor:
                    metrics.append(json.loads(row[0]))
        
        if not metrics:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(metrics)
        
        # Extract features
        features = [
            'request_count',
            'modification_rate',
            'error_rate',
            'avg_response_time',
            'safety_violations',
            'risk_score'
        ]
        X = df[features].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Detect anomalies
        anomaly_scores = self.detector.fit_predict(X_scaled)
        
        # Find anomalous points
        anomalies = []
        for i, score in enumerate(anomaly_scores):
            if score == -1:  # Anomaly
                anomalies.append({
                    'timestamp': df.index[i],
                    'metrics': metrics[i],
                    'score': float(self.detector.score_samples(X_scaled[i:i+1])[0])
                })
        
        return anomalies
    
    async def identify_patterns(
        self,
        tenant_id: str,
        window_hours: int = 168  # 1 week
    ) -> List[BehaviorPattern]:
        """Identify recurring behavior patterns"""
        # Get historical metrics
        since = datetime.now() - timedelta(hours=window_hours)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT metrics 
                FROM behavior_metrics 
                WHERE tenant_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (tenant_id, since.isoformat())) as cursor:
                metrics = []
                async for row in cursor:
                    metrics.append(json.loads(row[0]))
        
        if not metrics:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(metrics)
        
        # Analyze patterns
        patterns = []
        
        # High resource usage pattern
        if (df['resource_usage'].apply(lambda x: max(x.values())) > 0.8).any():
            patterns.append(BehaviorPattern(
                id=str(uuid.uuid4()),
                name="High Resource Usage",
                description="Consistently high resource utilization",
                indicators={
                    'resource_usage': float(
                        df['resource_usage']
                        .apply(lambda x: max(x.values()))
                        .mean()
                    )
                },
                severity="warning",
                frequency=float(
                    (df['resource_usage'].apply(lambda x: max(x.values())) > 0.8)
                    .mean()
                ),
                first_seen=df.index[0],
                last_seen=df.index[-1]
            ))
        
        # High error rate pattern
        if (df['error_rate'] > 0.1).any():
            patterns.append(BehaviorPattern(
                id=str(uuid.uuid4()),
                name="Elevated Error Rate",
                description="Higher than normal error rates",
                indicators={
                    'error_rate': float(df['error_rate'].mean()),
                    'request_count': int(df['request_count'].mean())
                },
                severity="warning" if df['error_rate'].mean() < 0.2 else "critical",
                frequency=float((df['error_rate'] > 0.1).mean()),
                first_seen=df.index[0],
                last_seen=df.index[-1]
            ))
        
        # Safety violation pattern
        if (df['safety_violations'] > 0).any():
            patterns.append(BehaviorPattern(
                id=str(uuid.uuid4()),
                name="Safety Violations",
                description="Repeated safety policy violations",
                indicators={
                    'violation_count': int(df['safety_violations'].sum()),
                    'risk_score': float(df['risk_score'].mean())
                },
                severity="critical",
                frequency=float((df['safety_violations'] > 0).mean()),
                first_seen=df.index[0],
                last_seen=df.index[-1]
            ))
        
        # Store patterns
        async with aiosqlite.connect(self.db_path) as db:
            for pattern in patterns:
                await db.execute("""
                    INSERT OR REPLACE INTO behavior_patterns
                    (id, tenant_id, name, description, indicators,
                    severity, frequency, first_seen, last_seen,
                    related_patterns)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern.id,
                    tenant_id,
                    pattern.name,
                    pattern.description,
                    json.dumps(pattern.indicators),
                    pattern.severity,
                    pattern.frequency,
                    pattern.first_seen.isoformat(),
                    pattern.last_seen.isoformat(),
                    json.dumps(pattern.related_patterns)
                ))
            await db.commit()
        
        return patterns
    
    async def get_risk_factors(
        self,
        tenant_id: str
    ) -> Dict[str, float]:
        """Calculate risk factors from behavior patterns"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get active patterns
            async with db.execute("""
                SELECT severity, COUNT(*) 
                FROM behavior_patterns
                WHERE tenant_id = ?
                GROUP BY severity
            """, (tenant_id,)) as cursor:
                severity_counts = dict(await cursor.fetchall())
            
            # Get recent metrics
            async with db.execute("""
                SELECT metrics
                FROM behavior_metrics
                WHERE tenant_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (tenant_id,)) as cursor:
                recent_metrics = [
                    json.loads(row[0])
                    async for row in cursor
                ]
        
        if not recent_metrics:
            return {}
        
        # Calculate risk factors
        df = pd.DataFrame(recent_metrics)
        return {
            'pattern_risk': (
                (severity_counts.get('critical', 0) * 1.0) +
                (severity_counts.get('warning', 0) * 0.5)
            ) / max(sum(severity_counts.values()), 1),
            'error_risk': float(df['error_rate'].mean()),
            'resource_risk': float(
                df['resource_usage']
                .apply(lambda x: max(x.values()))
                .mean()
            ),
            'safety_risk': float(
                (df['safety_violations'] > 0).mean()
            ),
            'overall_risk': float(df['risk_score'].mean())
        }
    
    async def correlate_patterns(
        self,
        tenant_id: str,
        min_correlation: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Find correlations between behavior patterns"""
        # Get all patterns for tenant
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, name, indicators, severity
                FROM behavior_patterns
                WHERE tenant_id = ?
            """, (tenant_id,)) as cursor:
                patterns = [
                    {
                        'id': row[0],
                        'name': row[1],
                        'indicators': json.loads(row[2]),
                        'severity': row[3]
                    }
                    async for row in cursor
                ]
        
        correlations = []
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i+1:]:
                # Calculate temporal correlation
                temporal_corr = self._calculate_temporal_correlation(
                    p1['indicators'],
                    p2['indicators']
                )
                
                # Calculate causal correlation
                causal_corr = self._calculate_causal_correlation(
                    p1['indicators'],
                    p2['indicators']
                )
                
                if temporal_corr > min_correlation or causal_corr > min_correlation:
                    correlation = {
                        'pattern_1': p1,
                        'pattern_2': p2,
                        'temporal_correlation': temporal_corr,
                        'causal_correlation': causal_corr
                    }
                    correlations.append(correlation)
                    
                    # Store correlation
                    await db.execute("""
                        INSERT OR REPLACE INTO pattern_correlations
                        (pattern_id_1, pattern_id_2, correlation_type,
                        correlation_strength, last_updated)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        p1['id'],
                        p2['id'],
                        'temporal',
                        temporal_corr,
                        datetime.now().isoformat()
                    ))
                    await db.execute("""
                        INSERT OR REPLACE INTO pattern_correlations
                        (pattern_id_1, pattern_id_2, correlation_type,
                        correlation_strength, last_updated)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        p1['id'],
                        p2['id'],
                        'causal',
                        causal_corr,
                        datetime.now().isoformat()
                    ))
            await db.commit()
        
        return correlations
    
    def _calculate_temporal_correlation(
        self,
        indicators1: Dict[str, Any],
        indicators2: Dict[str, Any]
    ) -> float:
        """Calculate temporal correlation between patterns"""
        # Convert indicators to time series
        ts1 = pd.Series(indicators1)
        ts2 = pd.Series(indicators2)
        
        # Calculate cross-correlation
        correlation = ts1.corr(ts2)
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    def _calculate_causal_correlation(
        self,
        indicators1: Dict[str, Any],
        indicators2: Dict[str, Any]
    ) -> float:
        """Calculate potential causal relationship between patterns"""
        # Use Granger causality test
        ts1 = pd.Series(indicators1)
        ts2 = pd.Series(indicators2)
        
        # Simple causal indicator based on lead/lag relationship
        correlation = ts1.corr(ts2.shift(1))
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    async def monitor_realtime(
        self,
        tenant_id: str,
        window_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """Monitor behavior in real-time and detect immediate concerns"""
        since = datetime.now() - timedelta(minutes=window_minutes)
        
        # Get recent metrics
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT metrics
                FROM behavior_metrics
                WHERE tenant_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (tenant_id, since.isoformat())) as cursor:
                metrics = [
                    json.loads(row[0])
                    async for row in cursor
                ]
        
        if not metrics:
            return []
        
        # Convert to sequences for LSTM
        df = pd.DataFrame(metrics)
        features = [
            'request_count',
            'modification_rate',
            'error_rate',
            'avg_response_time',
            'safety_violations',
            'risk_score'
        ]
        X = df[features].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Reshape for LSTM (samples, timesteps, features)
        X_seq = np.array([X_scaled])
        
        # Predict next values
        predictions = self.sequence_model.predict(X_seq)
        
        # Compare with actual values and generate alerts
        alerts = []
        if len(X_scaled) > 0:
            last_actual = X_scaled[-1]
            diff = np.abs(predictions[0] - last_actual)
            
            # Check for significant deviations
            for i, feature in enumerate(features):
                if diff[i] > 2.0:  # More than 2 standard deviations
                    alert = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'anomaly',
                        'feature': feature,
                        'severity': 'critical' if diff[i] > 3.0 else 'warning',
                        'details': {
                            'actual': float(last_actual[i]),
                            'predicted': float(predictions[0][i]),
                            'deviation': float(diff[i])
                        }
                    }
                    alerts.append(alert)
                    
                    # Store alert
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("""
                            INSERT INTO realtime_alerts
                            (id, tenant_id, timestamp, alert_type,
                            severity, details)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            alert['id'],
                            tenant_id,
                            alert['timestamp'],
                            alert['type'],
                            alert['severity'],
                            json.dumps(alert['details'])
                        ))
                        await db.commit()
        
        return alerts
