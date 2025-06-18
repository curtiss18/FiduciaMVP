'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/layout'
import { Settings, User, Bell, Link as LinkIcon, Shield } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader 
        title="Settings"
      />

      {/* Content Area */}
      <div className="flex-1 p-6 space-y-6">
        {/* Profile Settings */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="h-5 w-5" />
            <h2 className="text-lg font-medium">Profile Settings</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Name</label>
              <input
                type="text"
                value="Demo Advisor"
                className="w-full max-w-md px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Firm</label>
              <input
                type="text"
                value="Fiducia Financial"
                className="w-full max-w-md px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <Button>Save Changes</Button>
          </div>
        </Card>

        {/* Notification Settings */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Bell className="h-5 w-5" />
            <h2 className="text-lg font-medium">Notifications</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Content Review Updates</p>
                <p className="text-sm text-muted-foreground">Get notified when compliance reviews are complete</p>
              </div>
              <input type="checkbox" defaultChecked className="rounded" />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Warren Tips</p>
                <p className="text-sm text-muted-foreground">Receive helpful tips for better content generation</p>
              </div>
              <input type="checkbox" defaultChecked className="rounded" />
            </div>
          </div>
        </Card>

        {/* Channel Integrations */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <LinkIcon className="h-5 w-5" />
            <h2 className="text-lg font-medium">Channel Integrations</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white text-sm">
                  Li
                </div>
                <div>
                  <p className="font-medium">LinkedIn</p>
                  <p className="text-sm text-muted-foreground">Not connected</p>
                </div>
              </div>
              <Button variant="outline">Connect</Button>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-black rounded flex items-center justify-center text-white text-sm">
                  X
                </div>
                <div>
                  <p className="font-medium">Twitter/X</p>
                  <p className="text-sm text-muted-foreground">Not connected</p>
                </div>
              </div>
              <Button variant="outline">Connect</Button>
            </div>
          </div>
        </Card>

        {/* Compliance Settings */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="h-5 w-5" />
            <h2 className="text-lg font-medium">Compliance Preferences</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Default Content Review Level</label>
              <select className="w-full max-w-md px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring">
                <option>Standard Review</option>
                <option>Enhanced Review</option>
                <option>Express Review</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Auto-submit for Review</p>
                <p className="text-sm text-muted-foreground">Automatically submit content when saved</p>
              </div>
              <input type="checkbox" className="rounded" />
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}