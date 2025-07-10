'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { ThemeToggle } from '../../../shared-ui/components/theme'
import { Button } from '@/components/ui/button'
import { User, Settings, Sun, Moon, Monitor } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ProfileDropdownProps {
  advisorName?: string
  advisorFirm?: string
  advisorInitials?: string
}

export const ProfileDropdown: React.FC<ProfileDropdownProps> = ({
  advisorName = "Demo Advisor",
  advisorFirm = "Fiducia Financial", 
  advisorInitials = "DA"
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Profile Avatar Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        {advisorInitials}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 top-10 w-64 bg-popover border border-border rounded-lg shadow-lg z-50 py-2">
          {/* Profile Info */}
          <div className="px-4 py-3 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                {advisorInitials}
              </div>
              <div>
                <div className="text-sm font-medium">{advisorName}</div>
                <div className="text-xs text-muted-foreground">{advisorFirm}</div>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="py-2">
            {/* Profile/Settings Link */}
            <Link 
              href="/settings"
              className="flex items-center gap-3 px-4 py-2 text-sm hover:bg-accent transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <User className="h-4 w-4" />
              Profile
            </Link>

            {/* Theme Toggle */}
            <div className="flex items-center gap-3 px-4 py-2 text-sm">
              <div className="flex items-center gap-3 w-full">
                <ThemeToggle 
                  ButtonComponent={Button}
                  icons={{ Sun, Moon, Monitor }}
                  className="h-8 w-8"
                />
                <span>Theme</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}