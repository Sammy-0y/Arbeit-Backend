#!/usr/bin/env python3
"""
Test runner script for Phase 1 automated tests
"""
import subprocess
import sys

def run_tests():
    """Run all Phase 1 tests"""
    print("="*60)
    print("ARBEIT TALENT PORTAL - PHASE 1 AUTOMATED TESTS")
    print("="*60)
    print()
    
    # Run pytest with coverage
    result = subprocess.run([
        "pytest",
        "/app/tests/",
        "-v",
        "--tb=short",
        "--color=yes",
        "-W", "ignore::DeprecationWarning"
    ], cwd="/app")
    
    print()
    print("="*60)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())