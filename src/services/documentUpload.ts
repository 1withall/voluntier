/**
 * Document Upload Service
 * Implements secure document uploading following industry best practices
 * - Client-side validation and file type checking
 * - File size limits and virus scanning preparation
 * - Encrypted upload with integrity validation
 * - Audit logging and security monitoring
 */

// Import types for telemetry without using hooks directly
interface TelemetryService {
  trackUserAction: (action: string, category: string, label?: string) => void
  trackPageView: (page: string) => void
  setUserId: (userId: string) => void
}

export interface DocumentMetadata {
  id: string
  originalName: string
  mimeType: string
  size: number
  hash: string
  uploadedAt: string
  uploadedBy: string
  documentType: DocumentType
  encryptionKey?: string
  verified: boolean
  verificationStatus: 'pending' | 'in_progress' | 'verified' | 'rejected'
  verificationNotes?: string
}

export type DocumentType = 
  | 'government_id'
  | 'proof_of_address'
  | 'organization_registration'
  | 'business_license'
  | 'reference_letter'
  | 'tax_exemption'
  | 'insurance_certificate'
  | 'other'

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface UploadOptions {
  documentType: DocumentType
  description?: string
  isRequired?: boolean
  maxSizeBytes?: number
  allowedMimeTypes?: string[]
}

// Security configuration
const SECURITY_CONFIG = {
  maxFileSize: 50 * 1024 * 1024, // 50MB
  allowedMimeTypes: [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/webp',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ],
  virusScanEndpoint: '/api/security/virus-scan',
  encryptionEndpoint: '/api/security/encrypt-document',
  uploadEndpoint: '/api/documents/upload',
  chunkSize: 1024 * 1024, // 1MB chunks for large files
}

export class DocumentUploadService {
  private telemetry: TelemetryService

  constructor(telemetryService?: TelemetryService) {
    this.telemetry = telemetryService || {
      trackUserAction: (action: string, category: string, label?: string) => {
        console.log(`Telemetry: ${action} - ${category} - ${label}`)
      },
      trackPageView: () => {},
      setUserId: () => {}
    }
  }

  /**
   * Validates file before upload
   */
  private validateFile(file: File, options: UploadOptions): { valid: boolean; error?: string } {
    // File size validation
    const maxSize = options.maxSizeBytes || SECURITY_CONFIG.maxFileSize
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size exceeds limit of ${Math.round(maxSize / 1024 / 1024)}MB`
      }
    }

    // MIME type validation
    const allowedTypes = options.allowedMimeTypes || SECURITY_CONFIG.allowedMimeTypes
    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type ${file.type} is not allowed. Allowed types: ${allowedTypes.join(', ')}`
      }
    }

    // File name validation (prevent path traversal)
    if (file.name.includes('..') || file.name.includes('/') || file.name.includes('\\')) {
      return {
        valid: false,
        error: 'Invalid file name. Special characters not allowed.'
      }
    }

    // Check for suspicious file extensions
    const suspiciousExtensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.cpl']
    const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
    if (suspiciousExtensions.includes(extension)) {
      return {
        valid: false,
        error: 'File type not permitted for security reasons.'
      }
    }

    return { valid: true }
  }

  /**
   * Generates file hash for integrity verification
   */
  private async generateFileHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer()
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  }

  /**
   * Encrypts file content client-side before upload
   */
  private async encryptFile(file: File): Promise<{ encryptedFile: Blob; encryptionKey: string }> {
    // Generate encryption key
    const key = await crypto.subtle.generateKey(
      { name: 'AES-GCM', length: 256 },
      true,
      ['encrypt', 'decrypt']
    )

    // Generate IV
    const iv = crypto.getRandomValues(new Uint8Array(12))

    // Encrypt file
    const fileBuffer = await file.arrayBuffer()
    const encryptedBuffer = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      key,
      fileBuffer
    )

    // Export key for storage
    const exportedKey = await crypto.subtle.exportKey('raw', key)
    const keyString = Array.from(new Uint8Array(exportedKey))
      .map(b => b.toString(16).padStart(2, '0')).join('')

    // Combine IV and encrypted data
    const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength)
    combined.set(iv, 0)
    combined.set(new Uint8Array(encryptedBuffer), iv.length)

    return {
      encryptedFile: new Blob([combined]),
      encryptionKey: keyString
    }
  }

  /**
   * Uploads file with progress tracking
   */
  private async uploadWithProgress(
    file: Blob,
    metadata: Partial<DocumentMetadata>,
    onProgress: (progress: UploadProgress) => void
  ): Promise<DocumentMetadata> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      const formData = new FormData()

      // Add file and metadata
      formData.append('file', file)
      formData.append('metadata', JSON.stringify(metadata))

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress: UploadProgress = {
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded / event.total) * 100)
          }
          onProgress(progress)
        }
      })

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText)
            resolve(response.document)
          } catch (error) {
            reject(new Error('Invalid server response'))
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`))
        }
      })

      // Handle errors
      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed due to network error'))
      })

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload was aborted'))
      })

      // Send request
      xhr.open('POST', SECURITY_CONFIG.uploadEndpoint)
      xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
      xhr.send(formData)
    })
  }

  /**
   * Main upload method
   */
  async uploadDocument(
    file: File,
    options: UploadOptions,
    onProgress: (progress: UploadProgress) => void = () => {}
  ): Promise<DocumentMetadata> {
    try {
      this.telemetry.trackUserAction('document_upload_started', 'security', options.documentType)

      // Validate file
      const validation = this.validateFile(file, options)
      if (!validation.valid) {
        throw new Error(validation.error)
      }

      // Generate file hash
      const hash = await this.generateFileHash(file)

      // Encrypt file
      const { encryptedFile, encryptionKey } = await this.encryptFile(file)

      // Prepare metadata
      const metadata: Partial<DocumentMetadata> = {
        id: crypto.randomUUID(),
        originalName: file.name,
        mimeType: file.type,
        size: file.size,
        hash,
        uploadedAt: new Date().toISOString(),
        documentType: options.documentType,
        encryptionKey,
        verified: false,
        verificationStatus: 'pending'
      }

      // Upload encrypted file
      const result = await this.uploadWithProgress(encryptedFile, metadata, onProgress)

      this.telemetry.trackUserAction('document_upload_completed', 'security', options.documentType)

      return result

    } catch (error) {
      this.telemetry.trackUserAction('document_upload_failed', 'security', error.message)
      throw error
    }
  }

  /**
   * Get uploaded documents for a user
   */
  async getDocuments(userId: string): Promise<DocumentMetadata[]> {
    try {
      const response = await fetch(`/api/documents/user/${userId}`)
      if (!response.ok) {
        throw new Error('Failed to fetch documents')
      }
      return await response.json()
    } catch (error) {
      this.telemetry.trackUserAction('document_fetch_failed', 'security', error.message)
      throw error
    }
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<void> {
    try {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('Failed to delete document')
      }
      this.telemetry.trackUserAction('document_deleted', 'security', documentId)
    } catch (error) {
      this.telemetry.trackUserAction('document_delete_failed', 'security', error.message)
      throw error
    }
  }
}

// Export singleton instance
export const documentUploadService = new DocumentUploadService()