#!/usr/bin/env python3
"""
Test script to verify play_sound_with_volume signature is correct.

This script:
1. Checks function definitions in sound.py
2. Checks all function calls in uwh.py
3. Tests the function with various argument counts
4. Reports any mismatches or errors

Usage:
    python3 test_sound_signature.py
"""

import ast
import inspect
import sys

def test_function_definitions():
    """Test that function definitions have the correct signature."""
    print("="*70)
    print("TEST 1: Function Definitions")
    print("="*70)
    
    # Import the module
    try:
        import sound
    except ImportError as e:
        print(f"✗ FAILED: Could not import sound module: {e}")
        return False
    
    # Check play_sound_with_volume
    sig = inspect.signature(sound.play_sound_with_volume)
    params = sig.parameters
    
    print("\nplay_sound_with_volume signature:")
    print(f"  Parameters: {list(params.keys())}")
    print(f"  Total: {len(params)}")
    print(f"  Required: {sum(1 for p in params.values() if p.default == inspect.Parameter.empty)}")
    print(f"  Optional: {sum(1 for p in params.values() if p.default != inspect.Parameter.empty)}")
    
    # Verify expected parameters
    expected_params = ['filename', 'sound_type', 'enable_sound', 'pips_volume', 
                       'siren_volume', 'air_volume', 'water_volume', 'siren_duration']
    actual_params = list(params.keys())
    
    if expected_params != actual_params:
        print(f"\n✗ FAILED: Parameter mismatch")
        print(f"  Expected: {expected_params}")
        print(f"  Actual: {actual_params}")
        return False
    
    # Check default value
    if params['siren_duration'].default != 1.5:
        print(f"\n✗ FAILED: Wrong default for siren_duration: {params['siren_duration'].default}")
        return False
    
    # Check total parameter count
    if len(params) != 8:
        print(f"\n✗ FAILED: Wrong parameter count: {len(params)}")
        return False
    
    print("\n✓ PASSED: Function definition is correct")
    return True


def test_function_calls():
    """Test that all calls to play_sound_with_volume have correct arguments."""
    print("\n" + "="*70)
    print("TEST 2: Function Calls")
    print("="*70)
    
    # Parse uwh.py
    try:
        with open('uwh.py', 'r') as f:
            uwh_tree = ast.parse(f.read(), filename='uwh.py')
    except Exception as e:
        print(f"✗ FAILED: Could not parse uwh.py: {e}")
        return False
    
    call_count = 0
    errors = []
    
    for node in ast.walk(uwh_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'play_sound_with_volume':
                call_count += 1
                num_args = len(node.args)
                num_keywords = len(node.keywords)
                total = num_args + num_keywords
                
                print(f"\nCall #{call_count} (line {node.lineno}):")
                print(f"  Positional: {num_args}, Keyword: {num_keywords}, Total: {total}")
                
                # Valid calls: 7 positional (using default), or 8 positional, or mix totaling 7-8
                if total < 7 or total > 8:
                    error_msg = f"  ✗ WRONG: Expected 7-8 arguments, got {total}"
                    print(error_msg)
                    errors.append(f"Line {node.lineno}: {error_msg}")
                elif num_args == 8 and num_keywords == 0:
                    print(f"  ✓ CORRECT: 8 positional arguments")
                elif num_args == 7 and num_keywords == 0:
                    print(f"  ✓ CORRECT: 7 positional (using default)")
                else:
                    print(f"  ✓ CORRECT: {num_args} positional + {num_keywords} keyword")
    
    print(f"\nTotal calls found: {call_count}")
    
    if errors:
        print(f"\n✗ FAILED: {len(errors)} call(s) have wrong argument count:")
        for error in errors:
            print(f"  {error}")
        return False
    
    if call_count == 0:
        print("✗ FAILED: No calls to play_sound_with_volume found")
        return False
    
    print("✓ PASSED: All function calls are correct")
    return True


def test_call_patterns():
    """Test that the function accepts valid argument patterns."""
    print("\n" + "="*70)
    print("TEST 3: Call Patterns")
    print("="*70)
    
    try:
        from sound import play_sound_with_volume
    except ImportError as e:
        print(f"✗ FAILED: Could not import: {e}")
        return False
    
    # Test 1: 8 arguments
    print("\nTest 3a: Call with 8 arguments")
    try:
        play_sound_with_volume("test.mp3", "pips", False, 50, 50, 50, 50, 1.5)
        print("  ✓ PASSED: Accepts 8 arguments")
    except TypeError as e:
        print(f"  ✗ FAILED: {e}")
        return False
    
    # Test 2: 7 arguments (using default)
    print("\nTest 3b: Call with 7 arguments (default siren_duration)")
    try:
        play_sound_with_volume("test.mp3", "pips", False, 50, 50, 50, 50)
        print("  ✓ PASSED: Accepts 7 arguments")
    except TypeError as e:
        print(f"  ✗ FAILED: {e}")
        return False
    
    # Test 3: 9 arguments (should fail)
    print("\nTest 3c: Call with 9 arguments (should reject)")
    try:
        play_sound_with_volume("test.mp3", "pips", False, 50, 50, 50, 50, 1.5, "extra")
        print("  ✗ FAILED: Should have rejected 9 arguments")
        return False
    except TypeError as e:
        print(f"  ✓ PASSED: Correctly rejected 9 arguments")
    
    # Test 4: 6 arguments (should fail)
    print("\nTest 3d: Call with 6 arguments (should reject)")
    try:
        play_sound_with_volume("test.mp3", "pips", False, 50, 50, 50)
        print("  ✗ FAILED: Should have rejected 6 arguments")
        return False
    except TypeError as e:
        print(f"  ✓ PASSED: Correctly rejected 6 arguments")
    
    print("\n✓ PASSED: All call pattern tests passed")
    return True


def main():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("play_sound_with_volume Signature Test Suite")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Function Definitions", test_function_definitions()))
    results.append(("Function Calls", test_function_calls()))
    results.append(("Call Patterns", test_call_patterns()))
    
    # Report summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:30s} {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("\nThe play_sound_with_volume function signature is CORRECT.")
        print("All definitions and calls match the intended specification:")
        print("  def play_sound_with_volume(filename, sound_type, enable_sound,")
        print("                             pips_volume, siren_volume, air_volume,")
        print("                             water_volume, siren_duration=1.5)")
        return 0
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("\nPlease review the errors above and fix the signature mismatches.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
