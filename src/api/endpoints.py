from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from src.services.claude_service import claude_service
from src.services.knowledge_base_service import get_knowledge_service
from src.services.async_knowledge_service import async_kb_service
from src.services.warren_database_service import warren_db_service
from src.services.enhanced_warren_service import enhanced_warren_service
from src.services.embedding_service import embedding_service
from src.services.vector_search_service import vector_search_service
from src.services.content_vectorization_service import content_vectorization_service
from src.core.database import check_db_connection, create_tables, get_db

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FiduciaMVP"}


@router.get("/test-claude")
async def test_claude():
    """Test Claude API connection"""
    result = await claude_service.test_connection()
    return result


@router.get("/test-database")
async def test_database():
    """Test database connection"""
    result = await check_db_connection()
    return result


@router.get("/setup-database")
async def setup_database():
    """Create database tables"""
    try:
        await create_tables()
        return {"status": "success", "message": "Database tables created"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/generate")
async def generate_content(request: dict):
    """Generate content using Claude AI"""
    prompt = request.get("prompt", "")
    if not prompt:
        return {"error": "Prompt is required"}
    
    try:
        content = await claude_service.generate_content(prompt)
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}


@router.post("/warren/generate")
async def warren_generate_content(request: dict):
    """Generate compliant marketing content using Warren AI with knowledge base"""
    user_request = request.get("request", "")
    content_type = request.get("content_type", "general")  # linkedin, twitter, email, etc.
    
    if not user_request:
        return {"error": "Content request is required"}
    
    try:
        # Get knowledge base service
        kb_service = get_knowledge_service()
        
        # Search for relevant compliance content
        search_results = kb_service.search_content(content_type, limit=3)
        regulation_results = kb_service.search_content("regulation", limit=2)
        disclaimer_results = kb_service.search_content("disclaimer", limit=2)
        
        # Build context from knowledge base
        context_parts = ["Here is relevant compliance information to consider:"]
        
        # Add regulation info
        if regulation_results:
            context_parts.append("\n## REGULATORY REQUIREMENTS:")
            for result in regulation_results[:1]:  # Top regulation result
                context_parts.append(f"From {result['file']['title']}:")
                for line in result['matching_lines'][:2]:
                    context_parts.append(f"- {line['content']}")
        
        # Add platform-specific guidance
        if search_results:
            context_parts.append(f"\n## {content_type.upper()} GUIDELINES:")
            for result in search_results[:1]:  # Top platform result
                for line in result['matching_lines'][:3]:
                    context_parts.append(f"- {line['content']}")
        
        # Add disclaimer requirements
        if disclaimer_results:
            context_parts.append("\n## REQUIRED DISCLAIMERS:")
            for result in disclaimer_results[:1]:
                for line in result['matching_lines'][:2]:
                    context_parts.append(f"- {line['content']}")
        
        context = "\n".join(context_parts)
        
        # Create enhanced prompt for Warren
        warren_prompt = f"""You are Warren, an AI assistant specialized in creating SEC and FINRA compliant marketing content for financial advisors.

{context}

USER REQUEST: {user_request}
CONTENT TYPE: {content_type}

Please create compliant marketing content that:
1. Follows all SEC Marketing Rule and FINRA 2210 requirements
2. Includes appropriate disclaimers and risk disclosures
3. Uses educational tone rather than promotional claims
4. Avoids performance predictions or guarantees
5. Is appropriate for the specified platform/content type

Generate the content now:"""

        # Generate content with Warren
        warren_content = await claude_service.generate_content(warren_prompt)
        
        # Return structured response
        return {
            "status": "success",
            "content": warren_content,
            "content_type": content_type,
            "knowledge_sources_used": len(search_results + regulation_results + disclaimer_results),
            "context_provided": bool(context_parts),
            "user_request": user_request
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/warren/generate-v2")
async def warren_generate_content_v2(request: dict):
    """
    Enhanced Warren content generation using refactored database.
    This is the new database-driven version with improved context retrieval.
    """
    user_request = request.get("request", "")
    content_type = request.get("content_type", "linkedin_post")  # Default to LinkedIn
    audience_type = request.get("audience_type", "general_education")
    user_id = request.get("user_id")
    session_id = request.get("session_id")
    
    if not user_request:
        return {"error": "Content request is required"}
    
    try:
        # Use the new database-driven Warren service
        result = await warren_db_service.generate_content_with_context(
            user_request=user_request,
            content_type=content_type,
            audience_type=audience_type,
            user_id=user_id,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/knowledge-base/load")
async def load_knowledge_base():
    """Get list of available knowledge base files"""
    try:
        kb_service = get_knowledge_service()
        files = kb_service.get_available_files()
        return {
            "status": "success",
            "available_files": len(files),
            "files": files
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge-base/summary")
async def get_knowledge_base_summary():
    """Get summary of knowledge base content (legacy file-based)"""
    try:
        kb_service = get_knowledge_service()
        summary = kb_service.get_summary()
        return {"status": "success", "summary": summary}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge-base/database/summary")
async def get_database_summary():
    """Get summary of refactored database content."""
    try:
        summary = await warren_db_service.get_database_summary()
        return {"status": "success", "summary": summary}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge-base/search")
async def search_knowledge_base(query: str, limit: int = 10):
    """Search knowledge base content"""
    try:
        kb_service = get_knowledge_service()
        results = kb_service.search_content(query, limit)
        return {"status": "success", "results": results, "query": query}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge-base/file/{filename}")
async def get_knowledge_base_file(filename: str):
    """Get content of a specific knowledge base file"""
    try:
        kb_service = get_knowledge_service()
        file_content = kb_service.get_file_content(filename)
        if file_content:
            return {"status": "success", "file": file_content}
        else:
            return {"status": "error", "error": "File not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/knowledge-base/load-to-database")
async def load_knowledge_base_to_database(force_reload: bool = Query(False, description="Force reload even if documents exist")):
    """Load all knowledge base files into PostgreSQL database"""
    try:
        result = await async_kb_service.load_all_documents(force_reload=force_reload)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge-base/database/summary")
async def get_database_summary():
    """Get summary of knowledge base content in database"""
    try:
        summary = await async_kb_service.get_document_summary()
        return {"status": "success", "summary": summary}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge-base/database/search")
async def search_database(query: str, limit: int = 10):
    """Search knowledge base content in database"""
    try:
        results = await async_kb_service.search_documents(query, limit)
        return {"status": "success", "results": results, "query": query}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ===== VECTOR SEARCH ENDPOINTS =====

@router.post("/warren/generate-v3")
async def warren_generate_content_v3(request: dict):
    """
    Warren V3 with Enhanced Vector Search + Automatic Fallbacks
    
    This is the Hybrid MVP+ implementation with:
    - Primary: Vector similarity search
    - Fallback: Text search if vector fails
    - Emergency fallback: Original Warren V2
    """
    user_request = request.get("request", "")
    content_type = request.get("content_type", "linkedin_post")
    audience_type = request.get("audience_type", "general_education")
    user_id = request.get("user_id")
    session_id = request.get("session_id")
    
    if not user_request:
        return {"error": "Content request is required"}
    
    try:
        # Use the enhanced Warren service with vector search
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request=user_request,
            content_type=content_type,
            audience_type=audience_type,
            user_id=user_id,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/embeddings/test")
async def test_embedding_service():
    """Test OpenAI embedding service connection and functionality."""
    try:
        result = await embedding_service.test_connection()
        return {"status": "success", "embedding_test": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/embeddings/vectorize-content")
async def vectorize_existing_content(force_update: bool = False):
    """
    Generate embeddings for all existing marketing content.
    This is a one-time operation to enable vector search.
    """
    try:
        result = await content_vectorization_service.vectorize_existing_marketing_content(
            force_update=force_update
        )
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/embeddings/status")
async def get_vectorization_status():
    """Get current status of content vectorization."""
    try:
        status = await content_vectorization_service.get_vectorization_status()
        return {"status": "success", "vectorization_status": status}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/embeddings/cost-estimate")
async def estimate_vectorization_cost():
    """Estimate the cost of vectorizing all unprocessed content."""
    try:
        estimate = await content_vectorization_service.estimate_vectorization_cost()
        return {"status": "success", "cost_estimate": estimate}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/vector-search/readiness")
async def check_vector_search_readiness():
    """
    Comprehensive check of vector search system readiness.
    Tests all components and provides production readiness assessment.
    """
    try:
        # This would be a method we'd add to enhanced_warren_service
        # For now, let's do a basic readiness check
        
        # Check embedding service
        embedding_test = await embedding_service.test_connection()
        
        # Check vectorization status
        vectorization_status = await content_vectorization_service.get_vectorization_status()
        
        # Check vector search stats
        vector_stats = await vector_search_service.get_vector_search_stats()
        
        # Determine overall readiness
        ready_for_production = (
            embedding_test.get("status") == "success" and
            vectorization_status.get("vector_search_available", False) and
            vector_stats.get("vector_search_ready", False)
        )
        
        return {
            "status": "success",
            "ready_for_production": ready_for_production,
            "components": {
                "embedding_service": embedding_test,
                "vectorization_status": vectorization_status,
                "vector_search_stats": vector_stats
            },
            "next_steps": [
                "Run /embeddings/vectorize-content to generate embeddings" if not vectorization_status.get("vector_search_available") else "Vector search ready",
                "Test /warren/generate-v3 endpoint for enhanced Warren",
                "Monitor performance with /vector-search/stats"
            ]
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/vector-search/test")
async def test_vector_search(request: dict):
    """
    Test vector search functionality with a sample query.
    
    Body: {
        "query": "retirement planning",
        "content_type": "linkedin_post", 
        "limit": 3
    }
    """
    query = request.get("query", "")
    content_type = request.get("content_type")
    limit = request.get("limit", 3)
    
    if not query:
        return {"error": "Query is required"}
    
    try:
        # Convert content_type to enum if provided
        content_type_enum = None
        if content_type:
            try:
                from src.models.refactored_database import ContentType
                content_type_enum = ContentType(content_type.lower())
            except ValueError:
                pass
        
        # Test vector search with lower threshold for testing
        results = await vector_search_service.search_marketing_content(
            query_text=query,
            content_type=content_type_enum,
            similarity_threshold=0.1,  # Use low threshold for testing
            limit=limit
        )
        
        return {
            "status": "success",
            "query": query,
            "content_type": content_type,
            "results_found": len(results),
            "results": results
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/vector-search/stats")
async def get_vector_search_stats():
    """Get statistics about vector search readiness."""
    try:
        stats = await vector_search_service.get_vector_search_stats()
        return {"status": "success", "vector_search_stats": stats}
    except Exception as e:
        return {"status": "error", "error": str(e)}
