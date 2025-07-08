// Core compliance types
export interface ReviewToken {
  contentId: string;
  ccoEmail: string;
  issuedAt: number;
  expiresAt?: number;
  signature: string;
}

export interface CCOSession {
  userId: string;
  ccoId: string;
  role: 'admin' | 'reviewer' | 'viewer';
  permissions: string[];
  teamId?: string;
  mfaVerified: boolean;
  sessionId: string;
  expiresAt: number;
}

// Content review types
export interface ContentForReview {
  id: string;
  title: string;
  content: string;
  contentType: 'linkedin_post' | 'email' | 'blog_post' | 'newsletter' | 'website_copy';
  platform: string;
  audience: string;
  createdAt: string;
  metadata: {
    wordCount: number;
    characterCount: number;
    estimatedReadTime: number;
    tags: string[];
  };
}

export interface AdvisorInfo {
  name: string;
  email: string;
  firm: string;
  phone?: string;
  licenseNumber?: string;
  specialties: string[];
}

export interface ReviewInfo {
  id: string;
  status: 'pending' | 'in_progress' | 'approved' | 'rejected';
  submittedAt: string;
  deadline?: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  ageInDays: number;
  estimatedReviewTime: number;
}

export interface ComplianceContext {
  companyPolicies: PolicyDocument[];
  regulatoryGuidelines: RegulatoryReference[];
  violationTypes: ViolationType[];
}

export interface PolicyDocument {
  id: string;
  title: string;
  category: 'marketing' | 'communication' | 'disclosure' | 'general';
  lastUpdated: string;
  summary: string;
  documentUrl?: string;
  applicableContent: string[];
}

export interface RegulatoryReference {
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

export interface ViolationType {
  id: string;
  category: 'company_policy' | 'finra_rule' | 'sec_regulation' | 'state_regulation';
  name: string;
  description: string;
  commonExamples: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  regulationReference?: string;
}

// Review feedback types
export interface SectionFeedback {
  sectionText: string;
  startPosition: number;
  endPosition: number;
  violationType: string;
  comment: string;
  suggestedFix?: string;
  regulationReference?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  aiAssisted: boolean;
}

export interface ReviewSubmission {
  token: string;
  decision: 'approved' | 'rejected';
  overallFeedback?: string;
  complianceScore?: number;
  sectionFeedback: SectionFeedback[];
  reviewTimeMinutes?: number;
  confidence: number;
}

// API response types
export interface ContentReviewResponse {
  content: ContentForReview;
  advisor: AdvisorInfo;
  review: ReviewInfo;
  compliance: ComplianceContext;
  upgrade: UpgradeInfo;
}

export interface UpgradeInfo {
  showPrompt: boolean;
  benefits: string[];
  pricingUrl: string;
  trialInfo: {
    available: boolean;
    durationDays: number;
    featuresIncluded: string[];
  };
}

export interface ReviewSubmissionResponse {
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

// Warren AI integration types
export interface ViolationAnalysisRequest {
  token: string;
  sectionText: string;
  suspectedViolation: string;
  context: {
    contentType: string;
    platform: string;
    audience: string;
    advisorSpecialties: string[];
  };
  analysisDepth: 'quick' | 'comprehensive';
}

export interface ViolationAnalysisResponse {
  analysis: {
    violationDetected: boolean;
    violationType: string;
    confidenceScore: number;
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
    warrenSessionId: string;
    processingTimeMs: number;
    sourcesConsulted: number;
    analysisVersion: string;
  };
}

export interface RegulationReference {
  source: 'FINRA' | 'SEC' | 'STATE';
  ruleNumber: string;
  ruleTitle: string;
  relevantSection: string;
  violationDescription: string;
  citationUrl: string;
  severity: 'guidance' | 'requirement' | 'prohibition';
  penalties: string[];
}

// Standard API response wrapper
export interface APIResponse<T> {
  success: true;
  data: T;
  meta?: {
    timestamp: string;
    requestId: string;
    version: string;
  };
}

export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
    field?: string;
  };
  meta: {
    timestamp: string;
    requestId: string;
  };
}
