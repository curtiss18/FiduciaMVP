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
  by_type: Record<string, number>
  by_status: Record<string, number>
  vectorization_stats: {
    vectorized: number
    total: number
    percentage: number
  }
}

interface ContentStatsCardsProps {
  stats: ContentStats | null
  contentLength: number
}

export default function ContentStatsCards({ stats, contentLength }: ContentStatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <Database className="w-5 h-5 mr-2" />
            Total Content
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{stats?.total_content || contentLength}</div>
          <p className="text-blue-100 text-sm">All content pieces</p>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-lg bg-gradient-to-br from-green-500 to-green-600 text-white">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Vectorized
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">
            {stats?.vectorization_stats?.vectorized || 0}
          </div>
          <p className="text-green-100 text-sm">
            {stats?.vectorization_stats?.percentage || 0}% coverage
          </p>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Approved
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">
            {stats?.by_status?.approved || 0}
          </div>
          <p className="text-purple-100 text-sm">Ready to use</p>
        </CardContent>
      </Card>

      <Card className="border-0 shadow-lg bg-gradient-to-br from-orange-500 to-orange-600 text-white">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            Pending
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">
            {stats?.by_status?.pending || 0}
          </div>
          <p className="text-orange-100 text-sm">Awaiting review</p>
        </CardContent>
      </Card>
    </div>
  )
}