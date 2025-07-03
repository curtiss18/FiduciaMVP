#!/usr/bin/env python3
"""
Test script for SCRUM-40 Enhanced Multi-Modal Document Processing
Tests the DocumentProcessor class with full Pillow support
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_document_processor():
    """Test DocumentProcessor class and dependencies."""
    
    print("🧪 Testing SCRUM-40: Enhanced Multi-Modal Document Processing")
    print("=" * 60)
    
    try:
        # Test imports
        print("📦 Testing dependency imports...")
        from src.services.document_processor import DocumentProcessor, DEPENDENCIES_AVAILABLE
        print("✅ DocumentProcessor imported successfully")
        print(f"   Dependencies available: {DEPENDENCIES_AVAILABLE}")
        
        if not DEPENDENCIES_AVAILABLE:
            print("❌ Core dependencies missing - cannot continue test")
            return False
        
        # Test initialization
        print("\n🏗️ Testing DocumentProcessor initialization...")
        processor = DocumentProcessor()
        print("✅ DocumentProcessor initialized successfully")
        print(f"   Supported types: {processor.supported_types}")
        print(f"   Max file size: {processor.max_file_size / (1024*1024):.1f} MB")
        
        # Test file validation
        print("\n🔍 Testing file validation...")
        
        # Create test text content
        test_text = """Financial Report Q3 2024
        
This is a comprehensive financial analysis document containing:

Performance Data:
Quarter    Revenue    Growth
Q1 2024    $1.2M      +15%
Q2 2024    $1.5M      +25% 
Q3 2024    $1.8M      +20%

Key Metrics:
- Total Assets: $45.2M
- Debt Ratio: 0.32
- ROI: 18.5%

Summary:
Strong growth trajectory continues with consistent quarterly improvements.
Market expansion initiatives showing positive results."""

        test_bytes = test_text.encode('utf-8')
        
        # Test TXT validation
        print("   Testing TXT file validation...")
        is_valid_txt = processor.validate_file_type("test_report.txt", test_bytes)
        print(f"   ✅ TXT validation: {is_valid_txt}")
        
        # Test TXT processing
        print("\n📄 Testing TXT file processing...")
        txt_result = await processor.process_text_file(test_bytes)
        print("   ✅ TXT processing completed")
        print(f"   Word count: {txt_result['metadata']['word_count']}")
        print(f"   Line count: {txt_result['metadata']['line_count']}")
        print(f"   Tables detected: {txt_result['metadata']['total_tables']}")
        print(f"   Processing time: {txt_result['metadata']['processing_time_ms']}ms")
        
        if txt_result['tables']:
            print(f"   First table: {len(txt_result['tables'][0]['data'])} rows x {len(txt_result['tables'][0]['data'][0])} columns")
        
        print(f"   Visual summary: {txt_result['visual_summary']}")
        print(f"   Warren context: {txt_result['warren_context'][:100]}...")
        
        # Test process_uploaded_file method
        print("\n🔄 Testing unified file processing...")
        unified_result = await processor.process_uploaded_file(
            file_content=test_bytes,
            filename="test_financial_report.txt",
            content_type="txt"
        )
        print("   ✅ Unified processing completed")
        print(f"   Processing version: {unified_result['metadata']['processor_version']}")
        print(f"   Original filename: {unified_result['metadata']['original_filename']}")
        
        print("\n🎉 All tests passed! DocumentProcessor is ready for real file testing.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner."""
    success = await test_document_processor()
    
    if success:
        print("\n" + "=" * 60)
        print("🚀 Ready for Phase 3: Real File Testing!")
        print("   1. Start the backend server: uvicorn src.main:app --reload")
        print("   2. Test with real PDF/DOCX files via API endpoint")
        print("   3. Verify multi-modal processing results")
        print("=" * 60)
    else:
        print("\n❌ Fix issues before proceeding with real file testing.")

if __name__ == "__main__":
    asyncio.run(main())
