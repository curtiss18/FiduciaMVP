# Compliance Portal - Technical Architecture Document

**Document Version**: 1.0  
**Created**: July 7, 2025  
**Project**: FiduciaMVP Compliance Portal  
**Status**: Draft - Ready for Development

---

## 🏗️ **System Architecture Overview**

### **Microservices Architecture Strategy**
The Compliance Portal follows FiduciaMVP's migration to microservices architecture, providing a standalone service that integrates seamlessly with the existing advisor ecosystem.

```
FiduciaMVP Microservices Architecture:
├── frontend-admin/          # Fiducia platform management
├── frontend-advisor/        # IAR content creation portal
├── frontend-compliance/     # 🆕 CCO content review portal
├── src/api/                 # Shared backend services
├── shared-ui/              # Unified design system
└── docs/compliance-portal/  # Compliance-specific documentation
```

### **Core Architecture Principles**
- **Service Independence**: Compliance portal operates independently with defined integration points
- **Shared Foundation**: Leverages existing infrastructure (database, APIs, design system)
- **Security First**: Enterprise-grade security with audit trails and access controls
- **Scalable Design**: Built to handle thousands of concurrent CCO users
- **Mobile Responsive**: Full functionality across all device types

---

## 🗄️ **Database Architecture & Schema Design**

### **Database Strategy**
**Approach**: Extend existing PostgreSQL database with compliance-specific tables while maintaining data integrity and performance.

### **New Compliance Tables**

#### **1. compliance_ccos Table**
```sql
CREATE TABLE compliance_ccos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    subscription_type VARCHAR(50) DEFAULT 'lite' CHECK (subscription_type IN ('lite', 'full')),
    seats_purchased INTEGER DEFAULT 1,
    seats_used INTEGER DEFAULT 0,
    trial_ends_at TIMESTAMP,
    subscription_status VARCHAR(50) DEFAULT 'active' CHECK (subscription_status IN ('active', 'trial', 'expired', 'cancelled')),
    billing_email VARCHAR(255),
    company_name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT seats_used_lte_purchased CHECK (seats_used <= seats_purchased),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes for performance
CREATE INDEX idx_compliance_ccos_email ON compliance_ccos(email);
CREATE INDEX idx_compliance_ccos_subscription ON compliance_ccos(subscription_type, subscription_status);
CREATE INDEX idx_compliance_ccos_trial ON compliance_ccos(trial_ends_at) WHERE subscription_type = 'full';
```

#### **2. cco_iar_relationships Table**
```sql
CREATE TABLE cco_iar_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cco_id UUID NOT NULL REFERENCES compliance_ccos(id) ON DELETE CASCADE,
    iar_email VARCHAR(255) NOT NULL, -- Email from advisor portal
    iar_name VARCHAR(255),
    iar_firm VARCHAR(255),
    relationship_type VARCHAR(50) DEFAULT 'connected' CHECK (relationship_type IN ('connected', 'pending', 'disconnected')),
    invitation_token VARCHAR(255) UNIQUE, -- For full version invitations
    invitation_sent_at TIMESTAMP,
    connection_accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate relationships
    UNIQUE(cco_id, iar_email)
);

-- Indexes for performance
CREATE INDEX idx_cco_iar_cco_id ON cco_iar_relationships(cco_id);
CREATE INDEX idx_cco_iar_email ON cco_iar_relationships(iar_email);
CREATE INDEX idx_cco_iar_status ON cco_iar_relationships(relationship_type);
CREATE INDEX idx_cco_iar_invitation ON cco_iar_relationships(invitation_token) WHERE invitation_token IS NOT NULL;
```

