import { CheckCircle, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface SuccessStateProps {
  title: string
  message: string
  showUpgrade?: boolean
}

export function SuccessState({ title, message, showUpgrade = false }: SuccessStateProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 text-green-500">
            <CheckCircle className="h-12 w-12" />
          </div>
          <CardTitle className="text-green-900">{title}</CardTitle>
          <CardDescription className="text-green-600">
            {message}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <Button 
            onClick={() => window.close()}
            variant="outline"
          >
            Close Window
          </Button>
          
          {showUpgrade && (
            <div className="pt-4 border-t">
              <p className="text-sm text-gray-600 mb-3">
                Want to manage multiple advisors and get advanced analytics?
              </p>
              <Button className="w-full">
                Upgrade to Full Version
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
