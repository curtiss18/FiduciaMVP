'use client'

import { useState } from 'react'
import { Audience } from '@/lib/types'
import { audienceApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
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

const DEMO_ADVISOR_ID = 'demo_advisor_001'

interface DeleteAudienceModalProps {
  open: boolean
  onClose: () => void
  audience: Audience
  onSuccess: () => void
}

export default function DeleteAudienceModal({
  open,
  onClose,
  audience,
  onSuccess
}: DeleteAudienceModalProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    try {
      setIsDeleting(true)
      
      await audienceApi.deleteAudience(audience.id.toString(), DEMO_ADVISOR_ID)
      
      toast({
        title: "Success",
        description: `Audience "${audience.name}" has been deleted.`,
      })
      
      onSuccess()
    } catch (error) {
      console.error('Error deleting audience:', error)
      toast({
        title: "Error",
        description: "Failed to delete audience. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsDeleting(false)
    }
  }

  const handleClose = () => {
    if (!isDeleting) {
      onClose()
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
              <DialogTitle>Delete Audience</DialogTitle>
              <DialogDescription>
                This action cannot be undone.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          <p className="text-sm text-muted-foreground mb-4">
            Are you sure you want to delete the audience <strong>"{audience.name}"</strong>?
          </p>
          
          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span>Audience:</span>
              <span className="font-medium">{audience.name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Members:</span>
              <span className="font-medium">
                {audience.contact_count || 0} contact{(audience.contact_count || 0) !== 1 ? 's' : ''}
              </span>
            </div>
            {audience.occupation && (
              <div className="flex justify-between text-sm">
                <span>Occupation:</span>
                <span className="font-medium">{audience.occupation}</span>
              </div>
            )}
          </div>

          <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <p className="text-sm text-orange-800 dark:text-orange-200">
              <strong>Note:</strong> Deleting this audience will remove it permanently, but the contacts 
              will remain in your contact list and can be added to other audiences.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete Audience'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