#### **3. content_reviews Table**
```sql
CREATE TABLE content_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES advisor_content(id) ON DELETE CASCADE,
    cco_email VARCHAR(255) NOT NULL, -- Supports both lite and full versions
    cco_id UUID REFERENCES compliance_ccos(id), -- NULL for lite version
    review_token VARCHAR(255) UNIQUE NOT NULL, -- Secure access token
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'in_progress')),
    decision VARCHAR(20) CHECK (decision IN ('approved', 'rejected')),
    overall_feedback TEXT,
    compliance_score INTEGER CHECK (compliance_score BETWEEN 1 AND 100),
    review_started_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    expires_at TIMESTAMP, -- Token expiration (NULL = no expiration)
    notification_sent_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Business logic constraints
    CONSTRAINT decision_requires_reviewed_at CHECK (
        (decision IS NULL AND reviewed_at IS NULL) OR 
        (decision IS NOT NULL AND reviewed_at IS NOT NULL)
    ),
    CONSTRAINT rejected_requires_feedback CHECK (
        decision != 'rejected' OR 
        (decision = 'rejected' AND overall_feedback IS NOT NULL AND length(overall_feedback) > 10)
    )
);

-- Indexes for performance
CREATE INDEX idx_content_reviews_content_id ON content_reviews(content_id);
CREATE INDEX idx_content_reviews_cco_email ON content_reviews(cco_email);
CREATE INDEX idx_content_reviews_cco_id ON content_reviews(cco_id) WHERE cco_id IS NOT NULL;
CREATE INDEX idx_content_reviews_token ON content_reviews(review_token);
CREATE INDEX idx_content_reviews_status ON content_reviews(status);
CREATE INDEX idx_content_reviews_pending ON content_reviews(created_at) WHERE status = 'pending';
CREATE INDEX idx_content_reviews_expires ON content_reviews(expires_at) WHERE expires_at IS NOT NULL;
```

#### **4. review_feedback Table**
```sql
CREATE TABLE review_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES content_reviews(id) ON DELETE CASCADE,
    section_text TEXT, -- The highlighted text being commented on
    section_start_pos INTEGER, -- Character position start
    section_end_pos INTEGER, -- Character position end
    violation_type VARCHAR(100) CHECK (violation_type IN (
        'company_policy', 'finra_rule', 'sec_regulation', 'state_regulation',
        'misleading_statement', 'performance_guarantee', 'omitted_disclosure',
        'unauthorized_testimonial', 'unapproved_claim', 'other'
    )),
    comment TEXT NOT NULL,
    suggested_fix TEXT,
    regulation_reference TEXT, -- Specific FINRA/SEC rule citation
    ai_generated BOOLEAN DEFAULT FALSE, -- Track AI-assisted feedback
    warren_session_id UUID, -- Link to Warren AI session if applicable
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Validation
    CONSTRAINT valid_section_positions CHECK (
        (section_start_pos IS NULL AND section_end_pos IS NULL) OR
        (section_start_pos IS NOT NULL AND section_end_pos IS NOT NULL AND section_end_pos > section_start_pos)
    ),
    CONSTRAINT comment_not_empty CHECK (length(trim(comment)) > 0)
);

-- Indexes for performance
CREATE INDEX idx_review_feedback_review_id ON review_feedback(review_id);
CREATE INDEX idx_review_feedback_violation_type ON review_feedback(violation_type);
CREATE INDEX idx_review_feedback_ai ON review_feedback(ai_generated);
CREATE INDEX idx_review_feedback_warren ON review_feedback(warren_session_id) WHERE warren_session_id IS NOT NULL;
```

#### **5. cco_team_members Table (Full Version)**
```sql
CREATE TABLE cco_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cco_id UUID NOT NULL REFERENCES compliance_ccos(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'reviewer' CHECK (role IN ('admin', 'reviewer', 'viewer')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    invitation_token VARCHAR(255) UNIQUE,
    invited_at TIMESTAMP,
    joined_at TIMESTAMP,
    last_login_at TIMESTAMP,
    permissions JSONB, -- Flexible permissions system
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate team members
    UNIQUE(cco_id, email)
);

-- Indexes for performance
CREATE INDEX idx_cco_team_members_cco_id ON cco_team_members(cco_id);
CREATE INDEX idx_cco_team_members_email ON cco_team_members(email);
CREATE INDEX idx_cco_team_members_status ON cco_team_members(status);
CREATE INDEX idx_cco_team_members_role ON cco_team_members(role);
```

### **Extended Existing Tables**

