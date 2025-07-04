'use client'

import React, { useState } from 'react'
import { advisorApi } from '@/lib/api'

export default function DocumentDebugPage() {
  const [results, setResults] = useState<Record<string, string>>({})
  const [sessionId, setSessionId] = useState('test_session_123')

  const updateResult = (testName: string, result: string) => {
    setResults(prev => ({ ...prev, [testName]: result }))
  }

  const debugSessionDocuments = async () => {
    try {
      updateResult('session_docs', 'Checking session documents...\n')
      
      const response = await advisorApi.getSessionDocuments(sessionId)
      
      let result = `✅ Session Documents Response:\n`
      result += JSON.stringify(response, null, 2)
      
      updateResult('session_docs', result)
    } catch (error: any) {
      updateResult('session_docs', `❌ Error: ${error.message}\n${JSON.stringify(error.response?.data, null, 2)}`)
    }
  }

  const debugBackendLogs = async () => {
    try {
      updateResult('backend_logs', 'Check your backend console for Warren generation logs...\n\nLook for:\n- "📄 Getting session documents for session"\n- "✅ Found X processed documents"\n- "📊 Document context Flow"\n\nIf you don\'t see these logs, the session_id isn\'t reaching Warren correctly.')
    } catch (error) {
      updateResult('backend_logs', `❌ Error: ${error}`)
    }
  }

  const debugWarrenRequest = async () => {
    try {
      updateResult('warren_debug', 'Testing Warren with explicit session_id...\n')
      
      // Test Warren directly with session_id
      const warrenResponse = await fetch('http://localhost:8000/api/v1/warren/generate-v3', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          request: 'Create a LinkedIn post about retirement planning',
          content_type: 'linkedin_post',
          audience_type: 'general_education',
          session_id: sessionId
        })
      })
      
      const data = await warrenResponse.json()
      
      let result = `✅ Warren Response:\n`
      result += `Session Documents Count: ${data.session_documents_count || 'Not present'}\n`
      result += `Session Documents Used: ${JSON.stringify(data.session_documents_used || 'Not present')}\n`
      result += `Session Documents Available: ${data.session_documents_available || 'Not present'}\n\n`
      result += `Full Response:\n${JSON.stringify(data, null, 2)}`
      
      updateResult('warren_debug', result)
    } catch (error: any) {
      updateResult('warren_debug', `❌ Warren Request Failed: ${error.message}`)
    }
  }

  const ResultBox = ({ testName }: { testName: string }) => (
    <div className="mt-2 p-3 rounded border text-xs font-mono whitespace-pre-wrap bg-gray-50 text-gray-800 border-gray-200 max-h-96 overflow-y-auto">
      {results[testName] || 'Click button to run test'}
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white p-8 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold mb-2">🔍 Document Context Debug - SCRUM-51</h1>
        <p className="text-gray-600 mb-6">Debug Warren's document context integration</p>
        
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Session ID to Debug:</label>
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded"
            placeholder="Enter session ID that should have documents"
          />
        </div>
        
        <div className="space-y-6">
          {/* Step 1: Check Session Documents */}
          <div className="border rounded-lg p-6 bg-blue-50">
            <h3 className="text-xl font-semibold mb-2">1. Check Session Documents in Database</h3>
            <p className="text-gray-600 mb-4">Verify documents are actually stored for this session:</p>
            <button 
              onClick={debugSessionDocuments}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            >
              Check Session Documents
            </button>
            <ResultBox testName="session_docs" />
          </div>

          {/* Step 2: Test Warren Direct */}
          <div className="border rounded-lg p-6 bg-green-50">
            <h3 className="text-xl font-semibold mb-2">2. Test Warren Document Context</h3>
            <p className="text-gray-600 mb-4">Send request directly to Warren with session_id:</p>
            <button 
              onClick={debugWarrenRequest}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
            >
              Test Warren with Session ID
            </button>
            <ResultBox testName="warren_debug" />
          </div>

          {/* Step 3: Backend Logs */}
          <div className="border rounded-lg p-6 bg-yellow-50">
            <h3 className="text-xl font-semibold mb-2">3. Check Backend Logs</h3>
            <p className="text-gray-600 mb-4">Monitor backend console for document retrieval logs:</p>
            <button 
              onClick={debugBackendLogs}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
            >
              View Expected Log Messages
            </button>
            <ResultBox testName="backend_logs" />
          </div>

          {/* Debug Instructions */}
          <div className="border rounded-lg p-6 bg-gray-50">
            <h3 className="text-xl font-semibold mb-2">🔍 Debug Checklist</h3>
            <div className="text-sm space-y-2">
              <p><strong>1. Documents Uploaded:</strong> Check if session has documents in database</p>
              <p><strong>2. Warren Integration:</strong> Check if Warren receives session_id parameter</p>
              <p><strong>3. Document Retrieval:</strong> Check if DocumentManager finds documents</p>
              <p><strong>4. Context Assembly:</strong> Check if documents reach AdvancedContextAssembler</p>
              <p><strong>5. Response Metadata:</strong> Check if response includes document information</p>
            </div>
          </div>

          {/* Common Issues */}
          <div className="border rounded-lg p-6 bg-red-50">
            <h3 className="text-xl font-semibold mb-2">❌ Common Issues</h3>
            <div className="text-sm space-y-2">
              <p><strong>No documents found:</strong> Documents not uploaded or session_id mismatch</p>
              <p><strong>Processing status:</strong> Documents not processed or missing summaries</p>
              <p><strong>Session ID:</strong> Warren chat not sending session_id to backend</p>
              <p><strong>Import errors:</strong> DocumentManager not imported correctly</p>
              <p><strong>Database connection:</strong> DocumentManager database queries failing</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}