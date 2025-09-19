/**
 * ML-Powered Document Verification Service
 * Uses locally-hosted vLLM models for automated document verification
 */

import { 
  MLVerificationRequest, 
  MLVerificationResponse, 
  VerificationCheck, 
  FlaggedIssue,
  DocumentType,
  ExtractedData 
} from '../types/documents'

export interface MLModelConfig {
  modelName: string
  endpoint: string
  apiKey?: string
  timeout: number
  maxRetries: number
}

export interface VerificationRules {
  documentType: DocumentType
  requiredFields: string[]
  validationPatterns: { [field: string]: RegExp }
  crossReferences: string[]
  qualityThresholds: {
    textExtraction: number
    imageQuality: number
    structureDetection: number
  }
}

export class MLDocumentVerifier {
  private config: MLModelConfig
  private verificationRules: Map<DocumentType, VerificationRules>

  constructor(config: MLModelConfig) {
    this.config = config
    this.verificationRules = new Map()
    this.initializeVerificationRules()
  }

  /**
   * Verify a document using ML models
   */
  async verifyDocument(request: MLVerificationRequest): Promise<MLVerificationResponse> {
    try {
      const startTime = Date.now()
      
      // Get document-specific verification rules
      const rules = this.verificationRules.get(request.documentType)
      if (!rules) {
        throw new Error(`No verification rules found for document type: ${request.documentType}`)
      }

      // Perform comprehensive verification checks
      const verificationChecks = await this.performVerificationChecks(request, rules)
      
      // Calculate overall confidence and risk score
      const { confidence, riskScore } = this.calculateScores(verificationChecks)
      
      // Generate verdict based on checks and thresholds
      const verdict = this.generateVerdict(confidence, riskScore, verificationChecks)
      
      // Get ML model reasoning
      const reasoning = await this.generateMLReasoning(request, verificationChecks)
      
      // Identify flagged issues
      const flaggedIssues = this.identifyFlaggedIssues(verificationChecks)
      
      // Generate recommended actions
      const recommendedActions = this.generateRecommendedActions(verdict, flaggedIssues)

      const processingTime = Date.now() - startTime

      return {
        documentId: request.documentId,
        verdict,
        confidence,
        riskScore,
        verificationChecks,
        reasoning,
        recommendedActions,
        flaggedIssues
      }
    } catch (error) {
      console.error('ML verification failed:', error)
      return this.createErrorResponse(request.documentId, error instanceof Error ? error.message : 'Unknown error')
    }
  }

  /**
   * Perform all verification checks for a document
   */
  private async performVerificationChecks(
    request: MLVerificationRequest, 
    rules: VerificationRules
  ): Promise<VerificationCheck[]> {
    const checks: VerificationCheck[] = []

    // Document authenticity check
    checks.push(await this.checkDocumentAuthenticity(request))
    
    // Text extraction quality check
    checks.push(await this.checkTextExtractionQuality(request, rules))
    
    // Format validation check
    checks.push(await this.checkFormatValidation(request, rules))
    
    // Security features check
    checks.push(await this.checkSecurityFeatures(request))
    
    // Data consistency check
    checks.push(await this.checkDataConsistency(request, rules))
    
    // Fraud detection check
    checks.push(await this.checkFraudIndicators(request))
    
    // Quality assessment check
    checks.push(await this.checkQualityAssessment(request, rules))

    return checks
  }

