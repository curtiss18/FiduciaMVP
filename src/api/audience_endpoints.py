"""
Audience API Endpoints
Handles CRUD operations for contacts, audiences, and their relationships
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from src.core.database import get_db
from src.models.audiences import AdvisorContact, AdvisorAudience, audience_contacts

logger = logging.getLogger(__name__)

# Create router with tags for API documentation
router = APIRouter(tags=["Audiences"])

# Pydantic models for request/response validation
class ContactCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field("prospect", max_length=50)
    notes: Optional[str] = None
    advisor_id: Optional[str] = "demo_advisor_001"

class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

class ContactResponse(BaseModel):
    id: int
    advisor_id: str
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    title: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AudienceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    occupation: Optional[str] = Field(None, max_length=255)
    relationship_type: Optional[str] = Field(None, max_length=255)
    characteristics: Optional[str] = None
    advisor_id: Optional[str] = "demo_advisor_001"

class AudienceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    occupation: Optional[str] = Field(None, max_length=255)
    relationship_type: Optional[str] = Field(None, max_length=255)
    characteristics: Optional[str] = None

class AudienceResponse(BaseModel):
    id: int
    advisor_id: str
    name: str
    description: Optional[str]
    occupation: Optional[str]
    relationship_type: Optional[str]
    characteristics: Optional[str]
    contact_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AudienceWithContactsResponse(AudienceResponse):
    contacts: List[ContactResponse]

class ContactAssignment(BaseModel):
    contact_ids: List[int] = Field(..., min_items=1)

# Contact CRUD Endpoints
@router.post("/contacts", response_model=ContactResponse, summary="Create a new contact")
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new contact for the advisor.
    
    - **first_name**: Contact's first name (required)
    - **last_name**: Contact's last name (required)
    - **email**: Contact's email address
    - **company**: Contact's company name
    - **title**: Contact's job title
    - **status**: Contact status (prospect, client, inactive)
    """
    try:
        db_contact = AdvisorContact(**contact.dict())
        db.add(db_contact)
        await db.commit()
        await db.refresh(db_contact)
        
        logger.info(f"Created contact: {db_contact.first_name} {db_contact.last_name}")
        return db_contact
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating contact: {str(e)}")

