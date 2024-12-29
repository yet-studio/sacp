"""
SafeAI CodeGuard Protocol - Analytics Demo Data Generator
Generates realistic example data for analytics demonstrations.
"""

import asyncio
import random
from datetime import datetime, timedelta
import uuid
import numpy as np
from typing import Dict, List

from ..behavior import BehaviorMetrics, BehaviorAnalyzer
from ..risk import RiskMetrics, RiskAnalyzer
from ..trends import TrendMetrics, TrendAnalyzer
from ..compliance import ComplianceMetrics, ComplianceAnalyzer

class DemoDataGenerator:
    """Generates realistic demo data for analytics"""
    
    def __init__(
        self,
        db_path: str,
        tenant_ids: List[str],
        days: int = 90
    ):
        self.db_path = db_path
        self.tenant_ids = tenant_ids
        self.days = days
        
        # Initialize analyzers
        self.behavior_analyzer = BehaviorAnalyzer(db_path)
        self.risk_analyzer = RiskAnalyzer(db_path)
        self.trend_analyzer = TrendAnalyzer(db_path)
        self.compliance_analyzer = ComplianceAnalyzer(db_path)
        
        # Set random seed for reproducibility
        random.seed(42)
        np.random.seed(42)
    
    def _generate_time_series(
        self,
        days: int,
        base: float,
        trend: float = 0.0,
        seasonality: float = 0.0,
        noise: float = 0.1
    ) -> List[float]:
        """Generate realistic time series data"""
        t = np.linspace(0, days, days * 24)  # Hourly data
        
        # Add trend
        series = base + trend * t
        
        # Add seasonality (daily and weekly patterns)
        if seasonality > 0:
            daily = seasonality * np.sin(2 * np.pi * t / 24)
            weekly = seasonality * np.sin(2 * np.pi * t / (24 * 7))
            series += daily + weekly
        
        # Add noise
        series += np.random.normal(0, noise, len(t))
        
        # Ensure non-negative values
        return np.maximum(series, 0).tolist()
    
    async def generate_behavior_data(self):
        """Generate behavior metrics data"""
        for tenant_id in self.tenant_ids:
            # Generate time series for each metric
            request_counts = self._generate_time_series(
                self.days, 100, trend=0.5, seasonality=20, noise=5
            )
            error_rates = self._generate_time_series(
                self.days, 0.05, trend=-0.0001, seasonality=0.01, noise=0.005
            )
            response_times = self._generate_time_series(
                self.days, 0.2, trend=0.001, seasonality=0.05, noise=0.02
            )
            
            start_time = datetime.now() - timedelta(days=self.days)
            
            # Record hourly metrics
            for hour in range(self.days * 24):
                current_time = start_time + timedelta(hours=hour)
                
                metrics = BehaviorMetrics(
                    request_count=int(request_counts[hour]),
                    modification_rate=random.uniform(0.1, 0.3),
                    error_rate=error_rates[hour],
                    avg_response_time=response_times[hour],
                    resource_usage={
                        'cpu': random.uniform(0.2, 0.8),
                        'memory': random.uniform(0.3, 0.7),
                        'disk': random.uniform(0.1, 0.4)
                    },
                    safety_violations=int(random.paretovariate(3)),
                    risk_score=random.uniform(0.1, 0.4)
                )
                
                await self.behavior_analyzer.record_metrics(tenant_id, metrics)
    
    async def generate_risk_data(self):
        """Generate risk assessment data"""
        for tenant_id in self.tenant_ids:
            # Generate time series for each metric
            safety_scores = self._generate_time_series(
                self.days, 0.9, trend=-0.001, seasonality=0.05, noise=0.02
            )
            reliability_scores = self._generate_time_series(
                self.days, 0.85, trend=0.001, seasonality=0.03, noise=0.01
            )
            
            start_time = datetime.now() - timedelta(days=self.days)
            
            # Record hourly metrics
            for hour in range(self.days * 24):
                current_time = start_time + timedelta(hours=hour)
                
                metrics = RiskMetrics(
                    safety_score=safety_scores[hour],
                    reliability_score=reliability_scores[hour],
                    compliance_score=random.uniform(0.8, 0.95),
                    vulnerability_score=random.uniform(0.1, 0.3),
                    impact_score=random.uniform(0.2, 0.5),
                    probability_score=random.uniform(0.1, 0.4)
                )
                
                await self.risk_analyzer.record_metrics(tenant_id, metrics)
    
    async def generate_trend_data(self):
        """Generate safety trend data"""
        for tenant_id in self.tenant_ids:
            # Generate time series for each metric
            violation_counts = self._generate_time_series(
                self.days, 5, trend=0.02, seasonality=2, noise=1
            )
            risk_levels = self._generate_time_series(
                self.days, 0.3, trend=0.001, seasonality=0.05, noise=0.02
            )
            
            start_time = datetime.now() - timedelta(days=self.days)
            
            # Record hourly metrics
            for hour in range(self.days * 24):
                current_time = start_time + timedelta(hours=hour)
                
                metrics = TrendMetrics(
                    safety_violations=int(violation_counts[hour]),
                    risk_level=risk_levels[hour],
                    incident_count=int(random.paretovariate(4)),
                    recovery_time=random.uniform(1, 24),
                    mitigation_effectiveness=random.uniform(0.6, 0.9),
                    compliance_rate=random.uniform(0.8, 0.95)
                )
                
                await self.trend_analyzer.record_metrics(tenant_id, metrics)
    
    async def generate_compliance_data(self):
        """Generate compliance monitoring data"""
        for tenant_id in self.tenant_ids:
            # Generate time series for each metric
            violations = self._generate_time_series(
                self.days, 3, trend=-0.01, seasonality=1, noise=0.5
            )
            adherence = self._generate_time_series(
                self.days, 0.9, trend=0.0005, seasonality=0.02, noise=0.01
            )
            
            start_time = datetime.now() - timedelta(days=self.days)
            
            # Record hourly metrics
            for hour in range(self.days * 24):
                current_time = start_time + timedelta(hours=hour)
                
                metrics = ComplianceMetrics(
                    policy_violations=int(violations[hour]),
                    policy_adherence=adherence[hour],
                    risk_violations=int(random.paretovariate(5)),
                    safety_compliance=random.uniform(0.85, 0.98),
                    audit_score=random.uniform(0.8, 0.95),
                    resolution_time=random.uniform(2, 48)
                )
                
                await self.compliance_analyzer.record_metrics(tenant_id, metrics)

async def main():
    """Generate demo data for all components"""
    # Example tenant IDs
    tenant_ids = [
        'demo-tenant-1',  # Enterprise customer
        'demo-tenant-2',  # Startup
        'demo-tenant-3'   # Research institution
    ]
    
    generator = DemoDataGenerator(
        db_path='analytics_demo.db',
        tenant_ids=tenant_ids,
        days=90  # 3 months of data
    )
    
    print("Generating behavior data...")
    await generator.generate_behavior_data()
    
    print("Generating risk data...")
    await generator.generate_risk_data()
    
    print("Generating trend data...")
    await generator.generate_trend_data()
    
    print("Generating compliance data...")
    await generator.generate_compliance_data()
    
    print("Demo data generation complete!")

if __name__ == '__main__':
    asyncio.run(main())