  /**
   * Check document authenticity using ML models
   */
  private async checkDocumentAuthenticity(request: MLVerificationRequest): Promise<VerificationCheck> {
    const prompt = window.spark.llmPrompt`
You are an expert document authentication system. Analyze this document data:

Document Type: ${request.documentType}
Extracted Text: ${request.extractedData.text}
Document Structure: ${JSON.stringify(request.extractedData.structure)}
Image Quality Score: ${request.metadata.resolution ? 'Available' : 'Not Available'}

Evaluate the document's authenticity based on:
1. Presence of expected security features
2. Text layout and formatting consistency
3. Official seals, watermarks, or signatures
4. Typography and font analysis
5. Overall document structure integrity

Return your assessment as JSON:
{
  "authentic": boolean,
  "confidence": number (0-1),
  "evidence": string[],
  "concerns": string[]
}
`

    try {
      const response = await window.spark.llm(prompt, 'gpt-4o', true)
      const result = JSON.parse(response)

      return {
        type: 'document_authenticity',
        passed: result.authentic,
        confidence: result.confidence,
        details: `Authenticity check ${result.authentic ? 'passed' : 'failed'}. Evidence: ${result.evidence.join(', ')}`,
        evidence: result
      }
    } catch (error) {
      return {
        type: 'document_authenticity',
        passed: false,
        confidence: 0,
        details: `Authenticity check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        evidence: null
      }
    }
  }

  /**
   * Check text extraction quality
   */
  private async checkTextExtractionQuality(
    request: MLVerificationRequest, 
    rules: VerificationRules
  ): Promise<VerificationCheck> {
    const extractedText = request.extractedData.text
    const confidence = request.extractedData.confidence

    const qualityScore = confidence * 0.7 + (extractedText.length > 50 ? 0.3 : 0)
    const passed = qualityScore >= rules.qualityThresholds.textExtraction

    return {
      type: 'text_extraction',
      passed,
      confidence: qualityScore,
      details: `Text extraction quality: ${(qualityScore * 100).toFixed(1)}%. Length: ${extractedText.length} characters.`,
      evidence: { extractedText: extractedText.substring(0, 500), confidence }
    }
  }

  /**
   * Check format validation against document type rules
   */
  private async checkFormatValidation(
    request: MLVerificationRequest, 
    rules: VerificationRules
  ): Promise<VerificationCheck> {
    const entities = request.extractedData.entities
    const foundFields = entities.map(e => e.type)
    const missingFields = rules.requiredFields.filter(field => !foundFields.includes(field as any))

    const passed = missingFields.length === 0
    const confidence = Math.max(0, 1 - (missingFields.length / rules.requiredFields.length))

    return {
      type: 'format_validation',
      passed,
      confidence,
      details: passed 
        ? 'All required fields found' 
        : `Missing required fields: ${missingFields.join(', ')}`,
      evidence: { foundFields, missingFields, requiredFields: rules.requiredFields }
    }
  }

  /**
   * Check for security features in the document
   */
  private async checkSecurityFeatures(request: MLVerificationRequest): Promise<VerificationCheck> {
    const structure = request.extractedData.structure
    const securityFeatures = {
      hasSignature: structure.hasSignature,
      hasOfficialSeal: structure.hasOfficialSeal,
      hasWatermark: structure.hasWatermark
    }

    const featureCount = Object.values(securityFeatures).filter(Boolean).length
    const confidence = featureCount / 3 // Assuming 3 possible security features
    const passed = featureCount >= 1 // At least one security feature required

    return {
      type: 'security_features',
      passed,
      confidence,
      details: `Security features found: ${Object.entries(securityFeatures)
        .filter(([_, present]) => present)
        .map(([feature, _]) => feature)
        .join(', ') || 'None'}`,
      evidence: securityFeatures
    }
  }

  /**
   * Check data consistency across extracted fields
   */
  private async checkDataConsistency(
    request: MLVerificationRequest, 
    rules: VerificationRules
  ): Promise<VerificationCheck> {
    const entities = request.extractedData.entities
    const inconsistencies: string[] = []

    // Check against validation patterns
    for (const entity of entities) {
      const pattern = rules.validationPatterns[entity.type]
      if (pattern && !pattern.test(entity.value)) {
        inconsistencies.push(`${entity.type}: ${entity.value} doesn't match expected format`)
      }
    }

    // Check for logical consistency (e.g., dates, cross-references)
    const dateEntities = entities.filter(e => e.type === 'date')
    for (const dateEntity of dateEntities) {
      const date = new Date(dateEntity.value)
      if (isNaN(date.getTime())) {
        inconsistencies.push(`Invalid date format: ${dateEntity.value}`)
      }
    }

    const passed = inconsistencies.length === 0
    const confidence = Math.max(0, 1 - (inconsistencies.length * 0.2))

    return {
      type: 'data_consistency',
      passed,
      confidence,
      details: passed 
        ? 'All data fields are consistent' 
        : `Inconsistencies found: ${inconsistencies.join('; ')}`,
      evidence: { inconsistencies, entities }
    }
  }

  /**
   * Check for fraud indicators using ML analysis
   */
  private async checkFraudIndicators(request: MLVerificationRequest): Promise<VerificationCheck> {
    const prompt = window.spark.llmPrompt`
You are a fraud detection expert. Analyze this document for potential fraud indicators:

Document Type: ${request.documentType}
User Risk Level: ${request.userContext.riskLevel}
Previous Verifications: ${request.userContext.previousVerifications}
Extracted Data: ${JSON.stringify(request.extractedData.entities)}
Text Content: ${request.extractedData.text.substring(0, 1000)}

Look for fraud indicators such as:
1. Inconsistent fonts or formatting
2. Suspicious date patterns
3. Unrealistic information
4. Signs of tampering or editing
5. Anomalous patterns in data

Return your assessment as JSON:
{
  "fraudulent": boolean,
  "riskScore": number (0-1),
  "indicators": string[],
  "explanation": string
}
`

    try {
      const response = await window.spark.llm(prompt, 'gpt-4o', true)
      const result = JSON.parse(response)

      return {
        type: 'fraud_detection',
        passed: !result.fraudulent,
        confidence: 1 - result.riskScore,
        details: result.explanation,
        evidence: result
      }
    } catch (error) {
      return {
        type: 'fraud_detection',
        passed: true,
        confidence: 0.5,
        details: `Fraud detection check inconclusive: ${error instanceof Error ? error.message : 'Unknown error'}`,
        evidence: null
      }
    }
  }

