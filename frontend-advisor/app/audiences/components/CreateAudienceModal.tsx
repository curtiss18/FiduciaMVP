'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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

interface CreateAudienceModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (audienceData: {
    name: string
    description?: string
    characteristics?: string
    occupation?: string
    relationshipType?: string
  }) => Promise<void>
}

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

export default function CreateAudienceModal({
  open,
  onClose,
  onSubmit
}: CreateAudienceModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    characteristics: '',
    occupation: '',
    relationshipType: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      return
    }

    try {
      setIsSubmitting(true)
      await onSubmit({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        characteristics: formData.characteristics.trim() || undefined,
        occupation: formData.occupation || undefined,
        relationshipType: formData.relationshipType || undefined
      })
      
      // Reset form
      setFormData({
        name: '',
        description: '',
        characteristics: '',
        occupation: '',
        relationshipType: ''
      })
    } catch (error) {
      console.error('Error creating audience:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
      // Reset form on close
      setFormData({
        name: '',
        description: '',
        characteristics: '',
        occupation: '',
        relationshipType: ''
      })
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Create New Audience</DialogTitle>
          <DialogDescription>
            Create a new audience group to organize your contacts based on shared characteristics.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Audience Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Audience Name *</Label>
            <Input
              id="name"
              placeholder="e.g., Local Doctors, Tech Executives"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe this audience group and how you plan to engage with them..."
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
            />
          </div>

          {/* Occupation and Relationship Type in two columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="occupation">Primary Occupation</Label>
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
              <Label htmlFor="relationshipType">Relationship Type</Label>
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
            <Label htmlFor="characteristics">Key Characteristics</Label>
            <Textarea
              id="characteristics"
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
              {isSubmitting ? 'Creating...' : 'Create Audience'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
