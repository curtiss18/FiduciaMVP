import React from 'react'
import { Button } from '@/components/ui/button'
import { RefreshCw, Settings, User, Moon, Sun, Monitor } from 'lucide-react'
import { ThemeToggle } from '../../../shared-ui/components/theme'

interface ChatHeaderProps {
  onRefresh?: () => void
  advisorName?: string
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ 
  onRefresh, 
  advisorName = "Advisor" 
}) => {
  return (
    <div className="border-b bg-background px-6 py-4">
      <div className="flex items-center justify-between max-w-4xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
            <span className="text-white font-semibold text-sm">W</span>
          </div>
          <div>
            <h1 className="font-semibold text-lg">Warren AI</h1>
            <p className="text-sm text-muted-foreground">
              Compliance-focused content assistant
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mr-4">
            <User className="h-4 w-4" />
            <span>{advisorName}</span>
          </div>
          
          <ThemeToggle 
            ButtonComponent={Button}
            icons={{ Sun, Moon, Monitor }}
          />
          
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
