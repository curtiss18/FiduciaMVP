#!/usr/bin/env python3
"""
Test script to understand current Warren import behavior before fixing __init__.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_warren_imports():
    """Test different Warren import patterns to understand current behavior."""
    print("Testing current Warren import behavior...")
    
    try:
        # Test 1: Import from warren package (what production code uses)
        from src.services.warren import enhanced_warren_service
        print("+ Successfully imported enhanced_warren_service from warren package")
        print(f"  Type: {type(enhanced_warren_service).__name__}")
        
        # Test 2: Check what's in __all__
        import src.services.warren as warren_pkg
        print(f"+ Warren package __all__: {warren_pkg.__all__}")
        
        # Test 3: Try to import individual services from package
        try:
            from src.services.warren import ContextRetrievalService
            print("+ Successfully imported ContextRetrievalService from warren package")
        except ImportError as e:
            print(f"- Failed to import ContextRetrievalService: {e}")
        
        # Test 4: Direct imports (what tests use)
        from src.services.warren.context_retrieval_service import ContextRetrievalService as DirectCRS
        print("+ Successfully imported ContextRetrievalService directly")
        
        # Test 5: Check if warren_orchestrator is available
        try:
            from src.services.warren import warren_orchestrator
            print("+ Successfully imported warren_orchestrator from warren package")
            print(f"  Type: {type(warren_orchestrator).__name__}")
        except ImportError as e:
            print(f"- Failed to import warren_orchestrator: {e}")
            
    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_warren_imports()
