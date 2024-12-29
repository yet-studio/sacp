"""
SafeAI CodeGuard Protocol - Analytics Dashboard Demo
Runs the analytics dashboards with demo data.
"""

import asyncio
from datetime import datetime, timedelta
import webbrowser

from ..behavior import BehaviorAnalyzer
from ..risk import RiskAnalyzer
from ..trends import TrendAnalyzer
from ..compliance import ComplianceAnalyzer

async def main():
    """Run analytics dashboards demo"""
    # Initialize analyzers
    db_path = 'analytics_demo.db'
    behavior_analyzer = BehaviorAnalyzer(db_path)
    risk_analyzer = RiskAnalyzer(db_path)
    trend_analyzer = TrendAnalyzer(db_path)
    compliance_analyzer = ComplianceAnalyzer(db_path)
    
    # Create dashboards for demo tenant
    tenant_id = 'demo-tenant-1'
    
    # Create and run dashboards
    behavior_app = behavior_analyzer.create_dashboard(tenant_id)
    risk_app = risk_analyzer.create_dashboard(tenant_id)
    trend_app = trend_analyzer.create_dashboard(tenant_id)
    compliance_app = compliance_analyzer.create_dashboard(tenant_id)
    
    # Run on different ports
    behavior_app.run_server(port=8050)
    risk_app.run_server(port=8051)
    trend_app.run_server(port=8052)
    compliance_app.run_server(port=8053)
    
    # Open dashboards in browser
    webbrowser.open('http://localhost:8050')  # Behavior Analytics
    webbrowser.open('http://localhost:8051')  # Risk Assessment
    webbrowser.open('http://localhost:8052')  # Safety Trends
    webbrowser.open('http://localhost:8053')  # Compliance

if __name__ == '__main__':
    asyncio.run(main())
