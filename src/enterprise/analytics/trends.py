"""
SafeAI CodeGuard Protocol - Safety Trend Analysis
Analyzes and forecasts safety trends in AI systems.
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
from prophet import Prophet
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose

@dataclass
class SafetyTrend:
    """Safety trend information"""
    id: str
    name: str
    description: str
    trend_type: str  # upward, downward, cyclic, stable
    confidence: float
    start_time: datetime
    end_time: datetime
    data_points: List[float]
    seasonality: Optional[Dict[str, float]] = None
    forecast: Optional[Dict[str, List[float]]] = None

@dataclass
class TrendMetrics:
    """Metrics for trend analysis"""
    safety_violations: int
    risk_level: float
    incident_count: int
    recovery_time: float
    mitigation_effectiveness: float
    compliance_rate: float
    timestamp: datetime = field(default_factory=datetime.now)

class TrendAnalyzer:
    """Analyzes safety trends and patterns"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scaler = StandardScaler()
        self.prophet = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            seasonality_mode='multiplicative'
        )
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS trend_metrics (
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    metrics BLOB NOT NULL,
                    PRIMARY KEY (timestamp, tenant_id)
                );
                
                CREATE TABLE IF NOT EXISTS safety_trends (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    trend_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    data_points BLOB NOT NULL,
                    seasonality BLOB,
                    forecast BLOB
                );
                
                CREATE TABLE IF NOT EXISTS trend_anomalies (
                    id TEXT PRIMARY KEY,
                    trend_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    details BLOB NOT NULL,
                    FOREIGN KEY (trend_id) 
                    REFERENCES safety_trends(id)
                );
                
                CREATE TABLE IF NOT EXISTS trend_correlations (
                    id TEXT PRIMARY KEY,
                    trend_id_1 TEXT NOT NULL,
                    trend_id_2 TEXT NOT NULL,
                    correlation_type TEXT NOT NULL,
                    correlation_value REAL NOT NULL,
                    significance REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (trend_id_1) 
                    REFERENCES safety_trends(id),
                    FOREIGN KEY (trend_id_2) 
                    REFERENCES safety_trends(id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_tenant_time 
                ON trend_metrics(tenant_id, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_trends_tenant 
                ON safety_trends(tenant_id, trend_type);
                
                CREATE INDEX IF NOT EXISTS idx_anomalies_trend 
                ON trend_anomalies(trend_id, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_correlations_trend 
                ON trend_correlations(trend_id_1, correlation_type);
            """)
        finally:
            conn.close()
    
    async def record_metrics(
        self,
        tenant_id: str,
        metrics: TrendMetrics
    ):
        """Record trend metrics"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO trend_metrics
                (timestamp, tenant_id, metrics)
                VALUES (?, ?, ?)
            """, (
                metrics.timestamp.isoformat(),
                tenant_id,
                json.dumps(metrics.__dict__)
            ))
            await db.commit()
    
    async def analyze_trends(
        self,
        tenant_id: str,
        window_days: int = 30
    ) -> List[SafetyTrend]:
        """Analyze safety trends over time"""
        # Get historical metrics
        since = datetime.now() - timedelta(days=window_days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT metrics
                FROM trend_metrics
                WHERE tenant_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (tenant_id, since.isoformat())) as cursor:
                metrics = [
                    json.loads(row[0])
                    async for row in cursor
                ]
        
        if not metrics:
            return []
        
        # Convert to DataFrame
        df = pd.DataFrame(metrics)
        df['ds'] = pd.to_datetime(df['timestamp'])
        
        trends = []
        
        # Analyze each metric
        for metric in [
            'safety_violations',
            'risk_level',
            'incident_count',
            'recovery_time',
            'mitigation_effectiveness',
            'compliance_rate'
        ]:
            # Prepare data for Prophet
            prophet_df = df[['ds', metric]].rename(columns={metric: 'y'})
            
            # Fit Prophet model
            self.prophet.fit(prophet_df)
            
            # Make future predictions
            future = self.prophet.make_future_dataframe(
                periods=window_days,
                freq='D'
            )
            forecast = self.prophet.predict(future)
            
            # Analyze trend type
            current_value = float(df[metric].iloc[-1])
            predicted_value = float(forecast['yhat'].iloc[-1])
            trend_direction = (
                'upward' if predicted_value > current_value * 1.1
                else 'downward' if predicted_value < current_value * 0.9
                else 'stable'
            )
            
            # Check for seasonality
            decomposition = seasonal_decompose(
                df[metric],
                period=7,  # Weekly seasonality
                extrapolate_trend='freq'
            )
            
            # Calculate confidence
            confidence = 1.0 - (
                forecast['yhat_upper'].std() / 
                forecast['yhat'].std()
            )
            
            trend = SafetyTrend(
                id=str(uuid.uuid4()),
                name=f"{metric.replace('_', ' ').title()} Trend",
                description=f"Trend analysis for {metric}",
                trend_type=trend_direction,
                confidence=float(confidence),
                start_time=df['ds'].iloc[0].to_pydatetime(),
                end_time=df['ds'].iloc[-1].to_pydatetime(),
                data_points=df[metric].tolist(),
                seasonality={
                    'weekly': float(decomposition.seasonal[7]),
                    'monthly': float(decomposition.seasonal[30])
                    if len(decomposition.seasonal) >= 30
                    else None
                },
                forecast={
                    'values': forecast['yhat'].tolist(),
                    'lower_bound': forecast['yhat_lower'].tolist(),
                    'upper_bound': forecast['yhat_upper'].tolist()
                }
            )
            trends.append(trend)
            
            # Store trend
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO safety_trends
                    (id, tenant_id, name, description, trend_type,
                    confidence, start_time, end_time, data_points,
                    seasonality, forecast)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend.id,
                    tenant_id,
                    trend.name,
                    trend.description,
                    trend.trend_type,
                    trend.confidence,
                    trend.start_time.isoformat(),
                    trend.end_time.isoformat(),
                    json.dumps(trend.data_points),
                    json.dumps(trend.seasonality),
                    json.dumps(trend.forecast)
                ))
                await db.commit()
        
        return trends
    
    async def detect_trend_anomalies(
        self,
        trend_id: str,
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in a safety trend"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get trend data
            async with db.execute("""
                SELECT data_points, forecast
                FROM safety_trends
                WHERE id = ?
            """, (trend_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return []
                
                data_points = json.loads(row[0])
                forecast = json.loads(row[1])
        
        # Convert to numpy arrays
        actual = np.array(data_points)
        predicted = np.array(forecast['values'])
        upper_bound = np.array(forecast['upper_bound'])
        lower_bound = np.array(forecast['lower_bound'])
        
        # Detect anomalies
        anomalies = []
        for i, (act, pred, upper, lower) in enumerate(
            zip(actual, predicted, upper_bound, lower_bound)
        ):
            deviation = abs(act - pred)
            threshold = sensitivity * (upper - lower)
            
            if deviation > threshold:
                anomaly = {
                    'id': str(uuid.uuid4()),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'deviation',
                    'severity': 'critical' if deviation > 2 * threshold else 'warning',
                    'details': {
                        'actual': float(act),
                        'predicted': float(pred),
                        'deviation': float(deviation),
                        'threshold': float(threshold)
                    }
                }
                anomalies.append(anomaly)
                
                # Store anomaly
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute("""
                        INSERT INTO trend_anomalies
                        (id, trend_id, timestamp, anomaly_type,
                        severity, details)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        anomaly['id'],
                        trend_id,
                        anomaly['timestamp'],
                        anomaly['type'],
                        anomaly['severity'],
                        json.dumps(anomaly['details'])
                    ))
                    await db.commit()
        
        return anomalies
    
    async def correlate_trends(
        self,
        tenant_id: str,
        min_correlation: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Find correlations between different safety trends"""
        # Get all trends for tenant
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, name, data_points
                FROM safety_trends
                WHERE tenant_id = ?
            """, (tenant_id,)) as cursor:
                trends = [
                    {
                        'id': row[0],
                        'name': row[1],
                        'data': json.loads(row[2])
                    }
                    async for row in cursor
                ]
        
        correlations = []
        for i, t1 in enumerate(trends):
            for t2 in trends[i+1:]:
                # Calculate correlation
                corr = np.corrcoef(t1['data'], t2['data'])[0, 1]
                if abs(corr) >= min_correlation:
                    # Calculate significance
                    n = len(t1['data'])
                    t_stat = corr * np.sqrt(
                        (n-2)/(1-corr**2)
                    )
                    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-2))
                    
                    correlation = {
                        'id': str(uuid.uuid4()),
                        'trend_1': {
                            'id': t1['id'],
                            'name': t1['name']
                        },
                        'trend_2': {
                            'id': t2['id'],
                            'name': t2['name']
                        },
                        'correlation': float(corr),
                        'significance': float(1 - p_value)
                    }
                    correlations.append(correlation)
                    
                    # Store correlation
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute("""
                            INSERT INTO trend_correlations
                            (id, trend_id_1, trend_id_2,
                            correlation_type, correlation_value,
                            significance, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            correlation['id'],
                            t1['id'],
                            t2['id'],
                            'pearson',
                            correlation['correlation'],
                            correlation['significance'],
                            datetime.now().isoformat()
                        ))
                        await db.commit()
        
        return correlations