#### **advisor_content Table Extensions**
```sql
-- Add compliance-related columns to existing advisor_content table
ALTER TABLE advisor_content ADD COLUMN IF NOT EXISTS cco_review_status VARCHAR(50) DEFAULT 'not_submitted' 
    CHECK (cco_review_status IN ('not_submitted', 'submitted', 'in_review', 'approved', 'rejected', 'revision_requested'));
ALTER TABLE advisor_content ADD COLUMN IF NOT EXISTS cco_email VARCHAR(255);
ALTER TABLE advisor_content ADD COLUMN IF NOT EXISTS submitted_for_review_at TIMESTAMP;
ALTER TABLE advisor_content ADD COLUMN IF NOT EXISTS review_deadline TIMESTAMP;
ALTER TABLE advisor_content ADD COLUMN IF NOT EXISTS review_priority VARCHAR(20) DEFAULT 'normal' 
    CHECK (review_priority IN ('low', 'normal', 'high', 'urgent'));

-- Indexes for compliance queries
CREATE INDEX IF NOT EXISTS idx_advisor_content_cco_review_status ON advisor_content(cco_review_status);
CREATE INDEX IF NOT EXISTS idx_advisor_content_cco_email ON advisor_content(cco_email) WHERE cco_email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_advisor_content_submitted_review ON advisor_content(submitted_for_review_at) WHERE submitted_for_review_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_advisor_content_review_deadline ON advisor_content(review_deadline) WHERE review_deadline IS NOT NULL;
```

---

## 🔐 **Authentication & Security Architecture**

### **Dual Authentication Strategy**

#### **Lite Version: Token-Based Security**
```typescript
interface ReviewToken {
  contentId: string;
  ccoEmail: string;
  issuedAt: number;
  expiresAt?: number; // Optional expiration
  signature: string; // HMAC signature for tamper detection
}

// Token generation algorithm
const generateReviewToken = (contentId: string, ccoEmail: string): string => {
  const payload = {
    contentId,
    ccoEmail,
    issuedAt: Date.now(),
    nonce: crypto.randomBytes(16).toString('hex')
  };
  
  const token = base64url.encode(JSON.stringify(payload));
  const signature = crypto.createHmac('sha256', process.env.JWT_SECRET)
    .update(token)
    .digest('base64url');
    
  return `${token}.${signature}`;
};
```

#### **Full Version: Account-Based Security**
```typescript
interface CCOSession {
  userId: string;
  ccoId: string;
  role: 'admin' | 'reviewer' | 'viewer';
  permissions: string[];
  teamId?: string;
  mfaVerified: boolean;
  sessionId: string;
  expiresAt: number;
}

// JWT-based session management
const createCCOSession = async (cco: CCO, teamMember?: TeamMember): Promise<string> => {
  const payload: CCOSession = {
    userId: teamMember?.id || cco.id,
    ccoId: cco.id,
    role: teamMember?.role || 'admin',
    permissions: calculatePermissions(cco, teamMember),
    teamId: teamMember?.id,
    mfaVerified: true, // Required for full version
    sessionId: crypto.randomUUID(),
    expiresAt: Date.now() + (8 * 60 * 60 * 1000) // 8 hours
  };
  
  return jwt.sign(payload, process.env.JWT_SECRET, { expiresIn: '8h' });
};
```

### **Security Controls**

#### **Token Security (Lite Version)**
```typescript
// Security middleware for token validation
const validateReviewToken = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const token = req.params.token || req.query.token;
    if (!token) throw new Error('Review token required');
    
    const [payload, signature] = token.split('.');
    const expectedSignature = crypto.createHmac('sha256', process.env.JWT_SECRET)
      .update(payload)
      .digest('base64url');
    
    if (signature !== expectedSignature) {
      throw new Error('Invalid token signature');
    }
    
    const data = JSON.parse(base64url.decode(payload));
    
    // Validate token hasn't expired (if expiration set)
    if (data.expiresAt && Date.now() > data.expiresAt) {
      throw new Error('Token expired');
    }
    
    // Verify content still exists and is in reviewable state
    const content = await getAdvisorContent(data.contentId);
    if (!content || content.cco_review_status === 'approved') {
      throw new Error('Content no longer available for review');
    }
    
    req.reviewContext = {
      contentId: data.contentId,
      ccoEmail: data.ccoEmail,
      tokenData: data
    };
    
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid or expired review token' });
  }
};
```

#### **Account Security (Full Version)**
```typescript
// Multi-factor authentication middleware
const requireMFA = async (req: Request, res: Response, next: NextFunction) => {
  const session = req.user as CCOSession;
  
  if (!session.mfaVerified) {
    return res.status(403).json({ 
      error: 'MFA verification required',
      mfaChallenge: await generateMFAChallenge(session.userId)
    });
  }
  
  next();
};

// Role-based access control
const requirePermission = (permission: string) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const session = req.user as CCOSession;
    
    if (!session.permissions.includes(permission)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    
    next();
  };
};
```

---

## 🔌 **API Architecture & Endpoints**

