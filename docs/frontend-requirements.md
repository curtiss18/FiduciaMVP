# FiduciaMVP Frontend Requirements & Architecture

## 🎯 **Executive Summary**

This document outlines the comprehensive frontend requirements for FiduciaMVP, including two distinct portals: the Advisor Portal (multi-tenant) and the Fiducia Admin Portal. The system is designed to serve the complex financial services industry structure with proper compliance workflows and channel management.

## 🏢 **Industry Structure & User Hierarchy**

### **Financial Services Entity Structure**
```
Registered Investment Advisor (RIA)
├── Compliance Team / CCO
├── Firm A (may be solo or multi-IAR)
│   ├── Investment Advisor Representative (IAR) 1
│   ├── Investment Advisor Representative (IAR) 2
│   └── Investment Advisor Representative (IAR) 3
├── Firm B
│   ├── Investment Advisor Representative (IAR) 4
│   └── Investment Advisor Representative (IAR) 5
└── Firm C (Solo Practice)
    └── Investment Advisor Representative (IAR) 6
```

### **Account Independence Model**
- **Individual Firms/IARs**: Can create independent accounts
- **Compliance Integration**: Automatic invites sent to associated RIA compliance team
- **RIA Management**: RIAs can create accounts to manage multiple firms/IARs
- **Scalable Structure**: Supports solo practices to large RIA networks

## 👥 **User Roles & Permissions**

### **User Role Definitions**

| Role | Description | Permissions | Scope |
|------|-------------|-------------|-------|
| **Fiducia Admin** | Platform administrators | Full system access, content management, user management | Global |
| **RIA Admin** | RIA-level management | Manage associated firms, compliance oversight | RIA-wide |
| **CCO/Compliance** | Compliance officers | Content review, approval, compliance management | RIA/Firm-wide |
| **Firm Admin** | Firm-level management | Manage firm IARs, firm settings | Firm-wide |
| **IAR/Advisor** | End users creating content | Content creation, channel management | Individual |

### **Permission Matrix**

| Action | Fiducia Admin | RIA Admin | CCO/Compliance | Firm Admin | IAR/Advisor |
|--------|---------------|-----------|----------------|------------|-------------|
| Create Content | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit for Approval | ✅ | ✅ | ❌ | ✅ | ✅ |
| Review/Approve Content | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage Vector Search DB | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage Users | ✅ | ✅ (RIA scope) | ❌ | ✅ (Firm scope) | ❌ |
| View Analytics | ✅ | ✅ | ✅ | ✅ | ✅ (own content) |
| Channel Integration | ✅ | ✅ | ❌ | ✅ | ✅ |

## 🔄 **Content Approval Workflow**

### **Detailed Workflow Process**

```
IAR Creates Content
       ↓
Submit to Compliance
       ↓
CCO Reviews Content
       ↓
   Compliance Decision
    ↙     ↓     ↘
Approved  Needs   Major
   ↓     Changes  Issues
Return     ↓       ↓
to IAR   CCO    CCO Uses
  ↓    Suggests Warren for
IAR     Edits   Auto-Adjust
Accepts   ↓       ↓
Content  IAR     CCO Reviews
  ↓     Makes   Adjustments
Schedule Changes    ↓
Distrib.   ↓    Back to
  ↓     Resubmit Decision
Distribute   ↓
to       Submit to
Channels  Compliance
```

### **Workflow Features Required**

#### **Version Control System**
- **Content Versioning**: Track all versions of content pieces
- **Change Tracking**: Highlight differences between versions
- **Rollback Capability**: Ability to revert to previous versions
- **Comment Threading**: Comments tied to specific versions

#### **Collaboration Features**
- **Inline Comments**: CCO can comment on specific parts of content
- **Suggestion Mode**: Track suggested changes vs. approved changes
- **Real-time Notifications**: Status updates for all stakeholders
- **Approval History**: Complete audit trail of approval decisions

#### **Warren Integration for CCO**
- **Auto-Adjustment**: CCO can invoke Warren to fix compliance issues
- **Suggestion Generation**: Warren suggests compliant alternatives
- **Batch Processing**: CCO can process multiple content pieces
- **Compliance Scoring**: Real-time compliance assessment

## 📁 **File Upload & Context Management**

### **Document Upload Strategy**

#### **Supported File Types (Phase 1)**
- **Text Documents**: .txt, .docx, .pdf
- **Spreadsheets**: .xlsx, .csv (for data context)
- **Rich Text**: .rtf, .md

#### **Future File Support (Phase 2+)**
- **Images**: .jpg, .png, .gif (for social media)
- **Video**: .mp4, .mov (for video content creation)
- **Audio**: .mp3, .wav (for podcast/radio content)