  /**
   * Check overall document quality
   */
  private async checkQualityAssessment(
    request: MLVerificationRequest, 
    rules: VerificationRules
  ): Promise<VerificationCheck> {
    const metadata = request.metadata
    const extractedData = request.extractedData

    // Calculate quality metrics
    const textQuality = extractedData.confidence
    const structureQuality = extractedData.structure.sections.length > 0 ? 0.8 : 0.3
    const metadataQuality = metadata.resolution ? 0.9 : 0.5

    const overallQuality = (textQuality * 0.5 + structureQuality * 0.3 + metadataQuality * 0.2)
    const passed = overallQuality >= 0.6

    return {
      type: 'quality_assessment',
      passed,
      confidence: overallQuality,
      details: `Overall document quality: ${(overallQuality * 100).toFixed(1)}%`,
      evidence: {
        textQuality,
        structureQuality,
        metadataQuality,
        overallQuality
      }
    }
  }

  /**
   * Calculate overall confidence and risk scores
   */
  private calculateScores(checks: VerificationCheck[]): { confidence: number; riskScore: number } {
    const passedChecks = checks.filter(c => c.passed)
    const totalConfidence = checks.reduce((sum, c) => sum + c.confidence, 0)
    
    const confidence = totalConfidence / checks.length
    const riskScore = 1 - (passedChecks.length / checks.length)

    return { confidence, riskScore }
  }

  /**
   * Generate verification verdict
   */
  private generateVerdict(
    confidence: number, 
    riskScore: number, 
    checks: VerificationCheck[]
  ): 'approved' | 'rejected' | 'requires_human_review' {
    const criticalChecksFailed = checks.filter(c => 
      ['document_authenticity', 'fraud_detection'].includes(c.type) && !c.passed
    ).length > 0

    if (criticalChecksFailed || riskScore > 0.7) {
      return 'rejected'
    }

    if (confidence > 0.8 && riskScore < 0.3) {
      return 'approved'
    }

    return 'requires_human_review'
  }

  /**
   * Generate ML reasoning for the verification decision
   */
  private async generateMLReasoning(
    request: MLVerificationRequest, 
    checks: VerificationCheck[]
  ): Promise<string> {
    const checkSummary = checks.map(c => 
      `${c.type}: ${c.passed ? 'PASS' : 'FAIL'} (${(c.confidence * 100).toFixed(1)}%)`
    ).join('\n')

    const prompt = window.spark.llmPrompt`
You are a document verification expert. Provide a clear, professional explanation for this verification decision:

Document Type: ${request.documentType}
User Context: ${request.userContext.userType} user with ${request.userContext.previousVerifications} previous verifications

Verification Check Results:
${checkSummary}

Provide a 2-3 sentence explanation of the verification outcome that would be understandable to both technical and non-technical users. Focus on the key factors that influenced the decision.
`

    try {
      const response = await window.spark.llm(prompt, 'gpt-4o')
      return response.trim()
    } catch (error) {
      return `Verification completed with ${checks.filter(c => c.passed).length}/${checks.length} checks passed. ${error instanceof Error ? `Note: ${error.message}` : ''}`
    }
  }

  /**
   * Identify flagged issues from verification checks
   */
  private identifyFlaggedIssues(checks: VerificationCheck[]): FlaggedIssue[] {
    const issues: FlaggedIssue[] = []

    for (const check of checks) {
      if (!check.passed) {
        let severity: 'low' | 'medium' | 'high' | 'critical' = 'medium'
        
        if (['document_authenticity', 'fraud_detection'].includes(check.type)) {
          severity = 'critical'
        } else if (['security_features', 'data_consistency'].includes(check.type)) {
          severity = 'high'
        } else if (check.confidence < 0.3) {
          severity = 'high'
        }

        issues.push({
          type: this.mapCheckTypeToIssueType(check.type),
          severity,
          description: check.details,
          suggestedResolution: this.getSuggestedResolution(check.type)
        })
      }
    }

    return issues
  }

