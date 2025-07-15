"""
Tests for Content Generation Strategies Package

Test Coverage:
- ContentGenerationStrategy interface and implementation contract
- BaseGenerationStrategy common functionality extraction
- StrategyFactory selection logic and fallback chains  
- Individual strategy implementations (Advanced, Standard, Legacy)
- Strategy comparative behavior and consistency
- Error handling and edge cases

Run all strategy tests:
    pytest tests/services/warren/strategies/ -v

Run specific test files:
    pytest tests/services/warren/strategies/test_base_generation_strategy.py -v
    pytest tests/services/warren/strategies/test_strategy_factory.py -v
    pytest tests/services/warren/strategies/test_individual_strategies.py -v
"""