### **API Namespace Strategy**
```typescript
// Compliance-specific namespace with shared endpoint reuse
const API_NAMESPACE = '/api/v1/compliance';

// Shared endpoints accessed with compliance context
const SHARED_ENDPOINTS = [
  '/api/v1/advisor/content/{id}', // Reuse with token auth
  '/api/v1/warren/generate-v3',   // Warren AI for CCOs
  '/api/v1/notifications/send'    // Email notifications
];
```

### **Lite Version API Endpoints**

#### **Content Access & Review**
```typescript
// GET /api/v1/compliance/content/{token}
// Access content for review using secure token
interface ContentReviewResponse {
  content: {
    id: string;
    title: string;
    content: string;
    contentType: 'linkedin_post' | 'email' | 'blog_post' | 'newsletter';
    platform: string;
    audience: string;
    createdAt: string;
  };
  advisor: {
    name: string;
    email: string;
    firm: string;
    phone?: string;
  };
  review: {
    id: string;
    status: 'pending' | 'in_progress' | 'approved' | 'rejected';
    submittedAt: string;
    deadline?: string;
    priority: 'low' | 'normal' | 'high' | 'urgent';
  };
  policies: {
    companyPolicies: PolicyDocument[];
    regulatoryGuidelines: RegulatoryReference[];
  };
}

// POST /api/v1/compliance/review/submit
// Submit review decision and feedback
interface ReviewSubmissionRequest {
  token: string;
  decision: 'approved' | 'rejected';
  overallFeedback?: string;
  sectionFeedback: Array<{
    sectionText: string;
    startPos: number;
    endPos: number;
    violationType: string;
    comment: string;
    suggestedFix?: string;
    regulationReference?: string;
  }>;
  complianceScore?: number; // 1-100
}
```

#### **AI Assistance**
```typescript
// POST /api/v1/compliance/ai/analyze-violation
// Get AI assistance for regulation identification
interface ViolationAnalysisRequest {
  token: string;
  sectionText: string;
  suspectedViolation: string;
  context: string;
}

interface ViolationAnalysisResponse {
  violationDetected: boolean;
  violationType: string;
  regulationReferences: Array<{
    source: 'FINRA' | 'SEC' | 'STATE';
    ruleNumber: string;
    ruleTitle: string;
    relevantSection: string;
    violationDescription: string;
    suggestedFix: string;
  }>;
  confidenceScore: number; // 0-100
  additionalContext: string;
}
```

### **Full Version API Endpoints**

#### **Dashboard & Analytics**
```typescript
// GET /api/v1/compliance/dashboard
// Multi-advisor dashboard data
interface DashboardResponse {
  pendingReviews: Array<{
    id: string;
    contentId: string;
    advisorName: string;
    contentTitle: string;
    submittedAt: string;
    ageInDays: number;
    priority: string;
    contentType: string;
  }>;
  recentActivity: Array<{
    type: 'review_completed' | 'content_submitted' | 'advisor_connected';
    advisorName: string;
    description: string;
    timestamp: string;
  }>;
  metrics: {
    totalPendingReviews: number;
    averageReviewTime: number; // hours
    approvalRate: number; // percentage
    monthlyReviewVolume: number;
    advisorCount: number;
  };
  alerts: Array<{
    type: 'overdue_review' | 'high_rejection_rate' | 'new_regulation';
    message: string;
    severity: 'low' | 'medium' | 'high';
    actionRequired: boolean;
  }>;
}

// GET /api/v1/compliance/advisors
// Advisor relationship management
interface AdvisorListResponse {
  advisors: Array<{
    id: string;
    name: string;
    email: string;
    firm: string;
    connectionStatus: 'connected' | 'pending' | 'disconnected';
    connectedAt: string;
    lastActivityAt: string;
    stats: {
      totalContentSubmitted: number;
      approvalRate: number;
      averageReviewTime: number;
      pendingReviews: number;
    };
  }>;
  pagination: {
    page: number;
    totalPages: number;
    totalCount: number;
  };
}
```

