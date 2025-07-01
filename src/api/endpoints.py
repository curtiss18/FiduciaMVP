from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging
from src.services.claude_service import claude_service
from src.services.knowledge_base_service import get_knowledge_service
from src.services.async_knowledge_service import async_kb_service
from src.services.warren_database_service import warren_db_service
from src.services.enhanced_warren_service import enhanced_warren_service
from src.services.embedding_service import embedding_service
from src.services.vector_search_service import vector_search_service
from src.services.content_vectorization_service import content_vectorization_service
from src.services.content_management_service import content_management_service
from src.services.youtube_transcript_service import youtube_transcript_service
from src.models.refactored_database import ContentType, AudienceType, ApprovalStatus, SourceType
from src.core.database import check_db_connection, create_tables, get_db

logger = logging.getLogger(__name__)

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
    Warren V3 with Enhanced Vector Search + Automatic Fallbacks + YouTube Support
    
    This is the Hybrid MVP+ implementation with:
    - Primary: Vector similarity search
    - Fallback: Text search if vector fails
    - Emergency fallback: Original Warren V2
    - Smart prompt selection: Main vs refinement prompts
    - NEW: YouTube video transcript integration
    """
    user_request = request.get("request", "")
    content_type = request.get("content_type", "linkedin_post")
    audience_type = request.get("audience_type", "general_education")
    user_id = request.get("user_id")
    session_id = request.get("session_id")
    
    # NEW: Check for refinement context
    current_content = request.get("current_content")
    is_refinement = request.get("is_refinement", False)
    
    # NEW: YouTube URL support
    youtube_url = request.get("youtube_url")
    
    if not user_request:
        return {"error": "Content request is required"}
    
    try:
        # NEW: Process YouTube URL if provided
        youtube_context = None
        if youtube_url:
            try:
                logger.info(f"Processing YouTube URL: {youtube_url}")
                transcript_result = await youtube_transcript_service.get_transcript_from_url(youtube_url)
                
                if transcript_result["success"]:
                    # Create context from transcript
                    transcript_text = transcript_result["transcript"]
                    metadata = transcript_result.get("metadata", {})
                    stats = transcript_result.get("stats", {})
                    
                    # DEBUG: Log transcript info
                    logger.info(f"YouTube transcript fetched: {len(transcript_text)} characters")
                    logger.info(f"Transcript preview: {transcript_text[:200]}...")
                    
                    youtube_context = {
                        "transcript": transcript_text,
                        "video_url": youtube_url,
                        "video_id": transcript_result.get("video_id"),
                        "metadata": metadata,
                        "stats": stats
                    }
                    
                    logger.info(f"YouTube transcript processed: {stats.get('character_count', 0)} characters")
                else:
                    logger.warning(f"YouTube transcript failed: {transcript_result['error']}")
                    return {
                        "status": "error",
                        "error": f"Could not process YouTube video: {transcript_result['error']}",
                        "youtube_url": youtube_url
                    }
                    
            except Exception as youtube_error:
                logger.error(f"YouTube processing exception: {str(youtube_error)}")
                return {
                    "status": "error", 
                    "error": f"YouTube processing failed: {str(youtube_error)}",
                    "youtube_url": youtube_url
                }
        
        # Use the enhanced Warren service with refinement support and YouTube context
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request=user_request,
            content_type=content_type,
            audience_type=audience_type,
            user_id=user_id,
            session_id=session_id,
            current_content=current_content,
            is_refinement=is_refinement,
            youtube_context=youtube_context  # NEW: Pass YouTube context
        )
        
        # Add YouTube info to response if it was used
        if youtube_context:
            result["youtube_info"] = {
                "url": youtube_url,
                "video_id": youtube_context["video_id"],
                "transcript_stats": youtube_context["stats"]
            }
        
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


@router.post("/embeddings/vectorize-compliance-rules")
async def vectorize_existing_compliance_rules(force_update: bool = False):
    """
    Generate embeddings for all existing compliance rules.
    This enables full vector search including disclaimers and compliance guidance.
    """
    try:
        result = await content_vectorization_service.vectorize_existing_compliance_rules(
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
                content_type_enum = ContentType(content_type.upper())
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


# ===== CONTENT MANAGEMENT CRUD ENDPOINTS =====

@router.get("/content")
async def list_content(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    audience_type: Optional[str] = Query(None, description="Filter by audience type"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    search: Optional[str] = Query(None, description="Search in title, content, and tags")
):
    """
    Get all marketing content with optional filtering and pagination.
    
    Supports filtering by:
    - content_type: website_blog, newsletter, linkedin_post, etc.
    - audience_type: client_communication, prospect_advertising, etc.
    - approval_status: pending, approved, rejected, needs_revision
    - source_type: fiducia_created, user_contributed, etc.
    - search: Text search in title, content, and tags
    """
    try:
        # Convert string enums to enum objects
        content_type_enum = None
        if content_type:
            try:
                content_type_enum = ContentType(content_type.upper())
            except ValueError:
                return {"status": "error", "error": f"Invalid content_type: {content_type}"}
        
        audience_type_enum = None
        if audience_type:
            try:
                audience_type_enum = AudienceType(audience_type.upper())
            except ValueError:
                return {"status": "error", "error": f"Invalid audience_type: {audience_type}"}
        
        approval_status_enum = None
        if approval_status:
            try:
                approval_status_enum = ApprovalStatus(approval_status.lower())
            except ValueError:
                return {"status": "error", "error": f"Invalid approval_status: {approval_status}"}
        
        source_type_enum = None
        if source_type:
            try:
                source_type_enum = SourceType(source_type.lower())
            except ValueError:
                return {"status": "error", "error": f"Invalid source_type: {source_type}"}
        
        # Get content from service
        result = await content_management_service.get_all_content(
            skip=skip,
            limit=limit,
            content_type=content_type_enum,
            audience_type=audience_type_enum,
            approval_status=approval_status_enum,
            search_query=search,
            source_type=source_type_enum
        )
        
        return result
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/content/enums")
async def get_content_enums():
    """Get available enum values for content creation/filtering."""
    try:
        return {
            "status": "success",
            "enums": {
                "content_types": [e.value for e in ContentType],
                "audience_types": [e.value for e in AudienceType],
                "approval_statuses": [e.value for e in ApprovalStatus],
                "source_types": [e.value for e in SourceType]
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/content/statistics")
async def get_content_statistics():
    """Get statistics about the content database."""
    try:
        result = await content_management_service.get_content_statistics()
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/content")
async def create_content(request: dict):
    """
    Create new marketing content with automatic vectorization.
    
    Required fields:
    - title: Content title
    - content_text: The actual content
    - content_type: Type from ContentType enum
    - audience_type: Type from AudienceType enum
    
    Optional fields:
    - tone: professional, casual, educational, promotional
    - topic_focus: retirement, investing, tax, estate
    - target_demographics: millennials, boomers, high_net_worth
    - approval_status: pending, approved, rejected, needs_revision (default: approved)
    - compliance_score: 0-1 scale (default: 1.0)
    - source_type: fiducia_created, user_contributed, etc. (default: fiducia_created)
    - original_source: URL, file path, or description
    - contributed_by_user_id: If user-contributed
    - tags: Array of tags
    """
    try:
        result = await content_management_service.create_content(request)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/content/{content_id}")
async def get_content_by_id(content_id: int):
    """Get a specific marketing content item by ID."""
    try:
        result = await content_management_service.get_content_by_id(content_id)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.put("/content/{content_id}")
async def update_content(content_id: int, request: dict):
    """
    Update existing marketing content with automatic re-vectorization.
    
    Any field can be updated. If title or content_text changes,
    the embedding will be automatically regenerated.
    """
    try:
        result = await content_management_service.update_content(content_id, request)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.delete("/content/{content_id}")
async def delete_content(content_id: int):
    """Delete marketing content and its embedding."""
    try:
        result = await content_management_service.delete_content(content_id)
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}
