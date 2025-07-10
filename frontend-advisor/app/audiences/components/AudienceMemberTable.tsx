'use client'

import { useState, useEffect, useRef } from 'react'
import { Audience, Contact } from '@/lib/types'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Users } from 'lucide-react'

interface AudienceMemberTableProps {
  audience: Audience
  onSelectionChange: (selectedContacts: Contact[]) => void
  onUpdate: () => void
}

export default function AudienceMemberTable({
  audience,
  onSelectionChange,
  onUpdate
}: AudienceMemberTableProps) {
  const [selectedContactIds, setSelectedContactIds] = useState<Set<number>>(new Set())
  const prevSelectedContactsRef = useRef<Contact[]>([])
  const contacts = audience.contacts || []

  // Reset selection when audience changes
  useEffect(() => {
    setSelectedContactIds(new Set())
    prevSelectedContactsRef.current = []
  }, [audience.id])

  // Notify parent of selection changes only when they actually change
  useEffect(() => {
    const selectedContacts = contacts.filter(contact => 
      selectedContactIds.has(contact.id)
    )
    
    // Only call onSelectionChange if the selection actually changed
    const prev = prevSelectedContactsRef.current
    const hasChanged = selectedContacts.length !== prev.length || 
      selectedContacts.some(contact => !prev.some(p => p.id === contact.id))
    
    if (hasChanged) {
      prevSelectedContactsRef.current = selectedContacts
      onSelectionChange(selectedContacts)
    }
  }, [selectedContactIds])

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedContactIds(new Set(contacts.map(contact => contact.id)))
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

  const isAllSelected = contacts.length > 0 && selectedContactIds.size === contacts.length
  const isIndeterminate = selectedContactIds.size > 0 && selectedContactIds.size < contacts.length

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

  if (contacts.length === 0) {
    return (
      <div className="text-center py-8 border border-dashed border-border rounded-lg">
        <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium text-muted-foreground mb-2">
          No contacts in this audience
        </h3>
        <p className="text-sm text-muted-foreground">
          Add contacts to this audience to get started
        </p>
      </div>
    )
  }

  return (
    <div className="border rounded-lg">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={isAllSelected}
                onCheckedChange={handleSelectAll}
                aria-label="Select all contacts"
                {...(isIndeterminate && { 'data-state': 'indeterminate' })}
              />
            </TableHead>
            <TableHead>Contact</TableHead>
            <TableHead>Company</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Phone</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contacts.map((contact) => (
            <TableRow key={contact.id}>
              <TableCell>
                <Checkbox
                  checked={selectedContactIds.has(contact.id)}
                  onCheckedChange={(checked) => 
                    handleSelectContact(contact.id, checked as boolean)
                  }
                  aria-label={`Select ${contact.first_name} ${contact.last_name}`}
                />
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-xs">
                      {getContactInitials(contact)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium">
                      {contact.first_name} {contact.last_name}
                    </div>
                    {contact.title && (
                      <div className="text-sm text-muted-foreground">
                        {contact.title}
                      </div>
                    )}
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <span className="text-sm">
                  {contact.company || '-'}
                </span>
              </TableCell>
              <TableCell>
                <Badge 
                  variant="secondary" 
                  className={getStatusColor(contact.status)}
                >
                  {contact.status}
                </Badge>
              </TableCell>
              <TableCell>
                <span className="text-sm">
                  {contact.email || '-'}
                </span>
              </TableCell>
              <TableCell>
                <span className="text-sm">
                  {contact.phone || '-'}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
