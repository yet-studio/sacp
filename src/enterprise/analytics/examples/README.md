# SafeAI CodeGuard Protocol - Analytics Examples

This directory contains example scripts and demo data for the SACP analytics module.

## Demo Data Generator

The `generate_demo_data.py` script creates realistic example data for all analytics components:

- Behavior Analytics
- Risk Assessment
- Safety Trends
- Compliance Monitoring

### Generated Data Features

1. **Behavior Data**:
   - Request patterns with daily/weekly seasonality
   - Error rates with slight downward trend
   - Resource usage patterns
   - Safety violation occurrences

2. **Risk Data**:
   - Safety scores with minor degradation
   - Reliability scores with improvement trend
   - Vulnerability patterns
   - Impact assessments

3. **Trend Data**:
   - Safety violation trends
   - Risk level progression
   - Recovery time patterns
   - Compliance rate changes

4. **Compliance Data**:
   - Policy violation patterns
   - Adherence improvements
   - Audit score variations
   - Resolution time tracking

### Usage

1. Generate demo data:
   ```bash
   python -m src.enterprise.analytics.examples.generate_demo_data
   ```

2. Run demo dashboards:
   ```bash
   python -m src.enterprise.analytics.examples.run_demo_dashboard
   ```

This will:
1. Create an SQLite database with 3 months of demo data
2. Launch interactive dashboards on localhost
3. Open dashboard URLs in your default browser

## Dashboard Ports

- Behavior Analytics: http://localhost:8050
- Risk Assessment: http://localhost:8051
- Safety Trends: http://localhost:8052
- Compliance: http://localhost:8053

## Example Tenants

The demo includes data for three example tenants:

1. `demo-tenant-1`: Enterprise customer
   - High request volume
   - Strict compliance requirements
   - Complex safety patterns

2. `demo-tenant-2`: Startup
   - Growing usage patterns
   - Evolving risk profile
   - Rapid changes

3. `demo-tenant-3`: Research institution
   - Experimental usage
   - Unique safety requirements
   - Specialized compliance needs
