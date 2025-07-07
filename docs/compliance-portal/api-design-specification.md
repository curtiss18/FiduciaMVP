# Compliance Portal - API Design Specification

**Document Version**: 1.0  
**Created**: July 7, 2025  
**Project**: FiduciaMVP Compliance Portal  
**Status**: Draft - Ready for Implementation

---

## 🔌 **API Design Philosophy**

### **Core Principles**
- **Microservices Integration**: Compliance API namespace with strategic endpoint reuse
- **Security First**: Token-based (lite) and JWT-based (full) authentication
- **RESTful Design**: Consistent HTTP methods, status codes, and resource naming
- **Audit Trail**: Complete logging for regulatory compliance requirements
- **Performance Optimized**: Caching, pagination, and efficient query patterns

### **API Namespace Strategy**
```
/api/v1/compliance/*     # Compliance-specific endpoints
/api/v1/advisor/*        # Shared advisor endpoints (with compliance auth)
/api/v1/warren/*         # Shared Warren AI endpoints
/api/v1/notifications/*  # Shared notification endpoints
```

### **Authentication Methods**

#### **Lite Version**: Token-Based Security
```typescript
// Review token structure
interface ReviewToken {
  contentId: string;
  ccoEmail: string;
  issuedAt: number;
  expiresAt?: number; // Optional expiration
  signature: string; // HMAC signature for tamper detection
}

// Usage in headers
Authorization: Bearer {review_token}
```

#### **Full Version**: JWT-Based Security
```typescript
// JWT payload structure
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

// Usage in headers
Authorization: Bearer {jwt_token}
```

### **Standard Response Format**
```typescript
// Success response wrapper
interface APIResponse<T> {
  success: true;
  data: T;
  meta?: {
    timestamp: string;
    requestId: string;
    version: string;
  };
}

// Error response wrapper
interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
    field?: string; // For validation errors
  };
  meta: {
    timestamp: string;
    requestId: string;
  };
}
```

### **HTTP Status Codes**
```typescript
// Standard status codes used across all endpoints
const STATUS_CODES = {
  200: 'OK - Request successful',
  201: 'Created - Resource created successfully',
  400: 'Bad Request - Invalid request data',
  401: 'Unauthorized - Authentication required',
  403: 'Forbidden - Insufficient permissions',
  404: 'Not Found - Resource not found',
  409: 'Conflict - Resource already exists',
  422: 'Unprocessable Entity - Validation failed',
  429: 'Too Many Requests - Rate limit exceeded',
  500: 'Internal Server Error - Server error'
};
```

---

## 🔓 **Lite Version API Endpoints**

### **Content Access & Review**

#### **GET /api/v1/compliance/content/{token}**
**Purpose**: Access content for review using secure token (lite version)

**Authentication**: Review token validation

**Request Parameters**:
```typescript
interface ContentAccessParams {
  token: string; // URL parameter - secure review token
}

// Optional query parameters
interface ContentAccessQuery {
  include?: 'policies' | 'guidelines' | 'history'; // Additional data to include
  format?: 'full' | 'summary'; // Response detail level
}
```

**Response**:
```typescript
interface ContentReviewResponse {
  content: {
    id: string;
    title: string;
    content: string; // Original content text
    contentType: 'linkedin_post' | 'email' | 'blog_post' | 'newsletter' | 'website_copy';
    platform: string; // Target platform (LinkedIn, Twitter, Email, etc.)
    audience: string; // Intended audience description
    createdAt: string; // ISO date string
    metadata: {
      wordCount: number;
      characterCount: number;
      estimatedReadTime: number; // minutes
      tags: string[];
    };
  };
  advisor: {
    name: string;
    email: string;
    firm: string;
    phone?: string;
    licenseNumber?: string;
    specialties: string[];
  };
  review: {
    id: string;
    status: 'pending' | 'in_progress' | 'approved' | 'rejected';
    submittedAt: string; // ISO date string
    deadline?: string; // ISO date string
    priority: 'low' | 'normal' | 'high' | 'urgent';
    ageInDays: number;
    estimatedReviewTime: number; // minutes
  };
  compliance: {
    companyPolicies: PolicyDocument[];
    regulatoryGuidelines: RegulatoryReference[];
    violationTypes: ViolationType[];
  };
  upgrade: {
    showPrompt: boolean;
    benefits: string[];
    pricingUrl: string;
    trialInfo: {
      available: boolean;
      durationDays: number;
      featuresIncluded: string[];
    };
  };
}

interface PolicyDocument {
  id: string;
  title: string;
  category: 'marketing' | 'communication' | 'disclosure' | 'general';
  lastUpdated: string;
  summary: string;
  documentUrl?: string;
  applicableContent: string[]; // Content types this policy applies to
}

interface RegulatoryReference {
  id: string;
  source: 'FINRA' | 'SEC' | 'STATE' | 'CFTC';
  ruleNumber: string;
  title: string;
  category: string;
  summary: string;
  fullTextUrl: string;
  effectiveDate: string;
  lastUpdated: string;
}

interface ViolationType {
  id: string;
  category: 'company_policy' | 'finra_rule' | 'sec_regulation' | 'state_regulation';
  name: string;
  description: string;
  commonExamples: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  regulationReference?: string;
}
```

**Error Responses**:
```typescript
// 401 Unauthorized - Invalid or expired token
{
  success: false,
  error: {
    code: 'INVALID_TOKEN',
    message: 'Review token is invalid or has expired',
    details: {
      tokenExpired: boolean,
      tokenMalformed: boolean
    }
  }
}

// 404 Not Found - Content not available
{
  success: false,
  error: {
    code: 'CONTENT_NOT_FOUND',
    message: 'Content is no longer available for review'
  }
}

// 410 Gone - Content already reviewed
{
  success: false,
  error: {
    code: 'REVIEW_COMPLETED',
    message: 'This content has already been reviewed',
    details: {
      reviewDecision: 'approved' | 'rejected',
      reviewedAt: string,
      reviewedBy: string
    }
  }
}
```
#### **POST /api/v1/compliance/review/submit**
**Purpose**: Submit review decision and feedback

