'use client'

import React, { useState } from 'react'
import { advisorApi, systemApi } from '@/lib/api'

export default function DocumentUploadTestPage() {
  const [results, setResults] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState<Record<string, boolean>>({})

  const updateResult = (testName: string, result: string, isError: boolean = false) => {
    setResults(prev => ({ ...prev, [testName]: result }))
    setLoading(prev => ({ ...prev, [testName]: false }))
  }

  const startTest = (testName: string) => {
    setLoading(prev => ({ ...prev, [testName]: true }))
    setResults(prev => ({ ...prev, [testName]: 'Running...' }))
  }

  const testTypeScript = () => {
    startTest('typescript')
    updateResult('typescript', 
      'Testing TypeScript compilation...\n\nPlease run in terminal:\ncd frontend-advisor\nnpm run type-check\n\nOr:\nnpx tsc --noEmit\n\nExpected: No errors related to document upload types'
    )
  }

  const testApiImports = () => {
    startTest('imports')
    try {
      let result = 'Testing API imports...\n'
      
      result += '✅ advisorApi imported successfully\n'
      
      if (typeof advisorApi.uploadDocuments === 'function') {
        result += '✅ uploadDocuments method exists\n'
      } else {
        result += '❌ uploadDocuments method missing\n'
      }
      
      if (typeof advisorApi.getSessionDocuments === 'function') {
        result += '✅ getSessionDocuments method exists\n'
      } else {
        result += '❌ getSessionDocuments method missing\n'
      }
      
      updateResult('imports', result)
    } catch (error) {
      updateResult('imports', '❌ Import failed: ' + (error as Error).message, true)
    }
  }

  const testFileUpload = async () => {
    startTest('upload')
    try {
      const fileInput = document.getElementById('fileInput') as HTMLInputElement
      const sessionIdInput = document.getElementById('sessionId') as HTMLInputElement
      const titlesInput = document.getElementById('titles') as HTMLInputElement
      
      if (!fileInput.files || fileInput.files.length === 0) {
        throw new Error('Please select at least one file')
      }
      
      if (!sessionIdInput.value) {
        throw new Error('Please provide a session ID')
      }
      
      const files = Array.from(fileInput.files)
      const titles = titlesInput.value ? titlesInput.value.split(',').map(t => t.trim()) : undefined
      
      let result = `Uploading ${files.length} file(s) to session: ${sessionIdInput.value}\n`
      if (titles) {
        result += `Custom titles: ${titles.join(', ')}\n`
      }
      
      const response = await advisorApi.uploadDocuments(sessionIdInput.value, files, titles)
      
      result += '\n✅ Upload completed!\n\n'
      result += 'Response:\n'
      result += JSON.stringify(response, null, 2)
      
      updateResult('upload', result)
    } catch (error: any) {
      let errorResult = '\n❌ Upload failed: ' + error.message
      if (error.response) {
        errorResult += '\n\nServer response:\n'
        errorResult += JSON.stringify(error.response.data, null, 2)
      }
      updateResult('upload', errorResult, true)
    }
  }

  const testSessionDocuments = async () => {
    startTest('retrieve')
    try {
      const sessionIdInput = document.getElementById('retrieveSessionId') as HTMLInputElement
      
      if (!sessionIdInput.value) {
        throw new Error('Please provide a session ID')
      }
      
      let result = 'Retrieving session documents...\n'
      
      const response = await advisorApi.getSessionDocuments(sessionIdInput.value)
      
      result += '\n✅ Retrieval completed!\n\n'
      result += 'Response:\n'
      result += JSON.stringify(response, null, 2)
      
      updateResult('retrieve', result)
    } catch (error: any) {
      let errorResult = '\n❌ Retrieval failed: ' + error.message
      if (error.response) {
        errorResult += '\n\nServer response:\n'
        errorResult += JSON.stringify(error.response.data, null, 2)
      }
      updateResult('retrieve', errorResult, true)
    }
  }

  const testBackendHealth = async () => {
    startTest('health')
    try {
      let result = 'Checking backend health...\n'
      
      const response = await systemApi.getHealth()
      
      result += '✅ Backend is healthy!\n\n'
      result += 'Response:\n'
      result += JSON.stringify(response.data, null, 2)
      
      // Test document endpoint specifically
      result += '\n\nTesting document upload endpoint accessibility...\n'
      const testResponse = await fetch('http://localhost:8000/api/v1/advisor/documents/upload-file', {
        method: 'OPTIONS'
      })
      
      if (testResponse.ok) {
        result += '✅ Document upload endpoint accessible\n'
      } else {
        result += '❌ Document upload endpoint not accessible\n'
      }
      
      updateResult('health', result)
    } catch (error: any) {
      updateResult('health', '\n❌ Backend health check failed: ' + error.message, true)
    }
  }

  const ResultBox = ({ testName, title }: { testName: string, title: string }) => (
    <div className={`mt-2 p-3 rounded border text-xs font-mono whitespace-pre-wrap ${
      results[testName]?.includes('❌') ? 'bg-red-50 text-red-800 border-red-200' :
      results[testName]?.includes('✅') ? 'bg-green-50 text-green-800 border-green-200' :
      'bg-gray-50 text-gray-800 border-gray-200'
    }`}>
      {results[testName] || 'Click button to run test'}
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white p-8 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold mb-2">🧪 Document Upload API Test - SCRUM-46</h1>
        <p className="text-gray-600 mb-6"><strong>Purpose:</strong> Test the newly implemented document upload API methods</p>
        
        <div className="space-y-6">
          {/* TypeScript Test */}
          <div className="border rounded-lg p-6 bg-gray-50">
            <h3 className="text-xl font-semibold mb-2">1. TypeScript Compilation Test</h3>
            <p className="text-gray-600 mb-4">First, check that TypeScript compiles without errors:</p>
            <button 
              onClick={testTypeScript}
              disabled={loading.typescript}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded"
            >
              {loading.typescript ? 'Testing...' : 'Test TypeScript Compilation'}
            </button>
            <ResultBox testName="typescript" title="TypeScript Results" />
          </div>

          {/* API Import Test */}
          <div className="border rounded-lg p-6 bg-gray-50">
            <h3 className="text-xl font-semibold mb-2">2. API Import Test</h3>
            <p className="text-gray-600 mb-4">Test that the new API methods are properly imported:</p>
            <button 
              onClick={testApiImports}
              disabled={loading.imports}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded"
            >
              {loading.imports ? 'Testing...' : 'Test API Imports'}
            </button>
            <ResultBox testName="imports" title="Import Results" />
          </div>

          {/* File Upload Test */}
          <div className="border rounded-lg p-6 bg-gray-50">
            <h3 className="text-xl font-semibold mb-2">3. Multi-File Upload Test</h3>
            <p className="text-gray-600 mb-4">Test actual file upload with multiple files:</p>
            <div className="space-y-2 mb-4">
              <input 
                type="file" 
                id="fileInput" 
                multiple 
                accept=".pdf,.docx,.txt"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <input 
                type="text" 
                id="sessionId" 
                placeholder="Session ID (e.g., test_session_123)" 
                defaultValue="test_session_123"
                className="w-full p-2 border border-gray-300 rounded"
              />
              <input 
                type="text" 
                id="titles" 
                placeholder="File titles (comma-separated, optional)"
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>
            <button 
              onClick={testFileUpload}
              disabled={loading.upload}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded"
            >
              {loading.upload ? 'Uploading...' : 'Upload Files'}
            </button>
            <ResultBox testName="upload" title="Upload Results" />
          </div>

          {/* Session Documents Test */}
          <div className="border rounded-lg p-6 bg-gray-50">
            <h3 className="text-xl font-semibold mb-2">4. Session Documents Retrieval Test</h3>
            <p className="text-gray-600 mb-4">Test retrieving documents for a session:</p>
            <input 
              type="text" 
              id="retrieveSessionId" 
              placeholder="Session ID" 
              defaultValue="test_session_123"
              className="w-full p-2 border border-gray-300 rounded mb-4"
            />
            <button 
              onClick={testSessionDocuments}
              disabled={loading.retrieve}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded"
            >
              {loading.retrieve ? 'Retrieving...' : 'Get Session Documents'}
            </button>
            <ResultBox testName="retrieve" title="Retrieve Results" />
          </div>

          {/* Backend Health Test */}
          <div className="border rounded-lg p-6 bg-gray-50">
            <h3 className="text-xl font-semibold mb-2">5. Backend Health Check</h3>
            <p className="text-gray-600 mb-4">Verify backend is running and endpoints are accessible:</p>
            <button 
              onClick={testBackendHealth}
              disabled={loading.health}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-4 py-2 rounded"
            >
              {loading.health ? 'Checking...' : 'Check Backend Health'}
            </button>
            <ResultBox testName="health" title="Health Results" />
          </div>
        </div>
      </div>
    </div>
  )
}