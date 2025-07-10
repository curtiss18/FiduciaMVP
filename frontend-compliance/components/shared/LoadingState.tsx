import { Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

interface LoadingStateProps {
  message?: string
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 text-blue-500">
            <Loader2 className="h-12 w-12 animate-spin" />
          </div>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-gray-600">{message}</p>
        </CardContent>
      </Card>
    </div>
  )
}
