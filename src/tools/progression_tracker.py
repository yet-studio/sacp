"""
SafeAI CodeGuard Protocol - Progression Tracker
Track improvements and regressions in test performance over time
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ProgressionMetric:
    """Metric for tracking progression between test runs"""
    timestamp: str
    test_name: str
    duration_change: float  # Positive = regression, Negative = improvement
    cpu_change: float
    memory_change: float
    status_change: str  # "improved", "regressed", "unchanged"
    details: Dict

class ProgressionTracker:
    """Track test progression over time"""
    
    def __init__(self, metrics_dir: str = ".metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.progression_dir = self.metrics_dir / "progression"
        self.progression_dir.mkdir(parents=True, exist_ok=True)
        
        # Load previous metrics if they exist
        self.previous_metrics = self._load_previous_metrics()
        
    def _load_previous_metrics(self) -> Dict:
        """Load the most recent metrics for comparison"""
        metrics_file = self.metrics_dir / "test_metrics.jsonl"
        if not metrics_file.exists():
            return {}
            
        previous = {}
        with open(metrics_file, 'r') as f:
            for line in f:
                try:
                    metric = json.loads(line.strip())
                    previous[metric['test_name']] = metric
                except:
                    continue
        return previous
        
    def compare_metrics(self, current_metric: Dict) -> ProgressionMetric:
        """Compare current metric with previous run"""
        test_name = current_metric['test_name']
        previous = self.previous_metrics.get(test_name)
        
        if not previous:
            return ProgressionMetric(
                timestamp=datetime.now().isoformat(),
                test_name=test_name,
                duration_change=0,
                cpu_change=0,
                memory_change=0,
                status_change="new",
                details={"message": "First run of this test"}
            )
            
        # Calculate changes
        duration_change = current_metric['duration'] - float(previous.get('duration', 0))
        cpu_change = current_metric.get('cpu_percent', 0) - float(previous.get('cpu_percent', 0))
        memory_change = current_metric.get('memory_mb', 0) - float(previous.get('memory_mb', 0))
        
        # Determine overall status
        if duration_change < 0 and cpu_change <= 0:
            status = "improved"
        elif duration_change > 0 or cpu_change > 5:  # 5% CPU increase threshold
            status = "regressed"
        else:
            status = "unchanged"
            
        return ProgressionMetric(
            timestamp=datetime.now().isoformat(),
            test_name=test_name,
            duration_change=duration_change,
            cpu_change=cpu_change,
            memory_change=memory_change,
            status_change=status,
            details={
                "previous_duration": previous.get('duration', 0),
                "current_duration": current_metric['duration'],
                "previous_cpu": previous.get('cpu_percent', 0),
                "current_cpu": current_metric.get('cpu_percent', 0),
                "previous_memory": previous.get('memory_mb', 0),
                "current_memory": current_metric.get('memory_mb', 0)
            }
        )
        
    def save_progression(self, metric: ProgressionMetric):
        """Save progression data"""
        progression_file = self.progression_dir / f"progression_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(progression_file, 'a') as f:
            f.write(json.dumps(asdict(metric)) + '\n')
            
    def print_progression_summary(self, metrics: List[ProgressionMetric]):
        """Print a summary of test progression"""
        improved = [m for m in metrics if m.status_change == "improved"]
        regressed = [m for m in metrics if m.status_change == "regressed"]
        unchanged = [m for m in metrics if m.status_change == "unchanged"]
        
        print("\n=== Test Progression Summary ===")
        print(f"Total Changes: {len(metrics)}")
        print(f"  ↑ {len(improved)} improved")
        print(f"  ↓ {len(regressed)} regressed")
        print(f"  = {len(unchanged)} unchanged")
        
        if improved:
            print("\nTop Improvements:")
            for m in sorted(improved, key=lambda x: x.duration_change)[:3]:
                print(f"  {m.test_name}")
                print(f"    Time: {abs(m.duration_change):.2f}s faster")
                print(f"    CPU: {abs(m.cpu_change):.1f}% less")
                print(f"    Memory: {abs(m.memory_change):.1f}MB less")
                
        if regressed:
            print("\nTop Regressions:")
            for m in sorted(regressed, key=lambda x: -x.duration_change)[:3]:
                print(f"  {m.test_name}")
                print(f"    Time: {m.duration_change:.2f}s slower")
                print(f"    CPU: {m.cpu_change:.1f}% more")
                print(f"    Memory: {m.memory_change:.1f}MB more")