#### **Upload Security & Processing**
- **Virus Scanning**: All uploads scanned before processing
- **Content Extraction**: Text extraction for context analysis
- **Size Limits**: Reasonable file size restrictions
- **Storage Management**: Secure cloud storage with retention policies

### **Context vs. Vector Search Separation**

#### **Critical Security Distinction**
```
Advisor Uploaded Content
├── Used for CONTEXT ONLY
├── Provides topic guidance to Warren
├── NEVER used in vector search
├── Cannot be assumed compliant
└── Stored separately from compliance database

Fiducia Compliance Database
├── Used for VECTOR SEARCH
├── Pre-approved compliant content
├── Professional compliance review
├── Safe for content generation
└── Fiducia admin managed only
```

#### **Implementation Requirements**
- **Separate Storage**: Advisor uploads isolated from vector search DB
- **Context Pipeline**: Advisor content → Text extraction → Context for Warren
- **Compliance Pipeline**: Vector search → Approved content only
- **Clear UI Indication**: Users understand content sources in generated material

## 🌐 **Channel Management & Distribution**

### **Channel Integration Strategy**

#### **Phase 1: Manual Distribution**
- **Copy/Paste Interface**: Clean formatting for manual posting
- **Platform Templates**: Pre-formatted for each channel
- **Export Options**: PDF, text, formatted HTML
- **Distribution Tracking**: Manual logging of where content was posted

#### **Phase 2: API Integration**
| Channel | Integration Type | Feasibility | Priority |
|---------|------------------|-------------|----------|
| **LinkedIn** | API Integration | High | High |
| **Twitter/X** | API Integration | High | High |
| **Facebook** | API Integration | Medium | Medium |
| **Website/Blog** | Webhook/API | High | High |
| **Email Marketing** | API Integration | High | Medium |
| **Newsletter** | Manual Export | High | Low |
| **TV/Radio Spots** | Manual Copy | Low | Low |

#### **Phase 3: Advanced Distribution**
- **Scheduling System**: Queue content for future posting
- **Multi-Channel Campaigns**: Coordinate across platforms
- **Analytics Integration**: Track engagement across channels
- **A/B Testing**: Test different versions across channels

### **Channel Management Features**

#### **Channel Configuration**
- **Platform Credentials**: Secure API key storage
- **Posting Preferences**: Default times, hashtags, formatting
- **Compliance Rules**: Platform-specific compliance requirements
- **Brand Consistency**: Logos, colors, standard disclaimers

#### **Distribution Dashboard**
- **Content Calendar**: Visual scheduling interface
- **Performance Metrics**: Engagement tracking by channel
- **Compliance Monitoring**: Ensure distributed content remains compliant
- **Audit Trail**: Complete record of what was posted where and when

## 🏗️ **Portal Architecture Design**

### **Portal 1: Advisor Portal (Multi-tenant)**

#### **Core Modules**

##### **1. Dashboard Module**
- **Content Overview**: Recent content, approval status, performance
- **Quick Actions**: Fast access to create content, check approvals
- **Analytics Summary**: Personal performance metrics
- **Notification Center**: Approval updates, system messages

##### **2. Warren Chat Interface**
- **Conversational UI**: Clean, professional chat interface
- **File Upload Integration**: Drag-and-drop document upload
- **Context Display**: Show uploaded documents being used
- **Clarification Workflow**: Warren asks follow-up questions
- **Real-time Generation**: Live content creation with progress indicators

##### **3. Content Management**
- **Content Library**: All generated content with search/filter
- **Version History**: Track changes and approvals
- **Status Tracking**: Pending, approved, distributed, rejected
- **Bulk Operations**: Select multiple pieces for batch actions

##### **4. Approval Workflow**
- **Submission Interface**: Submit content with notes to CCO
- **Review Dashboard**: See content under review
- **Feedback Integration**: View CCO comments and suggestions
- **Re-submission**: Easy workflow for revised content

##### **5. Channel Management**
- **Channel Setup**: Connect and configure social media accounts
- **Distribution Interface**: Post content to selected channels
- **Scheduling System**: Queue content for future posting
- **Performance Tracking**: View engagement metrics

##### **6. File Management**
- **Document Library**: Uploaded files for context
- **File Organization**: Folders, tags, search functionality
- **Usage Tracking**: See which files were used in content generation
- **Sharing Controls**: Control which files are available to Warren

#### **Technical Requirements**
- **Multi-tenant Architecture**: Complete data isolation between firms
- **Role-based Access Control**: Granular permissions system
- **Real-time Updates**: WebSocket integration for live notifications
- **Mobile Responsive**: Full functionality on mobile devices
- **Performance Optimization**: Fast loading, efficient API calls

### **Portal 2: Fiducia Admin Dashboard**

#### **Core Modules**

