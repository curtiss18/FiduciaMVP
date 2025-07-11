"""
Unit tests for budget models.

Tests for BudgetAllocation and BudgetConfig classes.
Requirement: 95%+ coverage for all models.
"""

import pytest
from src.services.context_assembly_service.models.budget_models import (
    BudgetAllocation, 
    BudgetConfig
)
from src.services.context_assembly_service.models.context_models import (
    RequestType,
    ContextType
)


class TestBudgetAllocation:
    """Test BudgetAllocation dataclass."""
    
    def create_valid_allocation(self, **overrides):
        """Helper to create a valid BudgetAllocation."""
        defaults = {
            "context_type": ContextType.COMPLIANCE_SOURCES,
            "allocated_tokens": 1000,
            "used_tokens": 0
        }
        defaults.update(overrides)
        return BudgetAllocation(**defaults)
    
    def test_valid_allocation_creation(self):
        """Test creating a valid BudgetAllocation."""
        allocation = self.create_valid_allocation()
        
        assert allocation.context_type == ContextType.COMPLIANCE_SOURCES
        assert allocation.allocated_tokens == 1000
        assert allocation.used_tokens == 0
    
    def test_negative_allocated_tokens_validation(self):
        """Test that negative allocated_tokens raises ValueError."""
        with pytest.raises(ValueError, match="allocated_tokens cannot be negative"):
            self.create_valid_allocation(allocated_tokens=-100)
    
    def test_negative_used_tokens_validation(self):
        """Test that negative used_tokens raises ValueError."""
        with pytest.raises(ValueError, match="used_tokens cannot be negative"):
            self.create_valid_allocation(used_tokens=-50)
    
    def test_used_exceeds_allocated_validation(self):
        """Test that used_tokens exceeding allocated_tokens raises ValueError."""
        with pytest.raises(ValueError, match="used_tokens cannot exceed allocated_tokens"):
            self.create_valid_allocation(allocated_tokens=100, used_tokens=150)
    
    def test_remaining_tokens_calculation(self):
        """Test remaining_tokens property."""
        allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=300)
        assert allocation.remaining_tokens == 700
        
        # Test when fully used
        full_allocation = self.create_valid_allocation(allocated_tokens=500, used_tokens=500)
        assert full_allocation.remaining_tokens == 0
    
    def test_utilization_rate_calculation(self):
        """Test utilization_rate property."""
        # 30% utilization
        allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=300)
        assert allocation.utilization_rate == 0.3
        
        # 100% utilization
        full_allocation = self.create_valid_allocation(allocated_tokens=500, used_tokens=500)
        assert full_allocation.utilization_rate == 1.0
        
        # 0% utilization
        empty_allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=0)
        assert empty_allocation.utilization_rate == 0.0
        
        # Edge case: zero allocated tokens
        zero_allocation = self.create_valid_allocation(allocated_tokens=0, used_tokens=0)
        assert zero_allocation.utilization_rate == 0.0
    
    def test_can_allocate(self):
        """Test can_allocate method."""
        allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=300)
        
        # Can allocate within remaining
        assert allocation.can_allocate(500) is True
        assert allocation.can_allocate(700) is True  # Exactly remaining
        
        # Cannot allocate more than remaining
        assert allocation.can_allocate(701) is False
        assert allocation.can_allocate(1000) is False
        
        # Can allocate zero
        assert allocation.can_allocate(0) is True
    
    def test_allocate_tokens_success(self):
        """Test successful token allocation."""
        allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=300)
        
        # Successful allocation
        result = allocation.allocate_tokens(200)
        assert result is True
        assert allocation.used_tokens == 500
        assert allocation.remaining_tokens == 500
        
        # Allocate remaining tokens
        result2 = allocation.allocate_tokens(500)
        assert result2 is True
        assert allocation.used_tokens == 1000
        assert allocation.remaining_tokens == 0
    
    def test_allocate_tokens_failure(self):
        """Test failed token allocation."""
        allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=800)
        
        # Cannot allocate more than remaining
        result = allocation.allocate_tokens(300)
        assert result is False
        assert allocation.used_tokens == 800  # Unchanged
        assert allocation.remaining_tokens == 200  # Unchanged
    
    def test_allocate_zero_tokens(self):
        """Test allocating zero tokens."""
        allocation = self.create_valid_allocation(allocated_tokens=1000, used_tokens=300)
        
        result = allocation.allocate_tokens(0)
        assert result is True
        assert allocation.used_tokens == 300  # Unchanged

