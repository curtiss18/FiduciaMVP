# Advisor Portal - Next Session Tasks

**Current Status**: Phase 1 Complete - Split-screen chat interface with delimiter system ready

## 🎯 **Immediate Next Steps**

### **1. Content Extraction Implementation** (Priority 1)
**File**: `frontend-advisor/components/chat/ChatInterface.tsx`

```typescript
// Add this function to ChatInterface.tsx
function parseWarrenResponse(response: string): ExtractedContent {
  const delimiter = '##MARKETINGCONTENT##';
  const startIndex = response.indexOf(delimiter);
  const endIndex = response.lastIndexOf(delimiter);
  
  if (startIndex !== -1 && endIndex !== -1 && startIndex !== endIndex) {
    const marketingContent = response.substring(
      startIndex + delimiter.length, 
      endIndex
    ).trim();
    
    // Extract title (first line)
    const lines = marketingContent.split('\n').filter(line => line.trim());
    const title = lines[0]?.trim() || 'Generated Content';
    
    return {
      marketingContent,
      conversationalResponse: response,
      hasMarketingContent: true,
      title
    };
  }
  
  return {
    marketingContent: null,
    conversationalResponse: response,
    hasMarketingContent: false
  };
}
```

### **2. Update Content Detection Logic**
**Replace**: The old `isGeneratedContent()` heuristic  
**With**: Delimiter-based detection using `parseWarrenResponse()`

### **3. Content Preview Integration**
**Update**: The `sendMessageToWarren()` function to:
- Parse Warren's response for delimited content
- Set `generatedContent` state when content is found
- Populate the right panel with extracted content

### **4. Test Warren's New Behavior**
**Verify**: Warren uses `##MARKETINGCONTENT##` delimiters consistently
**Test Message**: "Create a LinkedIn post about retirement planning"
**Expected**: Content appears in right panel, separated from conversation

## 🔧 **Quick Implementation Guide**

### **Step 1**: Add ExtractedContent interface to `lib/types.ts`
### **Step 2**: Implement `parseWarrenResponse()` function 
### **Step 3**: Update Warren response handling in `sendMessageToWarren()`
### **Step 4**: Test end-to-end content extraction and preview

## 📋 **Files to Modify**
- `lib/types.ts` - Add ExtractedContent interface
- `components/chat/ChatInterface.tsx` - Add parsing logic
- Test the delimiter system with Warren

## 🎯 **Success Criteria**
- [ ] Warren responses parsed for `##MARKETINGCONTENT##` delimiters
- [ ] Extracted content appears in right panel preview
- [ ] Chat conversation continues normally on left
- [ ] Content extraction works reliably with Warren's new prompt format

---

**Ready to implement content extraction and complete the split-screen functionality!**
