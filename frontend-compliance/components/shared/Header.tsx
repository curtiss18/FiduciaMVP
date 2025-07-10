import { Shield } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-blue-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">
              Fiducia Compliance Portal
            </span>
          </div>
          <div className="text-sm text-gray-500">
            Content Review Interface
          </div>
        </div>
      </div>
    </header>
  )
}
