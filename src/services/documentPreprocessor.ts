/**
 * Document Preprocessing Service
 * Handles document analysis, extraction, and preparation for ML verification
 */

import { DocumentUpload, DocumentMetadata, ProcessingResult } from '../types/documents'

export interface PreprocessingConfig {
  enableOCR: boolean
  enableTextExtraction: boolean
  enableImageAnalysis: boolean
  supportedFormats: string[]
  maxFileSizeBytes: number
  qualityThresholds: {
    minResolution: number
    minContrast: number
    maxBlur: number
  }
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

export class DocumentPreprocessor {
  private config: PreprocessingConfig
  private apiEndpoint: string

  constructor(config: PreprocessingConfig, apiEndpoint: string = '/api/ml') {
    this.config = config
    this.apiEndpoint = apiEndpoint
  }

  /**
   * Preprocess a single document file
   */
  async preprocessDocument(file: File): Promise<ProcessingResult> {
    try {
      // Validate file format and size
      this.validateFile(file)

      // Extract basic metadata
      const metadata = await this.extractBasicMetadata(file)

      // Convert to optimal format for processing
      const processedFile = await this.optimizeForProcessing(file)

      // Extract text and analyze structure
      const extractedData = await this.extractDocumentData(processedFile)

      // Perform quality assessment
      const qualityScore = await this.assessDocumentQuality(processedFile)

      return {
        success: true,
        metadata,
        extractedData,
        qualityScore,
        processingTime: Date.now() - metadata.uploadTimestamp,
        errors: []
      }
    } catch (error) {
      return {
        success: false,
        metadata: null,
        extractedData: null,
        qualityScore: 0,
        processingTime: 0,
        errors: [error instanceof Error ? error.message : 'Unknown preprocessing error']
      }
    }
  }

  /**
   * Process multiple documents in batch
   */
  async preprocessBatch(files: File[]): Promise<ProcessingResult[]> {
    const results: ProcessingResult[] = []
    
    // Process files in parallel with concurrency limit
    const BATCH_SIZE = 3
    for (let i = 0; i < files.length; i += BATCH_SIZE) {
      const batch = files.slice(i, i + BATCH_SIZE)
      const batchResults = await Promise.all(
        batch.map(file => this.preprocessDocument(file))
      )
      results.push(...batchResults)
    }

    return results
  }

  /**
   * Validate file format and constraints
   */
  private validateFile(file: File): void {
    if (!this.config.supportedFormats.includes(file.type)) {
      throw new Error(`Unsupported file format: ${file.type}`)
    }

    if (file.size > this.config.maxFileSizeBytes) {
      throw new Error(`File size exceeds limit: ${file.size} bytes`)
    }

    // Check for potentially malicious files
    this.performSecurityScan(file)
  }

  /**
   * Security scan for malicious content
   */
  private performSecurityScan(file: File): void {
    // Check file extension vs MIME type mismatch
    const expectedMimeTypes = this.getExpectedMimeTypes(file.name)
    if (!expectedMimeTypes.includes(file.type)) {
      throw new Error('File extension and MIME type mismatch detected')
    }

    // Additional security checks would be implemented here
    // - Embedded script detection
    // - Malware signature scanning
    // - File header validation
  }

  /**
   * Extract basic file metadata
   */
  private async extractBasicMetadata(file: File): Promise<DocumentMetadata> {
    return {
      fileName: file.name,
      fileSize: file.size,
      mimeType: file.type,
      uploadTimestamp: Date.now(),
      checksum: await this.calculateChecksum(file),
      lastModified: file.lastModified
    }
  }

  /**
   * Optimize file for ML processing
   */
  private async optimizeForProcessing(file: File): Promise<File> {
    if (file.type.startsWith('image/')) {
      return await this.optimizeImage(file)
    } else if (file.type === 'application/pdf') {
      return await this.optimizePDF(file)
    }
    return file
  }

