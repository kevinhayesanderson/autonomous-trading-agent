"""
Autonomous Test & Verification Suite (Self-Testing AI Agent Engine)
Enforces mathematical, architectural, and safety invariants before market analysis.
Run standalone:
    python scripts/test_system.py
"""

import os
import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.test_system import TestAIAgenticSystem

def run_self_verification():
    print("\n" + "=" * 80)
    print(" [AI AGENTIC SYSTEM SELF-VERIFICATION SUITE]")
    print(" Verifying system integrity, safety invariants, and tariffs before execution...")
    print("=" * 80)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIAgenticSystem)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("=" * 80)
        print(f" [ALL {result.testsRun} SYSTEM TESTS PASSED] System verified and ready for market operations.")
        print("=" * 80 + "\n")
        return True
    else:
        print("=" * 80)
        print(f" [CRITICAL FAIL] {len(result.failures)} test(s) failed, {len(result.errors)} error(s).")
        print(" Halting pipeline to protect capital from architectural failure.")
        print("=" * 80 + "\n")
        return False

if __name__ == "__main__":
    success = run_self_verification()
    sys.exit(0 if success else 1)
