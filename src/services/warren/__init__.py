"""
Warren Refactored Services

Main entry point for Warren content generation services.

Usage:
    from src.services.warren import enhanced_warren_service
"""

# Import main orchestrator for easy access
from .content_generation_orchestrator import ContentGenerationOrchestrator

# Create service instance for drop-in replacement
warren_orchestrator = ContentGenerationOrchestrator()

# For backward compatibility, alias to match existing enhanced_warren_service pattern
enhanced_warren_service = warren_orchestrator

__all__ = [
    'ContentGenerationOrchestrator',
    'warren_orchestrator', 
    'enhanced_warren_service'  # Drop-in replacement
]
