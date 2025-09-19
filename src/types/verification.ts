export interface DocumentVerificationRequest {
  id: string
  userId: string
  documentType: 'government_id' | 'proof_of_address' | 'organization_license' | 'business_registration' | 'reference_letter' | 'certification'
  documentUrl: string
  uploadedAt: string
  status: 'pending' | 'processing' | 'verified' | 'rejected' | 'requires_human_review'
  metadata: {
    fileName: string
    fileSize: number
    mimeType: string
    extractedData?: Record<string, any>
    confidenceScore?: number
    flags?: string[]
  }
  verificationResults?: {
    ocrText?: string
    extractedFields?: Record<string, any>
    authenticityScore?: number
    qualityScore?: number
    complianceChecks?: Array<{
      check: string
      passed: boolean
      details?: string
    }>
  }
  rejectionReason?: string
  reviewedBy?: string
  reviewedAt?: string
  expiresAt?: string
}

export interface ReferenceVerificationRequest {
  id: string
  userId: string
  referenceType: 'personal' | 'professional' | 'organization'
  referenceName: string
  referenceEmail: string
  referencePhone?: string
  relationship: string
  yearsKnown: number
  status: 'pending' | 'sent' | 'responded' | 'verified' | 'failed' | 'expired'
  verificationCode: string
  requestedAt: string
  respondedAt?: string
  expiresAt: string
  response?: {
    canRecommend: boolean
    relationship: string
    yearsKnown: number
    trustworthiness: 1 | 2 | 3 | 4 | 5
    reliability: 1 | 2 | 3 | 4 | 5
    comments?: string
  }
  metadata: {
    ipAddress?: string
    userAgent?: string
    geolocation?: string
  }
}

export interface InPersonVerificationRequest {
  id: string
  userId: string
  organizationId: string
  verifierUserId: string
  qrCode: string
  status: 'pending' | 'scheduled' | 'completed' | 'failed' | 'expired'
  scheduledAt?: string
  completedAt?: string
  location?: {
    name: string
    address: string
    coordinates?: {
      lat: number
      lng: number
    }
  }
  verificationData?: {
    documentsVerified: string[]
    identityConfirmed: boolean
    biometricMatch?: boolean
    notes?: string
  }
  expiresAt: string
}

export interface VerificationWorkflow {
  id: string
  userId: string
  userType: 'individual' | 'organization' | 'business'
  status: 'in_progress' | 'completed' | 'failed' | 'requires_action'
  startedAt: string
  completedAt?: string
  requiredSteps: VerificationStep[]
  completedSteps: string[]
  currentStep?: string
  riskScore: number
  fraudFlags: string[]
  compliance: {
    kycCompleted: boolean
    amlCompleted: boolean
    documentsVerified: boolean
    referencesVerified: boolean
    inPersonVerified: boolean
  }
}

export interface VerificationStep {
  id: string
  type: 'document_upload' | 'reference_submission' | 'in_person_verification' | 'background_check' | 'compliance_review'
  name: string
  description: string
  required: boolean
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped'
  dependencies?: string[]
  estimatedDuration: number // in minutes
  instructions: string[]
  requirements: Record<string, any>
  completedAt?: string
  result?: Record<string, any>
}

export interface VerificationAuditLog {
  id: string
  userId: string
  workflowId: string
  action: string
  timestamp: string
  actor: 'system' | 'user' | 'admin' | 'ai_agent'
  details: Record<string, any>
  riskImpact: 'none' | 'low' | 'medium' | 'high' | 'critical'
  ipAddress?: string
  userAgent?: string
}