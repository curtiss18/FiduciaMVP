"""Test runner for SCRUM-110 optimization tests."""

import subprocess
import sys
import os

def run_tests():
    """Run all optimization tests and report results."""
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    sys.path.insert(0, project_root)
    
    test_files = [
        "test_text_token_manager.py",
        "test_basic_context_optimizer.py", 
        "test_regression_performance.py",
        "compression/test_compression_strategy_factory.py",
        "compression/test_structure_preserving_compressor.py",
        "compression/test_conversation_compressor.py",
        "compression/test_generic_compressor.py"
    ]
    
    base_path = "tests/services/context_assembler/unit/optimization"
    
    print("Running SCRUM-110 Optimization Tests")
    print("=" * 50)
    
    total_passed = 0
    total_failed = 0
    
    for test_file in test_files:
        test_path = os.path.join(base_path, test_file)
        print(f"\nRunning {test_file}...")
        
        try:
            # Run pytest on specific file
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_path, 
                "-v", 
                "--tb=short",
                "--maxfail=5"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"PASS {test_file} - PASSED")
                # Count passed tests from output
                passed_count = result.stdout.count(" PASSED")
                total_passed += passed_count
            else:
                print(f"FAIL {test_file} - FAILED") 
                print(f"Error output: {result.stderr}")
                failed_count = result.stdout.count(" FAILED")
                total_failed += failed_count
                
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT {test_file} - TIMEOUT")
            total_failed += 1
        except Exception as e:
            print(f"ERROR {test_file} - ERROR: {e}")
            total_failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results Summary:")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_failed}")
    print(f"   Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    
    if total_failed == 0:
        print("\nAll tests passed! SCRUM-110 ready for validation.")
    else:
        print(f"\n{total_failed} tests failed. Review and fix before completion.")
    
    return total_failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
