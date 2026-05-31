#!/usr/bin/env python
"""
Test execution script for the eBay App

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --coverage         # Run tests with coverage report
    python run_tests.py --api              # Run only API tests
    python run_tests.py --database         # Run only database tests
    python run_tests.py --frontend         # Run only frontend tests
    python run_tests.py --listing-generator # Run only listing generator tests
    python run_tests.py --price-generator  # Run only price generator tests
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"\nFAILED: {description}")
        return False
    else:
        print(f"\nPASSED: {description}")
        return True


def main():
    """Main test execution function"""
    # Use virtual environment python to run pytest
    python_exe = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
    base_cmd = [python_exe, "-m", "pytest", "tests/"]
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    if "--unit" in args:
        base_cmd.extend(["-m", "unit"])
        print("Running UNIT TESTS only...")
    elif "--integration" in args:
        base_cmd.extend(["-m", "integration"])
        print("Running INTEGRATION TESTS only...")
    elif "--api" in args:
        base_cmd.extend(["-m", "api"])
        print("Running API TESTS only...")
    elif "--database" in args:
        base_cmd.extend(["-m", "database"])
        print("Running DATABASE TESTS only...")
    elif "--frontend" in args:
        base_cmd.extend(["-m", "frontend"])
        print("Running FRONTEND TESTS only...")
    elif "--listing-generator" in args:
        base_cmd.extend(["-k", "listing"])
        print("Running LISTING GENERATOR TESTS only...")
    elif "--price-generator" in args:
        base_cmd.extend(["-k", "price"])
        print("Running PRICE GENERATOR TESTS only...")
    elif "--coverage" in args:
        base_cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
        print("Running tests with COVERAGE REPORT...")
    else:
        print("Running ALL TESTS...")
    
    # Add verbose output
    base_cmd.extend(["-v"])
    
    # Run the tests
    success = run_command(base_cmd, "Test Suite")
    
    if not success:
        sys.exit(1)
    
    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
