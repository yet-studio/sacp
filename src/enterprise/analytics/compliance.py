"""
SafeAI CodeGuard Protocol - Compliance Dashboards
Provides real-time compliance monitoring and reporting.
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
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

@dataclass
class ComplianceMetrics:
    """Core compliance metrics"""
    policy_violations: int
    policy_adherence: float
    risk_violations: int
    safety_compliance: float
    audit_score: float
    resolution_time: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ComplianceReport:
    """Compliance report details"""
    id: str
    tenant_id: str
    report_type: str
    start_time: datetime
    end_time: datetime
    metrics: Dict[str, Any]
    violations: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime = field(default_factory=datetime.now)

class ComplianceAnalyzer:
    """Analyzes compliance data and generates reports"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS compliance_metrics (
                    timestamp TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    metrics BLOB NOT NULL,
                    PRIMARY KEY (timestamp, tenant_id)
                );
                
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    metrics BLOB NOT NULL,
                    violations BLOB NOT NULL,
                    recommendations BLOB NOT NULL,
                    generated_at TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS compliance_violations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detection_time TEXT NOT NULL,
                    resolution_time TEXT,
                    status TEXT NOT NULL,
                    details BLOB NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS compliance_recommendations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    impact_score REAL NOT NULL,
                    implementation_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_tenant_time 
                ON compliance_metrics(tenant_id, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_reports_tenant 
                ON compliance_reports(tenant_id, report_type);
                
                CREATE INDEX IF NOT EXISTS idx_violations_tenant 
                ON compliance_violations(tenant_id, status);
                
                CREATE INDEX IF NOT EXISTS idx_recommendations_tenant 
                ON compliance_recommendations(tenant_id, priority);
            """)
        finally:
            conn.close()
    
    async def record_metrics(
        self,
        tenant_id: str,
        metrics: ComplianceMetrics
    ):
        """Record compliance metrics"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO compliance_metrics
                (timestamp, tenant_id, metrics)
                VALUES (?, ?, ?)
            """, (
                metrics.timestamp.isoformat(),
                tenant_id,
                json.dumps(metrics.__dict__)
            ))
            await db.commit()
    
    async def generate_report(
        self,
        tenant_id: str,
        report_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> ComplianceReport:
        """Generate compliance report"""
        # Get metrics for time period
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT metrics
                FROM compliance_metrics
                WHERE tenant_id = ? 
                AND timestamp >= ?
                AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (
                tenant_id,
                start_time.isoformat(),
                end_time.isoformat()
            )) as cursor:
                metrics = [
                    json.loads(row[0])
                    async for row in cursor
                ]
            
            # Get violations
            async with db.execute("""
                SELECT violation_type, severity, description,
                       detection_time, resolution_time, status, details
                FROM compliance_violations
                WHERE tenant_id = ?
                AND detection_time >= ?
                AND detection_time <= ?
            """, (
                tenant_id,
                start_time.isoformat(),
                end_time.isoformat()
            )) as cursor:
                violations = [
                    {
                        'type': row[0],
                        'severity': row[1],
                        'description': row[2],
                        'detection_time': row[3],
                        'resolution_time': row[4],
                        'status': row[5],
                        'details': json.loads(row[6])
                    }
                    async for row in cursor
                ]
        
        if not metrics:
            return None
        
        # Calculate aggregate metrics
        df = pd.DataFrame(metrics)
        agg_metrics = {
            'avg_policy_adherence': float(df['policy_adherence'].mean()),
            'total_violations': int(df['policy_violations'].sum()),
            'avg_safety_compliance': float(df['safety_compliance'].mean()),
            'avg_audit_score': float(df['audit_score'].mean()),
            'avg_resolution_time': float(df['resolution_time'].mean())
        }
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            tenant_id,
            agg_metrics,
            violations
        )
        
        # Create report
        report = ComplianceReport(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            report_type=report_type,
            start_time=start_time,
            end_time=end_time,
            metrics=agg_metrics,
            violations=violations,
            recommendations=recommendations
        )
        
        # Store report
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO compliance_reports
                (id, tenant_id, report_type, start_time,
                end_time, metrics, violations,
                recommendations, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.id,
                report.tenant_id,
                report.report_type,
                report.start_time.isoformat(),
                report.end_time.isoformat(),
                json.dumps(report.metrics),
                json.dumps(report.violations),
                json.dumps(report.recommendations),
                report.generated_at.isoformat()
            ))
            await db.commit()
        
        return report
    
    async def _generate_recommendations(
        self,
        tenant_id: str,
        metrics: Dict[str, Any],
        violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Policy adherence recommendations
        if metrics['avg_policy_adherence'] < 0.9:
            recommendations.append({
                'id': str(uuid.uuid4()),
                'category': 'policy',
                'priority': 'high',
                'description': 'Improve policy adherence through training',
                'impact_score': 0.8,
                'implementation_status': 'pending'
            })
        
        # Safety compliance recommendations
        if metrics['avg_safety_compliance'] < 0.95:
            recommendations.append({
                'id': str(uuid.uuid4()),
                'category': 'safety',
                'priority': 'critical',
                'description': 'Enhance safety controls and monitoring',
                'impact_score': 0.9,
                'implementation_status': 'pending'
            })
        
        # Resolution time recommendations
        if metrics['avg_resolution_time'] > 24:  # hours
            recommendations.append({
                'id': str(uuid.uuid4()),
                'category': 'operations',
                'priority': 'medium',
                'description': 'Optimize violation resolution workflow',
                'impact_score': 0.7,
                'implementation_status': 'pending'
            })
        
        # Store recommendations
        async with aiosqlite.connect(self.db_path) as db:
            for rec in recommendations:
                await db.execute("""
                    INSERT INTO compliance_recommendations
                    (id, tenant_id, category, priority,
                    description, impact_score,
                    implementation_status, created_at,
                    updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec['id'],
                    tenant_id,
                    rec['category'],
                    rec['priority'],
                    rec['description'],
                    rec['impact_score'],
                    rec['implementation_status'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
            await db.commit()
        
        return recommendations
    
    def create_dashboard(self, tenant_id: str) -> Dash:
        """Create interactive compliance dashboard"""
        app = Dash(__name__)
        
        app.layout = html.Div([
            html.H1('Compliance Dashboard'),
            
            # Time range selector
            dcc.DatePickerRange(
                id='date-range',
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now()
            ),
            
            # Metrics overview
            html.Div([
                dcc.Graph(id='metrics-graph'),
                dcc.Graph(id='violations-graph'),
                dcc.Graph(id='compliance-trends')
            ]),
            
            # Violations table
            html.Div([
                html.H2('Active Violations'),
                html.Table(id='violations-table')
            ]),
            
            # Recommendations
            html.Div([
                html.H2('Recommendations'),
                html.Div(id='recommendations-list')
            ])
        ])
        
        @app.callback(
            [
                Output('metrics-graph', 'figure'),
                Output('violations-graph', 'figure'),
                Output('compliance-trends', 'figure'),
                Output('violations-table', 'children'),
                Output('recommendations-list', 'children')
            ],
            [
                Input('date-range', 'start_date'),
                Input('date-range', 'end_date')
            ]
        )
        async def update_dashboard(start_date, end_date):
            """Update dashboard components"""
            # Get report data
            report = await self.generate_report(
                tenant_id,
                'dashboard',
                datetime.fromisoformat(start_date),
                datetime.fromisoformat(end_date)
            )
            
            if not report:
                return {}, {}, {}, [], []
            
            # Create metrics graph
            metrics_fig = go.Figure(data=[
                go.Indicator(
                    mode='gauge+number',
                    value=report.metrics['avg_policy_adherence'] * 100,
                    title={'text': 'Policy Adherence'},
                    gauge={'axis': {'range': [0, 100]}}
                )
            ])
            
            # Create violations graph
            violations_df = pd.DataFrame(report.violations)
            violations_fig = px.bar(
                violations_df,
                x='detection_time',
                color='severity',
                title='Violations by Severity'
            )
            
            # Create trends graph
            trends_fig = px.line(
                pd.DataFrame(report.metrics),
                title='Compliance Trends'
            )
            
            # Create violations table
            violations_table = html.Table([
                html.Thead([
                    html.Tr([
                        html.Th('Type'),
                        html.Th('Severity'),
                        html.Th('Status'),
                        html.Th('Detection Time')
                    ])
                ]),
                html.Tbody([
                    html.Tr([
                        html.Td(v['type']),
                        html.Td(v['severity']),
                        html.Td(v['status']),
                        html.Td(v['detection_time'])
                    ])
                    for v in report.violations[:10]  # Show latest 10
                ])
            ])
            
            # Create recommendations list
            recommendations_list = html.Ul([
                html.Li([
                    html.Strong(f"{r['category']} - {r['priority']}: "),
                    html.Span(r['description'])
                ])
                for r in report.recommendations
            ])
            
            return (
                metrics_fig,
                violations_fig,
                trends_fig,
                violations_table,
                recommendations_list
            )
        
        return app
