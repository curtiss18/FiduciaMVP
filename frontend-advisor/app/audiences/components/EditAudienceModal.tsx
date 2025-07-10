'use client'

import { useState, useEffect } from 'react'
import { Audience } from '@/lib/types'
import { audienceApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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

const DEMO_ADVISOR_ID = 'demo_advisor_001'

const OCCUPATION_OPTIONS = [
  'Healthcare/Medical',
  'Technology/Software',
  'Finance/Banking',
  'Legal/Law',
  'Education/Academic',
  'Real Estate',
  'Engineering',
  'Sales/Marketing',
  'Consulting',
  'Manufacturing',
  'Retail',
  'Other'
]

const RELATIONSHIP_TYPE_OPTIONS = [
  'Client',
  'Prospect',
  'Referral Source',
  'Professional Network',
  'Family/Friends',
  'Business Partner',
  'Vendor/Supplier',
  'Other'
]

interface EditAudienceModalProps {
  open: boolean
  onClose: () => void
  audience: Audience
  onSuccess: () => void
}

export default function EditAudienceModal({
  open,
  onClose,
  audience,
  onSuccess
}: EditAudienceModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    characteristics: '',
    occupation: '',
    relationshipType: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Initialize form data when audience changes
  useEffect(() => {
    if (audience) {
      setFormData({
        name: audience.name || '',
        description: audience.description || '',
        characteristics: audience.characteristics || '',
        occupation: audience.occupation || '',
        relationshipType: audience.relationship_type || ''
      })
    }
  }, [audience])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      return
    }

    try {
      setIsSubmitting(true)
      
      await audienceApi.updateAudience(
        audience.id.toString(),
        DEMO_ADVISOR_ID,
        {
          name: formData.name.trim(),
          description: formData.description.trim() || null,
          characteristics: formData.characteristics.trim() || null,
          occupation: formData.occupation || null,
          relationship_type: formData.relationshipType || null
        }
      )
      
      toast({
        title: "Success",
        description: "Audience updated successfully!",
      })
      
      onSuccess()
    } catch (error) {
      console.error('Error updating audience:', error)
      toast({
        title: "Error",
        description: "Failed to update audience. Please try again.",
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

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Edit Audience</DialogTitle>
          <DialogDescription>
            Update the details and characteristics of your audience group.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Audience Name */}
          <div className="space-y-2">
            <Label htmlFor="edit-name">Audience Name *</Label>
            <Input
              id="edit-name"
              placeholder="e.g., Local Doctors, Tech Executives"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="edit-description">Description</Label>
            <Textarea
              id="edit-description"
              placeholder="Describe this audience group and how you plan to engage with them..."
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
            />
          </div>

          {/* Occupation and Relationship Type in two columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit-occupation">Primary Occupation</Label>
              <Select
                value={formData.occupation}
                onValueChange={(value) => setFormData(prev => ({ ...prev, occupation: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select occupation" />
                </SelectTrigger>
                <SelectContent>
                  {OCCUPATION_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-relationshipType">Relationship Type</Label>
              <Select
                value={formData.relationshipType}
                onValueChange={(value) => setFormData(prev => ({ ...prev, relationshipType: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select relationship" />
                </SelectTrigger>
                <SelectContent>
                  {RELATIONSHIP_TYPE_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Characteristics */}
          <div className="space-y-2">
            <Label htmlFor="edit-characteristics">Key Characteristics</Label>
            <Textarea
              id="edit-characteristics"
              placeholder="Define key characteristics, interests, or traits that describe this audience..."
              value={formData.characteristics}
              onChange={(e) => setFormData(prev => ({ ...prev, characteristics: e.target.value }))}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!formData.name.trim() || isSubmitting}
            >
              {isSubmitting ? 'Updating...' : 'Update Audience'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