  /**
   * Optimize image files for better OCR results
   */
  private async optimizeImage(file: File): Promise<File> {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')!
      const img = new Image()

      img.onload = () => {
        // Resize to optimal dimensions for OCR
        const maxDimension = 2048
        const scale = Math.min(maxDimension / img.width, maxDimension / img.height, 1)
        
        canvas.width = img.width * scale
        canvas.height = img.height * scale

        // Apply preprocessing filters
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        
        // Enhance contrast and brightness for better OCR
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        this.enhanceImageData(imageData)
        ctx.putImageData(imageData, 0, 0)

        canvas.toBlob((blob) => {
          if (blob) {
            resolve(new File([blob], file.name, { type: 'image/png' }))
          } else {
            reject(new Error('Failed to optimize image'))
          }
        }, 'image/png', 0.95)
      }

      img.onerror = reject
      img.src = URL.createObjectURL(file)
    }) as Promise<File>
  }

  /**
   * Enhance image data for better OCR performance
   */
  private enhanceImageData(imageData: ImageData): void {
    const data = imageData.data
    
    for (let i = 0; i < data.length; i += 4) {
      // Convert to grayscale and enhance contrast
      const avg = (data[i] + data[i + 1] + data[i + 2]) / 3
      const enhanced = this.enhanceContrast(avg)
      
      data[i] = enhanced     // Red
      data[i + 1] = enhanced // Green
      data[i + 2] = enhanced // Blue
      // Alpha channel (data[i + 3]) remains unchanged
    }
  }

  /**
   * Enhance contrast using histogram equalization
   */
  private enhanceContrast(value: number): number {
    // Simple contrast enhancement - could be replaced with more sophisticated algorithms
    const normalized = value / 255
    const enhanced = Math.pow(normalized, 0.8) * 255
    return Math.max(0, Math.min(255, enhanced))
  }

  /**
   * Optimize PDF files for processing
   */
  private async optimizePDF(file: File): Promise<File> {
    // For now, return the original file
    // In a full implementation, this would:
    // - Flatten layers
    // - Optimize image quality
    // - Remove unnecessary metadata
    return file
  }

  /**
   * Extract text and structured data from document
   */
  private async extractDocumentData(file: File): Promise<ExtractedData> {
    const formData = new FormData()
    formData.append('document', file)
    formData.append('config', JSON.stringify({
      enableOCR: this.config.enableOCR,
      enableTextExtraction: this.config.enableTextExtraction,
      enableImageAnalysis: this.config.enableImageAnalysis
    }))

    const response = await fetch(`${this.apiEndpoint}/extract`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Security-Token': await this.getSecurityToken()
      }
    })

    if (!response.ok) {
      throw new Error(`Document extraction failed: ${response.statusText}`)
    }

    return await response.json()
  }

  /**
   * Assess document quality for verification reliability
   */
  private async assessDocumentQuality(file: File): Promise<number> {
    if (!file.type.startsWith('image/')) {
      return 0.9 // Assume good quality for non-image documents
    }

    return new Promise((resolve) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')!
      const img = new Image()

      img.onload = () => {
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        
        // Calculate quality metrics
        const sharpness = this.calculateSharpness(imageData)
        const contrast = this.calculateContrast(imageData)
        const brightness = this.calculateBrightness(imageData)

        // Combine metrics into overall quality score
        const qualityScore = (sharpness * 0.4 + contrast * 0.3 + brightness * 0.3)
        resolve(Math.max(0, Math.min(1, qualityScore)))
      }

      img.onerror = () => resolve(0)
      img.src = URL.createObjectURL(file)
    })
  }

  /**
   * Calculate image sharpness using Laplacian variance
   */
  private calculateSharpness(imageData: ImageData): number {
    const data = imageData.data
    const width = imageData.width
    const height = imageData.height
    
    let variance = 0
    let count = 0

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const idx = (y * width + x) * 4
        
        // Convert to grayscale
        const center = (data[idx] + data[idx + 1] + data[idx + 2]) / 3
        
        // Calculate Laplacian
        const neighbors = [
          ((y - 1) * width + x) * 4,     // top
          ((y + 1) * width + x) * 4,     // bottom
          (y * width + (x - 1)) * 4,     // left
          (y * width + (x + 1)) * 4      // right
        ]
        
        const neighborSum = neighbors.reduce((sum, nIdx) => {
          return sum + (data[nIdx] + data[nIdx + 1] + data[nIdx + 2]) / 3
        }, 0)
        
        const laplacian = 4 * center - neighborSum
        variance += laplacian * laplacian
        count++
      }
    }

    return Math.min(1, variance / count / 10000) // Normalize
  }

  /**
   * Calculate image contrast
   */
  private calculateContrast(imageData: ImageData): number {
    const data = imageData.data
    let min = 255
    let max = 0

    for (let i = 0; i < data.length; i += 4) {
      const gray = (data[i] + data[i + 1] + data[i + 2]) / 3
      min = Math.min(min, gray)
      max = Math.max(max, gray)
    }

    return (max - min) / 255
  }

  /**
   * Calculate image brightness
   */
  private calculateBrightness(imageData: ImageData): number {
    const data = imageData.data
    let sum = 0
    let count = 0

    for (let i = 0; i < data.length; i += 4) {
      const gray = (data[i] + data[i + 1] + data[i + 2]) / 3
      sum += gray
      count++
    }

    const avgBrightness = sum / count / 255
    
    // Optimal brightness is around 0.5-0.7
    const optimal = 0.6
    return 1 - Math.abs(avgBrightness - optimal) / optimal
  }

  /**
   * Calculate file checksum for integrity verification
   */
  private async calculateChecksum(file: File): Promise<string> {
    const buffer = await file.arrayBuffer()
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  }

  /**
   * Get expected MIME types for file extension
   */
  private getExpectedMimeTypes(fileName: string): string[] {
    const ext = fileName.split('.').pop()?.toLowerCase()
    
    const mimeMap: { [key: string]: string[] } = {
      'pdf': ['application/pdf'],
      'jpg': ['image/jpeg'],
      'jpeg': ['image/jpeg'],
      'png': ['image/png'],
      'gif': ['image/gif'],
      'bmp': ['image/bmp'],
      'tiff': ['image/tiff'],
      'tif': ['image/tiff']
    }

    return mimeMap[ext || ''] || []
  }

  /**
   * Get security token for API requests
   */
  private async getSecurityToken(): Promise<string> {
    // In a real implementation, this would get a JWT or similar token
    return 'dummy-security-token'
  }
}

/**
 * Factory function to create configured preprocessor instance
 */
export function createDocumentPreprocessor(): DocumentPreprocessor {
  const config: PreprocessingConfig = {
    enableOCR: true,
    enableTextExtraction: true,
    enableImageAnalysis: true,
    supportedFormats: [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/bmp',
      'image/tiff'
    ],
    maxFileSizeBytes: 50 * 1024 * 1024, // 50MB
    qualityThresholds: {
      minResolution: 300,
      minContrast: 0.3,
      maxBlur: 0.2
    }
  }

  return new DocumentPreprocessor(config)
}