import { OnboardingProgress, OnboardingAnalytics, OnboardingStep, OnboardingTemplate, OnboardingSession } from '../types/onboarding'
import { UserProfile } from '../types/profiles'

/**
 * Onboarding Analytics Service
 * Tracks user progress, completion rates, and identifies optimization opportunities
 */
export class OnboardingAnalyticsService {
  private static instance: OnboardingAnalyticsService
  
  static getInstance(): OnboardingAnalyticsService {
    if (!OnboardingAnalyticsService.instance) {
      OnboardingAnalyticsService.instance = new OnboardingAnalyticsService()
    }
    return OnboardingAnalyticsService.instance
  }

  /**
   * Initialize onboarding progress for a new user
   */
  async initializeOnboardingProgress(userId: string, userType: 'individual' | 'organization' | 'business'): Promise<OnboardingProgress> {
    const template = await this.getOnboardingTemplate(userType)
    const sessionId = this.generateSessionId()
    
    const progress: OnboardingProgress = {
      id: `progress_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      userId,
      userType,
      status: 'not_started',
      startedAt: new Date().toISOString(),
      lastActiveAt: new Date().toISOString(),
      completedSteps: [],
      failedSteps: [],
      skippedSteps: [],
      analytics: {
        totalSteps: template.steps.length,
        completedSteps: 0,
        progressPercentage: 0,
        estimatedTimeRemaining: template.steps.reduce((sum, step) => sum + step.estimatedDuration, 0),
        totalTimeSpent: 0,
        averageStepDuration: 0,
        stepsWithErrors: 0,
        retryAttempts: 0
      },
      metadata: {
        deviceInfo: this.getDeviceInfo(),
        browserInfo: this.getBrowserInfo()
      }
    }

    await this.storeOnboardingProgress(progress)
    await this.createOnboardingSession(userId, progress.id, sessionId)
    
    return progress
  }

  /**
   * Start onboarding process
   */
  async startOnboarding(userId: string): Promise<OnboardingProgress> {
    const progress = await this.getOnboardingProgress(userId)
    if (!progress) throw new Error('Onboarding progress not found')

    const updatedProgress: OnboardingProgress = {
      ...progress,
      status: 'in_progress',
      startedAt: new Date().toISOString(),
      lastActiveAt: new Date().toISOString()
    }

    await this.storeOnboardingProgress(updatedProgress)
    await this.trackAnalyticsEvent(userId, 'onboarding', 'step_started', Date.now())
    
    return updatedProgress
  }

  /**
   * Track step completion
   */
  async completeStep(userId: string, stepId: string, duration: number, data?: Record<string, any>): Promise<OnboardingProgress> {
    const progress = await this.getOnboardingProgress(userId)
    if (!progress) throw new Error('Onboarding progress not found')

    const template = await this.getOnboardingTemplate(progress.userType)
    const step = template.steps.find(s => s.id === stepId)
    if (!step) throw new Error('Step not found')

    // Add to completed steps
    const completedStep = {
      stepId,
      completedAt: new Date().toISOString(),
      duration: Math.round(duration / 1000), // Convert to seconds
      attempts: this.getStepAttempts(progress, stepId) + 1,
      data
    }

    // Remove from failed steps if it was there
    const updatedFailedSteps = progress.failedSteps.filter(f => f.stepId !== stepId)
    const updatedCompletedSteps = [...progress.completedSteps.filter(c => c.stepId !== stepId), completedStep]

    // Update analytics
    const totalTimeSpent = updatedCompletedSteps.reduce((sum, step) => sum + step.duration, 0) / 60 // Convert to minutes
    const avgDuration = updatedCompletedSteps.length > 0 ? totalTimeSpent / updatedCompletedSteps.length : 0
    const completedCount = updatedCompletedSteps.length
    const progressPercentage = Math.round((completedCount / template.steps.length) * 100)
    
    // Calculate estimated time remaining
    const remainingSteps = template.steps.filter(s => !updatedCompletedSteps.some(c => c.stepId === s.id))
    const estimatedTimeRemaining = remainingSteps.reduce((sum, step) => sum + step.estimatedDuration, 0)

    const updatedProgress: OnboardingProgress = {
      ...progress,
      lastActiveAt: new Date().toISOString(),
      completedSteps: updatedCompletedSteps,
      failedSteps: updatedFailedSteps,
      currentStepId: this.getNextStepId(template, updatedCompletedSteps),
      status: completedCount === template.steps.length ? 'completed' : 'in_progress',
      completedAt: completedCount === template.steps.length ? new Date().toISOString() : undefined,
      analytics: {
        ...progress.analytics,
        completedSteps: completedCount,
        progressPercentage,
        estimatedTimeRemaining,
        totalTimeSpent,
        averageStepDuration: avgDuration
      }
    }

    await this.storeOnboardingProgress(updatedProgress)
    await this.trackAnalyticsEvent(userId, stepId, 'step_completed', duration, {
      attempts: completedStep.attempts,
      progressPercentage
    })

    return updatedProgress
  }

  /**
   * Track step failure
   */
  async failStep(userId: string, stepId: string, reason: string, canRetry: boolean = true): Promise<OnboardingProgress> {
    const progress = await this.getOnboardingProgress(userId)
    if (!progress) throw new Error('Onboarding progress not found')

    const attempts = this.getStepAttempts(progress, stepId) + 1
    const failedStep = {
      stepId,
      failedAt: new Date().toISOString(),
      reason,
      attempts,
      canRetry
    }

    // Update or add failed step
    const updatedFailedSteps = progress.failedSteps.filter(f => f.stepId !== stepId)
    updatedFailedSteps.push(failedStep)

    const updatedProgress: OnboardingProgress = {
      ...progress,
      lastActiveAt: new Date().toISOString(),
      failedSteps: updatedFailedSteps,
      analytics: {
        ...progress.analytics,
        stepsWithErrors: progress.analytics.stepsWithErrors + 1,
        retryAttempts: progress.analytics.retryAttempts + (attempts > 1 ? 1 : 0)
      }
    }

    await this.storeOnboardingProgress(updatedProgress)
    await this.trackAnalyticsEvent(userId, stepId, 'step_failed', 0, {
      reason,
      attempts,
      canRetry
    })

    return updatedProgress
  }

  /**
   * Skip a step
   */
  async skipStep(userId: string, stepId: string, reason: string): Promise<OnboardingProgress> {
    const progress = await this.getOnboardingProgress(userId)
    if (!progress) throw new Error('Onboarding progress not found')

    const skippedStep = {
      stepId,
      skippedAt: new Date().toISOString(),
      reason
    }

    const template = await this.getOnboardingTemplate(progress.userType)
    const updatedSkippedSteps = [...progress.skippedSteps.filter(s => s.stepId !== stepId), skippedStep]
    const nextStepId = this.getNextStepId(template, progress.completedSteps, updatedSkippedSteps)

    const updatedProgress: OnboardingProgress = {
      ...progress,
      lastActiveAt: new Date().toISOString(),
      skippedSteps: updatedSkippedSteps,
      currentStepId: nextStepId
    }

    await this.storeOnboardingProgress(updatedProgress)
    await this.trackAnalyticsEvent(userId, stepId, 'step_skipped', 0, { reason })

    return updatedProgress
  }

  /**
   * Track help viewed event
   */
  async trackHelpViewed(userId: string, stepId: string, helpType: 'text' | 'video'): Promise<void> {
    await this.trackAnalyticsEvent(userId, stepId, 'help_viewed', 0, { helpType })
  }

  /**
   * Track video watched event
   */
  async trackVideoWatched(userId: string, stepId: string, duration: number, completed: boolean): Promise<void> {
    await this.trackAnalyticsEvent(userId, stepId, 'video_watched', duration, { completed })
  }

  /**
   * Get onboarding analytics for a user
   */
  async getUserAnalytics(userId: string): Promise<{
    progress: OnboardingProgress | null
    session: OnboardingSession | null
    analytics: OnboardingAnalytics[]
  }> {
    const progress = await this.getOnboardingProgress(userId)
    const session = await this.getCurrentSession(userId)
    const analytics = await this.getUserAnalyticsEvents(userId)

    return { progress, session, analytics }
  }

  /**
   * Get aggregated analytics for onboarding optimization
   */
  async getAggregatedAnalytics(userType?: 'individual' | 'organization' | 'business'): Promise<{
    completionRates: Record<string, number>
    averageCompletionTime: number
    commonDropoffPoints: Array<{ stepId: string; dropoffRate: number }>
    errorPatterns: Array<{ stepId: string; errorType: string; frequency: number }>
    performanceMetrics: {
      totalStarted: number
      totalCompleted: number
      overallCompletionRate: number
      averageStepsCompleted: number
    }
  }> {
    const allProgress = await this.getAllOnboardingProgress()
    const filteredProgress = userType ? allProgress.filter(p => p.userType === userType) : allProgress

    if (filteredProgress.length === 0) {
      return {
        completionRates: {},
        averageCompletionTime: 0,
        commonDropoffPoints: [],
        errorPatterns: [],
        performanceMetrics: {
          totalStarted: 0,
          totalCompleted: 0,
          overallCompletionRate: 0,
          averageStepsCompleted: 0
        }
      }
    }

    const totalStarted = filteredProgress.length
    const totalCompleted = filteredProgress.filter(p => p.status === 'completed').length
    const overallCompletionRate = totalCompleted / totalStarted

    // Calculate completion rates by step
    const stepCompletionRates: Record<string, number> = {}
    const allSteps = new Set<string>()
    
    filteredProgress.forEach(progress => {
      progress.completedSteps.forEach(step => allSteps.add(step.stepId))
    })

    allSteps.forEach(stepId => {
      const completed = filteredProgress.filter(p => p.completedSteps.some(s => s.stepId === stepId)).length
      stepCompletionRates[stepId] = completed / totalStarted
    })

    // Calculate average completion time
    const completedProgress = filteredProgress.filter(p => p.status === 'completed')
    const averageCompletionTime = completedProgress.length > 0 ? 
      completedProgress.reduce((sum, p) => sum + p.analytics.totalTimeSpent, 0) / completedProgress.length : 0

    // Find common dropoff points
    const dropoffPoints: Record<string, number> = {}
    filteredProgress.forEach(progress => {
      if (progress.status !== 'completed' && progress.currentStepId) {
        dropoffPoints[progress.currentStepId] = (dropoffPoints[progress.currentStepId] || 0) + 1
      }
    })

    const commonDropoffPoints = Object.entries(dropoffPoints)
      .map(([stepId, count]) => ({ stepId, dropoffRate: count / totalStarted }))
      .sort((a, b) => b.dropoffRate - a.dropoffRate)
      .slice(0, 5)

    // Analyze error patterns
    const errorPatterns: Record<string, Record<string, number>> = {}
    filteredProgress.forEach(progress => {
      progress.failedSteps.forEach(failed => {
        if (!errorPatterns[failed.stepId]) errorPatterns[failed.stepId] = {}
        errorPatterns[failed.stepId][failed.reason] = (errorPatterns[failed.stepId][failed.reason] || 0) + 1
      })
    })

    const formattedErrorPatterns = Object.entries(errorPatterns)
      .flatMap(([stepId, errors]) => 
        Object.entries(errors).map(([errorType, frequency]) => ({ stepId, errorType, frequency }))
      )
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10)

    const averageStepsCompleted = filteredProgress.reduce((sum, p) => sum + p.analytics.completedSteps, 0) / totalStarted

    return {
      completionRates: stepCompletionRates,
      averageCompletionTime,
      commonDropoffPoints,
      errorPatterns: formattedErrorPatterns,
      performanceMetrics: {
        totalStarted,
        totalCompleted,
        overallCompletionRate,
        averageStepsCompleted
      }
    }
  }

  /**
   * Private helper methods
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private getDeviceInfo(): string {
    return navigator.userAgent
  }

  private getBrowserInfo(): string {
    return `${navigator.appName} ${navigator.appVersion}`
  }

  private getStepAttempts(progress: OnboardingProgress, stepId: string): number {
    const completed = progress.completedSteps.find(s => s.stepId === stepId)
    const failed = progress.failedSteps.find(s => s.stepId === stepId)
    
    return Math.max(completed?.attempts || 0, failed?.attempts || 0)
  }

  private getNextStepId(template: OnboardingTemplate, completedSteps: OnboardingProgress['completedSteps'], skippedSteps: OnboardingProgress['skippedSteps'] = []): string | undefined {
    const completedIds = new Set(completedSteps.map(s => s.stepId))
    const skippedIds = new Set(skippedSteps.map(s => s.stepId))
    
    // Find the next step that hasn't been completed or skipped and has all dependencies met
    const nextStep = template.steps
      .filter(step => !completedIds.has(step.id) && !skippedIds.has(step.id))
      .find(step => step.dependencies.every(dep => completedIds.has(dep)))
    
    return nextStep?.id
  }

  /**
   * Storage methods
   */
  private async storeOnboardingProgress(progress: OnboardingProgress): Promise<void> {
    const existing = (await ((window as any).spark?.kv?.get('onboarding_progress') as OnboardingProgress[])) || []
    const updated = existing.filter(p => p.id !== progress.id)
    updated.push(progress)
    await ((window as any).spark?.kv?.set('onboarding_progress', updated))
  }

  /**
   * Get onboarding progress for a user
   */
  async getOnboardingProgress(userId: string): Promise<OnboardingProgress | null> {
    const allProgress = (await ((window as any).spark?.kv?.get('onboarding_progress') as OnboardingProgress[])) || []
    return allProgress.find(p => p.userId === userId) || null
  }

  private async getAllOnboardingProgress(): Promise<OnboardingProgress[]> {
    return (await ((window as any).spark?.kv?.get('onboarding_progress') as OnboardingProgress[])) || []
  }

  private async trackAnalyticsEvent(userId: string, stepId: string, event: OnboardingAnalytics['event'], duration: number, metadata: Record<string, any> = {}): Promise<void> {
    const analytics: OnboardingAnalytics = {
      id: `analytics_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      userId,
      stepId,
      event,
      timestamp: new Date().toISOString(),
      duration,
      metadata: {
        ...metadata,
        userAgent: navigator.userAgent,
        deviceType: this.getDeviceType(),
        networkSpeed: 'unknown'
      },
      sessionId: await this.getCurrentSessionId(userId) || 'unknown'
    }

    const existing = (await ((window as any).spark?.kv?.get('onboarding_analytics') as OnboardingAnalytics[])) || []
    existing.push(analytics)
    await ((window as any).spark?.kv?.set('onboarding_analytics', existing))
  }