#### **Advanced Review Operations**
```typescript
// POST /api/v1/compliance/reviews/bulk-action
// Bulk approve/reject operations
interface BulkReviewRequest {
  reviewIds: string[];
  action: 'approve' | 'reject' | 'request_changes';
  feedback?: string;
  applyTemplate?: string; // Template ID for standardized feedback
}

// GET /api/v1/compliance/reviews/history
// Review history with search and filtering
interface ReviewHistoryResponse {
  reviews: Array<{
    id: string;
    contentTitle: string;
    advisorName: string;
    decision: 'approved' | 'rejected';
    reviewedAt: string;
    feedbackSummary: string;
    violationTypes: string[];
    reviewTimeHours: number;
  }>;
  filters: {
    dateRange: { start: string; end: string };
    advisors: string[];
    decisions: string[];
    violationTypes: string[];
  };
  pagination: PaginationInfo;
}
```

#### **Warren AI Integration**
```typescript
// POST /api/v1/compliance/warren/improve-content
// Use Warren to improve content during review
interface WarrenImprovementRequest {
  contentId: string;
  issues: Array<{
    sectionText: string;
    violationType: string;
    description: string;
  }>;
  improvementGoals: string[];
}

interface WarrenImprovementResponse {
  improvedContent: string;
  changes: Array<{
    originalText: string;
    improvedText: string;
    rationale: string;
    regulationReference?: string;
  }>;
  complianceScore: number;
  additionalSuggestions: string[];
  warrenSessionId: string; // For audit trail
}
```

---

## 📱 **Frontend Architecture**

### **Technology Stack**
```json
{
  "framework": "Next.js 14",
  "language": "TypeScript",
  "styling": "Tailwind CSS",
  "components": "Shadcn/ui + shared-ui",
  "stateManagement": "React Query + Zustand",
  "authentication": "NextAuth.js (full version)",
  "icons": "Lucide React",
  "forms": "React Hook Form",
  "validation": "Zod"
}
```

### **Project Structure**
```
frontend-compliance/
├── app/                          # Next.js 14 App Router
│   ├── (lite)/                   # Lite version routes
│   │   ├── review/[token]/       # Token-based review page
│   │   └── upgrade/              # Upgrade to full version
│   ├── (full)/                   # Full version routes (auth required)
│   │   ├── dashboard/            # Main dashboard
│   │   ├── advisors/             # Advisor management
│   │   ├── reviews/              # Review history & bulk operations
│   │   ├── analytics/            # Compliance analytics
│   │   └── settings/             # Account & team management
│   ├── api/                      # API route handlers
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page
├── components/                   # React components
│   ├── lite/                     # Lite version specific components
│   │   ├── ReviewInterface.tsx   # Main review interface
│   │   ├── ContentViewer.tsx     # Content display component
│   │   ├── FeedbackForm.tsx      # Feedback submission form
│   │   └── UpgradePrompt.tsx     # Upgrade call-to-action
│   ├── full/                     # Full version specific components
│   │   ├── Dashboard.tsx         # Main dashboard
│   │   ├── AdvisorList.tsx       # Advisor management
│   │   ├── ReviewHistory.tsx     # Review history table
│   │   ├── BulkActions.tsx       # Bulk review operations
│   │   └── Analytics.tsx         # Analytics dashboard
│   ├── shared/                   # Shared components
│   │   ├── ContentPreview.tsx    # Content display
│   │   ├── FeedbackEditor.tsx    # Rich feedback editor
│   │   ├── ViolationSelector.tsx # Violation type selector
│   │   ├── WarrenChat.tsx        # Warren AI integration
│   │   └── Navigation.tsx        # Portal navigation
│   └── ui/                       # UI components (from shared-ui)
├── lib/                          # Utilities and configurations
│   ├── api.ts                    # API client
│   ├── auth.ts                   # Authentication configuration
│   ├── types.ts                  # TypeScript interfaces
│   ├── utils.ts                  # Utility functions
│   └── validations.ts            # Zod schemas
├── hooks/                        # Custom React hooks
│   ├── useReviewToken.ts         # Token validation hook
│   ├── useComplianceData.ts      # Data fetching hooks
│   └── useWarrenChat.ts          # Warren AI integration
└── middleware.ts                 # Next.js middleware for auth
```

### **Component Architecture Patterns**

