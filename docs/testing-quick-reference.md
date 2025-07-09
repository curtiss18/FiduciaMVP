# Quick Testing Reference
## FiduciaMVP Testing Commands and Setup

**For Developers**: Quick reference for running tests and setting up testing environment.

---

## 🚀 Quick Start

### 1. Environment Setup
```powershell
# Navigate to project
cd C:\Users\curti\OneDrive\Desktop\WebDev\FiduciaMVP

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start test infrastructure
docker-compose --profile testing up -d postgres_test redis_test

# Verify containers are running
docker ps
```

### 2. Run Integration Tests
```powershell
# Run all Warren integration tests
python -m pytest tests/integration/warren/ -v

# Run with output visible
python -m pytest tests/integration/warren/ -v -s

# Run specific test
python -m pytest tests/integration/warren/test_warren_basic_integration.py::TestWarrenBasicIntegration::test_warren_end_to_end_basic_workflow -v
```

### 3. Performance Testing
```powershell
# Run performance tests only
python -m pytest -m performance -v -s

# Run all integration tests (includes performance)
python -m pytest -m integration -v -s
```

---

## 📋 Test Categories

| Test Type | Command | Purpose |
|-----------|---------|---------|
| **All Integration** | `pytest tests/integration/ -v` | Complete workflow testing |
| **Warren Basic** | `pytest tests/integration/warren/test_warren_basic_integration.py -v` | Core Warren functionality |
| **Performance** | `pytest -m performance -v` | Benchmark validation |
| **Unit Tests** | `pytest tests/unit/ -v` | Component testing |

---

## 🔧 Test Infrastructure

### Containers
- **Test Database**: `postgres_test` on port 5433
- **Test Redis**: `redis_test` on port 6380
- **Status Check**: `docker ps` to verify running

### Configuration
- **Test Config**: `.env.test` (API keys copied from main `.env`)
- **Database**: `fiducia_mvp_test` (isolated from dev)
- **Fixtures**: `tests/fixtures/` (test data and utilities)

---

## ✅ Current Test Status

**Last Updated**: July 8, 2025

### Integration Test Results
```
✅ test_warren_end_to_end_basic_workflow - PASSED
✅ test_warren_error_handling - PASSED  
✅ test_warren_different_content_types - PASSED
✅ test_warren_performance_basic - PASSED

Performance: 0.00 seconds (EXCELLENT)
Content Types: linkedin_post, newsletter, blog_post, email_template
Error Handling: Proper validation and recovery
```

### Performance Benchmarks
- **Response Time**: < 0.01s (Target: < 2s) ✅
- **Content Generation**: All types working ✅
- **Error Rate**: 0% (Target: < 0.1%) ✅
- **Database Integration**: Real PostgreSQL ✅

---

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```powershell
# Restart test containers
docker-compose --profile testing restart postgres_test redis_test

# Check container status
docker ps
```

**Import Errors**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Verify you're in project root
pwd  # Should show FiduciaMVP directory
```

**Async Test Issues**
- Ensure `@pytest.mark.asyncio` decorator is present
- Check pytest-asyncio is installed: `pip list | findstr asyncio`

### Debug Commands
```powershell
# Verbose output with full details
python -m pytest tests/integration/ -v --tb=long

# Stop on first failure
python -m pytest tests/integration/ -x

# Run only failed tests
python -m pytest tests/integration/ --lf
```

---

## 📝 Writing New Tests

### Basic Integration Test Template
```python
import pytest
from src.services.warren import ContentGenerationOrchestrator

class TestNewFeature:
    @pytest.fixture
    def warren_orchestrator(self):
        return ContentGenerationOrchestrator()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_new_feature(self, warren_orchestrator):
        # Arrange
        request = {"user_request": "test", "content_type": "linkedin_post"}
        
        # Act
        result = await warren_orchestrator.generate_content_with_enhanced_context(**request)
        
        # Assert
        assert result["status"] == "success"
        assert "content" in result
```

### Key Points
- Always use `@pytest.mark.asyncio` for async tests
- Use `@pytest.mark.integration` for integration tests
- Test real Warren functionality, mock only external APIs
- Include both success and error scenarios

---

**For complete documentation, see**: `docs/testing-infrastructure.md`
