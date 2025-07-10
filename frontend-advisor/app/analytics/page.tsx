'use client'

import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout'
import { BarChart3, TrendingUp, Users, FileText } from 'lucide-react'

export default function AnalyticsPage() {
  // For now, we'll simulate empty analytics. In the future, this will come from API
  const hasData = false

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader 
        title="Analytics"
      />

      {/* Content Area */}
      {hasData ? (
        // Analytics dashboard will go here when we have data
        <div className="flex-1 p-6 space-y-6">
          {/* Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Content</p>
                  <p className="text-2xl font-semibold">24</p>
                </div>
                <FileText className="h-8 w-8 text-muted-foreground" />
              </div>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Approved</p>
                  <p className="text-2xl font-semibold">18</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Warren Sessions</p>
                  <p className="text-2xl font-semibold">12</p>
                </div>
                <Users className="h-8 w-8 text-blue-500" />
              </div>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">This Month</p>
                  <p className="text-2xl font-semibold">8</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-500" />
              </div>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-medium mb-4">Content Performance</h3>
              <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                <p className="text-muted-foreground">Chart placeholder</p>
              </div>
            </Card>
            
            <Card className="p-6">
              <h3 className="text-lg font-medium mb-4">Compliance Trends</h3>
              <div className="h-64 bg-muted rounded-lg flex items-center justify-center">
                <p className="text-muted-foreground">Chart placeholder</p>
              </div>
            </Card>
          </div>
        </div>
      ) : (
        // Empty state
        <div className="flex-1 p-6">
          <div className="flex justify-center pt-16">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-6">
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
              <h2 className="text-xl font-semibold mb-3">
                Your content analytics will appear here
              </h2>
              <p className="text-muted-foreground text-sm leading-relaxed mb-6">
                Start creating and distributing content with Warren to see performance insights, compliance metrics, and engagement data.
              </p>
              <Link href="/chat">
                <Button>
                  Create Content to See Analytics
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}