**Authentication**: Review token validation

**Request Body**:
```typescript
interface ReviewSubmissionRequest {
  token: string;
  decision: 'approved' | 'rejected';
  overallFeedback?: string; // Required for rejections (min 10 characters)
  complianceScore?: number; // 1-100, optional
  sectionFeedback: SectionFeedback[];
  reviewTimeMinutes?: number; // Time spent reviewing
  confidence: number; // 1-100, CCO's confidence in decision
}

interface SectionFeedback {
  sectionText: string; // Highlighted text from content
  startPosition: number; // Character position start (0-based)
  endPosition: number; // Character position end
  violationType: string; // From violation types list
  comment: string; // CCO's specific comment on this section
  suggestedFix?: string; // Optional improvement suggestion
  regulationReference?: string; // Specific rule/regulation reference
  severity: 'low' | 'medium' | 'high' | 'critical';
  aiAssisted: boolean; // Whether AI helped identify this issue
}
```

**Validation Rules**:
- `decision: 'rejected'` requires `overallFeedback` with minimum 10 characters
- `sectionFeedback` array can be empty for approvals but recommended for rejections
- `complianceScore` must be 1-100 if provided
- `startPosition` must be less than `endPosition`
- `violationType` must exist in violation types list
- `confidence` required, must be 1-100

**Response**:
```typescript
interface ReviewSubmissionResponse {
  success: boolean;
  reviewId: string;
  submittedAt: string;
  decision: 'approved' | 'rejected';
  processingStatus: {
    advisorNotified: boolean;
    emailSent: boolean;
    statusUpdated: boolean;
  };
  nextSteps: {
    advisorActions: string[];
    ccoActions: string[];
  };
  upgrade: {
    showPrompt: boolean;
    message: string;
    benefitsUnlocked: string[];
    ctaText: string;
    ctaUrl: string;
  };
  analytics: {
    reviewTimeSeconds: number;
    feedbackItemsProvided: number;
    complianceIssuesIdentified: number;
  };
}
```

**Error Responses**:
```typescript
// 422 Validation Error
{
  success: false,
  error: {
    code: 'VALIDATION_ERROR',
    message: 'Review submission validation failed',
    details: {
      missingFeedback: boolean,
      invalidSections: string[],
      invalidScore: boolean
    }
  }
}

// 409 Conflict - Already reviewed
{
  success: false,
  error: {
    code: 'ALREADY_REVIEWED',
    message: 'This content has already been reviewed',
    details: {
      existingDecision: 'approved' | 'rejected',
      reviewedAt: string
    }
  }
}
```

#### **POST /api/v1/compliance/ai/analyze-violation**
**Purpose**: Get AI assistance for regulation identification

**Authentication**: Review token validation

**Request Body**:
```typescript
interface ViolationAnalysisRequest {
  token: string;
  sectionText: string; // Text to analyze (max 1000 characters)
  suspectedViolation: string; // CCO's description of suspected issue
  context: {
    contentType: string;
    platform: string;
    audience: string;
    advisorSpecialties: string[];
  };
  analysisDepth: 'quick' | 'comprehensive'; // Analysis detail level
}
```

**Response**:
```typescript
interface ViolationAnalysisResponse {
  analysis: {
    violationDetected: boolean;
    violationType: string;
    confidenceScore: number; // 0-100
    severity: 'low' | 'medium' | 'high' | 'critical';
    explanation: string;
  };
  regulations: RegulationReference[];
  suggestions: {
    suggestedFix: string;
    alternativeLanguage: string[];
    additionalContext: string;
    recommendedActions: string[];
  };
  metadata: {
    warrenSessionId: string; // For audit trail
    processingTimeMs: number;
    sourcesConsulted: number;
    analysisVersion: string;
  };
}

interface RegulationReference {
  source: 'FINRA' | 'SEC' | 'STATE';
  ruleNumber: string;
  ruleTitle: string;
  relevantSection: string;
  violationDescription: string;
  citationUrl: string;
  severity: 'guidance' | 'requirement' | 'prohibition';
  penalties: string[];
}
```

#### **GET /api/v1/compliance/upgrade/info**
**Purpose**: Get upgrade information and pricing (lite version)

**Authentication**: Review token validation

**Response**:
```typescript
interface UpgradeInfoResponse {
  pricing: {
    monthlyPricePerSeat: number; // $300
    minimumSeats: number; // 1
    maximumSeats: number; // 50
    annualDiscount: number; // 10% if paid annually
  };
  trial: {
    available: boolean;
    durationDays: number; // 30 days
    fullFeaturesIncluded: boolean;
    requiresCreditCard: boolean;
  };
  features: {
    lite: UpgradeFeature[];
    full: UpgradeFeature[];
    comparison: FeatureComparison[];
  };
  benefits: {
    timesSavings: string; // "Save 15+ hours per month"
    efficiency: string; // "Review 3x faster with AI assistance"
    insights: string; // "Advanced analytics and reporting"
  };
  support: {
    migrationSupport: boolean;
    trainingIncluded: boolean;
    supportLevel: 'email' | 'priority' | 'dedicated';
  };
}

interface UpgradeFeature {
  id: string;
  name: string;
  description: string;
  category: 'review' | 'analytics' | 'collaboration' | 'automation';
  available: boolean;
}

interface FeatureComparison {
  feature: string;
  lite: boolean | string;
  full: boolean | string;
  highlight: boolean; // Whether to emphasize this difference
}
```

