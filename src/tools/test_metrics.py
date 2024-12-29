"""
Test Metrics Collector for SACP
Lightweight tool to monitor test performance and coverage
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pytest
import coverage

@dataclass
class TestMetric:
    """Single test execution metric"""
    test_name: str
    duration: float
    result: str
    timestamp: str
    memory_usage: Optional[float] = None

@dataclass
class TestSuiteMetrics:
    """Overall test suite metrics"""
    total_duration: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    coverage_percentage: float
    timestamp: str
    slowest_tests: List[TestMetric]

class TestMetricsCollector:
    """Collects and stores test execution metrics"""
    
    def __init__(self, metrics_dir: str = ".metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)
        self.current_run: Dict[str, TestMetric] = {}
        self.cov = coverage.Coverage()
        
    def pytest_runtest_setup(self, item):
        """Called before each test"""
        self.current_run[item.nodeid] = {
            'start_time': time.time()
        }

    def pytest_runtest_teardown(self, item):
        """Called after each test"""
        if item.nodeid in self.current_run:
            duration = time.time() - self.current_run[item.nodeid]['start_time']
            self.current_run[item.nodeid]['duration'] = duration

    def pytest_runtest_logreport(self, report):
        """Called when test results are available"""
        if report.when == 'call':
            nodeid = report.nodeid
            if nodeid in self.current_run:
                metric = TestMetric(
                    test_name=nodeid,
                    duration=self.current_run[nodeid].get('duration', 0),
                    result=report.outcome,
                    timestamp=datetime.now().isoformat()
                )
                self._save_test_metric(metric)

    def pytest_sessionfinish(self, session):
        """Called when test session ends"""
        duration = time.time() - session.start_time
        
        # Get test counts
        counts = session.testscollector.stats
        total = sum(counts.values())
        passed = counts.get('passed', 0)
        failed = counts.get('failed', 0)
        skipped = counts.get('skipped', 0)
        
        # Get coverage
        self.cov.stop()
        coverage_data = self.cov.get_data()
        total_lines = 0
        covered_lines = 0
        for filename in coverage_data.measured_files():
            _, executable, _, missing, _ = self.cov.analysis2(filename)
            total_lines += len(executable)
            covered_lines += len(executable) - len(missing)
        
        coverage_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # Get slowest tests
        sorted_tests = sorted(
            [m for m in self.current_run.values() if 'duration' in m],
            key=lambda x: x['duration'],
            reverse=True
        )
        slowest_tests = sorted_tests[:10]  # Top 10 slowest
        
        metrics = TestSuiteMetrics(
            total_duration=duration,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            coverage_percentage=coverage_pct,
            timestamp=datetime.now().isoformat(),
            slowest_tests=[TestMetric(
                test_name=t['nodeid'],
                duration=t['duration'],
                result='completed',
                timestamp=datetime.now().isoformat()
            ) for t in slowest_tests]
        )
        
        self._save_suite_metrics(metrics)

    def _save_test_metric(self, metric: TestMetric):
        """Save individual test metric"""
        metrics_file = self.metrics_dir / 'test_metrics.jsonl'
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(vars(metric)) + '\n')

    def _save_suite_metrics(self, metrics: TestSuiteMetrics):
        """Save suite-wide metrics"""
        metrics_file = self.metrics_dir / 'suite_metrics.jsonl'
        with open(metrics_file, 'a') as f:
            f.write(json.dumps(vars(metrics)) + '\n')

    def get_slow_tests(self, threshold_seconds: float = 1.0) -> List[TestMetric]:
        """Get list of tests that run slower than threshold"""
        metrics_file = self.metrics_dir / 'test_metrics.jsonl'
        slow_tests = []
        
        if metrics_file.exists():
            with open(metrics_file) as f:
                for line in f:
                    metric = json.loads(line)
                    if metric['duration'] > threshold_seconds:
                        slow_tests.append(TestMetric(**metric))
        
        return sorted(slow_tests, key=lambda x: x.duration, reverse=True)

    def get_trend_data(self, days: int = 7) -> List[TestSuiteMetrics]:
        """Get test suite metrics for the last N days"""
        metrics_file = self.metrics_dir / 'suite_metrics.jsonl'
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        trend_data = []
        
        if metrics_file.exists():
            with open(metrics_file) as f:
                for line in f:
                    metric = json.loads(line)
                    timestamp = datetime.fromisoformat(metric['timestamp']).timestamp()
                    if timestamp > cutoff:
                        trend_data.append(TestSuiteMetrics(**metric))
        
        return sorted(trend_data, key=lambda x: x.timestamp)

def print_metrics_report():
    """Print a summary report of test metrics"""
    collector = TestMetricsCollector()
    
    print("\n=== Test Performance Report ===\n")
    
    # Show slow tests
    print("Slow Tests (>1s):")
    slow_tests = collector.get_slow_tests()
    for test in slow_tests[:5]:  # Top 5
        print(f"  {test.test_name}: {test.duration:.2f}s")
    
    # Show trends
    print("\nTrend Data (Last 7 Days):")
    trends = collector.get_trend_data()
    for metric in trends[-5:]:  # Last 5 runs
        print(f"""
  Run at: {metric.timestamp}
  Duration: {metric.total_duration:.1f}s
  Tests: {metric.total_tests} ({metric.passed_tests} passed, {metric.failed_tests} failed)
  Coverage: {metric.coverage_percentage:.1f}%
        """)
