export interface OnboardingStep {
  id: string
  name: string
  description: string
  type: 'form' | 'document_upload' | 'verification' | 'review' | 'confirmation'
  userTypes: Array<'individual' | 'organization' | 'business'>
  required: boolean
  order: number
  dependencies: string[]
  estimatedDuration: number // in minutes
  instructions: string[]
  validationRules?: Record<string, any>
  helpText?: string
  videoUrl?: string
}

export interface OnboardingProgress {
  id: string
  userId: string
  userType: 'individual' | 'organization' | 'business'
  status: 'not_started' | 'in_progress' | 'completed' | 'suspended' | 'failed'
  startedAt: string
  completedAt?: string
  suspendedAt?: string
  lastActiveAt: string
  currentStepId?: string
  completedSteps: Array<{
    stepId: string
    completedAt: string
    duration: number // in seconds
    attempts: number
    data?: Record<string, any>
  }>
  failedSteps: Array<{
    stepId: string
    failedAt: string
    reason: string
    attempts: number
    canRetry: boolean
  }>
  skippedSteps: Array<{
    stepId: string
    skippedAt: string
    reason: string
  }>
  analytics: {
    totalSteps: number
    completedSteps: number
    progressPercentage: number
    estimatedTimeRemaining: number // in minutes
    totalTimeSpent: number // in minutes
    averageStepDuration: number // in minutes
    stepsWithErrors: number
    retryAttempts: number
  }
  metadata: {
    deviceInfo?: string
    browserInfo?: string
    referralSource?: string
    initialUtmParams?: Record<string, string>
  }
}

export interface OnboardingAnalytics {
  id: string
  userId: string
  stepId: string
  event: 'step_started' | 'step_completed' | 'step_failed' | 'step_skipped' | 'step_abandoned' | 'help_viewed' | 'video_watched'
  timestamp: string
  duration?: number // in milliseconds
  metadata: {
    attempts?: number
    errorType?: string
    errorMessage?: string
    fieldsFilled?: string[]
    validationErrors?: string[]
    userAgent?: string
    deviceType?: 'desktop' | 'tablet' | 'mobile'
    networkSpeed?: 'slow' | 'fast' | 'unknown'
    pageLoadTime?: number
  }
  sessionId: string
  riskFlags?: string[]
}

export interface OnboardingTemplate {
  id: string
  name: string
  userType: 'individual' | 'organization' | 'business'
  version: string
  isActive: boolean
  steps: OnboardingStep[]
  requirements: {
    minimumAge?: number
    requiredDocuments: string[]
    requiredReferences: number
    requiresInPersonVerification: boolean
    complianceChecks: string[]
  }
  customization: {
    brandColors?: Record<string, string>
    logo?: string
    welcomeMessage?: string
    completionMessage?: string
  }
  analytics: {
    totalStarted: number
    totalCompleted: number
    completionRate: number
    averageCompletionTime: number // in minutes
    commonDropoffPoints: Array<{
      stepId: string
      dropoffRate: number
    }>
    errorPatterns: Array<{
      stepId: string
      errorType: string
      frequency: number
    }>
  }
}

export interface OnboardingSession {
  id: string
  userId: string
  progressId: string
  startedAt: string
  endedAt?: string
  isActive: boolean
  deviceInfo: {
    userAgent: string
    platform: string
    isMobile: boolean
    screenResolution: string
  }
  interactions: Array<{
    timestamp: string
    action: string
    element?: string
    data?: Record<string, any>
  }>
  performance: {
    pageLoadTimes: Record<string, number>
    apiResponseTimes: Record<string, number>
    errorCount: number
    warnings: string[]
  }
}