#### **Lite Version: Single-Page Review Interface**
```typescript
// components/lite/ReviewInterface.tsx
interface ReviewInterfaceProps {
  token: string;
}

const ReviewInterface: React.FC<ReviewInterfaceProps> = ({ token }) => {
  const { data: reviewData, isLoading, error } = useReviewData(token);
  const [decision, setDecision] = useState<'approved' | 'rejected' | null>(null);
  const [feedback, setFeedback] = useState<ReviewFeedback[]>([]);
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Content Viewer */}
          <ContentViewer 
            content={reviewData?.content}
            advisor={reviewData?.advisor}
            onTextSelection={handleTextSelection}
          />
          
          {/* Review Tools */}
          <div className="space-y-6">
            <AdvisorInfo advisor={reviewData?.advisor} />
            <FeedbackEditor 
              feedback={feedback}
              onChange={setFeedback}
            />
            <DecisionPanel 
              decision={decision}
              onChange={setDecision}
              onSubmit={handleSubmitReview}
            />
          </div>
        </div>
      </main>
      
      <UpgradePrompt />
    </div>
  );
};
```

#### **Full Version: Dashboard-Centric Architecture**
```typescript
// components/full/Dashboard.tsx
const Dashboard: React.FC = () => {
  const { data: dashboardData } = useDashboardData();
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Metrics Overview */}
        <MetricsGrid metrics={dashboardData?.metrics} />
        
        {/* Pending Reviews */}
        <PendingReviewsTable 
          reviews={dashboardData?.pendingReviews}
          onBulkAction={handleBulkAction}
        />
        
        {/* Recent Activity */}
        <ActivityFeed activities={dashboardData?.recentActivity} />
        
        {/* Analytics Charts */}
        <AnalyticsCharts 
          timeRange={selectedTimeRange}
          onTimeRangeChange={setSelectedTimeRange}
        />
      </div>
    </DashboardLayout>
  );
};
```

---

## 🔄 **Integration Architecture**

### **Advisor Portal Integration Points**

#### **Content Submission Integration**
```typescript
// advisor portal integration
const submitForReview = async (contentId: string, ccoEmail: string) => {
  try {
    // 1. Update content status in advisor portal
    await advisorApi.updateContentStatus(contentId, 'submitted');
    
    // 2. Create review record in compliance system
    const review = await complianceApi.createReview({
      contentId,
      ccoEmail,
      submittedBy: currentUser.id,
      priority: 'normal'
    });
    
    // 3. Generate secure review token
    const token = generateReviewToken(contentId, ccoEmail);
    
    // 4. Send email notification to CCO
    await emailService.sendReviewNotification({
      to: ccoEmail,
      token,
      content: contentData,
      advisor: currentUser
    });
    
    // 5. Update advisor portal UI
    showSuccessNotification('Content submitted for review');
    
    return { reviewId: review.id, token };
  } catch (error) {
    throw new SubmissionError('Failed to submit content for review');
  }
};
```

#### **Review Completion Integration**
```typescript
// Webhook handler for review completion
const handleReviewComplete = async (reviewData: ReviewCompletion) => {
  try {
    // 1. Update content status in advisor portal
    await advisorApi.updateContentStatus(
      reviewData.contentId, 
      reviewData.decision === 'approved' ? 'approved' : 'rejected'
    );
    
    // 2. Store feedback in advisor portal
    if (reviewData.feedback) {
      await advisorApi.storeFeedback(reviewData.contentId, {
        overallFeedback: reviewData.overallFeedback,
        sectionFeedback: reviewData.sectionFeedback,
        violationTypes: reviewData.violationTypes,
        complianceScore: reviewData.complianceScore
      });
    }
    
    // 3. Send notification to advisor
    await notificationService.notifyAdvisor({
      advisorId: reviewData.advisorId,
      type: 'review_completed',
      message: `Your content "${reviewData.contentTitle}" has been ${reviewData.decision}`,
      actionUrl: `/library/${reviewData.contentId}`
    });
    
    // 4. Send email notification
    await emailService.sendReviewResultNotification({
      to: reviewData.advisorEmail,
      decision: reviewData.decision,
      feedback: reviewData.feedback,
      contentTitle: reviewData.contentTitle
    });
    
  } catch (error) {
    logger.error('Failed to process review completion', error);
    // Queue for retry
    await retryQueue.add('review-completion', reviewData);
  }
};
```

### **Shared Database Access Patterns**

