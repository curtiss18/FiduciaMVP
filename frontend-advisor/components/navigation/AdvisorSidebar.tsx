'use client'

import React, { useState, useEffect } from 'react'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import { ThemeToggle } from '../../../shared-ui/components/theme'
import { Button } from '@/components/ui/button'
import { 
  MessageSquare, 
  Library, 
  BarChart3, 
  Settings, 
  Menu, 
  X,
  ChevronLeft,
  ChevronRight,
  User
} from 'lucide-react'

export interface NavigationItem {
  id: string
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string | number
}

const navigationItems: NavigationItem[] = [
  {
    id: 'chat',
    label: 'Warren',
    href: '/chat',
    icon: MessageSquare
  },
  {
    id: 'library',
    label: 'Library',
    href: '/library',
    icon: Library
  },
  {
    id: 'analytics',
    label: 'Analytics',
    href: '/analytics',
    icon: BarChart3
  },
  {
    id: 'settings',
    label: 'Settings',
    href: '/settings',
    icon: Settings
  }
]

interface AdvisorSidebarProps {
  className?: string
}

export const AdvisorSidebar: React.FC<AdvisorSidebarProps> = ({ className }) => {
  const pathname = usePathname()
  const [isExpanded, setIsExpanded] = useState(true)
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  // Load saved sidebar state
  useEffect(() => {
    const savedState = localStorage.getItem('advisor-sidebar-expanded')
    if (savedState !== null) {
      setIsExpanded(JSON.parse(savedState))
    }
  }, [])

  // Save sidebar state
  const toggleExpanded = () => {
    const newState = !isExpanded
    setIsExpanded(newState)
    localStorage.setItem('advisor-sidebar-expanded', JSON.stringify(newState))
  }

  // Close mobile sidebar when route changes
  useEffect(() => {
    setIsMobileOpen(false)
  }, [pathname])

  // Hardcoded advisor profile for MVP
  const advisorProfile = {
    name: 'Demo Advisor',
    firm: 'Fiducia Financial',
    initials: 'DA'
  }

  const SidebarContent = ({ isMobile = false }: { isMobile?: boolean }) => (
    <>
      {/* Header */}
      <div className="flex items-center justify-between px-4 border-b border-border h-[73px]">
        {(isExpanded || isMobile) ? (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0">
              {advisorProfile.initials}
            </div>
            <div>
              <div className="text-sm font-medium">{advisorProfile.name}</div>
              <div className="text-xs text-muted-foreground">{advisorProfile.firm}</div>
            </div>
          </div>
        ) : (
          <div className="w-full flex justify-center">
            <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
              {advisorProfile.initials}
            </div>
          </div>
        )}
        
        {/* Desktop expand/collapse toggle */}
        {!isMobile && (
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleExpanded}
            className="h-8 w-8 p-0"
          >
            {isExpanded ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        )}

        {/* Mobile close button */}
        {isMobile && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMobileOpen(false)}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || 
                          (item.href !== '/chat' && pathname.startsWith(item.href))
          
          if (isMobile) {
            // Mobile navigation - always show text, handle navigation properly
            return (
              <Link
                key={item.id}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                  "hover:bg-accent hover:text-accent-foreground",
                  isActive && "bg-primary text-primary-foreground hover:bg-primary/90"
                )}
                onClick={() => setIsMobileOpen(false)} // Close mobile menu on navigation
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-auto bg-muted text-muted-foreground px-2 py-0.5 rounded-full text-xs">
                    {item.badge}
                  </span>
                )}
              </Link>
            )
          }

          // Desktop navigation - responsive to expanded state
          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                "hover:bg-accent hover:text-accent-foreground",
                isActive && "bg-primary text-primary-foreground hover:bg-primary/90",
                !isExpanded && "justify-center"
              )}
              title={!isExpanded ? item.label : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {isExpanded && (
                <>
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="ml-auto bg-muted text-muted-foreground px-2 py-0.5 rounded-full text-xs">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className={cn(
          "flex items-center gap-3",
          !isExpanded && !isMobile && "justify-center"
        )}>
          <ThemeToggle 
            ButtonComponent={Button}
            icons={{
              Sun: () => <span>☀️</span>,
              Moon: () => <span>🌙</span>,
              Monitor: () => <span>💻</span>
            }}
          />
          {(isExpanded || isMobile) && (
            <span className="text-sm text-muted-foreground">Theme</span>
          )}
        </div>
      </div>
    </>
  )

  return (
    <>
      {/* Mobile Menu Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 h-10 w-10 p-0 bg-background border border-border shadow-md"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col bg-card border-r border-border transition-all duration-300 ease-in-out",
          isExpanded ? "w-64" : "w-16",
          className
        )}
      >
        <SidebarContent isMobile={false} />
      </aside>

      {/* Mobile Sidebar */}
      <aside
        className={cn(
          "lg:hidden fixed left-0 top-0 z-50 h-full w-64 bg-card border-r border-border transform transition-transform duration-300 ease-in-out",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent isMobile={true} />
      </aside>
    </>
  )
}

// Mobile Menu Hook for pages to trigger sidebar
export const useMobileSidebar = () => {
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  
  return {
    isMobileOpen,
    openMobileSidebar: () => setIsMobileOpen(true),
    closeMobileSidebar: () => setIsMobileOpen(false)
  }
}