---## 🔐 **Full Version API Endpoints**

### **Authentication & Account Management**

#### **POST /api/v1/compliance/auth/register**
**Purpose**: Register new CCO account (full version)

**Authentication**: None (public endpoint)

**Request Body**:
```typescript
interface RegistrationRequest {
  // Account details
  email: string; // Must be valid email format
  password: string; // Min 12 characters, complexity requirements
  confirmPassword: string; // Must match password
  
  // Company information
  companyName: string;
  companyType: 'ria' | 'broker_dealer' | 'compliance_firm' | 'other';
  
  // Personal information
  firstName: string;
  lastName: string;
  jobTitle: string;
  phone?: string;
  
  // Subscription details
  seatsRequested: number; // 1-50, default 1
  billingEmail?: string; // If different from account email
  
  // Optional
  referralCode?: string;
  marketingConsent: boolean;
  termsAccepted: boolean; // Required
  privacyPolicyAccepted: boolean; // Required
}
```

**Validation Rules**:
- Email must be valid and not already registered
- Password must meet complexity requirements (12+ chars, mixed case, numbers, symbols)
- Company name required, min 2 characters
- seatsRequested must be 1-50
- termsAccepted and privacyPolicyAccepted must be true

**Response**:
```typescript
interface RegistrationResponse {
  success: boolean;
  user: {
    id: string;
    email: string;
    name: string;
    companyName: string;
    subscriptionStatus: 'trial';
  };
  subscription: {
    type: 'trial';
    trialEndsAt: string; // 30 days from registration
    seatsIncluded: number;
    monthlyPrice: number; // What they'll pay after trial
  };
  nextSteps: {
    verifyEmail: {
      required: boolean;
      emailSent: boolean;
      verificationUrl?: string; // For testing environments
    };
    setupMFA: {
      required: boolean;
      methods: string[]; // ['sms', 'email', 'authenticator']
    };
    completeProfile: {
      required: boolean;
      missingFields: string[];
    };
  };
  onboarding: {
    welcomeUrl: string;
    tutorialUrl: string;
    supportEmail: string;
  };
}
```

#### **POST /api/v1/compliance/auth/login**
**Purpose**: Authenticate CCO user

**Authentication**: None (login endpoint)

**Request Body**:
```typescript
interface LoginRequest {
  email: string;
  password: string;
  mfaCode?: string; // Required if MFA enabled for user
  rememberMe?: boolean; // Extend session duration
  deviceId?: string; // For device tracking
}
```

**Response**:
```typescript
interface LoginResponse {
  success: boolean;
  authentication: {
    accessToken: string; // JWT token (8 hours)
    refreshToken: string; // For token renewal (30 days)
    tokenType: 'Bearer';
    expiresIn: number; // Seconds until access token expires
  };
  user: {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'reviewer' | 'viewer';
    companyName: string;
    permissions: string[];
    avatar?: string;
  };
  subscription: {
    type: 'trial' | 'active' | 'expired' | 'cancelled';
    seatsTotal: number;
    seatsUsed: number;
    expiresAt?: string;
    billingStatus: 'current' | 'past_due' | 'cancelled';
  };
  session: {
    sessionId: string;
    lastLoginAt: string;
    mfaVerified: boolean;
    deviceTrusted: boolean;
  };
  // Conditional response fields
  mfaRequired?: {
    required: boolean;
    methods: string[];
    challenge: string; // For SMS/Email MFA
  };
  passwordExpired?: {
    expired: boolean;
    changeRequired: boolean;
    changeUrl: string;
  };
}
```

#### **POST /api/v1/compliance/auth/refresh**
**Purpose**: Refresh access token using refresh token

**Authentication**: Refresh token in body

**Request Body**:
```typescript
interface RefreshTokenRequest {
  refreshToken: string;
}
```

**Response**:
```typescript
interface RefreshTokenResponse {
  success: boolean;
  accessToken: string;
  refreshToken: string; // New refresh token
  expiresIn: number;
}
```

#### **POST /api/v1/compliance/auth/logout**
**Purpose**: Logout and invalidate tokens

**Authentication**: JWT token

**Request Body**:
```typescript
interface LogoutRequest {
  allDevices?: boolean; // Logout from all devices
}
```

**Response**:
```typescript
interface LogoutResponse {
  success: boolean;
  message: string;
  tokensInvalidated: number;
}
```

### **Account & Team Management**

#### **GET /api/v1/compliance/account/profile**
**Purpose**: Get account profile information

**Authentication**: JWT token

**Response**:
```typescript
interface AccountProfileResponse {
  account: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    jobTitle: string;
    phone?: string;
    avatar?: string;
    companyName: string;
    companyType: string;
    timezone: string;
    locale: string;
  };
  subscription: {
    type: 'trial' | 'active' | 'expired';
    plan: 'standard' | 'premium' | 'enterprise';
    seatsTotal: number;
    seatsUsed: number;
    monthlyPrice: number;
    billingCycle: 'monthly' | 'annual';
    nextBillingDate?: string;
    trialEndsAt?: string;
  };
  security: {
    mfaEnabled: boolean;
    lastPasswordChange: string;
    sessionCount: number;
    trustedDevices: number;
  };
  usage: {
    reviewsThisMonth: number;
    averageReviewTime: number;
    lastActivityAt: string;
    totalReviewsCompleted: number;
  };
}
```

#### **PUT /api/v1/compliance/account/profile**
**Purpose**: Update account profile

**Authentication**: JWT token