class TestBudgetConfig:
    """Test BudgetConfig dataclass."""
    
    def create_valid_config(self, **overrides):
        """Helper to create a valid BudgetConfig."""
        defaults = {
            "request_type": RequestType.CREATION,
            "context_budgets": {
                ContextType.SYSTEM_PROMPT: 5000,
                ContextType.COMPLIANCE_SOURCES: 25000,
                ContextType.USER_INPUT: 2000
            },
            "buffer_tokens": 50000,
            "max_total_tokens": 200000
        }
        defaults.update(overrides)
        return BudgetConfig(**defaults)
    
    def test_valid_config_creation(self):
        """Test creating a valid BudgetConfig."""
        config = self.create_valid_config()
        
        assert config.request_type == RequestType.CREATION
        assert config.buffer_tokens == 50000
        assert config.max_total_tokens == 200000
        assert len(config.context_budgets) == 3
    
    def test_negative_buffer_tokens_validation(self):
        """Test that negative buffer_tokens raises ValueError."""
        with pytest.raises(ValueError, match="buffer_tokens cannot be negative"):
            self.create_valid_config(buffer_tokens=-1000)
    
    def test_invalid_max_total_tokens_validation(self):
        """Test that invalid max_total_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_total_tokens must be positive"):
            self.create_valid_config(max_total_tokens=0)
        
        with pytest.raises(ValueError, match="max_total_tokens must be positive"):
            self.create_valid_config(max_total_tokens=-1000)
    
    def test_excessive_allocation_validation(self):
        """Test that excessive total allocation raises ValueError."""
        excessive_budgets = {
            ContextType.SYSTEM_PROMPT: 100000,
            ContextType.COMPLIANCE_SOURCES: 100000,
            ContextType.USER_INPUT: 50000
        }
        
        with pytest.raises(ValueError, match="Total allocated tokens .* exceeds max_total_tokens"):
            self.create_valid_config(
                context_budgets=excessive_budgets,
                buffer_tokens=50000,
                max_total_tokens=200000
            )
    
    def test_total_allocated_tokens_calculation(self):
        """Test total_allocated_tokens property."""
        config = self.create_valid_config()
        expected = 5000 + 25000 + 2000  # 32000
        assert config.total_allocated_tokens == expected
    
    def test_available_tokens_calculation(self):
        """Test available_tokens property."""
        config = self.create_valid_config(max_total_tokens=200000, buffer_tokens=50000)
        assert config.available_tokens == 150000
    
    def test_get_allocation_for_context(self):
        """Test get_allocation_for_context method."""
        config = self.create_valid_config()
        
        # Existing context type
        assert config.get_allocation_for_context(ContextType.SYSTEM_PROMPT) == 5000
        assert config.get_allocation_for_context(ContextType.COMPLIANCE_SOURCES) == 25000
        
        # Non-existing context type
        assert config.get_allocation_for_context(ContextType.DOCUMENT_SUMMARIES) == 0
    
    def test_create_allocations(self):
        """Test create_allocations method."""
        config = self.create_valid_config()
        allocations = config.create_allocations()
        
        assert len(allocations) == 3
        assert isinstance(allocations[ContextType.SYSTEM_PROMPT], BudgetAllocation)
        assert allocations[ContextType.SYSTEM_PROMPT].allocated_tokens == 5000
        assert allocations[ContextType.SYSTEM_PROMPT].used_tokens == 0
        
        assert allocations[ContextType.COMPLIANCE_SOURCES].allocated_tokens == 25000
        assert allocations[ContextType.USER_INPUT].allocated_tokens == 2000
    
    def test_get_default_config_creation(self):
        """Test get_default_config class method for CREATION."""
        config = BudgetConfig.get_default_config(RequestType.CREATION)
        
        assert config.request_type == RequestType.CREATION
        assert config.buffer_tokens == 48000
        assert config.context_budgets[ContextType.SYSTEM_PROMPT] == 5000
        assert config.context_budgets[ContextType.CONVERSATION_HISTORY] == 40000
        assert config.context_budgets[ContextType.DOCUMENT_SUMMARIES] == 30000
        assert config.context_budgets[ContextType.COMPLIANCE_SOURCES] == 25000
        assert config.context_budgets[ContextType.VECTOR_SEARCH_RESULTS] == 20000
        assert config.context_budgets[ContextType.YOUTUBE_CONTEXT] == 30000
        assert config.context_budgets[ContextType.USER_INPUT] == 2000
    
    def test_get_default_config_refinement(self):
        """Test get_default_config class method for REFINEMENT."""
        config = BudgetConfig.get_default_config(RequestType.REFINEMENT)
        
        assert config.request_type == RequestType.REFINEMENT
        assert config.buffer_tokens == 98000
        assert config.context_budgets[ContextType.SYSTEM_PROMPT] == 5000
        assert config.context_budgets[ContextType.CURRENT_CONTENT] == 15000
        assert config.context_budgets[ContextType.CONVERSATION_HISTORY] == 25000
        assert config.context_budgets[ContextType.DOCUMENT_SUMMARIES] == 20000
        assert config.context_budgets[ContextType.COMPLIANCE_SOURCES] == 20000
        assert config.context_budgets[ContextType.VECTOR_SEARCH_RESULTS] == 15000
        assert config.context_budgets[ContextType.USER_INPUT] == 2000
    
    def test_get_default_config_analysis(self):
        """Test get_default_config class method for ANALYSIS."""
        config = BudgetConfig.get_default_config(RequestType.ANALYSIS)
        
        assert config.request_type == RequestType.ANALYSIS
        assert config.buffer_tokens == 58000
        assert config.context_budgets[ContextType.SYSTEM_PROMPT] == 5000
        assert config.context_budgets[ContextType.DOCUMENT_SUMMARIES] == 50000
        assert config.context_budgets[ContextType.CONVERSATION_HISTORY] == 30000
        assert config.context_budgets[ContextType.COMPLIANCE_SOURCES] == 30000
        assert config.context_budgets[ContextType.VECTOR_SEARCH_RESULTS] == 25000
        assert config.context_budgets[ContextType.USER_INPUT] == 2000
    
    def test_get_default_config_conversation(self):
        """Test get_default_config class method for CONVERSATION."""
        config = BudgetConfig.get_default_config(RequestType.CONVERSATION)
        
        assert config.request_type == RequestType.CONVERSATION
        assert config.buffer_tokens == 108000
        assert config.context_budgets[ContextType.SYSTEM_PROMPT] == 5000
        assert config.context_budgets[ContextType.CONVERSATION_HISTORY] == 60000
        assert config.context_budgets[ContextType.COMPLIANCE_SOURCES] == 15000
        assert config.context_budgets[ContextType.VECTOR_SEARCH_RESULTS] == 10000
        assert config.context_budgets[ContextType.USER_INPUT] == 2000
    
    def test_default_configs_are_valid(self):
        """Test that all default configurations are valid (don't exceed limits)."""
        for request_type in RequestType:
            config = BudgetConfig.get_default_config(request_type)
            
            # Should not raise any validation errors
            total_allocated = config.total_allocated_tokens + config.buffer_tokens
            assert total_allocated <= config.max_total_tokens
            
            # Verify all budgets are positive
            for context_type, budget in config.context_budgets.items():
                assert budget > 0, f"Budget for {context_type} should be positive"
    
    def test_boundary_conditions(self):
        """Test boundary conditions for budget configuration."""
        # Minimum valid configuration
        min_config = BudgetConfig(
            request_type=RequestType.CREATION,
            context_budgets={ContextType.USER_INPUT: 1},
            buffer_tokens=0,
            max_total_tokens=1
        )
        assert min_config.total_allocated_tokens == 1
        assert min_config.available_tokens == 1
        
        # Maximum valid configuration
        max_budget = {ContextType.USER_INPUT: 199999}
        max_config = BudgetConfig(
            request_type=RequestType.CREATION,
            context_budgets=max_budget,
            buffer_tokens=1,
            max_total_tokens=200000
        )
        assert max_config.total_allocated_tokens == 199999
        assert max_config.available_tokens == 199999
