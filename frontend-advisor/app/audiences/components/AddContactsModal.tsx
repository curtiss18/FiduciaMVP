'use client'

import { useState, useEffect } from 'react'
import { Audience, Contact } from '@/lib/types'
import { audienceApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { toast } from '@/components/ui/use-toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search, Users } from 'lucide-react'
import api from '@/lib/api'

const DEMO_ADVISOR_ID = 'demo_advisor_001'

interface AddContactsModalProps {
  open: boolean
  onClose: () => void
  audience: Audience
  onSuccess: () => void
}

export default function AddContactsModal({
  open,
  onClose,
  audience,
  onSuccess
}: AddContactsModalProps) {
  const [allContacts, setAllContacts] = useState<Contact[]>([])
  const [availableContacts, setAvailableContacts] = useState<Contact[]>([])
  const [selectedContactIds, setSelectedContactIds] = useState<Set<number>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Load contacts when modal opens
  useEffect(() => {
    if (open) {
      loadAvailableContacts()
      setSelectedContactIds(new Set())
      setSearchTerm('')
      setStatusFilter('all')
    }
  }, [open, audience.id])

  const loadAvailableContacts = async () => {
    try {
      setLoading(true)
      const response = await audienceApi.getContacts(DEMO_ADVISOR_ID)
      const contacts = response.contacts || []
      
      // Filter out contacts that are already in this audience
      const existingContactIds = new Set(
        (audience.contacts || []).map(contact => contact.id)
      )
      
      const available = contacts.filter(contact => 
        !existingContactIds.has(contact.id)
      )
      
      setAllContacts(contacts)
      setAvailableContacts(available)
    } catch (error) {
      console.error('Error loading contacts:', error)
      toast({
        title: "Error",
        description: "Failed to load contacts. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Filter contacts based on search and status
  const filteredContacts = availableContacts.filter(contact => {
    const matchesSearch = searchTerm === '' || 
      `${contact.first_name} ${contact.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contact.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contact.company?.toLowerCase().includes(searchTerm.toLowerCase())
    
    // Exact status matching with correct values
    const matchesStatus = statusFilter === 'all' || contact.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedContactIds(new Set(filteredContacts.map(contact => contact.id)))
    } else {
      setSelectedContactIds(new Set())
    }
  }

  const handleSelectContact = (contactId: number, checked: boolean) => {
    const newSelection = new Set(selectedContactIds)
    if (checked) {
      newSelection.add(contactId)
    } else {
      newSelection.delete(contactId)
    }
    setSelectedContactIds(newSelection)
  }

  const handleSubmit = async () => {
    if (selectedContactIds.size === 0) return

    try {
      setIsSubmitting(true)
      
      // Add contacts to audience using the API
      const selectedContacts = Array.from(selectedContactIds)
      
      await api.post(`/audiences/${audience.id}/contacts`, {
        advisor_id: DEMO_ADVISOR_ID,
        contact_ids: selectedContacts
      })
      
      toast({
        title: "Success",
        description: `Added ${selectedContactIds.size} contact${selectedContactIds.size === 1 ? '' : 's'} to ${audience.name}!`,
      })
      
      onSuccess()
    } catch (error) {
      console.error('Error adding contacts to audience:', error)
      toast({
        title: "Error",
        description: "Failed to add contacts to audience. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  const getContactInitials = (contact: Contact) => {
    return `${contact.first_name.charAt(0)}${contact.last_name.charAt(0)}`.toUpperCase()
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'client':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'prospect':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
      case 'referral source':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
    }
  }

  const isAllSelected = filteredContacts.length > 0 && selectedContactIds.size === filteredContacts.length
  const isIndeterminate = selectedContactIds.size > 0 && selectedContactIds.size < filteredContacts.length

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Add Contacts to {audience.name}</DialogTitle>
          <DialogDescription>
            Select contacts to add to this audience. Only contacts not already in this audience are shown.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search and Filter */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search contacts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="prospect">Prospects</SelectItem>
                <SelectItem value="client">Clients</SelectItem>
                <SelectItem value="referral_source">Referral Sources</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Select All */}
          {filteredContacts.length > 0 && (
            <div className="flex items-center gap-2 pb-2 border-b">
              <Checkbox
                checked={isAllSelected}
                onCheckedChange={handleSelectAll}
                {...(isIndeterminate && { 'data-state': 'indeterminate' })}
              />
              <span className="text-sm font-medium">
                Select all ({filteredContacts.length} contacts)
              </span>
              {selectedContactIds.size > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {selectedContactIds.size} selected
                </Badge>
              )}
            </div>
          )}

          {/* Contacts List */}
          <div className="max-h-96 overflow-y-auto space-y-2">
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading contacts...
              </div>
            ) : filteredContacts.length === 0 ? (
              <div className="text-center py-8">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">
                  No available contacts
                </h3>
                <p className="text-sm text-muted-foreground">
                  {availableContacts.length === 0 
                    ? "All contacts are already in this audience"
                    : "Try adjusting your search or filters"
                  }
                </p>
              </div>
            ) : (
              filteredContacts.map((contact) => (
                <div
                  key={contact.id}
                  className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50"
                >
                  <Checkbox
                    checked={selectedContactIds.has(contact.id)}
                    onCheckedChange={(checked) => 
                      handleSelectContact(contact.id, checked as boolean)
                    }
                  />
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="text-sm">
                      {getContactInitials(contact)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">
                      {contact.first_name} {contact.last_name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {contact.company && `${contact.company} • `}
                      {contact.email || 'No email'}
                    </div>
                  </div>
                  <Badge 
                    variant="secondary" 
                    className={getStatusColor(contact.status)}
                  >
                    {contact.status}
                  </Badge>
                </div>
              ))
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={selectedContactIds.size === 0 || isSubmitting}
          >
            {isSubmitting 
              ? 'Adding...' 
              : `Add ${selectedContactIds.size} Contact${selectedContactIds.size === 1 ? '' : 's'}`
            }
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
