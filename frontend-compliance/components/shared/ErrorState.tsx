import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface ErrorStateProps {
  title?: string
  message: string
  showRetry?: boolean
  onRetry?: () => void
}

export function ErrorState({ 
  title = "Error", 
  message, 
  showRetry = false, 
  onRetry 
}: ErrorStateProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 text-red-500">
            <AlertCircle className="h-12 w-12" />
          </div>
          <CardTitle className="text-red-900">{title}</CardTitle>
          <CardDescription className="text-red-600">
            {message}
          </CardDescription>
        </CardHeader>
        {showRetry && onRetry && (
          <CardContent className="text-center">
            <Button 
              onClick={onRetry}
              variant="outline"
              className="inline-flex items-center"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </CardContent>
        )}
      </Card>
    </div>
  )
}
