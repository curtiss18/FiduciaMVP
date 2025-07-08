import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Fiducia Compliance Portal',
  description: 'Professional content review and compliance management for financial advisors',
  keywords: ['compliance', 'financial advisors', 'content review', 'FINRA', 'SEC'],
  authors: [{ name: 'Fiducia Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} compliance-portal`}>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  )
}
