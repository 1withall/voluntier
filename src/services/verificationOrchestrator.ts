import { DocumentVerificationService, ReferenceVerificationService } from './verificationWorkflow'
import { OnboardingAnalyticsService } from './onboardingAnalytics'
import { VerificationWorkflow, VerificationStep } from '../types/verification'
import { UserProfile } from '../types/profiles'

/**
 * Verification Workflow Orchestrator
 * Coordinates all verification processes and integrates with onboarding analytics
 */
export class VerificationOrchestrator {
  private static instance: VerificationOrchestrator
  private documentService = DocumentVerificationService.getInstance()
  private referenceService = ReferenceVerificationService.getInstance()
  private analyticsService = OnboardingAnalyticsService.getInstance()

  static getInstance(): VerificationOrchestrator {
    if (!VerificationOrchestrator.instance) {
      VerificationOrchestrator.instance = new VerificationOrchestrator()
    }
    return VerificationOrchestrator.instance
  }

  /**
   * Initialize comprehensive verification workflow for a user
   */
  async initializeVerificationWorkflow(userProfile: UserProfile): Promise<VerificationWorkflow> {
    const workflowId = `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    const workflow: VerificationWorkflow = {
      id: workflowId,
      userId: userProfile.id,
      userType: userProfile.userType,
      status: 'in_progress',
      startedAt: new Date().toISOString(),
      requiredSteps: this.getRequiredSteps(userProfile.userType),
      completedSteps: [],
      riskScore: 0.5, // Initial neutral risk score
      fraudFlags: [],
      compliance: {
        kycCompleted: false,
        amlCompleted: false,
        documentsVerified: false,
        referencesVerified: false,
        inPersonVerified: false
      }
    }

    await this.storeVerificationWorkflow(workflow)
    
    // Initialize onboarding analytics if not already done
    try {
      await this.analyticsService.initializeOnboardingProgress(userProfile.id, userProfile.userType)
    } catch (error) {
      // Already initialized
    }

    return workflow
  }

  /**
   * Check and update verification workflow status
   */
  async updateWorkflowStatus(userId: string): Promise<VerificationWorkflow | null> {
    const workflow = await this.getVerificationWorkflow(userId)
    if (!workflow) return null

    // Get current verification status
    const [documentRequests, referenceRequests] = await Promise.all([
      this.documentService.getUserVerificationRequests(userId),
      this.referenceService.getUserReferenceRequests(userId)
    ])

    // Update compliance status
    const updatedCompliance = { ...workflow.compliance }
    
    // Check document verification
    const requiredDocs = this.getRequiredDocuments(workflow.userType)
    const verifiedDocs = documentRequests.filter(req => 
      requiredDocs.includes(req.documentType) && req.status === 'verified'
    )
    updatedCompliance.documentsVerified = verifiedDocs.length === requiredDocs.length

    // Check reference verification
    const requiredRefs = workflow.userType === 'organization' ? 3 : 2
    const verifiedRefs = referenceRequests.filter(req => req.status === 'verified')
    updatedCompliance.referencesVerified = verifiedRefs.length >= requiredRefs

    // Update completed steps
    const updatedSteps = [...workflow.completedSteps]
    
    if (updatedCompliance.documentsVerified && !updatedSteps.includes('document_upload')) {
      updatedSteps.push('document_upload')
      await this.analyticsService.completeStep(userId, 'document_upload', 60000) // 1 minute
    }
    
    if (updatedCompliance.referencesVerified && !updatedSteps.includes('references')) {
      updatedSteps.push('references')
      await this.analyticsService.completeStep(userId, 'references', 45000) // 45 seconds
    }

    // Calculate risk score
    const riskScore = this.calculateRiskScore(documentRequests, referenceRequests, workflow.fraudFlags)
    
    // Determine if workflow is complete
    const allStepsCompleted = workflow.requiredSteps.every(step => 
      !step.required || updatedSteps.includes(step.id)
    )
    
    const updatedWorkflow: VerificationWorkflow = {
      ...workflow,
      status: allStepsCompleted ? 'completed' : 'in_progress',
      completedAt: allStepsCompleted ? new Date().toISOString() : undefined,
      completedSteps: updatedSteps,
      riskScore,
      compliance: updatedCompliance
    }

    await this.storeVerificationWorkflow(updatedWorkflow)
    return updatedWorkflow
  }

  /**
   * Get verification workflow for a user
   */
  async getVerificationWorkflow(userId: string): Promise<VerificationWorkflow | null> {
    const workflows = (await ((window as any).spark?.kv?.get('verification_workflows') as VerificationWorkflow[])) || []
    return workflows.find(w => w.userId === userId) || null
  }

  /**
   * Get verification progress summary
   */
  async getVerificationSummary(userId: string): Promise<{
    workflow: VerificationWorkflow | null
    documentsStatus: { uploaded: number; verified: number; required: number }
    referencesStatus: { submitted: number; verified: number; required: number }
    overallProgress: number
    nextActions: string[]
  }> {
    const workflow = await this.getVerificationWorkflow(userId)
    
    if (!workflow) {
      return {
        workflow: null,
        documentsStatus: { uploaded: 0, verified: 0, required: 0 },
        referencesStatus: { submitted: 0, verified: 0, required: 0 },
        overallProgress: 0,
        nextActions: ['Initialize verification workflow']
      }
    }

    const [documentRequests, referenceRequests] = await Promise.all([
      this.documentService.getUserVerificationRequests(userId),
      this.referenceService.getUserReferenceRequests(userId)
    ])

    const requiredDocs = this.getRequiredDocuments(workflow.userType)
    const requiredRefs = workflow.userType === 'organization' ? 3 : 2

    const documentsStatus = {
      uploaded: documentRequests.length,
      verified: documentRequests.filter(req => req.status === 'verified').length,
      required: requiredDocs.length
    }

    const referencesStatus = {
      submitted: referenceRequests.length,
      verified: referenceRequests.filter(req => req.status === 'verified').length,
      required: requiredRefs
    }

    const totalRequired = workflow.requiredSteps.filter(step => step.required).length
    const completed = workflow.completedSteps.length
    const overallProgress = Math.round((completed / totalRequired) * 100)

    const nextActions = this.generateNextActions(workflow, documentsStatus, referencesStatus)

    return {
      workflow,
      documentsStatus,
      referencesStatus,
      overallProgress,
      nextActions
    }
  }

  /**
   * Generate intelligent next action recommendations
   */
  private generateNextActions(
    workflow: VerificationWorkflow,
    documentsStatus: { uploaded: number; verified: number; required: number },
    referencesStatus: { submitted: number; verified: number; required: number }
  ): string[] {
    const actions: string[] = []

    // Document actions
    if (documentsStatus.uploaded < documentsStatus.required) {
      const remaining = documentsStatus.required - documentsStatus.uploaded
      actions.push(`Upload ${remaining} more required document${remaining > 1 ? 's' : ''}`)
    }

    // Reference actions
    if (referencesStatus.submitted < referencesStatus.required) {
      const remaining = referencesStatus.required - referencesStatus.submitted
      actions.push(`Submit ${remaining} more reference${remaining > 1 ? 's' : ''}`)
    }

    // Pending verifications
    if (documentsStatus.uploaded > documentsStatus.verified) {
      actions.push('Wait for document verification to complete')
    }

    if (referencesStatus.submitted > referencesStatus.verified) {
      actions.push('Follow up with references to complete verification')
    }

    // In-person verification
    if (workflow.compliance.documentsVerified && workflow.compliance.referencesVerified && !workflow.compliance.inPersonVerified) {
      actions.push('Schedule in-person verification appointment')
    }

    // High risk score
    if (workflow.riskScore > 0.7) {
      actions.push('Address security concerns - additional verification may be required')
    }

    if (actions.length === 0) {
      actions.push('All verification steps completed')
    }

    return actions
  }

  /**
   * Calculate dynamic risk score based on verification data
   */
  private calculateRiskScore(
    documentRequests: any[],
    referenceRequests: any[],
    fraudFlags: string[]
  ): number {
    let score = 0.3 // Base score

    // Document verification impact
    const rejectedDocs = documentRequests.filter(req => req.status === 'rejected').length
    const lowConfidenceDocs = documentRequests.filter(req => 
      req.metadata.confidenceScore && req.metadata.confidenceScore < 0.7
    ).length

    score += rejectedDocs * 0.2
    score += lowConfidenceDocs * 0.1

    // Reference verification impact
    const failedRefs = referenceRequests.filter(req => req.status === 'failed').length
    const lowRatedRefs = referenceRequests.filter(req => 
      req.response && (req.response.trustworthiness < 3 || req.response.reliability < 3)
    ).length

    score += failedRefs * 0.15
    score += lowRatedRefs * 0.1

    // Fraud flags impact
    score += fraudFlags.length * 0.1

    return Math.min(Math.max(score, 0), 1) // Clamp between 0 and 1
  }

  /**
   * Get required verification steps based on user type
   */
  private getRequiredSteps(userType: 'individual' | 'organization' | 'business'): VerificationStep[] {
    const baseSteps: VerificationStep[] = [
      {
        id: 'document_upload',
        type: 'document_upload',
        name: 'Document Upload',
        description: 'Upload required identification and supporting documents',
        required: true,
        status: 'pending',
        dependencies: [],
        estimatedDuration: 10,
        instructions: ['Prepare clear photos of documents', 'Ensure all text is readable', 'Upload in supported formats'],
        requirements: { documentTypes: this.getRequiredDocuments(userType) }
      },
      {
        id: 'references',
        type: 'reference_submission',
        name: 'Reference Verification',
        description: 'Provide and verify personal or professional references',
        required: true,
        status: 'pending',
        dependencies: ['document_upload'],
        estimatedDuration: 15,
        instructions: ['Contact references in advance', 'Provide accurate contact information', 'Follow up if needed'],
        requirements: { referenceCount: userType === 'organization' ? 3 : 2 }
      }
    ]

    if (userType === 'individual' || userType === 'organization') {
      baseSteps.push({
        id: 'in_person_verification',
        type: 'in_person_verification',
        name: 'In-Person Verification',
        description: 'Complete verification with a local organization representative',
        required: true,
        status: 'pending',
        dependencies: ['document_upload', 'references'],
        estimatedDuration: 30,
        instructions: ['Schedule appointment', 'Bring original documents', 'Arrive on time'],
        requirements: { requiresPhysicalPresence: true }
      })
    }

    return baseSteps
  }

  /**
   * Get required documents based on user type
   */
  private getRequiredDocuments(userType: 'individual' | 'organization' | 'business'): string[] {
    const baseRequirements = ['government_id', 'proof_of_address']
    
    if (userType === 'organization') {
      return [...baseRequirements, 'organization_license']
    }
    
    if (userType === 'business') {
      return [...baseRequirements, 'business_registration']
    }
    
    return baseRequirements
  }

  /**
   * Storage methods
   */
  private async storeVerificationWorkflow(workflow: VerificationWorkflow): Promise<void> {
    const existing = (await ((window as any).spark?.kv?.get('verification_workflows') as VerificationWorkflow[])) || []
    const updated = existing.filter(w => w.id !== workflow.id)
    updated.push(workflow)
    await ((window as any).spark?.kv?.set('verification_workflows', updated))
  }
}