#### **Content Access Service**
```typescript
// Shared service for content access across portals
class ContentAccessService {
  // Advisor portal access (full permissions)
  async getContentForAdvisor(advisorId: string, contentId: string) {
    return db.advisor_content.findFirst({
      where: { id: contentId, advisor_id: advisorId },
      include: { reviews: true, feedback: true }
    });
  }
  
  // Compliance portal access (review permissions only)
  async getContentForReview(token: string) {
    const reviewData = await this.validateReviewToken(token);
    
    return db.advisor_content.findFirst({
      where: { id: reviewData.contentId },
      select: {
        id: true,
        title: true,
        content: true,
        content_type: true,
        platform: true,
        audience: true,
        created_at: true,
        advisor: {
          select: { name: true, email: true, firm: true, phone: true }
        }
      }
    });
  }
  
  // Admin portal access (full system permissions)
  async getContentForAdmin(contentId: string) {
    return db.advisor_content.findFirst({
      where: { id: contentId },
      include: { 
        advisor: true, 
        reviews: { include: { feedback: true } },
        distribution: true 
      }
    });
  }
}
```

### **Email Integration Architecture**

#### **Notification Service**
```typescript
interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  htmlBody: string;
  textBody: string;
  variables: string[];
}

class ComplianceEmailService {
  private templates: Map<string, EmailTemplate> = new Map();
  
  async sendReviewInvitation(data: ReviewInvitationData) {
    const template = this.templates.get('review_invitation');
    
    const emailData = {
      to: data.ccoEmail,
      subject: this.renderTemplate(template.subject, data),
      html: this.renderTemplate(template.htmlBody, {
        ...data,
        reviewUrl: `${process.env.COMPLIANCE_PORTAL_URL}/review/${data.token}`,
        expiresAt: data.expiresAt,
        advisorName: data.advisor.name,
        advisorFirm: data.advisor.firm,
        contentTitle: data.content.title,
        contentType: data.content.type,
        urgency: data.priority
      })
    };
    
    return this.emailProvider.send(emailData);
  }
  
  async sendReviewReminder(reviewId: string) {
    const review = await db.content_reviews.findFirst({
      where: { id: reviewId },
      include: { content: { include: { advisor: true } } }
    });
    
    if (!review || review.status !== 'pending') return;
    
    const daysSinceSubmission = Math.floor(
      (Date.now() - review.created_at.getTime()) / (1000 * 60 * 60 * 24)
    );
    
    await this.sendEmail('review_reminder', {
      to: review.cco_email,
      reviewUrl: `${process.env.COMPLIANCE_PORTAL_URL}/review/${review.review_token}`,
      daysSinceSubmission,
      advisorName: review.content.advisor.name,
      contentTitle: review.content.title
    });
    
    // Update reminder count
    await db.content_reviews.update({
      where: { id: reviewId },
      data: { reminder_count: review.reminder_count + 1 }
    });
  }
}
```

---

## 📊 **Performance & Scalability Architecture**

### **Database Performance Optimization**

#### **Query Optimization Strategies**
```sql
-- Optimized query for CCO dashboard (full version)
SELECT 
  cr.id,
  cr.created_at,
  cr.status,
  ac.title as content_title,
  ac.content_type,
  ac.platform,
  cir.iar_name as advisor_name,
  cir.iar_firm as advisor_firm,
  EXTRACT(EPOCH FROM (NOW() - cr.created_at))/86400 as age_days
FROM content_reviews cr
JOIN advisor_content ac ON cr.content_id = ac.id
JOIN cco_iar_relationships cir ON cr.cco_email = cir.iar_email
WHERE cr.cco_id = $1 
  AND cr.status = 'pending'
ORDER BY cr.created_at ASC -- Oldest first for priority
LIMIT 50;

-- Index to support this query
CREATE INDEX idx_content_reviews_cco_pending ON content_reviews(cco_id, status, created_at) 
WHERE status = 'pending';
```

#### **Caching Strategy**
```typescript
// Redis caching for frequently accessed data
class ComplianceCacheService {
  private redis = new Redis(process.env.REDIS_URL);
  
  // Cache CCO dashboard data (5 minutes TTL)
  async getCCODashboard(ccoId: string): Promise<DashboardData | null> {
    const cached = await this.redis.get(`cco:dashboard:${ccoId}`);
    return cached ? JSON.parse(cached) : null;
  }
  
  async setCCODashboard(ccoId: string, data: DashboardData) {
    await this.redis.setex(
      `cco:dashboard:${ccoId}`, 
      300, // 5 minutes
      JSON.stringify(data)
    );
  }
  
  // Cache review token validation (1 hour TTL)
  async validateTokenFromCache(token: string): Promise<TokenData | null> {
    const cached = await this.redis.get(`token:${token}`);
    if (cached) {
      return JSON.parse(cached);
    }
    
    // Validate token and cache result
    const tokenData = await this.validateToken(token);
    if (tokenData) {
      await this.redis.setex(`token:${token}`, 3600, JSON.stringify(tokenData));
    }
    
    return tokenData;
  }
  
  // Invalidate cache when review is completed
  async invalidateReviewCache(ccoId: string, contentId: string) {
    await Promise.all([
      this.redis.del(`cco:dashboard:${ccoId}`),
      this.redis.del(`content:${contentId}`),
      this.redis.del(`cco:pending:${ccoId}`)
    ]);
  }
}
```

