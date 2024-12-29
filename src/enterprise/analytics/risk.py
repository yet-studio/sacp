"""
SafeAI CodeGuard Protocol - Predictive Risk Assessment
Analyzes and predicts potential risks in AI systems.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid
import sqlite3
import aiosqlite
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

@dataclass
class RiskMetrics:
    """Core risk metrics for assessment"""
    safety_score: float
    reliability_score: float
    compliance_score: float
    vulnerability_score: float
    impact_score: float
    probability_score: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class RiskFactor:
    """Identified risk factor"""
    id: str
    name: str
    description: str
    category: str
    severity: str
    probability: float
    impact: float
    mitigation_status: str
    detection_time: datetime
    last_updated: datetime
    related_metrics: Dict[str, float] = field(default_factory=dict)

class RiskAnalyzer:
    """Analyzes and predicts potential risks"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scaler = StandardScaler()
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.deep_model = self._build_deep_model()
        self._ensure_db()
    
    def _build_deep_model(self) -> Sequential:
        """Build deep learning model for risk prediction"""
        model = Sequential([
            Dense(64, activation='relu', input_shape=(12,)),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        return model
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS risk_metrics (
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    metrics BLOB NOT NULL,
                    PRIMARY KEY (timestamp, tenant_id)
                );
                
                CREATE TABLE IF NOT EXISTS risk_factors (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    probability REAL NOT NULL,
                    impact REAL NOT NULL,
                    mitigation_status TEXT NOT NULL,
                    detection_time TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    related_metrics BLOB NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS risk_predictions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    predictions BLOB NOT NULL,
                    confidence REAL NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS mitigation_actions (
                    id TEXT PRIMARY KEY,
                    risk_factor_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    effectiveness REAL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (risk_factor_id) 
                    REFERENCES risk_factors(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_tenant_time 
                ON risk_metrics(tenant_id, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_factors_tenant 
                ON risk_factors(tenant_id, severity);
                
                CREATE INDEX IF NOT EXISTS idx_predictions_tenant 
                ON risk_predictions(tenant_id, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_actions_risk 
                ON mitigation_actions(risk_factor_id, status);
            """)
        finally:
            conn.close()
    
    async def record_metrics(
        self,
        tenant_id: str,
        metrics: RiskMetrics
    ):
        """Record risk metrics"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO risk_metrics
                (timestamp, tenant_id, metrics)
                VALUES (?, ?, ?)
            """, (
                metrics.timestamp.isoformat(),
                tenant_id,
                json.dumps(metrics.__dict__)
            ))
            await db.commit()
    
    async def predict_risks(
        self,
        tenant_id: str,
        timeframe_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Predict potential risks in the specified timeframe"""
        # Get historical metrics
        since = datetime.now() - timedelta(hours=timeframe_hours * 2)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT metrics
                FROM risk_metrics
                WHERE tenant_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (tenant_id, since.isoformat())) as cursor:
                metrics = [
                    json.loads(row[0])
                    async for row in cursor
                ]
        
        if not metrics:
            return []
        
        # Prepare features
        df = pd.DataFrame(metrics)
        features = [
            'safety_score',
            'reliability_score',
            'compliance_score',
            'vulnerability_score',
            'impact_score',
            'probability_score'
        ]
        X = df[features].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Generate predictions
        risk_probs = self.classifier.predict_proba(X_scaled)
        risk_scores = self.regressor.predict(X_scaled)
        deep_risks = self.deep_model.predict(X_scaled)
        
        # Combine predictions
        predictions = []
        for i, (probs, score, deep_risk) in enumerate(
            zip(risk_probs, risk_scores, deep_risks)
        ):
            prediction = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'risk_probability': float(probs[1]),
                'risk_score': float(score),
                'deep_risk': float(deep_risk[0]),
                'confidence': float(np.mean([probs[1], score, deep_risk[0]])),
                'features': {
                    name: float(X_scaled[i][j])
                    for j, name in enumerate(features)
                }
            }
            predictions.append(prediction)
        
        # Store predictions
        async with aiosqlite.connect(self.db_path) as db:
            for pred in predictions:
                await db.execute("""
                    INSERT INTO risk_predictions
                    (id, tenant_id, timestamp, prediction_type,
                    timeframe, predictions, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pred['id'],
                    tenant_id,
                    pred['timestamp'],
                    'combined',
                    f"{timeframe_hours}h",
                    json.dumps(pred),
                    pred['confidence']
                ))
            await db.commit()
        
        return predictions
    
    async def identify_risk_factors(
        self,
        tenant_id: str,
        min_probability: float = 0.3
    ) -> List[RiskFactor]:
        """Identify specific risk factors from predictions"""
        # Get recent predictions
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT predictions
                FROM risk_predictions
                WHERE tenant_id = ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (tenant_id,)) as cursor:
                predictions = [
                    json.loads(row[0])
                    async for row in cursor
                ]
        
        if not predictions:
            return []
        
        # Analyze predictions for risk factors
        risk_factors = []
        
        # High vulnerability risk
        df = pd.DataFrame([p['features'] for p in predictions])
        if (df['vulnerability_score'] > 0.7).any():
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                name="High Vulnerability Risk",
                description="System shows elevated vulnerability levels",
                category="security",
                severity="critical",
                probability=float(df['vulnerability_score'].mean()),
                impact=0.8,
                mitigation_status="open",
                detection_time=datetime.now(),
                last_updated=datetime.now(),
                related_metrics={
                    'vulnerability_score': float(df['vulnerability_score'].mean()),
                    'safety_score': float(df['safety_score'].mean())
                }
            ))
        
        # Compliance risk
        if (df['compliance_score'] < 0.6).any():
            risk_factors.append(RiskFactor(
                id=str(uuid.uuid4()),
                name="Compliance Risk",
                description="Potential compliance violations detected",
                category="compliance",
                severity="warning",
                probability=float(1 - df['compliance_score'].mean()),
                impact=0.7,
                mitigation_status="open",
                detection_time=datetime.now(),
                last_updated=datetime.now(),
                related_metrics={
                    'compliance_score': float(df['compliance_score'].mean()),
                    'impact_score': float(df['impact_score'].mean())
                }
            ))
        
        # Store risk factors
        async with aiosqlite.connect(self.db_path) as db:
            for factor in risk_factors:
                await db.execute("""
                    INSERT INTO risk_factors
                    (id, tenant_id, name, description, category,
                    severity, probability, impact, mitigation_status,
                    detection_time, last_updated, related_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    factor.id,
                    tenant_id,
                    factor.name,
                    factor.description,
                    factor.category,
                    factor.severity,
                    factor.probability,
                    factor.impact,
                    factor.mitigation_status,
                    factor.detection_time.isoformat(),
                    factor.last_updated.isoformat(),
                    json.dumps(factor.related_metrics)
                ))
            await db.commit()
        
        return risk_factors
    
    async def suggest_mitigations(
        self,
        risk_factor_id: str
    ) -> List[Dict[str, Any]]:
        """Suggest mitigation actions for a risk factor"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get risk factor details
            async with db.execute("""
                SELECT category, severity, probability, impact
                FROM risk_factors
                WHERE id = ?
            """, (risk_factor_id,)) as cursor:
                factor = await cursor.fetchone()
                if not factor:
                    return []
                
                category, severity, probability, impact = factor
        
        # Generate mitigation suggestions based on risk profile
        suggestions = []
        
        if category == "security":
            if severity == "critical":
                suggestions.extend([
                    {
                        'id': str(uuid.uuid4()),
                        'action_type': 'immediate',
                        'description': 'Implement additional security controls',
                        'estimated_effectiveness': 0.8
                    },
                    {
                        'id': str(uuid.uuid4()),
                        'action_type': 'required',
                        'description': 'Conduct security audit',
                        'estimated_effectiveness': 0.7
                    }
                ])
        
        elif category == "compliance":
            suggestions.extend([
                {
                    'id': str(uuid.uuid4()),
                    'action_type': 'recommended',
                    'description': 'Review compliance policies',
                    'estimated_effectiveness': 0.6
                },
                {
                    'id': str(uuid.uuid4()),
                    'action_type': 'optional',
                    'description': 'Update documentation',
                    'estimated_effectiveness': 0.4
                }
            ])
        
        # Store suggestions
        async with aiosqlite.connect(self.db_path) as db:
            for suggestion in suggestions:
                await db.execute("""
                    INSERT INTO mitigation_actions
                    (id, risk_factor_id, action_type, description,
                    status, effectiveness, created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    suggestion['id'],
                    risk_factor_id,
                    suggestion['action_type'],
                    suggestion['description'],
                    'suggested',
                    suggestion['estimated_effectiveness'],
                    datetime.now().isoformat(),
                    None
                ))
            await db.commit()
        
        return suggestions
