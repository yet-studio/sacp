#!/usr/bin/env python3
"""
SACP Core Verification Script
Monitors development progress and validates core functionality
"""

import time
import psutil
import json
from pathlib import Path
from typing import Dict, List, Any
import logging
import importlib
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreVerifier:
    """Verifies core SACP functionality"""
    
    def __init__(self):
        self.metrics_file = Path('metrics.json')
        self.results: Dict[str, Any] = {
            'timestamp': time.time(),
            'tests': {},
            'metrics': {
                'passed': 0,
                'failed': 0,
                'performance': {}
            }
        }

    def verify_protocol(self) -> bool:
        """Verify core protocol functionality"""
        try:
            from src.core.protocol import SafetyProtocol, SafetyLevel
            
            # Test initialization
            protocol = SafetyProtocol()
            assert protocol.safety_level == SafetyLevel.READ_ONLY
            
            # Test validation
            assert protocol.validate_change({"type": "read", "file": "test.py"})
            assert not protocol.validate_change({"type": "write", "file": "test.py"})
            
            # Test history
            assert protocol.log_change({"type": "read", "file": "test.py"})
            history = protocol.get_history()
            assert len(history) == 1
            assert history[0]["validated"] == True
            
            logger.info("Protocol verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Protocol verification failed: {str(e)}")
            return False

    def verify_safety_validator(self) -> bool:
        """Verify safety validator functionality"""
        try:
            from src.core.safety.validator import SafetyValidator
            
            validator = SafetyValidator()
            context = {"operation": "read", "file": "test.py"}
            
            result = validator.validate(context)
            assert result.valid
            
            logger.info("Safety validator verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Safety validator verification failed: {str(e)}")
            return False

    def run_verification(self) -> bool:
        """Run all verifications"""
        tests = [
            ("protocol", self.verify_protocol),
            ("safety_validator", self.verify_safety_validator)
        ]
        
        for name, test_func in tests:
            start_time = time.time()
            memory_before = psutil.Process().memory_info().rss
            
            try:
                result = test_func()
                self.results['tests'][name] = result
                self.results['metrics']['passed'] += 1 if result else 0
                self.results['metrics']['failed'] += 0 if result else 1
                
            except Exception as e:
                logger.error(f"Test '{name}' failed: {str(e)}")
                self.results['tests'][name] = False
                self.results['metrics']['failed'] += 1
            
            self.results['metrics']['performance'][name] = {
                'time': time.time() - start_time,
                'memory': psutil.Process().memory_info().rss - memory_before
            }
        
        return self.results['metrics']['failed'] == 0

    def save_results(self):
        """Save verification results"""
        self.metrics_file.write_text(json.dumps(self.results, indent=2))

def main():
    verifier = CoreVerifier()
    success = verifier.run_verification()
    verifier.save_results()
    
    if not success:
        logger.error("Core verification failed")
        sys.exit(1)
    
    logger.info("Core verification completed successfully")

if __name__ == "__main__":
    main()