##### **1. Vector Search Content Management**
- **Content Database**: View/edit all vector search content
- **Embedding Management**: Monitor vectorization status
- **Content Quality Control**: Review and approve new content
- **Performance Analytics**: Vector search effectiveness metrics

##### **2. User & Firm Management**
- **User Directory**: All users across all RIAs/firms
- **Firm Hierarchy**: Visual representation of RIA/firm/IAR structure
- **Account Provisioning**: Create and manage accounts
- **Access Control**: Manage permissions and role assignments

##### **3. System Analytics**
- **Usage Metrics**: Content generation, user activity, system performance
- **Business Intelligence**: Revenue metrics, customer success indicators
- **Performance Monitoring**: API response times, error rates
- **Cost Tracking**: AI usage costs, infrastructure spending

##### **4. Platform Configuration**
- **System Settings**: Global configuration options
- **Feature Flags**: Enable/disable features for testing
- **API Management**: Monitor and configure API access
- **Compliance Settings**: Global compliance rules and templates

##### **5. Support Tools**
- **User Support**: Help desk integration, user issue tracking
- **Content Review**: Review flagged content across all users
- **System Health**: Monitor infrastructure and services
- **Audit Logs**: Complete system activity logging

## 🔧 **Technology Stack Recommendations**

### **Frontend Framework**
- **Next.js 14**: App Router, Server Components, optimal performance
- **TypeScript**: Type safety, better developer experience
- **Tailwind CSS**: Consistent, professional styling
- **Shadcn/ui**: High-quality, accessible components

### **State Management**
- **React Query**: Server state management, caching
- **Zustand**: Client state management, simple and effective
- **React Hook Form**: Form handling with validation

### **Authentication & Security**
- **NextAuth.js**: Robust authentication with multiple providers
- **JWT Tokens**: Secure, scalable authentication
- **Role-based Access Control**: Granular permission system
- **API Security**: Rate limiting, input validation

### **Real-time Features**
- **WebSocket Integration**: Real-time notifications and updates
- **Server-Sent Events**: Live status updates
- **Optimistic Updates**: Immediate UI feedback

### **File Handling**
- **React Dropzone**: User-friendly file upload
- **File Processing**: Server-side text extraction and analysis
- **Cloud Storage**: Secure, scalable file storage

## 📅 **Development Phases**

### **Phase 1: Core Advisor Portal (4-6 weeks)**
- Authentication system with basic multi-tenancy
- Warren chat interface with file upload
- Basic content management and approval workflow
- Simple channel management (copy/paste)

### **Phase 2: Enhanced Advisor Features (3-4 weeks)**
- Advanced approval workflow with version control
- Improved file management and context handling
- Basic analytics and performance tracking
- Mobile optimization

### **Phase 3: Admin Portal (4-5 weeks)**
- Complete admin dashboard
- Vector search content management
- User and firm management
- System analytics and monitoring

### **Phase 4: Advanced Features (6-8 weeks)**
- API channel integrations (LinkedIn, Twitter)
- Advanced analytics and business intelligence
- Content recommendation engine
- Advanced compliance tools

## 🎯 **Success Metrics**

### **User Experience Metrics**
- **Time to First Content**: How quickly new users generate content
- **Approval Cycle Time**: Average time from creation to approval
- **User Adoption Rate**: Percentage of registered users actively creating content
- **Content Quality Score**: Compliance pass rates

### **Business Metrics**
- **Monthly Active Users**: Engaged user base
- **Content Generation Volume**: Total content pieces created
- **Revenue per User**: Average subscription value
- **Customer Satisfaction**: NPS scores, support ticket volume

### **Technical Metrics**
- **Application Performance**: Page load times, API response times
- **System Reliability**: Uptime, error rates
- **Cost Efficiency**: Infrastructure costs per user
- **Security Metrics**: Zero security incidents, compliance audit results

## 🚨 **Risk Considerations**

### **Compliance Risks**
- **Content Mixing**: Ensure advisor uploads never contaminate compliance database
- **Approval Workflow**: Maintain strict separation between creation and approval
- **Audit Trail**: Complete logging for regulatory compliance
- **Data Retention**: Proper handling of sensitive financial data

### **Technical Risks**
- **Multi-tenancy Complexity**: Ensure complete data isolation
- **Scalability**: Plan for rapid user growth
- **Integration Challenges**: Third-party API limitations and changes
- **Performance**: Maintain speed with increasing content volume

### **Business Risks**
- **Feature Creep**: Focus on core value proposition
- **User Adoption**: Ensure interface is intuitive for financial advisors
- **Competition**: Stay ahead of feature parity with competitors
- **Pricing Strategy**: Balance feature richness with market accessibility

---

**This document serves as the comprehensive blueprint for FiduciaMVP frontend development, ensuring both portals meet the complex needs of the financial services industry while maintaining the highest standards of compliance and user experience.**