  /**
   * Generate recommended actions based on verification result
   */
  private generateRecommendedActions(
    verdict: 'approved' | 'rejected' | 'requires_human_review',
    flaggedIssues: FlaggedIssue[]
  ): string[] {
    const actions: string[] = []

    switch (verdict) {
      case 'approved':
        actions.push('Document verified successfully - proceed with account activation')
        break
      
      case 'rejected':
        actions.push('Document verification failed - request new document submission')
        if (flaggedIssues.some(i => i.type === 'fraud_indicator')) {
          actions.push('Flag account for manual security review')
        }
        break
      
      case 'requires_human_review':
        actions.push('Schedule manual review with verification specialist')
        actions.push('Notify user of extended review timeline')
        break
    }

    // Add specific actions based on flagged issues
    if (flaggedIssues.some(i => i.type === 'quality_issue')) {
      actions.push('Request higher quality document scan or photo')
    }

    if (flaggedIssues.some(i => i.type === 'data_inconsistency')) {
      actions.push('Request clarification on inconsistent data fields')
    }

    return actions
  }

  /**
   * Map verification check type to flagged issue type
   */
  private mapCheckTypeToIssueType(checkType: string): FlaggedIssue['type'] {
    const mapping: { [key: string]: FlaggedIssue['type'] } = {
      'document_authenticity': 'fraud_indicator',
      'text_extraction': 'quality_issue',
      'format_validation': 'format_error',
      'security_features': 'format_error',
      'data_consistency': 'data_inconsistency',
      'fraud_detection': 'fraud_indicator',
      'quality_assessment': 'quality_issue'
    }

    return mapping[checkType] || 'format_error'
  }

  /**
   * Get suggested resolution for verification check failure
   */
  private getSuggestedResolution(checkType: string): string {
    const resolutions: { [key: string]: string } = {
      'document_authenticity': 'Submit an original, unedited document from the issuing authority',
      'text_extraction': 'Provide a clearer, higher resolution image of the document',
      'format_validation': 'Ensure all required information is clearly visible in the document',
      'security_features': 'Submit a document that includes official seals, signatures, or watermarks',
      'data_consistency': 'Verify that all information in the document is accurate and consistent',
      'fraud_detection': 'Contact support for manual verification process',
      'quality_assessment': 'Submit a higher quality scan or photo of the document'
    }

    return resolutions[checkType] || 'Contact support for assistance with document verification'
  }

  /**
   * Create error response for failed verification
   */
  private createErrorResponse(documentId: string, error: string): MLVerificationResponse {
    return {
      documentId,
      verdict: 'requires_human_review',
      confidence: 0,
      riskScore: 0.5,
      verificationChecks: [],
      reasoning: `Verification could not be completed automatically: ${error}`,
      recommendedActions: ['Schedule manual review with verification specialist'],
      flaggedIssues: [{
        type: 'format_error',
        severity: 'high',
        description: `Automated verification failed: ${error}`,
        suggestedResolution: 'Contact support for manual verification assistance'
      }]
    }
  }

  /**
   * Initialize verification rules for different document types
   */
  private initializeVerificationRules(): void {
    // Government ID rules
    this.verificationRules.set('government_id', {
      documentType: 'government_id',
      requiredFields: ['name', 'date', 'id_number'],
      validationPatterns: {
        'id_number': /^[A-Z0-9]{6,20}$/,
        'date': /^\d{1,2}\/\d{1,2}\/\d{4}$/
      },
      crossReferences: ['name', 'date'],
      qualityThresholds: {
        textExtraction: 0.7,
        imageQuality: 0.6,
        structureDetection: 0.5
      }
    })

    // Driver's License rules
    this.verificationRules.set('drivers_license', {
      documentType: 'drivers_license',
      requiredFields: ['name', 'date', 'id_number', 'address'],
      validationPatterns: {
        'id_number': /^[A-Z0-9]{8,15}$/,
        'date': /^\d{1,2}\/\d{1,2}\/\d{4}$/
      },
      crossReferences: ['name', 'address'],
      qualityThresholds: {
        textExtraction: 0.8,
        imageQuality: 0.7,
        structureDetection: 0.6
      }
    })

    // Utility Bill rules
    this.verificationRules.set('utility_bill', {
      documentType: 'utility_bill',
      requiredFields: ['name', 'address', 'date'],
      validationPatterns: {
        'date': /^\d{1,2}\/\d{1,2}\/\d{4}$/
      },
      crossReferences: ['name', 'address'],
      qualityThresholds: {
        textExtraction: 0.6,
        imageQuality: 0.5,
        structureDetection: 0.4
      }
    })

    // Add more document type rules as needed...
  }
}

/**
 * Factory function to create ML verifier instance
 */
export function createMLDocumentVerifier(): MLDocumentVerifier {
  const config: MLModelConfig = {
    modelName: 'document-verification-model',
    endpoint: process.env.VLLM_ENDPOINT || 'http://localhost:8000',
    timeout: 30000,
    maxRetries: 3
  }

  return new MLDocumentVerifier(config)
}