  private async getUserAnalyticsEvents(userId: string): Promise<OnboardingAnalytics[]> {
    const allAnalytics = (await ((window as any).spark?.kv?.get('onboarding_analytics') as OnboardingAnalytics[])) || []
    return allAnalytics.filter(a => a.userId === userId)
  }

  private async createOnboardingSession(userId: string, progressId: string, sessionId: string): Promise<void> {
    const session: OnboardingSession = {
      id: sessionId,
      userId,
      progressId,
      startedAt: new Date().toISOString(),
      isActive: true,
      deviceInfo: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        isMobile: /Mobile|Android|iPhone|iPad/.test(navigator.userAgent),
        screenResolution: `${screen.width}x${screen.height}`
      },
      interactions: [],
      performance: {
        pageLoadTimes: {},
        apiResponseTimes: {},
        errorCount: 0,
        warnings: []
      }
    }

    const existing = (await ((window as any).spark?.kv?.get('onboarding_sessions') as OnboardingSession[])) || []
    existing.push(session)
    await ((window as any).spark?.kv?.set('onboarding_sessions', existing))
  }

  private async getCurrentSession(userId: string): Promise<OnboardingSession | null> {
    const sessions = (await ((window as any).spark?.kv?.get('onboarding_sessions') as OnboardingSession[])) || []
    return sessions.find(s => s.userId === userId && s.isActive) || null
  }

  private async getCurrentSessionId(userId: string): Promise<string | null> {
    const session = await this.getCurrentSession(userId)
    return session?.id || null
  }

  private getDeviceType(): 'desktop' | 'tablet' | 'mobile' {
    const userAgent = navigator.userAgent
    if (/Mobile|Android|iPhone/.test(userAgent)) return 'mobile'
    if (/iPad|Tablet/.test(userAgent)) return 'tablet'
    return 'desktop'
  }

  private async getOnboardingTemplate(userType: 'individual' | 'organization' | 'business'): Promise<OnboardingTemplate> {
    // Return mock template - in real implementation this would come from configuration
    const templates: Record<string, OnboardingTemplate> = {
      individual: {
        id: 'individual_v1',
        name: 'Individual Onboarding',
        userType: 'individual',
        version: '1.0',
        isActive: true,
        steps: [
          {
            id: 'personal_info',
            name: 'Personal Information',
            description: 'Provide your basic personal information',
            type: 'form',
            userTypes: ['individual'],
            required: true,
            order: 1,
            dependencies: [],
            estimatedDuration: 5,
            instructions: ['Fill in your full name', 'Provide contact details', 'Set your preferences']
          },
          {
            id: 'document_upload',
            name: 'Document Verification',
            description: 'Upload required identification documents',
            type: 'document_upload',
            userTypes: ['individual'],
            required: true,
            order: 2,
            dependencies: ['personal_info'],
            estimatedDuration: 10,
            instructions: ['Upload government ID', 'Upload proof of address']
          },
          {
            id: 'references',
            name: 'References',
            description: 'Provide personal references',
            type: 'form',
            userTypes: ['individual'],
            required: true,
            order: 3,
            dependencies: ['document_upload'],
            estimatedDuration: 8,
            instructions: ['Provide two personal references', 'Include contact information']
          },
          {
            id: 'verification',
            name: 'In-Person Verification',
            description: 'Complete in-person verification',
            type: 'verification',
            userTypes: ['individual'],
            required: true,
            order: 4,
            dependencies: ['references'],
            estimatedDuration: 30,
            instructions: ['Schedule verification appointment', 'Attend verification meeting']
          }
        ],
        requirements: {
          requiredDocuments: ['government_id', 'proof_of_address'],
          requiredReferences: 2,
          requiresInPersonVerification: true,
          complianceChecks: ['kyc', 'aml']
        },
        customization: {},
        analytics: {
          totalStarted: 0,
          totalCompleted: 0,
          completionRate: 0,
          averageCompletionTime: 0,
          commonDropoffPoints: [],
          errorPatterns: []
        }
      },
      organization: {
        id: 'organization_v1',
        name: 'Organization Onboarding',
        userType: 'organization',
        version: '1.0',
        isActive: true,
        steps: [
          {
            id: 'org_info',
            name: 'Organization Information',
            description: 'Provide organization details',
            type: 'form',
            userTypes: ['organization'],
            required: true,
            order: 1,
            dependencies: [],
            estimatedDuration: 10,
            instructions: ['Organization name and type', 'Mission statement', 'Contact details']
          },
          {
            id: 'legal_docs',
            name: 'Legal Documentation',
            description: 'Upload legal documents',
            type: 'document_upload',
            userTypes: ['organization'],
            required: true,
            order: 2,
            dependencies: ['org_info'],
            estimatedDuration: 15,
            instructions: ['Upload incorporation documents', 'Upload tax exemption certificates']
          },
          {
            id: 'leadership',
            name: 'Leadership Information',
            description: 'Provide leadership team details',
            type: 'form',
            userTypes: ['organization'],
            required: true,
            order: 3,
            dependencies: ['legal_docs'],
            estimatedDuration: 12,
            instructions: ['List board members', 'Provide executive information']
          }
        ],
        requirements: {
          requiredDocuments: ['organization_license', 'tax_documents'],
          requiredReferences: 3,
          requiresInPersonVerification: true,
          complianceChecks: ['nonprofit_status', 'legal_compliance']
        },
        customization: {},
        analytics: {
          totalStarted: 0,
          totalCompleted: 0,
          completionRate: 0,
          averageCompletionTime: 0,
          commonDropoffPoints: [],
          errorPatterns: []
        }
      },
      business: {
        id: 'business_v1',
        name: 'Business Onboarding',
        userType: 'business',
        version: '1.0',
        isActive: true,
        steps: [
          {
            id: 'business_info',
            name: 'Business Information',
            description: 'Provide business details',
            type: 'form',
            userTypes: ['business'],
            required: true,
            order: 1,
            dependencies: [],
            estimatedDuration: 8,
            instructions: ['Business name and type', 'Industry and services', 'Contact information']
          },
          {
            id: 'registration_docs',
            name: 'Registration Documents',
            description: 'Upload business registration',
            type: 'document_upload',
            userTypes: ['business'],
            required: true,
            order: 2,
            dependencies: ['business_info'],
            estimatedDuration: 12,
            instructions: ['Upload business registration', 'Upload licenses']
          }
        ],
        requirements: {
          requiredDocuments: ['business_registration', 'licenses'],
          requiredReferences: 2,
          requiresInPersonVerification: false,
          complianceChecks: ['business_registration', 'license_validation']
        },
        customization: {},
        analytics: {
          totalStarted: 0,
          totalCompleted: 0,
          completionRate: 0,
          averageCompletionTime: 0,
          commonDropoffPoints: [],
          errorPatterns: []
        }
      }
    }

    return templates[userType]
  }
}