**Request Body**:
```typescript
interface UpdateProfileRequest {
  firstName?: string;
  lastName?: string;
  jobTitle?: string;
  phone?: string;
  companyName?: string;
  timezone?: string;
  locale?: string;
  avatar?: string; // Base64 encoded or URL
  preferences?: {
    emailNotifications: boolean;
    smsNotifications: boolean;
    reviewReminders: boolean;
    weeklyReports: boolean;
  };
}
```

#### **GET /api/v1/compliance/team/members**
**Purpose**: Get team members (full version)

**Authentication**: JWT token with 'team_view' permission

**Query Parameters**:
```typescript
interface TeamMembersParams {
  page?: number;
  limit?: number;
  role?: 'admin' | 'reviewer' | 'viewer';
  status?: 'active' | 'inactive' | 'pending';
  search?: string; // Search by name or email
}
```

**Response**:
```typescript
interface TeamMembersResponse {
  members: TeamMember[];
  pagination: PaginationInfo;
  summary: {
    totalMembers: number;
    activeMembers: number;
    pendingInvitations: number;
    availableSeats: number;
  };
}

interface TeamMember {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'reviewer' | 'viewer';
  status: 'active' | 'inactive' | 'pending';
  permissions: string[];
  invitedAt: string;
  joinedAt?: string;
  lastLoginAt?: string;
  reviewsCompleted: number;
  averageReviewTime: number;
}
```

#### **POST /api/v1/compliance/team/invite**
**Purpose**: Invite team member

**Authentication**: JWT token with 'team_manage' permission

**Request Body**:
```typescript
interface InviteTeamMemberRequest {
  email: string;
  name: string;
  role: 'admin' | 'reviewer' | 'viewer';
  permissions?: string[]; // Custom permissions
  message?: string; // Personal message in invitation
  expiresInDays?: number; // Default 7 days
}
```

**Response**:
```typescript
interface InviteTeamMemberResponse {
  success: boolean;
  invitation: {
    id: string;
    email: string;
    role: string;
    expiresAt: string;
    invitationUrl: string;
  };
  emailSent: boolean;
  seatsRemaining: number;
}
```

---### **Dashboard & Analytics**

#### **GET /api/v1/compliance/dashboard**
**Purpose**: Multi-advisor dashboard data

**Authentication**: JWT token (full version)

**Query Parameters**:
```typescript
interface DashboardParams {
  timeRange?: '24h' | '7d' | '30d' | '90d'; // Default: 7d
  advisorIds?: string[]; // Filter specific advisors
  includeMetrics?: boolean; // Default: true
  includeAlerts?: boolean; // Default: true
  timezone?: string; // For time-based data
}
```

**Response**:
```typescript
interface DashboardResponse {
  summary: {
    totalPendingReviews: number;
    averageReviewTimeHours: number;
    approvalRatePercent: number;
    monthlyReviewVolume: number;
    connectedAdvisors: number;
    overdueReviews: number;
  };
  pendingReviews: PendingReview[];
  recentActivity: Activity[];
  metrics: DashboardMetrics;
  alerts: Alert[];
  quickStats: {
    todayReviews: number;
    weekReviews: number;
    monthReviews: number;
    quarterReviews: number;
  };
}

interface PendingReview {
  id: string;
  contentId: string;
  contentTitle: string;
  contentType: string;
  advisorName: string;
  advisorFirm: string;
  advisorEmail: string;
  submittedAt: string;
  ageInDays: number;
  ageInHours: number;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  estimatedReviewTime: number; // minutes
  platform: string;
  audience: string;
  complexity: 'simple' | 'moderate' | 'complex';
  tags: string[];
}

interface Activity {
  id: string;
  type: 'review_completed' | 'content_submitted' | 'advisor_connected' | 'violation_detected' | 'bulk_action';
  advisorName: string;
  advisorFirm?: string;
  contentTitle?: string;
  description: string;
  timestamp: string;
  severity?: 'low' | 'medium' | 'high';
  metadata?: {
    reviewDecision?: 'approved' | 'rejected';
    violationCount?: number;
    bulkActionCount?: number;
  };
}

interface DashboardMetrics {
  reviewVelocity: {
    daily: number[];
    dates: string[];
    trend: 'increasing' | 'decreasing' | 'stable';
  };
  approvalTrends: {
    approved: number;
    rejected: number;
    period: string;
    approvalRate: number;
  }[];
  violationTypes: {
    type: string;
    category: string;
    count: number;
    percentage: number;
    trend: 'up' | 'down' | 'stable';
  }[];
  advisorPerformance: {
    advisorName: string;
    advisorId: string;
    approvalRate: number;
    averageReviewTime: number;
    totalSubmissions: number;
    qualityScore: number;
  }[];
  timeDistribution: {
    hour: number;
    reviewCount: number;
    approvalRate: number;
  }[];
}

interface Alert {
  id: string;
  type: 'overdue_review' | 'high_rejection_rate' | 'new_regulation' | 'system_maintenance' | 'usage_limit';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  actionRequired: boolean;
  actionUrl?: string;
  actionText?: string;
  createdAt: string;
  expiresAt?: string;
  dismissible: boolean;
  metadata?: {
    advisorName?: string;
    reviewCount?: number;
    violationType?: string;
  };
}
```

#### **GET /api/v1/compliance/advisors**
**Purpose**: Advisor relationship management

**Authentication**: JWT token (full version)

**Query Parameters**:
```typescript
interface AdvisorListParams {
  page?: number; // Default: 1
  limit?: number; // Default: 25, max: 100
  search?: string; // Search by name, email, firm
  status?: 'connected' | 'pending' | 'disconnected' | 'all';
  sortBy?: 'name' | 'firm' | 'lastActivity' | 'approvalRate' | 'reviewCount';
  sortOrder?: 'asc' | 'desc';
  firm?: string; // Filter by firm
  dateRange?: {
    start: string;
    end: string;
  };
}
```

