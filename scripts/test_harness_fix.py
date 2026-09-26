"""Test script to validate F1 harness fixes."""
import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.harness.runner import TestRunner
from backend.harness.validate import RepositoryValidator


def test_pytest_environment():
    """Test 1: Verify pytest environment detection."""
    print("\n" + "="*60)
    print("TEST 1: Pytest Environment Verification")
    print("="*60)
    
    runner = TestRunner(project_root)
    env_check = runner.verify_pytest_environment()
    
    print(f"Verified: {env_check['verified']}")
    print(f"JSON Report Available: {env_check['json_report']}")
    print(f"Pytest Version: {env_check.get('pytest_version', 'N/A')}")
    print(f"Python Executable: {env_check.get('python_executable', 'N/A')}")
    
    if env_check.get('warnings'):
        print(f"Warnings: {env_check['warnings']}")
    
    assert env_check['verified'], "Pytest environment should be verified"
    assert env_check['json_report'], "pytest-json-report should be available"
    print("✓ Pytest environment is properly configured")


def test_repository_validation_flakeguard():
    """Test 2: Validate FlakeGuard repository itself."""
    print("\n" + "="*60)
    print("TEST 2: FlakeGuard Repository Validation")
    print("="*60)
    
    validator = RepositoryValidator()
    validation = validator.detect_pytest_compatibility(project_root)
    
    print(f"Compatible: {validation['compatible']}")
    print(f"Confidence: {validation['confidence']:.1%}")
    print(f"Indicators: {len(validation['indicators'])}")
    for indicator in validation['indicators']:
        print(f"  - {indicator}")
    
    if validation['test_files']:
        print(f"Test Files Found: {len(validation['test_files'])}")
        for test_file in validation['test_files'][:5]:
            print(f"  - {test_file}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    assert validation['compatible'], "FlakeGuard should be pytest-compatible"
    print("✓ FlakeGuard repository is pytest-compatible")


def test_repository_validation_sample():
    """Test 3: Validate sample-repo."""
    print("\n" + "="*60)
    print("TEST 3: Sample Repository Validation")
    print("="*60)
    
    sample_repo = project_root / "sample-repo"
    
    validator = RepositoryValidator()
    validation = validator.detect_pytest_compatibility(sample_repo)
    
    print(f"Compatible: {validation['compatible']}")
    print(f"Confidence: {validation['confidence']:.1%}")
    print(f"Indicators: {len(validation['indicators'])}")
    for indicator in validation['indicators']:
        print(f"  - {indicator}")
    
    if validation['test_files']:
        print(f"Test Files Found: {len(validation['test_files'])}")
        for test_file in validation['test_files'][:5]:
            print(f"  - {test_file}")
    
    assert validation['compatible'], "sample-repo should be pytest-compatible"
    print("✓ sample-repo is pytest-compatible")


def test_test_collection_flakeguard():
    """Test 4: Collect tests from FlakeGuard repository."""
    print("\n" + "="*60)
    print("TEST 4: FlakeGuard Test Collection")
    print("="*60)
    
    runner = TestRunner(project_root)
    
    try:
        test_ids = runner.collect_test_ids()
        print(f"Tests Collected: {len(test_ids)}")
        
        if test_ids:
            print("Sample tests:")
            for test_id in test_ids[:10]:
                print(f"  - {test_id}")
        
        assert len(test_ids) > 0, "Should collect at least one test from FlakeGuard"
        print(f"✓ Successfully collected {len(test_ids)} tests from FlakeGuard")
        
    except Exception as e:
        print(f"✗ Test collection failed: {e}")
        raise


def test_test_collection_sample():
    """Test 5: Collect tests from sample-repo."""
    print("\n" + "="*60)
    print("TEST 5: Sample Repository Test Collection")
    print("="*60)
    
    sample_repo = project_root / "sample-repo"
    runner = TestRunner(sample_repo)
    
    try:
        test_ids = runner.collect_test_ids()
        print(f"Tests Collected: {len(test_ids)}")
        
        if test_ids:
            print("Sample tests:")
            for test_id in test_ids[:10]:
                print(f"  - {test_id}")
        
        assert len(test_ids) > 0, "Should collect at least one test from sample-repo"
        print(f"✓ Successfully collected {len(test_ids)} tests from sample-repo")
        
    except Exception as e:
        print(f"✗ Test collection failed: {e}")
        raise


def test_single_run_sample():
    """Test 6: Execute a single test run on sample-repo."""
    print("\n" + "="*60)
    print("TEST 6: Sample Repository Single Test Run")
    print("="*60)
    
    sample_repo = project_root / "sample-repo"
    runner = TestRunner(sample_repo)
    
    try:
        print("Running tests (this may take a moment)...")
        test_run = runner.run_tests(run_index=0, ordering_seed=42)
        
        print(f"Run ID: {test_run.run_id}")
        print(f"Total Tests: {test_run.total_tests}")
        print(f"Passed: {test_run.passed}")
        print(f"Failed: {test_run.failed}")
        print(f"Duration: {test_run.duration_seconds:.2f}s")
        print(f"Return Code: {test_run.returncode}")
        
        if test_run.executions:
            print("\nTest Executions:")
            for exec in test_run.executions[:5]:
                print(f"  - {exec.test_name}: {exec.status.value}")
        
        assert test_run.total_tests > 0, "Should execute at least one test"
        print(f"✓ Successfully executed {test_run.total_tests} tests")
        
    except Exception as e:
        print(f"✗ Test run failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Run all harness validation tests."""
    print("\n" + "#"*60)
    print("# FlakeGuard F1 Harness Validation Tests")
    print("#"*60)
    
    tests = [
        ("Pytest Environment Verification", test_pytest_environment),
        ("FlakeGuard Repository Validation", test_repository_validation_flakeguard),
        ("Sample Repository Validation", test_repository_validation_sample),
        ("FlakeGuard Test Collection", test_test_collection_flakeguard),
        ("Sample Repository Test Collection", test_test_collection_sample),
        ("Sample Repository Single Run", test_single_run_sample),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            failed += 1
    
    print("\n" + "#"*60)
    print(f"# Test Results: {passed} passed, {failed} failed")
    print("#"*60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
