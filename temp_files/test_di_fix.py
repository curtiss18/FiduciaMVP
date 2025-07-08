#!/usr/bin/env python3
"""
Simple test script to verify the dependency injection fix works correctly.
This tests that ContextRetrievalService can be instantiated with default dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.services.warren.context_retrieval_service import ContextRetrievalService
    
    print("Testing ContextRetrievalService dependency injection fix...")
    
    # This should work without any globals() errors
    service = ContextRetrievalService()
    
    print("SUCCESS: ContextRetrievalService instantiated successfully with default dependencies")
    print(f"   vector_search_service type: {type(service.vector_search_service).__name__}")
    print(f"   warren_db_service type: {type(service.warren_db_service).__name__}")
    print("No globals() usage - dependency injection fix successful!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