**Response**:
```typescript
interface AdvisorListResponse {
  advisors: AdvisorSummary[];
  pagination: {
    page: number;
    limit: number;
    totalPages: number;
    totalCount: number;
  };
  filters: {
    availableStatuses: string[];
    availableFirms: string[];
    totalConnected: number;
    totalPending: number;
    totalDisconnected: number;
  };
  summary: {
    totalAdvisors: number;
    activeThisMonth: number;
    newThisMonth: number;
    averageApprovalRate: number;
  };
}

interface AdvisorSummary {
  id: string;
  name: string;
  email: string;
  firm: string;
  phone?: string;
  licenseNumber?: string;
  specialties: string[];
  connectionStatus: 'connected' | 'pending' | 'disconnected';
  connectedAt: string;
  lastActivityAt: string;
  stats: {
    totalContentSubmitted: number;
    pendingReviews: number;
    approvalRate: number; // percentage
    averageReviewTimeHours: number;
    lastSubmissionAt?: string;
    complianceScore: number; // 1-100
    qualityTrend: 'improving' | 'declining' | 'stable';
  };
  preferences: {
    notificationEmail: boolean;
    urgentOnly: boolean;
    preferredReviewTime: number; // hours
    reminderFrequency: 'daily' | 'weekly' | 'never';
  };
  tags: string[];
  notes?: string; // CCO notes about this advisor
}
```

#### **GET /api/v1/compliance/advisor/{id}**
**Purpose**: Get detailed advisor information

**Authentication**: JWT token (full version)

**Response**:
```typescript
interface AdvisorDetailResponse {
  advisor: {
    id: string;
    name: string;
    email: string;
    firm: string;
    phone?: string;
    licenseNumber?: string;
    specialties: string[];
    registrationDate: string;
    connectionStatus: 'connected' | 'pending' | 'disconnected';
    connectedAt: string;
    lastActivityAt: string;
    biography?: string;
    website?: string;
    socialProfiles: {
      linkedin?: string;
      twitter?: string;
    };
  };
  performance: {
    overallStats: {
      totalSubmissions: number;
      approvalRate: number;
      averageReviewTime: number;
      complianceScore: number;
      qualityTrend: 'improving' | 'declining' | 'stable';
    };
    monthlyTrends: {
      month: string;
      submissions: number;
      approvals: number;
      rejections: number;
      avgReviewTime: number;
    }[];
    violationHistory: {
      violationType: string;
      count: number;
      lastOccurrence: string;
      resolved: boolean;
    }[];
  };
  recentContent: {
    id: string;
    title: string;
    type: string;
    platform: string;
    submittedAt: string;
    status: string;
    decision?: 'approved' | 'rejected';
    reviewTime?: number;
  }[];
  relationship: {
    connectionType: 'lite' | 'full';
    invitedBy?: string;
    invitedAt?: string;
    preferences: {
      notificationSettings: any;
      reviewPreferences: any;
    };
    notes: string;
    tags: string[];
  };
}
```

---### **Advanced Review Operations**

#### **POST /api/v1/compliance/reviews/bulk-action**
**Purpose**: Bulk approve/reject operations

**Authentication**: JWT token with 'bulk_review' permission

**Request Body**:
```typescript
interface BulkReviewRequest {
  reviewIds: string[]; // Max 50 reviews per request
  action: 'approve' | 'reject' | 'request_changes';
  feedback?: string; // Overall feedback for all reviews
  applyTemplate?: string; // Template ID for standardized feedback
  individualFeedback?: {
    [reviewId: string]: {
      feedback: string;
      violationTypes: string[];
      complianceScore: number;
      sectionFeedback: SectionFeedback[];
    };
  };
  notifyAdvisors: boolean; // Default: true
  priority: 'normal' | 'high'; // Processing priority
  reason?: string; // Reason for bulk action (for audit)
}
```

**Response**:
```typescript
interface BulkReviewResponse {
  success: boolean;
  batchId: string; // For tracking batch operation
  processed: {
    total: number;
    successful: number;
    failed: number;
    skipped: number;
  };
  results: BulkActionResult[];
  summary: {
    approved: number;
    rejected: number;
    requestedChanges: number;
  };
  notifications: {
    emailsSent: number;
    emailsFailed: number;
    advisorsNotified: string[];
  };
  estimatedCompletionTime: string; // For large batches
}

interface BulkActionResult {
  reviewId: string;
  contentId: string;
  contentTitle: string;
  advisorName: string;
  advisorEmail: string;
  status: 'success' | 'failed' | 'skipped';
  action: 'approved' | 'rejected' | 'requested_changes';
  error?: string;
  warning?: string;
  processedAt: string;
}
```

#### **GET /api/v1/compliance/reviews/history**
**Purpose**: Review history with search and filtering

**Authentication**: JWT token (full version)

**Query Parameters**:
```typescript
interface ReviewHistoryParams {
  page?: number; // Default: 1
  limit?: number; // Default: 25, max: 100
  startDate?: string; // ISO date
  endDate?: string; // ISO date
  advisorIds?: string[];
  decisions?: ('approved' | 'rejected')[];
  violationTypes?: string[];
  platforms?: string[];
  contentTypes?: string[];
  search?: string; // Search content title, advisor name
  sortBy?: 'reviewedAt' | 'advisorName' | 'contentTitle' | 'reviewTime' | 'complianceScore';
  sortOrder?: 'asc' | 'desc';
  includeMetadata?: boolean; // Include detailed metadata
}
```

