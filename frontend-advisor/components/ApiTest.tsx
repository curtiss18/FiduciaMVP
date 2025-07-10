'use client'

import React, { useState } from 'react'
import { advisorApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export const ApiTest: React.FC = () => {
  const [testResults, setTestResults] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const addResult = (message: string) => {
    setTestResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`])
  }

  const runApiTest = async () => {
    setIsLoading(true)
    setTestResults([])
    addResult('🧪 Starting API connectivity test...')

    try {
      // Test 1: Create a session
      addResult('📋 Creating session...')
      const sessionResponse = await advisorApi.createSession('demo_advisor_001', 'Frontend Integration Test')
      addResult(`✅ Session created: ${sessionResponse.session.session_id}`)
      
      // Test 2: Save a message
      addResult('💬 Saving message...')
      const messageResponse = await advisorApi.saveMessage(
        sessionResponse.session.session_id,
        'user',
        'Test message from frontend API client'
      )
      addResult(`✅ Message saved: ${messageResponse.message.id}`)
      
      // Test 3: Get session messages
      addResult('📨 Retrieving messages...')
      const messagesResponse = await advisorApi.getSessionMessages(
        sessionResponse.session.session_id,
        'demo_advisor_001'
      )
      addResult(`✅ Retrieved ${messagesResponse.messages.length} messages`)
      
      addResult('🎉 API integration working perfectly!')
      
    } catch (error: any) {
      addResult(`❌ API test failed: ${error.message}`)
      console.error('API test error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>API Connectivity Test</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button 
          onClick={runApiTest} 
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Testing...' : 'Run API Test'}
        </Button>
        
        {testResults.length > 0 && (
          <div className="bg-muted p-4 rounded-lg max-h-64 overflow-y-auto">
            <h4 className="font-semibold mb-2">Test Results:</h4>
            {testResults.map((result, index) => (
              <div key={index} className="text-sm font-mono mb-1">
                {result}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
