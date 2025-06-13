#!/usr/bin/env python3
"""
Simple test runner for html_utils tests.

This script runs the HTML utilities tests and provides a summary of results.
Can be used in environments where pytest is not available.
"""

import sys
import unittest
from io import StringIO


def run_html_utils_tests():
    """Run the HTML utilities tests and return results."""
    
    # Import the test module
    try:
        from test_html_utils import TestHtmlUtilsSimple
    except ImportError as e:
        print(f"Error importing test module: {e}")
        return False
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHtmlUtilsSimple)
    
    # Run the tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    
    # Print the results
    output = stream.getvalue()
    print(output)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    # Print details of failures and errors
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Return True if all tests passed
    return len(result.failures) == 0 and len(result.errors) == 0


def main():
    """Main function to run tests."""
    print("HTML Utils Test Runner")
    print("="*60)
    print("Running tests for html_utils module...")
    print()
    
    try:
        success = run_html_utils_tests()
        
        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()