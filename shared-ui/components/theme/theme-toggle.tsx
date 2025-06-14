'use client'

import * as React from 'react'
import { useTheme } from './theme-provider'

// Simple theme toggle without external dependencies
export function ThemeToggle({ 
  ButtonComponent, 
  className,
  icons 
}: { 
  ButtonComponent?: React.ComponentType<any>
  className?: string
  icons?: {
    Sun: React.ComponentType<any>
    Moon: React.ComponentType<any>
    Monitor: React.ComponentType<any>
  }
}) {
  const { theme, setTheme } = useTheme()

  const toggleTheme = () => {
    if (theme === 'light') {
      setTheme('dark')
    } else if (theme === 'dark') {
      setTheme('system')
    } else {
      setTheme('light')
    }
  }

  const getIcon = () => {
    if (!icons) {
      // Fallback text when no icons provided
      switch (theme) {
        case 'light': return '☀️'
        case 'dark': return '🌙'
        case 'system': return '💻'
        default: return '💻'
      }
    }

    const { Sun, Moon, Monitor } = icons
    switch (theme) {
      case 'light':
        return <Sun className="h-4 w-4" />
      case 'dark':
        return <Moon className="h-4 w-4" />
      case 'system':
        return <Monitor className="h-4 w-4" />
      default:
        return <Monitor className="h-4 w-4" />
    }
  }

  const getTooltip = () => {
    switch (theme) {
      case 'light':
        return 'Switch to dark mode'
      case 'dark':
        return 'Switch to system preference'
      case 'system':
        return 'Switch to light mode'
      default:
        return 'Toggle theme'
    }
  }

  // If ButtonComponent is provided, use it
  if (ButtonComponent) {
    return (
      <ButtonComponent
        variant="ghost"
        size="sm"
        onClick={toggleTheme}
        className={`h-9 w-9 p-0 transition-all duration-200 hover:bg-accent ${className || ''}`}
      >
        {getIcon()}
      </ButtonComponent>
    )
  }

  // Fallback basic button
  return (
    <button
      onClick={toggleTheme}
      className={`h-9 w-9 p-0 transition-all duration-200 hover:bg-accent rounded-md inline-flex items-center justify-center ${className || ''}`}
      title={getTooltip()}
    >
      <span className="sr-only">{getTooltip()}</span>
      {getIcon()}
    </button>
  )
}