@router.get("/contacts", response_model=List[ContactResponse], summary="List all contacts")
async def list_contacts(
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID to filter contacts"),
    skip: int = Query(0, ge=0, description="Number of contacts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of contacts to return"),
    search: Optional[str] = Query(None, description="Search in name, company, or email"),
    status: Optional[str] = Query(None, description="Filter by contact status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of contacts for the advisor.
    
    - **advisor_id**: Filter contacts by advisor
    - **skip**: Pagination offset
    - **limit**: Maximum number of contacts to return
    - **search**: Search term for filtering contacts
    - **status**: Filter by contact status (prospect, client, referral_source)
    """
    try:
        # Test basic database connection first
        test_query = select(AdvisorContact).limit(1)
        test_result = await db.execute(test_query)
        logger.info("Database connection successful")
        
        # Build the main query
        query = select(AdvisorContact).where(AdvisorContact.advisor_id == advisor_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (AdvisorContact.first_name.ilike(search_term)) |
                (AdvisorContact.last_name.ilike(search_term)) |
                (AdvisorContact.company.ilike(search_term)) |
                (AdvisorContact.email.ilike(search_term))
            )
        
        if status:
            query = query.where(AdvisorContact.status == status)
        
        query = query.offset(skip).limit(limit).order_by(AdvisorContact.last_name, AdvisorContact.first_name)
        
        logger.info(f"Executing query for advisor_id: {advisor_id}")
        result = await db.execute(query)
        contacts = result.scalars().all()
        
        logger.info(f"Found {len(contacts)} contacts")
        return contacts
        
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error retrieving contacts: {str(e)}")

@router.get("/contacts/{contact_id}", response_model=ContactResponse, summary="Get a specific contact")
async def get_contact(
    contact_id: int,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific contact by ID."""
    try:
        query = select(AdvisorContact).where(
            AdvisorContact.id == contact_id,
            AdvisorContact.advisor_id == advisor_id
        )
        
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return contact
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving contact: {str(e)}")

@router.put("/contacts/{contact_id}", response_model=ContactResponse, summary="Update a contact")
async def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Update a specific contact."""
    try:
        # Check if contact exists and belongs to advisor
        query = select(AdvisorContact).where(
            AdvisorContact.id == contact_id,
            AdvisorContact.advisor_id == advisor_id
        )
        
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Update only provided fields
        update_data = contact_update.dict(exclude_unset=True)
        if update_data:
            update_query = update(AdvisorContact).where(
                AdvisorContact.id == contact_id
            ).values(**update_data)
            
            await db.execute(update_query)
            await db.commit()
            await db.refresh(contact)
        
        logger.info(f"Updated contact: {contact.first_name} {contact.last_name}")
        return contact
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating contact: {str(e)}")

@router.delete("/contacts/{contact_id}", summary="Delete a contact")
async def delete_contact(
    contact_id: int,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific contact."""
    try:
        # Check if contact exists and belongs to advisor
        query = select(AdvisorContact).where(
            AdvisorContact.id == contact_id,
            AdvisorContact.advisor_id == advisor_id
        )
        
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Delete the contact (cascade will handle relationships)
        delete_query = delete(AdvisorContact).where(AdvisorContact.id == contact_id)
        await db.execute(delete_query)
        await db.commit()
        
        logger.info(f"Deleted contact: {contact.first_name} {contact.last_name}")
        return {"message": "Contact deleted successfully", "contact_id": contact_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting contact {contact_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting contact: {str(e)}")

# Audience CRUD Endpoints
@router.post("/audiences", response_model=AudienceResponse, summary="Create a new audience")
async def create_audience(
    audience: AudienceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new audience group.
    
    - **name**: Audience name (required)
    - **description**: Description of the audience
    - **occupation**: Common occupation (e.g., "Healthcare/Medical")
    - **relationship_type**: Type of relationship (e.g., "Professional Network")
    - **characteristics**: Detailed characteristics for Warren targeting
    """
    try:
        db_audience = AdvisorAudience(**audience.dict())
        db.add(db_audience)
        await db.commit()
        await db.refresh(db_audience)
        
        logger.info(f"Created audience: {db_audience.name}")
        return db_audience
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating audience: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating audience: {str(e)}")

@router.get("/audiences", response_model=List[AudienceResponse], summary="List all audiences")
async def list_audiences(
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID to filter audiences"),
    skip: int = Query(0, ge=0, description="Number of audiences to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of audiences to return"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a list of audiences for the advisor."""
    try:
        query = select(AdvisorAudience).where(
            AdvisorAudience.advisor_id == advisor_id
        ).offset(skip).limit(limit).order_by(AdvisorAudience.name)
        
        result = await db.execute(query)
        audiences = result.scalars().all()
        
        return audiences
        
    except Exception as e:
        logger.error(f"Error listing audiences: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving audiences: {str(e)}")

@router.get("/audiences/{audience_id}", response_model=AudienceWithContactsResponse, summary="Get a specific audience with contacts")
async def get_audience(
    audience_id: int,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific audience by ID with its associated contacts."""
    try:
        query = select(AdvisorAudience).options(
            selectinload(AdvisorAudience.contacts)
        ).where(
            AdvisorAudience.id == audience_id,
            AdvisorAudience.advisor_id == advisor_id
        )
        
        result = await db.execute(query)
        audience = result.scalar_one_or_none()
        
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
        
        return audience
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audience {audience_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving audience: {str(e)}")

@router.put("/audiences/{audience_id}", response_model=AudienceResponse, summary="Update an audience")
async def update_audience(
    audience_id: int,
    audience_update: AudienceUpdate,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Update a specific audience."""
    try:
        # Check if audience exists and belongs to advisor
        query = select(AdvisorAudience).where(
            AdvisorAudience.id == audience_id,
            AdvisorAudience.advisor_id == advisor_id
        )
        
        result = await db.execute(query)
        audience = result.scalar_one_or_none()
        
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
        
        # Update only provided fields
        update_data = audience_update.dict(exclude_unset=True)
        if update_data:
            update_query = update(AdvisorAudience).where(
                AdvisorAudience.id == audience_id
            ).values(**update_data)
            
            await db.execute(update_query)
            await db.commit()
            await db.refresh(audience)
        
        logger.info(f"Updated audience: {audience.name}")
        return audience
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating audience {audience_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating audience: {str(e)}")

@router.delete("/audiences/{audience_id}", summary="Delete an audience")
async def delete_audience(
    audience_id: int,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific audience."""
    try:
        # Check if audience exists and belongs to advisor
        query = select(AdvisorAudience).where(
            AdvisorAudience.id == audience_id,
            AdvisorAudience.advisor_id == advisor_id
        )
        
        result = await db.execute(query)
        audience = result.scalar_one_or_none()
        
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
        
        # Delete the audience (cascade will handle relationships)
        delete_query = delete(AdvisorAudience).where(AdvisorAudience.id == audience_id)
        await db.execute(delete_query)
        await db.commit()
        
        logger.info(f"Deleted audience: {audience.name}")
        return {"message": "Audience deleted successfully", "audience_id": audience_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting audience {audience_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting audience: {str(e)}")

# Relationship Management Endpoints
@router.post("/audiences/{audience_id}/contacts", summary="Add contacts to an audience")
async def add_contacts_to_audience(
    audience_id: int,
    assignment: ContactAssignment,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Add multiple contacts to an audience."""
    try:
        # Verify audience exists and belongs to advisor
        audience_query = select(AdvisorAudience).where(
            AdvisorAudience.id == audience_id,
            AdvisorAudience.advisor_id == advisor_id
        )
        audience_result = await db.execute(audience_query)
        audience = audience_result.scalar_one_or_none()
        
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
        
        # Verify all contacts exist and belong to advisor
        contacts_query = select(AdvisorContact).where(
            AdvisorContact.id.in_(assignment.contact_ids),
            AdvisorContact.advisor_id == advisor_id
        )
        contacts_result = await db.execute(contacts_query)
        contacts = contacts_result.scalars().all()
        
        if len(contacts) != len(assignment.contact_ids):
            raise HTTPException(status_code=400, detail="One or more contacts not found")
        
        # Add contacts to audience using direct SQL insertion to avoid async relationship issues
        added_count = 0
        for contact_id in assignment.contact_ids:
            # Check if relationship already exists
            existing_query = select(audience_contacts).where(
                audience_contacts.c.audience_id == audience_id,
                audience_contacts.c.contact_id == contact_id
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.fetchone()
            
            if not existing:
                # Insert new relationship
                insert_stmt = audience_contacts.insert().values(
                    audience_id=audience_id,
                    contact_id=contact_id
                )
                await db.execute(insert_stmt)
                added_count += 1
        
        # Update contact count manually
        count_query = select(func.count(audience_contacts.c.contact_id)).where(
            audience_contacts.c.audience_id == audience_id
        )
        count_result = await db.execute(count_query)
        new_count = count_result.scalar()
        
        # Update the audience contact count
        update_stmt = update(AdvisorAudience).where(
            AdvisorAudience.id == audience_id
        ).values(contact_count=new_count)
        await db.execute(update_stmt)
        
        await db.commit()
        
        logger.info(f"Added {added_count} contacts to audience {audience_id}")
        return {
            "message": f"Added {added_count} contact(s) to audience",
            "audience_id": audience_id,
            "added_contact_ids": assignment.contact_ids,
            "total_contacts_in_audience": new_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding contacts to audience {audience_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding contacts to audience: {str(e)}")

@router.delete("/audiences/{audience_id}/contacts/{contact_id}", summary="Remove a contact from an audience")
async def remove_contact_from_audience(
    audience_id: int,
    contact_id: int,
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for access control"),
    db: AsyncSession = Depends(get_db)
):
    """Remove a contact from an audience."""
    try:
        # Verify audience exists and belongs to advisor
        audience_query = select(AdvisorAudience).options(
            selectinload(AdvisorAudience.contacts)
        ).where(
            AdvisorAudience.id == audience_id,
            AdvisorAudience.advisor_id == advisor_id
        )
        audience_result = await db.execute(audience_query)
        audience = audience_result.scalar_one_or_none()
        
        if not audience:
            raise HTTPException(status_code=404, detail="Audience not found")
        
        # Find contact in audience
        contact_to_remove = None
        for contact in audience.contacts:
            if contact.id == contact_id:
                contact_to_remove = contact
                break
        
        if not contact_to_remove:
            raise HTTPException(status_code=404, detail="Contact not found in this audience")
        
        # Remove contact from audience
        audience.contacts.remove(contact_to_remove)
        
        # Update contact count
        audience.update_contact_count()
        
        await db.commit()
        
        logger.info(f"Removed contact {contact_id} from audience: {audience.name}")
        return {
            "message": "Contact removed from audience",
            "audience_id": audience_id,
            "contact_id": contact_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing contact {contact_id} from audience {audience_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing contact from audience: {str(e)}")

# Statistics and utility endpoints
@router.get("/statistics", summary="Get audience and contact statistics")
async def get_audience_statistics(
    advisor_id: str = Query("demo_advisor_001", description="Advisor ID for statistics"),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about contacts and audiences."""
    try:
        # Count contacts
        contacts_query = select(func.count(AdvisorContact.id)).where(
            AdvisorContact.advisor_id == advisor_id
        )
        contacts_result = await db.execute(contacts_query)
        total_contacts = contacts_result.scalar()
        
        # Count audiences
        audiences_query = select(func.count(AdvisorAudience.id)).where(
            AdvisorAudience.advisor_id == advisor_id
        )
        audiences_result = await db.execute(audiences_query)
        total_audiences = audiences_result.scalar()
        
        # Count relationships
        relationships_query = select(func.count()).select_from(audience_contacts)
        relationships_result = await db.execute(relationships_query)
        total_relationships = relationships_result.scalar()
        
        return {
            "advisor_id": advisor_id,
            "total_contacts": total_contacts,
            "total_audiences": total_audiences,
            "total_relationships": total_relationships,
            "avg_contacts_per_audience": round(total_relationships / max(total_audiences, 1), 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")
