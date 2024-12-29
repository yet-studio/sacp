"""
SafeAI CodeGuard Protocol - Test Metrics Plugin
Pytest plugin to collect and analyze test execution metrics
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import pytest
import psutil
from .progression_tracker import ProgressionTracker, ProgressionMetric

@dataclass
class TestMetric:
    """Single test execution metric"""
    test_name: str
    duration: float
    result: str
    timestamp: str
    cpu_percent: float
    memory_mb: float
    step_name: str

@dataclass
class TestSuiteMetrics:
    """Overall test suite metrics"""
    total_duration: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    timestamp: str
    slowest_tests: List[Dict]
    avg_cpu_percent: float
    peak_cpu_percent: float
    avg_memory_mb: float
    peak_memory_mb: float

class MetricsPlugin:
    """Pytest plugin to collect test metrics"""
    
    def __init__(self, metrics_dir: str = ".metrics"):
        self.metrics_dir = Path(metrics_dir).resolve()
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.current_run: Dict[str, Dict] = {}
        self.start_time = None
        self.test_outcomes = {"passed": 0, "failed": 0, "skipped": 0}
        self.process = psutil.Process()
        self.cpu_samples = []
        self.memory_samples = []
        self.progression_tracker = ProgressionTracker(str(self.metrics_dir))
        self.progression_metrics = []
        
    def _get_resource_usage(self):
        """Get current resource usage"""
        return {
            'cpu_percent': self.process.cpu_percent(),
            'memory_mb': self.process.memory_info().rss / 1024 / 1024
        }

    def _record_resource_sample(self):
        """Record current resource usage"""
        usage = self._get_resource_usage()
        self.cpu_samples.append(usage['cpu_percent'])
        self.memory_samples.append(usage['memory_mb'])
        return usage

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item):
        """Wrap test execution to measure duration and resources"""
        self.current_run[item.nodeid] = {
            'start_time': time.time(),
            **self._record_resource_sample(),
            'step': 'setup'
        }
        yield
        if item.nodeid in self.current_run:
            end_usage = self._record_resource_sample()
            self.current_run[item.nodeid].update({
                'duration': time.time() - self.current_run[item.nodeid]['start_time'],
                'end_cpu': end_usage['cpu_percent'],
                'end_memory': end_usage['memory_mb'],
                'step': 'teardown'
            })

    def pytest_runtest_logreport(self, report):
        """Record test results with resource metrics"""
        if report.when == 'call':
            nodeid = report.nodeid
            if nodeid in self.current_run:
                self.test_outcomes[report.outcome] += 1
                usage = self._record_resource_sample()
                metric = TestMetric(
                    test_name=nodeid,
                    duration=self.current_run[nodeid].get('duration', 0),
                    result=report.outcome,
                    timestamp=datetime.now().isoformat(),
                    cpu_percent=usage['cpu_percent'],
                    memory_mb=usage['memory_mb'],
                    step_name=self.current_run[nodeid].get('step', 'unknown')
                )
                self._save_test_metric(metric)
                
                # Track progression
                progression = self.progression_tracker.compare_metrics(asdict(metric))
                self.progression_tracker.save_progression(progression)
                self.progression_metrics.append(progression)

    def pytest_sessionstart(self, session):
        """Called when test session starts"""
        self.start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus):
        """Called when test session ends, calculate resource statistics"""
        duration = time.time() - self.start_time
        
        # Calculate resource statistics
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        peak_cpu = max(self.cpu_samples) if self.cpu_samples else 0
        avg_memory = sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        peak_memory = max(self.memory_samples) if self.memory_samples else 0
        
        # Get slowest tests
        sorted_tests = sorted(
            [(k, v) for k, v in self.current_run.items() if 'duration' in v],
            key=lambda x: x[1]['duration'],
            reverse=True
        )
        slowest_tests = [
            {
                'test_name': test[0],
                'duration': test[1]['duration'],
                'cpu_percent': test[1].get('end_cpu', 0),
                'memory_mb': test[1].get('end_memory', 0)
            }
            for test in sorted_tests[:10]  # Top 10 slowest
        ]
        
        metrics = TestSuiteMetrics(
            total_duration=duration,
            total_tests=sum(self.test_outcomes.values()),
            passed_tests=self.test_outcomes['passed'],
            failed_tests=self.test_outcomes['failed'],
            skipped_tests=self.test_outcomes['skipped'],
            timestamp=datetime.now().isoformat(),
            slowest_tests=slowest_tests,
            avg_cpu_percent=avg_cpu,
            peak_cpu_percent=peak_cpu,
            avg_memory_mb=avg_memory,
            peak_memory_mb=peak_memory
        )
        
        self._save_suite_metrics(metrics)
        self._print_summary(metrics)

    def _save_test_metric(self, metric: TestMetric):
        """Save individual test metric"""
        metrics_file = self.metrics_dir / 'test_metrics.jsonl'
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metric)) + '\n')

    def _save_suite_metrics(self, metrics: TestSuiteMetrics):
        """Save suite-wide metrics"""
        metrics_file = self.metrics_dir / 'suite_metrics.jsonl'
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')

    def _print_summary(self, metrics: TestSuiteMetrics):
        """Print test execution summary with resource usage"""
        print("\n=== Test Execution Summary ===")
        print(f"Duration: {metrics.total_duration:.2f}s")
        print(f"Tests: {metrics.total_tests} total")
        print(f"  ✓ {metrics.passed_tests} passed")
        print(f"  ✗ {metrics.failed_tests} failed")
        print(f"  - {metrics.skipped_tests} skipped")
        
        print("\nResource Usage:")
        print(f"  CPU: {metrics.avg_cpu_percent:.1f}% avg, {metrics.peak_cpu_percent:.1f}% peak")
        print(f"  Memory: {metrics.avg_memory_mb:.1f}MB avg, {metrics.peak_memory_mb:.1f}MB peak")
        
        print("\nSlowest Tests:")
        for test in metrics.slowest_tests[:5]:  # Show top 5
            print(f"  {test['test_name']}: {test['duration']:.2f}s")
            print(f"    CPU: {test['cpu_percent']:.1f}%, Memory: {test['memory_mb']:.1f}MB")
            
        # Print progression summary
        if self.progression_metrics:
            self.progression_tracker.print_progression_summary(self.progression_metrics)

@pytest.fixture
def metrics_plugin():
    """Fixture to access metrics plugin"""
    return MetricsPlugin()

def pytest_configure(config):
    """Register the plugin"""
    plugin = MetricsPlugin()
    config.pluginmanager.register(plugin, 'metrics_plugin')
