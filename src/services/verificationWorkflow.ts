import { DocumentVerificationRequest, ReferenceVerificationRequest, VerificationWorkflow, VerificationAuditLog } from '../types/verification'

// Simple localStorage utility functions to replace Spark KV
const localStorageGet = <T>(key: string): T | null => {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : null
  } catch {
    return null
  }
}

const localStorageSet = <T>(key: string, value: T): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Ignore errors
  }
}

/**
 * Automated Document Verification Service
 * Handles document processing, OCR, authenticity checks, and compliance validation
 */
export class DocumentVerificationService {
  private static instance: DocumentVerificationService
  
  static getInstance(): DocumentVerificationService {
    if (!DocumentVerificationService.instance) {
      DocumentVerificationService.instance = new DocumentVerificationService()
    }
    return DocumentVerificationService.instance
  }

  /**
   * Submit document for automated verification
   */
  async submitDocument(
    userId: string,
    documentType: DocumentVerificationRequest['documentType'],
    file: File
  ): Promise<DocumentVerificationRequest> {
    const documentId = `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    // Simulate file upload and create verification request
    const request: DocumentVerificationRequest = {
      id: documentId,
      userId,
      documentType,
      documentUrl: URL.createObjectURL(file),
      uploadedAt: new Date().toISOString(),
      status: 'pending',
      metadata: {
        fileName: file.name,
        fileSize: file.size,
        mimeType: file.type
      },
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days
    }

    // Store request
    await this.storeVerificationRequest(request)
    
    // Start automated processing
    setTimeout(() => this.processDocument(documentId), 1000)
    
    return request
  }

  /**
   * Automated document processing pipeline
   */
  private async processDocument(documentId: string): Promise<void> {
    const request = await this.getVerificationRequest(documentId)
    if (!request) return

    try {
      // Update status to processing
      await this.updateVerificationStatus(documentId, 'processing')

      // Simulate OCR and data extraction
      const ocrResults = await this.performOCR(request)
      
      // Perform authenticity checks
      const authenticityScore = await this.checkAuthenticity(request, ocrResults)
      
      // Quality assessment
      const qualityScore = await this.assessQuality(request)
      
      // Compliance validation
      const complianceChecks = await this.validateCompliance(request, ocrResults)
      
      // Calculate overall confidence
      const confidenceScore = this.calculateConfidence(authenticityScore, qualityScore, complianceChecks)
      
      // Determine final status
      const finalStatus = this.determineFinalStatus(confidenceScore, complianceChecks)
      
      // Update verification results
      const updatedRequest: DocumentVerificationRequest = {
        ...request,
        status: finalStatus,
        metadata: {
          ...request.metadata,
          confidenceScore,
          flags: this.generateFlags(authenticityScore, qualityScore, complianceChecks)
        },
        verificationResults: {
          ocrText: ocrResults.text,
          extractedFields: ocrResults.fields,
          authenticityScore,
          qualityScore,
          complianceChecks
        }
      }

      await this.storeVerificationRequest(updatedRequest)
      
      // Log audit event
      await this.logVerificationEvent(request.userId, documentId, 'document_processed', {
        status: finalStatus,
        confidenceScore,
        processingTime: Date.now() - new Date(request.uploadedAt).getTime()
      })

    } catch (error) {
      await this.updateVerificationStatus(documentId, 'requires_human_review')
      await this.logVerificationEvent(request.userId, documentId, 'processing_error', { error: error.message })
    }
  }

  /**
   * Simulate OCR processing
   */
  private async performOCR(request: DocumentVerificationRequest): Promise<{ text: string; fields: Record<string, any> }> {
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Mock OCR results based on document type
    const mockResults = {
      government_id: {
        text: "DRIVER LICENSE\nJOHN DOE\nDOB: 01/15/1985\nEXP: 12/31/2025",
        fields: {
          name: "John Doe",
          dateOfBirth: "1985-01-15",
          expirationDate: "2025-12-31",
          documentNumber: "D123456789"
        }
      },
      proof_of_address: {
        text: "UTILITY BILL\nJOHN DOE\n123 MAIN ST\nANYTOWN, ST 12345",
        fields: {
          name: "John Doe",
          address: "123 Main St, Anytown, ST 12345",
          issueDate: new Date().toISOString().split('T')[0]
        }
      },
      organization_license: {
        text: "NONPROFIT ORGANIZATION LICENSE\nCOMMUNITY HELPERS INC\nLIC#: NP123456",
        fields: {
          organizationName: "Community Helpers Inc",
          licenseNumber: "NP123456",
          issueDate: "2024-01-01",
          expirationDate: "2025-12-31"
        }
      }
    }

    return mockResults[request.documentType] || { text: "Unable to extract text", fields: {} }
  }

  /**
   * Check document authenticity
   */
  private async checkAuthenticity(request: DocumentVerificationRequest, ocrResults: any): Promise<number> {
    // Simulate authenticity checks
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    let score = 0.85 // Base score
    
    // Check for common fraud indicators
    if (ocrResults.fields.name && ocrResults.fields.name.length > 0) score += 0.05
    if (ocrResults.fields.expirationDate && new Date(ocrResults.fields.expirationDate) > new Date()) score += 0.05
    if (request.metadata.fileSize > 50000) score += 0.03 // Minimum quality threshold
    
    return Math.min(score, 1.0)
  }

  /**
   * Assess document quality
   */
  private async assessQuality(request: DocumentVerificationRequest): Promise<number> {
    // Simulate quality assessment
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    let score = 0.8 // Base quality score
    
    // File size indicates image quality
    if (request.metadata.fileSize > 100000) score += 0.1
    if (request.metadata.fileSize > 500000) score += 0.05
    
    // MIME type check
    if (request.metadata.mimeType.includes('image/')) score += 0.05
    
    return Math.min(score, 1.0)
  }

  /**
   * Validate compliance requirements
   */
  private async validateCompliance(request: DocumentVerificationRequest, ocrResults: any): Promise<Array<{ check: string; passed: boolean; details?: string }>> {
    const checks: Array<{ check: string; passed: boolean; details?: string }> = []
    
    // Document-specific compliance checks
    switch (request.documentType) {
      case 'government_id':
        checks.push({
          check: 'valid_expiration',
          passed: ocrResults.fields.expirationDate ? new Date(ocrResults.fields.expirationDate) > new Date() : false,
          details: ocrResults.fields.expirationDate ? 'Expires on ' + ocrResults.fields.expirationDate : 'No expiration date found'
        })
        checks.push({
          check: 'name_present',
          passed: !!(ocrResults.fields.name && ocrResults.fields.name.trim().length > 0),
          details: 'Name field validation'
        })
        break
        
      case 'proof_of_address':
        checks.push({
          check: 'recent_document',
          passed: ocrResults.fields.issueDate ? (Date.now() - new Date(ocrResults.fields.issueDate).getTime()) < (90 * 24 * 60 * 60 * 1000) : false,
          details: 'Document must be less than 90 days old'
        })
        checks.push({
          check: 'address_present',
          passed: !!(ocrResults.fields.address && ocrResults.fields.address.trim().length > 0),
          details: 'Address field validation'
        })
        break
        
      case 'organization_license':
        checks.push({
          check: 'license_valid',
          passed: ocrResults.fields.expirationDate ? new Date(ocrResults.fields.expirationDate) > new Date() : true,
          details: 'License validity check'
        })
        checks.push({
          check: 'license_number_format',
          passed: !!(ocrResults.fields.licenseNumber && /^[A-Z]{2}\d{6}$/.test(ocrResults.fields.licenseNumber)),
          details: 'License number format validation'
        })
        break
    }
    
    return checks
  }

  /**
   * Calculate overall confidence score
   */
  private calculateConfidence(authenticityScore: number, qualityScore: number, complianceChecks: Array<{ check: string; passed: boolean }>): number {
    const complianceScore = complianceChecks.length > 0 ? 
      complianceChecks.filter(c => c.passed).length / complianceChecks.length : 0.5
    
    return (authenticityScore * 0.4 + qualityScore * 0.3 + complianceScore * 0.3)
  }

  /**
   * Determine final verification status
   */
  private determineFinalStatus(confidenceScore: number, complianceChecks: Array<{ check: string; passed: boolean }>): DocumentVerificationRequest['status'] {
    const criticalChecksFailed = complianceChecks.some(c => !c.passed && (c.check === 'valid_expiration' || c.check === 'license_valid'))
    
    if (criticalChecksFailed) return 'rejected'
    if (confidenceScore >= 0.85) return 'verified'
    if (confidenceScore >= 0.7) return 'requires_human_review'
    return 'rejected'
  }

  /**
   * Generate risk flags
   */
  private generateFlags(authenticityScore: number, qualityScore: number, complianceChecks: Array<{ check: string; passed: boolean }>): string[] {
    const flags: string[] = []
    
    if (authenticityScore < 0.7) flags.push('low_authenticity_score')
    if (qualityScore < 0.6) flags.push('poor_image_quality')
    if (complianceChecks.some(c => !c.passed)) flags.push('compliance_issues')
    
    return flags
  }

  /**
   * Storage and retrieval methods
   */
  private async storeVerificationRequest(request: DocumentVerificationRequest): Promise<void> {
    const storageKey = `verification_requests`
    const existing = localStorageGet<DocumentVerificationRequest[]>(storageKey) || []
    const updated = existing.filter(r => r.id !== request.id)
    updated.push(request)
    localStorageSet(storageKey, updated)
  }

  private async getVerificationRequest(documentId: string): Promise<DocumentVerificationRequest | null> {
    const requests = localStorageGet<DocumentVerificationRequest[]>('verification_requests') || []
    return requests.find(r => r.id === documentId) || null
  }

  private async updateVerificationStatus(documentId: string, status: DocumentVerificationRequest['status']): Promise<void> {
    const request = await this.getVerificationRequest(documentId)
    if (request) {
      request.status = status
      await this.storeVerificationRequest(request)
    }
  }

  private async logVerificationEvent(userId: string, documentId: string, action: string, details: Record<string, any>): Promise<void> {
    const auditLog: VerificationAuditLog = {
      id: `audit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      userId,
      workflowId: documentId,
      action,
      timestamp: new Date().toISOString(),
      actor: 'system',
      details,
      riskImpact: details.error ? 'medium' : 'low'
    }

