# SCRUM-42 Document Context Integration for Warren V3

# Insert this code right before the Warren service call in endpoints.py
# Around line 340, replace the comment "# Use the enhanced Warren service..."

        # NEW: Retrieve session documents for context (SCRUM-42 Integration)
        session_document_summaries = []
        if session_id:
            try:
                logger.info(f"Retrieving documents for session: {session_id}")
                document_manager = DocumentManager()
                session_documents = await document_manager.list_session_documents(session_id)
                
                if session_documents:
                    logger.info(f"Found {len(session_documents)} documents for session {session_id}")
                    
                    # Get AI summaries for Warren context
                    for doc in session_documents:
                        try:
                            doc_summary = await document_manager.get_context_summary(
                                document_id=doc['id'],
                                context_length=800  # Optimized for Warren context
                            )
                            if doc_summary:
                                session_document_summaries.append({
                                    "document_id": doc['id'],
                                    "title": doc['title'],
                                    "summary": doc_summary,
                                    "content_type": doc['content_type']
                                })
                                logger.info(f"Added document summary: {doc['title']} ({len(doc_summary)} chars)")
                        except Exception as doc_error:
                            logger.warning(f"Could not get summary for document {doc['id']}: {str(doc_error)}")
                else:
                    logger.info(f"No documents found for session {session_id}")
                    
            except Exception as doc_error:
                logger.error(f"Error retrieving session documents: {str(doc_error)}")
                # Continue without documents - don't fail the request

        # Use the enhanced Warren service with refinement support, YouTube context, and document context
        result = await enhanced_warren_service.generate_content_with_enhanced_context(
            user_request=user_request,
            content_type=content_type,
            audience_type=audience_type,
            user_id=user_id,
            session_id=session_id,
            current_content=current_content,
            is_refinement=is_refinement,
            youtube_context=youtube_context,  # YouTube context
            document_summaries=session_document_summaries,  # NEW: Document context
            use_conversation_context=True  # Enable conversation memory
        )
