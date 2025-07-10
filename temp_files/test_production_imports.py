#!/usr/bin/env python3
"""
Test production import patterns to verify SCRUM-87 fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_production_imports():
    """Test the exact import patterns used in production code."""
    print("Testing production import patterns...")
    
    try:
        # Test the exact import from src.api.endpoints.py
        from src.services.warren import enhanced_warren_service
        print("+ Production import successful: enhanced_warren_service")
        print(f"  Type: {type(enhanced_warren_service).__name__}")
        
        # Test that we can call the main method
        print("+ Testing enhanced_warren_service interface...")
        
        # Check it has the expected method (without calling it)
        if hasattr(enhanced_warren_service, 'generate_content_with_enhanced_context'):
            print("+ Main method available: generate_content_with_enhanced_context")
        else:
            print("- Main method NOT available")
            
        # Test the orchestrator imports
        from src.services.warren import warren_orchestrator, ContentGenerationOrchestrator
        print("+ Orchestrator imports successful")
        
        # Verify they're the same instance
        if warren_orchestrator is enhanced_warren_service:
            print("+ enhanced_warren_service and warren_orchestrator are same instance")
        else:
            print("- enhanced_warren_service and warren_orchestrator are different instances")
            
        print("SUCCESS: All production imports working correctly!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_production_imports()
    if not success:
        sys.exit(1)
