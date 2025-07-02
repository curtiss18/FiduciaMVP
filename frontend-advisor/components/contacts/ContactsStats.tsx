'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, UserCheck, UserPlus, Building } from 'lucide-react'
import { AudienceStatistics } from '@/lib/types'
import { Skeleton } from '@/components/ui/skeleton'

interface ContactsStatsProps {
  statistics: AudienceStatistics | null
  loading: boolean
}

export const ContactsStats: React.FC<ContactsStatsProps> = ({ statistics, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-[60px] mb-1" />
              <Skeleton className="h-3 w-[120px]" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const stats = [
    {
      title: "Total Contacts",
      value: statistics?.total_contacts || 0,
      icon: Users,
      description: "All contacts in your CRM",
      color: "text-blue-600"
    },
    {
      title: "Total Audiences",
      value: statistics?.total_audiences || 0,
      icon: Building,
      description: "Audience groups created",
      color: "text-green-600"
    },
    {
      title: "Relationships",
      value: statistics?.total_relationships || 0,
      icon: UserCheck,
      description: "Contact-to-audience assignments",
      color: "text-purple-600"
    },
    {
      title: "Avg per Audience",
      value: statistics?.avg_contacts_per_audience || 0,
      icon: UserPlus,
      description: "Average contacts per audience",
      color: "text-orange-600",
      isDecimal: true
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.title} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <Icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stat.isDecimal ? stat.value.toFixed(1) : stat.value}
              </div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}