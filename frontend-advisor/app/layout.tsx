import '../../shared-ui/styles/globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { cn } from '@/lib/utils'
import { ThemeProvider } from '../../shared-ui/components/theme'
import { AdvisorSidebar } from '@/components/navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Warren AI - Advisor Portal',
  description: 'AI-powered compliance content generation for financial advisors',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(
        "min-h-screen bg-background font-sans antialiased",
        inter.className
      )}>
        <ThemeProvider
          defaultTheme="system"
          storageKey="fiducia-advisor-theme"
        >
          <div className="flex min-h-screen">
            <AdvisorSidebar />
            <main className="flex-1 overflow-hidden">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