**Response**:
```typescript
interface ReviewHistoryResponse {
  reviews: ReviewHistoryItem[];
  pagination: PaginationInfo;
  filters: {
    dateRange: { earliest: string; latest: string };
    availableAdvisors: { id: string; name: string; firm: string }[];
    availableViolationTypes: string[];
    availablePlatforms: string[];
    availableContentTypes: string[];
  };
  analytics: {
    totalReviews: number;
    averageReviewTime: number;
    approvalRate: number;
    commonViolations: { type: string; count: number; percentage: number }[];
    monthlyTrends: {
      month: string;
      reviewCount: number;
      approvalRate: number;
      avgReviewTime: number;
    }[];
  };
}

interface ReviewHistoryItem {
  id: string;
  contentId: string;
  contentTitle: string;
  contentType: string;
  contentPreview: string; // First 100 characters
  advisor: {
    id: string;
    name: string;
    email: string;
    firm: string;
  };
  review: {
    decision: 'approved' | 'rejected';
    reviewedAt: string;
    submittedAt: string;
    reviewTimeMinutes: number;
    reviewedBy: string; // CCO who reviewed
    complianceScore?: number;
  };
  feedback: {
    overallFeedback: string;
    violationTypes: string[];
    sectionFeedbackCount: number;
    severity: 'low' | 'medium' | 'high' | 'critical';
  };
  content: {
    platform: string;
    audience: string;
    wordCount: number;
    tags: string[];
  };
  outcome: {
    advisorAccepted?: boolean;
    distributionStatus?: 'distributed' | 'pending' | 'not_distributed';
    distributedAt?: string;
    distributionChannels?: string[];
  };
}
```

#### **GET /api/v1/compliance/reviews/templates**
**Purpose**: Get feedback templates for standardized responses

**Authentication**: JWT token (full version)

**Query Parameters**:
```typescript
interface TemplatesParams {
  category?: 'approval' | 'rejection' | 'modification';
  violationType?: string;
  platform?: string;
  includeCustom?: boolean; // Include user-created templates
}
```

**Response**:
```typescript
interface TemplatesResponse {
  templates: FeedbackTemplate[];
  categories: string[];
  usage: {
    [templateId: string]: {
      usageCount: number;
      lastUsed: string;
      effectiveness: number; // Based on advisor acceptance rate
    };
  };
}

interface FeedbackTemplate {
  id: string;
  name: string;
  category: 'approval' | 'rejection' | 'modification';
  violationType?: string;
  subject: string;
  content: string;
  variables: TemplateVariable[]; // Placeholders like {{advisorName}}
  applicablePlatforms: string[];
  isCustom: boolean; // User-created vs system template
  createdBy?: string;
  createdAt: string;
  lastModified: string;
  usageCount: number;
  effectiveness: number; // 0-100 based on outcomes
}

interface TemplateVariable {
  name: string;
  description: string;
  required: boolean;
  defaultValue?: string;
  type: 'text' | 'number' | 'date' | 'select';
  options?: string[]; // For select type
}
```

### **Warren AI Integration**

#### **POST /api/v1/compliance/warren/improve-content**
**Purpose**: Use Warren to improve content during review

**Authentication**: JWT token with 'warren_access' permission

**Request Body**:
```typescript
interface WarrenImprovementRequest {
  contentId: string;
  originalContent: string;
  issues: ContentIssue[];
  improvementGoals: string[];
  context: {
    platform: string;
    audience: string;
    contentType: string;
    advisorBackground: {
      firm: string;
      specialties: string[];
      licenseType: string;
    };
  };
  preferences: {
    preserveStyle: boolean; // Maintain original tone/style
    preserveLength: boolean; // Keep similar word count
    maintainIntent: boolean; // Preserve original message
    complianceLevel: 'strict' | 'moderate' | 'flexible';
  };
}

interface ContentIssue {
  sectionText: string;
  violationType: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  regulationReference?: string;
  suggestedCategory: string;
}
```

**Response**:
```typescript
interface WarrenImprovementResponse {
  sessionId: string; // Warren session for audit trail
  improvedContent: string;
  changes: ContentChange[];
  analysis: {
    originalComplianceScore: number;
    improvedComplianceScore: number;
    scoreImprovement: number;
    issuesResolved: number;
    issuesRemaining: ContentIssue[];
    newIssuesCreated: ContentIssue[];
  };
  suggestions: {
    additionalImprovements: string[];
    alternativeApproaches: string[];
    disclaimersToAdd: string[];
    platformOptimizations: string[];
  };
  metadata: {
    processingTimeMs: number;
    sourcesUsed: number;
    confidenceScore: number; // 0-100
    warrenVersion: string;
    requestTokens: number;
    responseTokens: number;
  };
  workflow: {
    requiresReview: boolean;
    autoApprovalEligible: boolean;
    recommendedAction: 'approve' | 'review' | 'reject';
    reviewPriority: 'low' | 'normal' | 'high';
  };
}

interface ContentChange {
  changeId: string;
  type: 'addition' | 'deletion' | 'modification' | 'replacement';
  originalText: string;
  improvedText: string;
  startPosition: number;
  endPosition: number;
  rationale: string;
  violationAddressed: string;
  regulationReference?: string;
  impactLevel: 'minor' | 'moderate' | 'major';
  confidence: number; // 0-100
  acceptanceRecommended: boolean;
}
```

#### **POST /api/v1/compliance/warren/analyze-content**
**Purpose**: Get Warren's compliance analysis of content

**Authentication**: JWT token (full version)

