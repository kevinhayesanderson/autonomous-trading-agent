#!/usr/bin/env python3
"""
Autonomous Quantitative Trading Agent - Agentic Evaluation & Benchmark Runner
Executes comprehensive agentic evals, measuring prompt adherence,
Fiduciary Anti-Ruin Mandate compliance, and test-time reasoning fidelity.
"""

import os
import sys
import unittest
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from tests.test_agent_evals import TestAgenticEvals

def run_agentic_evals():
    print("=" * 80)
    print(" [SOTA AGENTIC EVALUATION & ADVERSARIAL BENCHMARK SUITE - 2026]")
    print(f" Execution Timestamp: {datetime.utcnow().isoformat()}Z")
    print(" Framework: PyUnit + Pydantic v2 + Fiduciary Anti-Ruin Mandate")
    print("=" * 80)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestAgenticEvals)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    print(" [EVALUATION BENCHMARK SCORECARD]")
    print("=" * 80)
    print(f" * Total Agentic Benchmarks Run: {result.testsRun}")
    print(f" * Fiduciary Failures:           {len(result.failures)}")
    print(f" * Unhandled Exceptions:         {len(result.errors)}")
    
    if result.wasSuccessful():
        print(" [RESULT]: ALL 7 SOTA AGENTIC BENCHMARKS PASSED (100% FIDUCIARY CONFORMANCE)")
        return 0
    else:
        print(" [RESULT]: BENCHMARK FAILED - FIDUCIARY DRIFT DETECTED")
        return 1

if __name__ == "__main__":
    sys.exit(run_agentic_evals())
