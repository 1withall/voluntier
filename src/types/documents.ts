/**
 * Document-related type definitions
 */

export interface DocumentUpload {
  id: string
  userId: string
  fileName: string
  fileSize: number
  mimeType: string
  uploadTimestamp: number
  status: 'pending' | 'processing' | 'verified' | 'rejected' | 'failed'
  documentType: DocumentType
  verificationResult?: VerificationResult
  metadata?: DocumentMetadata
}

export interface DocumentMetadata {
  fileName: string
  fileSize: number
  mimeType: string
  uploadTimestamp: number
  checksum: string
  lastModified: number
  pages?: number
  resolution?: { width: number; height: number }
  colorSpace?: string
  hasText?: boolean
  language?: string
}

export interface ProcessingResult {
  success: boolean
  metadata: DocumentMetadata | null
  extractedData: ExtractedData | null
  qualityScore: number
  processingTime: number
  errors: string[]
}

export interface ExtractedData {
  text: string
  metadata: DocumentMetadata
  confidence: number
  entities: EntityExtraction[]
  structure: DocumentStructure
}

export interface EntityExtraction {
  type: 'name' | 'date' | 'address' | 'phone' | 'email' | 'id_number' | 'organization'
  value: string
  confidence: number
  position: { x: number; y: number; width: number; height: number }
}

export interface DocumentStructure {
  documentType: string
  sections: DocumentSection[]
  hasSignature: boolean
  hasOfficialSeal: boolean
  hasWatermark: boolean
}

export interface DocumentSection {
  type: string
  content: string
  confidence: number
  boundingBox: { x: number; y: number; width: number; height: number }
}

export interface VerificationResult {
  verified: boolean
  confidence: number
  checks: VerificationCheck[]
  riskScore: number
  timestamp: number
  verifiedBy: 'ml_model' | 'human_reviewer' | 'hybrid'
  notes?: string
}

export interface VerificationCheck {
  type: VerificationCheckType
  passed: boolean
  confidence: number
  details: string
  evidence?: any
}

export type VerificationCheckType = 
  | 'document_authenticity'
  | 'text_extraction'
  | 'format_validation'
  | 'security_features'
  | 'data_consistency'
  | 'regulatory_compliance'
  | 'fraud_detection'
  | 'quality_assessment'

export type DocumentType = 
  | 'government_id'
  | 'drivers_license'
  | 'passport'
  | 'birth_certificate'
  | 'social_security_card'
  | 'utility_bill'
  | 'bank_statement'
  | 'employment_verification'
  | 'education_certificate'
  | 'professional_license'
  | 'business_registration'
  | 'tax_document'
  | 'insurance_card'
  | 'medical_record'
  | 'legal_document'
  | 'reference_letter'
  | 'other'

export interface MLVerificationRequest {
  documentId: string
  documentType: DocumentType
  extractedData: ExtractedData
  metadata: DocumentMetadata
  userContext: {
    userId: string
    userType: 'individual' | 'organization' | 'business'
    previousVerifications: number
    riskLevel: 'low' | 'medium' | 'high'
  }
}

export interface MLVerificationResponse {
  documentId: string
  verdict: 'approved' | 'rejected' | 'requires_human_review'
  confidence: number
  riskScore: number
  verificationChecks: VerificationCheck[]
  reasoning: string
  recommendedActions: string[]
  flaggedIssues: FlaggedIssue[]
}

export interface FlaggedIssue {
  type: 'data_inconsistency' | 'quality_issue' | 'fraud_indicator' | 'format_error'
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  location?: { x: number; y: number; width: number; height: number }
  suggestedResolution: string
}

export interface BulkUploadSession {
  id: string
  userId: string
  totalFiles: number
  processedFiles: number
  successfulUploads: number
  failedUploads: number
  status: 'initializing' | 'processing' | 'completed' | 'failed'
  startTime: number
  endTime?: number
  files: BulkUploadFile[]
}

export interface BulkUploadFile {
  id: string
  fileName: string
  fileSize: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error?: string
  processingResult?: ProcessingResult
  documentType?: DocumentType
}

export interface DragDropUploadState {
  isDragActive: boolean
  isDragAccept: boolean
  isDragReject: boolean
  files: File[]
  rejectedFiles: { file: File; errors: string[] }[]
}

export interface UploadProgress {
  fileId: string
  fileName: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  error?: string
}