**Request Body**:
```typescript
interface WarrenAnalysisRequest {
  content: string;
  context: {
    platform: string;
    audience: string;
    contentType: string;
    advisorInfo: {
      firm: string;
      licenseType: string;
      specialties: string[];
      complianceHistory: {
        recentViolations: string[];
        approvalRate: number;
      };
    };
  };
  analysisType: 'comprehensive' | 'violation_detection' | 'compliance_scoring' | 'risk_assessment';
  depth: 'quick' | 'standard' | 'thorough';
}
```

**Response**:
```typescript
interface WarrenAnalysisResponse {
  sessionId: string;
  analysis: {
    overallComplianceScore: number; // 1-100
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
    violationsDetected: DetectedViolation[];
    complianceGaps: ComplianceGap[];
    strengthAreas: string[];
    improvementAreas: string[];
  };
  recommendations: {
    immediateChanges: RecommendedChange[];
    suggestedImprovements: string[];
    disclaimersNeeded: DisclaimerRecommendation[];
    platformOptimizations: string[];
    reviewPriority: 'low' | 'normal' | 'high' | 'urgent';
  };
  regulatory: {
    applicableRules: RegulatoryRule[];
    potentialViolations: PotentialViolation[];
    complianceChecklist: ChecklistItem[];
  };
  metadata: {
    analysisDepth: string;
    sourcesConsulted: number;
    processingTimeMs: number;
    lastUpdated: string;
    warrenVersion: string;
    confidence: number;
  };
}

interface DetectedViolation {
  id: string;
  type: string;
  category: 'prohibited_language' | 'missing_disclosure' | 'misleading_claim' | 'performance_guarantee';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affectedText: string;
  textPosition: { start: number; end: number };
  regulationReference: {
    source: string;
    ruleNumber: string;
    section: string;
    url: string;
  };
  suggestedFix: string;
  confidenceLevel: number;
  falsePositiveRisk: number; // 0-100
}

interface ComplianceGap {
  area: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  recommendation: string;
  regulatoryBasis: string;
}

interface RecommendedChange {
  priority: 'must_fix' | 'should_fix' | 'consider_fixing';
  description: string;
  originalText: string;
  suggestedReplacement: string;
  rationale: string;
  regulationBasis: string;
}

interface DisclaimerRecommendation {
  type: 'risk_disclosure' | 'performance_disclaimer' | 'fee_disclosure' | 'regulatory_disclaimer';
  text: string;
  placement: 'beginning' | 'end' | 'inline';
  required: boolean;
  regulatoryBasis: string;
}

interface RegulatoryRule {
  source: 'FINRA' | 'SEC' | 'STATE';
  ruleNumber: string;
  title: string;
  applicability: string;
  requirements: string[];
  penalties: string[];
}

interface PotentialViolation {
  ruleNumber: string;
  description: string;
  likelihood: number; // 0-100
  severity: 'minor' | 'moderate' | 'major' | 'severe';
  preventionSteps: string[];
}

interface ChecklistItem {
  id: string;
  requirement: string;
  status: 'compliant' | 'non_compliant' | 'unclear' | 'not_applicable';
  explanation: string;
  actionRequired?: string;
}
```

---**This API Design Specification provides comprehensive technical documentation for implementing the Compliance Portal APIs, ensuring consistency, security, and scalability across both lite and full versions.**

---

## 🔗 **Shared Endpoint Integration**

### **Advisor Portal Integration Endpoints**

#### **POST /api/v1/advisor/content/{id}/submit-review**
**Purpose**: Submit content for compliance review (called from advisor portal)

**Authentication**: Advisor JWT token

**Request Body**:
```typescript
interface SubmitForReviewRequest {
  ccoEmail: string; // CCO email for lite version
  ccoId?: string; // CCO ID for full version (if relationship exists)
  priority: 'low' | 'normal' | 'high' | 'urgent';
  deadline?: string; // ISO date string
  notes?: string; // Additional context for CCO
  requestType: 'initial' | 'revision' | 'resubmission';
  notificationPreferences: {
    sendEmail: boolean;
    sendSMS: boolean;
    urgentOnly: boolean;
  };
}
```

**Response**:
```typescript
interface SubmitForReviewResponse {
  success: boolean;
  reviewId: string;
  reviewToken: string; // For lite version access
  submittedAt: string;
  estimatedReviewTime: string; // "2-3 business days"
  ccoNotified: boolean;
  reviewUrl: string; // URL for CCO access
  status: 'submitted' | 'in_queue' | 'assigned';
  tracking: {
    submissionId: string;
    expectedResponseBy: string;
    reminderSchedule: string[];
  };
}
```

#### **GET /api/v1/advisor/content/{id}/review-status**
**Purpose**: Check review status from advisor portal

**Authentication**: Advisor JWT token

**Response**:
```typescript
interface ReviewStatusResponse {
  contentId: string;
  reviewStatus: 'not_submitted' | 'submitted' | 'in_review' | 'approved' | 'rejected' | 'changes_requested';
  submittedAt?: string;
  reviewedAt?: string;
  cco: {
    email: string;
    name?: string; // If full version relationship
    firm?: string;
    responseTime: string; // "Usually responds within 24 hours"
  };
  timing: {
    estimatedCompletion?: string;
    ageInHours: number;
    isOverdue: boolean;
    remindersSent: number;
  };
  feedback?: {
    overallFeedback: string;
    sectionFeedback: SectionFeedback[];
    complianceScore: number;
    violationTypes: string[];
    reviewTimeMinutes: number;
  };
  nextSteps: string[]; // What advisor should do next
  actions: {
    canWithdraw: boolean;
    canResubmit: boolean;
    canRequestUrgent: boolean;
  };
}
```

### **Notification System Integration**

#### **POST /api/v1/notifications/compliance/review-invitation**
**Purpose**: Send review invitation email (internal system call)

**Authentication**: Internal system token

