'use client'

import React, { useState, useEffect } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'

import { ContactsTable } from '@/components/contacts/ContactsTable'
import { ContactForm } from '@/components/contacts/ContactForm'
import { ContactFilters } from '@/components/contacts/ContactFilters'
import { Button } from '@/components/ui/button'
import { Users, Plus, FileText } from 'lucide-react'
import { audienceApi } from '@/lib/api'
import { Contact } from '@/lib/types'
import { useToast } from '@/hooks/use-toast'

const DEMO_ADVISOR_ID = 'demo_advisor_001'

export default function ContactsPage() {
  const { toast } = useToast()
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [showContactForm, setShowContactForm] = useState(false)
  const [editingContact, setEditingContact] = useState<Contact | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  // Load contacts
  const loadData = async () => {
    try {
      setLoading(true)
      const contactsData = await audienceApi.getContacts(DEMO_ADVISOR_ID, searchTerm, statusFilter)
      setContacts(contactsData.contacts || [])
    } catch (error) {
      console.error('Error loading contacts data:', error)
      toast({
        title: "Error",
        description: "Failed to load contacts data. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [searchTerm, statusFilter])

  const handleCreateContact = async (contactData: any) => {
    try {
      await audienceApi.createContact({
        advisorId: DEMO_ADVISOR_ID,
        ...contactData
      })
      setShowContactForm(false)
      loadData()
      toast({
        title: "Success",
        description: "Contact created successfully.",
      })
    } catch (error) {
      console.error('Error creating contact:', error)
      toast({
        title: "Error", 
        description: "Failed to create contact. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleUpdateContact = async (contactData: any) => {
    if (!editingContact) return
    
    try {
      await audienceApi.updateContact(editingContact.id.toString(), DEMO_ADVISOR_ID, contactData)
      setEditingContact(null)
      setShowContactForm(false)  // Close the modal
      loadData()
      toast({
        title: "Success",
        description: "Contact updated successfully.",
      })
    } catch (error) {
      console.error('Error updating contact:', error)
      toast({
        title: "Error",
        description: "Failed to update contact. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleDeleteContact = async (contactId: string) => {
    try {
      await audienceApi.deleteContact(contactId, DEMO_ADVISOR_ID)
      loadData()
      toast({
        title: "Success",
        description: "Contact deleted successfully.",
      })
    } catch (error) {
      console.error('Error deleting contact:', error)
      toast({
        title: "Error",
        description: "Failed to delete contact. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleEditContact = (contact: Contact) => {
    setEditingContact(contact)
    setShowContactForm(true)
  }

  const handleCloseForm = () => {
    setShowContactForm(false)
    setEditingContact(null)
  }

  const headerActions = (
    <div className="flex gap-2">
      <Button variant="outline" size="sm">
        <FileText className="h-4 w-4 mr-2" />
        Export
      </Button>
      <Button onClick={() => setShowContactForm(true)} size="sm">
        <Plus className="h-4 w-4 mr-2" />
        Add Contact
      </Button>
    </div>
  )

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Contacts"
        subtitle="Manage your prospects, clients, and referral sources"
        icon={Users}
        actions={headerActions}
      />
      
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Filters */}
        <ContactFilters
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
        />

        {/* Contacts Table */}
        <ContactsTable
          contacts={contacts}
          loading={loading}
          onEdit={handleEditContact}
          onDelete={handleDeleteContact}
        />

        {/* Contact Form Modal */}
        <ContactForm
          open={showContactForm}
          onClose={handleCloseForm}
          onSubmit={editingContact ? handleUpdateContact : handleCreateContact}
          contact={editingContact}
          loading={loading}
        />
      </div>
    </div>
  )
}