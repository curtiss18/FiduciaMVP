import { AdvisorInfo, ReviewInfo } from '@/lib/types'
import { formatDate, formatRelativeTime, getPriorityColor } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { User, Building, Phone, Mail, Clock, AlertCircle } from 'lucide-react'

interface AdvisorInfoProps {
  advisor: AdvisorInfo
  review: ReviewInfo
}

export function AdvisorInfo({ advisor, review }: AdvisorInfoProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          Advisor Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Advisor Details */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-gray-500" />
            <span className="font-medium">{advisor.name}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Building className="h-4 w-4 text-gray-500" />
            <span>{advisor.firm}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-gray-500" />
            <a 
              href={`mailto:${advisor.email}`}
              className="text-blue-600 hover:text-blue-800"
            >
              {advisor.email}
            </a>
          </div>
          
          {advisor.phone && (
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-gray-500" />
              <a 
                href={`tel:${advisor.phone}`}
                className="text-blue-600 hover:text-blue-800"
              >
                {advisor.phone}
              </a>
            </div>
          )}
        </div>

        {/* Review Status */}
        <div className="pt-4 border-t space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-700">Status:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              review.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
              review.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {review.status.replace('_', ' ')}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-700">Priority:</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(review.priority)}`}>
              {review.priority}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-700">Submitted:</span>
            <span className="text-sm text-gray-900">
              {formatRelativeTime(review.submittedAt)}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-700">Est. Review Time:</span>
            <span className="text-sm text-gray-900">
              {review.estimatedReviewTime} minutes
            </span>
          </div>

          {review.deadline && (
            <div className="flex items-center gap-2 text-orange-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">
                Deadline: {formatDate(review.deadline)}
              </span>
            </div>
          )}
        </div>

        {/* Specialties */}
        {advisor.specialties && advisor.specialties.length > 0 && (
          <div className="pt-4 border-t">
            <span className="font-medium text-gray-700 block mb-2">Specialties:</span>
            <div className="flex flex-wrap gap-2">
              {advisor.specialties.map((specialty, index) => (
                <span 
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                >
                  {specialty}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
