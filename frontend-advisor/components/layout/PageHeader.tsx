'use client'

import React from 'react'
import { ProfileDropdown } from './ProfileDropdown'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: React.ReactNode
  className?: string
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  actions,
  className
}) => {
  return (
    <div className={cn("border-b bg-background px-4 lg:px-6 h-[73px] flex items-center", className)}>
      <div className="flex items-center justify-between w-full">
        {/* Left Side - Title */}
        <div className="flex items-center gap-3 pl-12 lg:pl-0">
          <div>
            <h1 className="font-semibold text-lg">{title}</h1>
            {subtitle && (
              <p className="text-sm text-muted-foreground hidden sm:block">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        
        {/* Right Side - Actions and Profile */}
        <div className="flex items-center gap-3">
          {/* Page-specific actions */}
          {actions}
          
          {/* Profile Dropdown */}
          <ProfileDropdown />
        </div>
      </div>
    </div>
  )
}