    const logs = localStorageGet<VerificationAuditLog[]>('verification_audit_logs') || []
    logs.push(auditLog)
    localStorageSet('verification_audit_logs', logs)
  }

  /**
   * Get verification requests for a user
   */
  async getUserVerificationRequests(userId: string): Promise<DocumentVerificationRequest[]> {
    const requests = (localStorageGet('verification_requests') as DocumentVerificationRequest[]) || []
    return requests.filter(r => r.userId === userId)
  }

  /**
   * Get verification request by ID
   */
  async getVerificationRequestById(documentId: string): Promise<DocumentVerificationRequest | null> {
    return this.getVerificationRequest(documentId)
  }
}

/**
 * Reference Verification Service
 * Handles automated reference checking and validation
 */
export class ReferenceVerificationService {
  private static instance: ReferenceVerificationService
  
  static getInstance(): ReferenceVerificationService {
    if (!ReferenceVerificationService.instance) {
      ReferenceVerificationService.instance = new ReferenceVerificationService()
    }
    return ReferenceVerificationService.instance
  }

  /**
   * Submit reference for verification
   */
  async submitReference(
    userId: string,
    referenceData: Pick<ReferenceVerificationRequest, 'referenceType' | 'referenceName' | 'referenceEmail' | 'referencePhone' | 'relationship' | 'yearsKnown'>
  ): Promise<ReferenceVerificationRequest> {
    const referenceId = `ref_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const verificationCode = Math.random().toString(36).substr(2, 8).toUpperCase()
    
    const request: ReferenceVerificationRequest = {
      id: referenceId,
      userId,
      ...referenceData,
      status: 'pending',
      verificationCode,
      requestedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
      metadata: {}
    }

    await this.storeReferenceRequest(request)
    
    // Send verification email
    setTimeout(() => this.sendVerificationEmail(referenceId), 500)
    
    return request
  }

  /**
   * Send verification email to reference
   */
  private async sendVerificationEmail(referenceId: string): Promise<void> {
    const request = await this.getReferenceRequest(referenceId)
    if (!request) return

    // Simulate email sending
    console.log(`Sending verification email to ${request.referenceEmail} with code ${request.verificationCode}`)
    
    await this.updateReferenceStatus(referenceId, 'sent')
    
    // Auto-respond for demo purposes after 3 seconds
    setTimeout(() => this.simulateReferenceResponse(referenceId), 3000)
  }

  /**
   * Simulate reference response for demo
   */
  private async simulateReferenceResponse(referenceId: string): Promise<void> {
    const request = await this.getReferenceRequest(referenceId)
    if (!request) return

    // Simulate positive reference response
    const response = {
      canRecommend: true,
      relationship: request.relationship,
      yearsKnown: request.yearsKnown,
      trustworthiness: 4 as const,
      reliability: 5 as const,
      comments: "Excellent individual with strong character and commitment to community service."
    }

    const updatedRequest: ReferenceVerificationRequest = {
      ...request,
      status: 'verified',
      respondedAt: new Date().toISOString(),
      response
    }

    await this.storeReferenceRequest(updatedRequest)
  }

  /**
   * Verify reference code (when reference responds)
   */
  async verifyReferenceCode(referenceId: string, code: string, response: ReferenceVerificationRequest['response']): Promise<boolean> {
    const request = await this.getReferenceRequest(referenceId)
    if (!request || request.verificationCode !== code.toUpperCase()) {
      return false
    }

    const updatedRequest: ReferenceVerificationRequest = {
      ...request,
      status: 'verified',
      respondedAt: new Date().toISOString(),
      response
    }

    await this.storeReferenceRequest(updatedRequest)
    return true
  }

  /**
   * Storage and retrieval methods
   */
  private async storeReferenceRequest(request: ReferenceVerificationRequest): Promise<void> {
    const storageKey = 'reference_requests'
    const existing = (localStorageGet(storageKey) as ReferenceVerificationRequest[]) || []
    const updated = existing.filter(r => r.id !== request.id)
    updated.push(request)
    localStorageSet(storageKey, updated)
  }

  private async getReferenceRequest(referenceId: string): Promise<ReferenceVerificationRequest | null> {
    const requests = (localStorageGet('reference_requests') as ReferenceVerificationRequest[]) || []
    return requests.find(r => r.id === referenceId) || null
  }

  private async updateReferenceStatus(referenceId: string, status: ReferenceVerificationRequest['status']): Promise<void> {
    const request = await this.getReferenceRequest(referenceId)
    if (request) {
      request.status = status
      await this.storeReferenceRequest(request)
    }
  }

  /**
   * Get reference requests for a user
   */
  async getUserReferenceRequests(userId: string): Promise<ReferenceVerificationRequest[]> {
    const requests = (localStorageGet('reference_requests') as ReferenceVerificationRequest[]) || []
    return requests.filter(r => r.userId === userId)
  }
}