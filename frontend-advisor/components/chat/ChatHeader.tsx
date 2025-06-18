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
    <div className="border-b bg-background px-4 lg:px-6 h-[73px] flex items-center">
      <div className="flex items-center justify-between w-full">
        {/* Main Header Content - Add left padding on mobile for menu button */}
        <div className="flex items-center gap-3 pl-12 lg:pl-0">
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white font-semibold text-sm">W</span>
          </div>
          <div>
            <h1 className="font-semibold text-lg">Warren AI</h1>
            <p className="text-sm text-muted-foreground hidden sm:block">
              Compliance-focused content assistant
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground mr-4">
            <User className="h-4 w-4" />
            <span>{advisorName}</span>
          </div>
          
          <div className="hidden lg:block">
            <ThemeToggle 
              ButtonComponent={Button}
              icons={{ Sun, Moon, Monitor }}
            />
          </div>
          
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          
          <Button variant="ghost" size="sm" className="hidden sm:flex">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
