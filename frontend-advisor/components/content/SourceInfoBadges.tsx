import React from 'react'
import { SourceInformation } from '@/lib/types'
import { cn } from '@/lib/utils'

interface SourceInfoBadgesProps {
  sourceInfo: SourceInformation
  className?: string
}

export const SourceInfoBadges: React.FC<SourceInfoBadgesProps> = ({ 
  sourceInfo, 
  className 
}) => {
  // Badge styling based on search strategy and fallback status
  const getSearchStrategyBadge = () => {
    if (sourceInfo.fallbackUsed) {
      return {
        color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
        label: 'FALLBACK'
      }
    }
    
    switch (sourceInfo.searchStrategy) {
      case 'vector':
        return {
          color: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
          label: 'VECTOR'
        }
      case 'hybrid':
        return {
          color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
          label: 'HYBRID'
        }
      case 'text':
        return {
          color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
          label: 'TEXT'
        }
      default:
        return {
          color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
          label: 'SEARCH'
        }
    }
  }

  // Source count badge styling based on total sources
  const getSourceCountBadge = () => {
    const { totalSources } = sourceInfo
    
    if (totalSources >= 5) {
      return {
        color: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-400',
        icon: '📚'
      }
    }
    if (totalSources >= 3) {
      return {
        color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
        icon: '📖'
      }
    }
    if (totalSources >= 1) {
      return {
        color: 'bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400',
        icon: '📄'
      }
    }
    return {
      color: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      icon: '❓'
    }
  }

  const searchBadge = getSearchStrategyBadge()
  const sourceBadge = getSourceCountBadge()

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Total Sources Badge */}
      <div className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
        sourceBadge.color
      )}>
        <span>{sourceBadge.icon}</span>
        <span>{sourceInfo.totalSources} sources</span>
      </div>

      {/* Source Breakdown Badges - Only show if we have detailed breakdown */}
      {(sourceInfo.marketingExamples > 0 || sourceInfo.complianceRules > 0) && (
        <>
          {sourceInfo.marketingExamples > 0 && (
            <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400">
              <span>💼</span>
              <span>{sourceInfo.marketingExamples} examples</span>
            </div>
          )}
          
          {sourceInfo.complianceRules > 0 && (
            <div className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400">
              <span>🛡️</span>
              <span>{sourceInfo.complianceRules} rules</span>
            </div>
          )}
        </>
      )}

      {/* Search Strategy Badge */}
      <div className={cn(
        'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
        searchBadge.color
      )}>
        {searchBadge.label}
      </div>
    </div>
  )
}
