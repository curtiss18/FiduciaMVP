'use client'

import { useState } from 'react'
import { Audience, Contact } from '@/lib/types'
import { Button } from '@/components/ui/button'
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
import { AlertTriangle } from 'lucide-react'
import api from '@/lib/api'

const DEMO_ADVISOR_ID = 'demo_advisor_001'

interface RemoveContactsModalProps {
  open: boolean
  onClose: () => void
  audience: Audience
  contacts: Contact[]
  onSuccess: () => void
}

export default function RemoveContactsModal({
  open,
  onClose,
  audience,
  contacts,
  onSuccess
}: RemoveContactsModalProps) {
  const [isRemoving, setIsRemoving] = useState(false)

  const handleRemove = async () => {
    try {
      setIsRemoving(true)
      
      // Remove each contact from the audience
      for (const contact of contacts) {
        await api.delete(`/audiences/${audience.id}/contacts/${contact.id}`, {
          params: { advisor_id: DEMO_ADVISOR_ID }
        })
      }
      
      toast({
        title: "Success",
        description: `Removed ${contacts.length} contact${contacts.length === 1 ? '' : 's'} from ${audience.name}.`,
      })
      
      onSuccess()
    } catch (error) {
      console.error('Error removing contacts from audience:', error)
      toast({
        title: "Error",
        description: "Failed to remove contacts from audience. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsRemoving(false)
    }
  }

  const handleClose = () => {
    if (!isRemoving) {
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

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle className="h-6 w-6 text-destructive" />
            </div>
            <div>
              <DialogTitle>Remove Contacts from Audience</DialogTitle>
              <DialogDescription>
                Remove selected contacts from this audience.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          <p className="text-sm text-muted-foreground mb-4">
            Are you sure you want to remove {contacts.length} contact{contacts.length === 1 ? '' : 's'} from 
            <strong> "{audience.name}"</strong>?
          </p>
          
          {/* Audience Info */}
          <div className="bg-muted/50 rounded-lg p-4 mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span>Audience:</span>
              <span className="font-medium">{audience.name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Contacts to remove:</span>
              <span className="font-medium">{contacts.length}</span>
            </div>
          </div>

          {/* Contacts List */}
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {contacts.map((contact) => (
              <div
                key={contact.id}
                className="flex items-center gap-3 p-2 border rounded-lg"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-xs">
                    {getContactInitials(contact)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">
                    {contact.first_name} {contact.last_name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {contact.company || 'No company'}
                  </div>
                </div>
                <Badge 
                  variant="secondary" 
                  className={`text-xs ${getStatusColor(contact.status)}`}
                >
                  {contact.status}
                </Badge>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <p className="text-sm text-orange-800 dark:text-orange-200">
              <strong>Note:</strong> This will only remove the contacts from this audience. 
              The contacts will remain in your contact list and can be added to other audiences.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isRemoving}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleRemove}
            disabled={isRemoving}
          >
            {isRemoving ? 'Removing...' : `Remove ${contacts.length} Contact${contacts.length === 1 ? '' : 's'}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