**Request Body**:
```typescript
interface ReviewInvitationRequest {
  ccoEmail: string;
  advisorInfo: {
    name: string;
    email: string;
    firm: string;
    phone?: string;
    licenseNumber?: string;
  };
  contentInfo: {
    id: string;
    title: string;
    type: string;
    platform: string;
    audience: string;
    wordCount: number;
    submittedAt: string;
  };
  reviewDetails: {
    reviewId: string;
    token: string;
    priority: string;
    deadline?: string;
    estimatedTime: number; // minutes
    specialInstructions?: string;
  };
  reviewUrl: string;
  branding: {
    companyName: string;
    logoUrl?: string;
    primaryColor?: string;
  };
}
```

---

## 🚨 **Error Handling & Status Codes**

### **Standard Error Response Format**
```typescript
interface APIError {
  success: false;
  error: {
    code: string; // Machine-readable error code
    message: string; // Human-readable error message
    details?: any; // Additional error context
    field?: string; // Specific field for validation errors
    timestamp: string;
    requestId: string;
    documentation?: string; // Link to relevant docs
  };
  meta: {
    timestamp: string;
    requestId: string;
    endpoint: string;
  };
}
```

### **Common Error Codes**

#### **Authentication Errors (401)**
```typescript
const AUTH_ERRORS = {
  INVALID_TOKEN: 'Authentication token is invalid or malformed',
  EXPIRED_TOKEN: 'Authentication token has expired',
  REVOKED_TOKEN: 'Authentication token has been revoked',
  MISSING_TOKEN: 'Authentication token is required',
  MFA_REQUIRED: 'Multi-factor authentication is required',
  ACCOUNT_LOCKED: 'Account has been temporarily locked'
};
```

#### **Authorization Errors (403)**
```typescript
const AUTHORIZATION_ERRORS = {
  INSUFFICIENT_PERMISSIONS: 'User does not have required permissions',
  RESOURCE_ACCESS_DENIED: 'Access to this resource is denied',
  ACCOUNT_SUSPENDED: 'Account has been suspended',
  FEATURE_NOT_AVAILABLE: 'Feature not available for current subscription',
  SEAT_LIMIT_EXCEEDED: 'Team seat limit has been exceeded'
};
```

#### **Validation Errors (422)**
```typescript
const VALIDATION_ERRORS = {
  INVALID_EMAIL: 'Email address format is invalid',
  PASSWORD_TOO_WEAK: 'Password does not meet security requirements',
  REQUIRED_FIELD_MISSING: 'Required field is missing',
  INVALID_ENUM_VALUE: 'Value is not one of the allowed options',
  STRING_TOO_LONG: 'Text exceeds maximum length',
  DUPLICATE_VALUE: 'Value already exists and must be unique'
};
```

#### **Business Logic Errors (409)**
```typescript
const BUSINESS_LOGIC_ERRORS = {
  REVIEW_ALREADY_COMPLETED: 'Content has already been reviewed',
  CONTENT_NOT_REVIEWABLE: 'Content is not in a reviewable state',
  ADVISOR_NOT_CONNECTED: 'Advisor is not connected to this CCO',
  SUBSCRIPTION_REQUIRED: 'Active subscription required for this action',
  BULK_ACTION_IN_PROGRESS: 'Another bulk action is currently in progress'
};
```

---

## 📝 **Implementation Guidelines**

### **API Versioning Strategy**
```typescript
// Current API version
const API_VERSION = 'v1';

// Version header support
const VERSION_HEADERS = {
  'API-Version': 'v1',
  'Accept-Version': 'application/vnd.fiducia.v1+json'
};

// Deprecation handling
interface DeprecationWarning {
  deprecated: boolean;
  deprecationDate?: string;
  sunsetDate?: string;
  replacementEndpoint?: string;
  migrationGuide?: string;
}
```

### **Security Headers**
```typescript
const SECURITY_HEADERS = {
  'Content-Security-Policy': "default-src 'self'",
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Referrer-Policy': 'strict-origin-when-cross-origin'
};
```

### **Audit Logging Requirements**
```typescript
interface AuditLogEntry {
  timestamp: string;
  requestId: string;
  userId?: string;
  userEmail?: string;
  action: string;
  resource: string;
  endpoint: string;
  method: string;
  statusCode: number;
  ipAddress: string;
  metadata?: {
    reviewDecision?: string;
    contentId?: string;
    advisorId?: string;
    warrenSessionId?: string;
  };
  sensitive: boolean;
  compliance: boolean;
}

// Required audit events
const AUDIT_EVENTS = [
  'review_submitted',
  'review_approved',
  'review_rejected',
  'bulk_action_performed',
  'warren_ai_used',
  'advisor_connected',
  'team_member_added',
  'account_created',
  'login_attempt',
  'password_changed'
];
```

### **Rate Limiting Configuration**
```typescript
const RATE_LIMITS = {
  lite: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 20, // 20 requests per window
  },
  full: {
    windowMs: 15 * 60 * 1000,
    max: 100, // 100 requests per window
  },
  warren: {
    windowMs: 60 * 1000, // 1 minute
    max: 10, // 10 AI requests per minute
  }
};
```

### **Performance Monitoring**
```typescript
interface PerformanceMetrics {
  responseTime: {
    p50: number; // 50th percentile
    p95: number; // 95th percentile
    p99: number; // 99th percentile
  };
  throughput: {
    requestsPerSecond: number;
    requestsPerMinute: number;
  };
  errorRate: {
    total: number; // Percentage
    byStatusCode: { [code: number]: number };
  };
}
```

---

**This API Design Specification provides comprehensive technical documentation for implementing the Compliance Portal APIs, ensuring consistency, security, and scalability across both lite and full versions.**