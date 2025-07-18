'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  Database,
  CheckCircle,
  FileText,
  AlertCircle
} from 'lucide-react'

interface ContentStats {
  total_content: number
  vectorized_content: number
  vectorization_percentage: number
  content_by_type: Record<string, number>
  content_by_source: Record<string, number>
  content_by_approval: Record<string, number>
}

interface ContentStatsCardsProps {
  stats: ContentStats | null
  contentLength: number
}

export default function ContentStatsCards({ stats, contentLength }: ContentStatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <Card className="border border-border bg-card hover:bg-accent/50 transition-colors">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center text-foreground">
            <Database className="w-5 h-5 mr-2 text-muted-foreground" />
            Total Content
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-foreground">{stats?.total_content || contentLength}</div>
          <p className="text-muted-foreground text-sm">All content pieces</p>
        </CardContent>
      </Card>

      <Card className="border border-border bg-card hover:bg-accent/50 transition-colors">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center text-foreground">
            <CheckCircle className="w-5 h-5 mr-2 text-green-600 dark:text-green-400" />
            Vectorized
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-foreground">
            {stats?.vectorized_content || 0}
          </div>
          <p className="text-muted-foreground text-sm">
            {stats?.vectorization_percentage || 0}% coverage
          </p>
        </CardContent>
      </Card>

      <Card className="border border-border bg-card hover:bg-accent/50 transition-colors">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center text-foreground">
            <FileText className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
            Approved
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-foreground">
            {stats?.content_by_approval?.approved || 0}
          </div>
          <p className="text-muted-foreground text-sm">Ready to use</p>
        </CardContent>
      </Card>

      <Card className="border border-border bg-card hover:bg-accent/50 transition-colors">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center text-foreground">
            <AlertCircle className="w-5 h-5 mr-2 text-orange-600 dark:text-orange-400" />
            Pending
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-foreground">
            {stats?.content_by_approval?.pending || 0}
          </div>
          <p className="text-muted-foreground text-sm">Awaiting review</p>
        </CardContent>
      </Card>
    </div>
  )
}