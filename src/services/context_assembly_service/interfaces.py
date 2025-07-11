"""Abstract Interfaces for Context Assembler Services"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from .models import (
    RequestType, 
    ContextType, 
    ContextElement, 
    BudgetConfig, 
    BudgetAllocation,
    QualityMetrics
)


class ContextGatheringStrategy(ABC):
    
    @abstractmethod
    async def gather_context(self, session_id: str, context_data: Optional[Dict[str, Any]] = None) -> List[ContextElement]:
        pass
    
    @abstractmethod
    def get_supported_context_types(self) -> List[ContextType]:
        pass


class BudgetAllocationStrategy(ABC):
    
    @abstractmethod
    async def allocate_budget(self, request_type: RequestType, user_input: str, available_tokens: int) -> Dict[ContextType, BudgetAllocation]:
        pass
    
    @abstractmethod
    def get_budget_config(self, request_type: RequestType) -> BudgetConfig:
        pass


class CompressionStrategy(ABC):
    
    @abstractmethod
    async def compress_content(self, content: str, target_tokens: int, context_type: ContextType) -> str:
        pass
    
    @abstractmethod
    def estimate_compression_ratio(self, content: str, context_type: ContextType) -> float:
        pass


class ContextAssemblyStrategy(ABC):
    
    @abstractmethod
    async def assemble_context(self, elements: List[ContextElement], budget_allocations: Dict[ContextType, BudgetAllocation]) -> str:
        pass
    
    @abstractmethod
    def assess_quality(self, assembled_context: str, elements: List[ContextElement]) -> QualityMetrics:
        pass


class RequestAnalysisStrategy(ABC):
    
    @abstractmethod
    def analyze_request_type(self, user_input: str, current_content: Optional[str] = None) -> RequestType:
        pass
    
    @abstractmethod
    def extract_requirements(self, user_input: str) -> Dict[str, Any]:
        pass
