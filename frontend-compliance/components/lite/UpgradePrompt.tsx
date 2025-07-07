import { UpgradeInfo } from '@/lib/types'
import { ArrowRight, Star, Zap, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface UpgradePromptProps {
  upgradeInfo: UpgradeInfo
}

export function UpgradePrompt({ upgradeInfo }: UpgradePromptProps) {
  if (!upgradeInfo.showPrompt) return null

  return (
    <div className="fixed bottom-6 right-6 max-w-sm z-50">
      <Card className="upgrade-prompt shadow-lg">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-blue-900">
            <Star className="h-5 w-5" />
            Upgrade to Full Version
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-blue-800">
            Manage multiple advisors with advanced analytics and AI assistance
          </p>
          
          <div className="space-y-2">
            {upgradeInfo.benefits.slice(0, 3).map((benefit, index) => (
              <div key={index} className="flex items-center gap-2 text-sm text-blue-700">
                {index === 0 && <Zap className="h-4 w-4" />}
                {index === 1 && <TrendingUp className="h-4 w-4" />}
                {index === 2 && <Star className="h-4 w-4" />}
                <span>{benefit}</span>
              </div>
            ))}
          </div>

          {upgradeInfo.trialInfo.available && (
            <div className="bg-blue-100 rounded-lg p-3">
              <p className="text-sm font-medium text-blue-900">
                {upgradeInfo.trialInfo.durationDays}-Day Free Trial
              </p>
              <p className="text-xs text-blue-700">
                Full features included, no credit card required
              </p>
            </div>
          )}

          <Button 
            className="w-full bg-blue-600 hover:bg-blue-700"
            onClick={() => window.open(upgradeInfo.pricingUrl, '_blank')}
          >
            Start Free Trial
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>

          <button
            className="text-xs text-blue-600 hover:text-blue-800 w-full text-center"
            onClick={() => {
              const prompt = document.querySelector('.upgrade-prompt')?.closest('.fixed')
              if (prompt) prompt.style.display = 'none'
            }}
          >
            Maybe later
          </button>
        </CardContent>
      </Card>
    </div>
  )
}