### **API Rate Limiting & Security**

#### **Rate Limiting Strategy**
```typescript
// Different rate limits for different user types
const rateLimits = {
  lite: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 20, // 20 requests per window
    message: 'Too many requests from this IP for lite version'
  },
  full: {
    windowMs: 15 * 60 * 1000,
    max: 100, // 100 requests per window
    message: 'Rate limit exceeded for full version'
  },
  api: {
    windowMs: 60 * 1000, // 1 minute
    max: 60, // 60 requests per minute
    message: 'API rate limit exceeded'
  }
};

// Dynamic rate limiting based on user type
const dynamicRateLimit = (req: Request, res: Response, next: NextFunction) => {
  const userType = determineUserType(req);
  const limit = rateLimits[userType];
  
  return rateLimit(limit)(req, res, next);
};
```

### **Scalability Considerations**

#### **Horizontal Scaling Architecture**
```yaml
# Docker Compose for scalable deployment
version: '3.8'
services:
  compliance-portal:
    image: fiducia/compliance-portal:latest
    replicas: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "3003:3000"
    depends_on:
      - postgres
      - redis
      
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=fiducia_compliance
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - compliance-portal
```

---

## 🔧 **Development & Deployment Architecture**

### **Environment Configuration**
```typescript
// Environment-specific configurations
interface EnvironmentConfig {
  database: {
    url: string;
    ssl: boolean;
    poolSize: number;
  };
  redis: {
    url: string;
    ttl: number;
  };
  email: {
    provider: 'sendgrid' | 'resend' | 'ses';
    apiKey: string;
    fromAddress: string;
  };
  auth: {
    jwtSecret: string;
    tokenExpiry: string;
    mfaRequired: boolean;
  };
  api: {
    baseUrl: string;
    rateLimit: number;
    timeout: number;
  };
  features: {
    warrenIntegration: boolean;
    advancedAnalytics: boolean;
    bulkOperations: boolean;
  };
}

const environments: Record<string, EnvironmentConfig> = {
  development: {
    database: {
      url: 'postgresql://localhost:5432/fiducia_dev',
      ssl: false,
      poolSize: 10
    },
    // ... other dev config
  },
  staging: {
    database: {
      url: process.env.STAGING_DATABASE_URL,
      ssl: true,
      poolSize: 20
    },
    // ... staging config
  },
  production: {
    database: {
      url: process.env.PRODUCTION_DATABASE_URL,
      ssl: true,
      poolSize: 50
    },
    // ... production config
  }
};
```

### **Monitoring & Observability**
```typescript
// Application monitoring setup
interface MonitoringConfig {
  metrics: {
    provider: 'prometheus' | 'datadog';
    endpoint: string;
  };
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error';
    destination: 'console' | 'file' | 'remote';
  };
  tracing: {
    enabled: boolean;
    sampleRate: number;
  };
  alerts: {
    errorThreshold: number;
    latencyThreshold: number;
    uptimeThreshold: number;
  };
}

// Key metrics to track
const complianceMetrics = {
  // Business metrics
  'reviews_submitted_total': 'Counter for total reviews submitted',
  'reviews_completed_total': 'Counter for completed reviews',
  'review_duration_seconds': 'Histogram of review completion time',
  'approval_rate': 'Gauge for current approval rate',
  
  // Technical metrics
  'api_request_duration_seconds': 'Histogram of API response times',
  'database_query_duration_seconds': 'Histogram of database query times',
  'cache_hit_rate': 'Gauge for cache effectiveness',
  'concurrent_users': 'Gauge for active user count',
  
  // Security metrics
  'failed_token_validations': 'Counter for invalid token attempts',
  'mfa_failures': 'Counter for MFA failures',
  'rate_limit_hits': 'Counter for rate limit violations'
};
```

---

**This Technical Architecture Document provides the comprehensive technical foundation for Compliance Portal development, ensuring scalable, secure, and maintainable implementation aligned with business requirements.**