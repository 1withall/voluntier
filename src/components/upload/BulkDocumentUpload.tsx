/**
 * Bulk Document Upload Component with Drag-and-Drop
 * Supports multiple file uploads with preprocessing and ML verification
 */

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { useLocalStorage } from '../../hooks/useLocalStorage'
import { useTelemetry } from '../../services/telemetry'
import { createDocumentPreprocessor } from '../../services/documentPreprocessor'
import { createSimplifiedMLDocumentVerifier } from '../../services/simplifiedMLVerifier'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Alert, AlertDescription } from '../ui/alert'
import { Upload, X, FileText, Warning, CheckCircle, Clock, Eye } from '@phosphor-icons/react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { 
  DocumentType, 
  BulkUploadSession, 
  BulkUploadFile, 
  DragDropUploadState,
  UploadProgress,
  ProcessingResult,
  MLVerificationRequest,
  MLVerificationResponse
} from '../../types/documents'
import { UserProfile } from '../../types/profiles'

interface BulkDocumentUploadProps {
  userProfile: UserProfile
  onUploadComplete?: (session: BulkUploadSession) => void
  onUploadError?: (error: string) => void
  maxFiles?: number
  maxFileSize?: number
}

export function BulkDocumentUpload({
  userProfile,
  onUploadComplete,
  onUploadError,
  maxFiles = 20,
  maxFileSize = 50 * 1024 * 1024 // 50MB
}: BulkDocumentUploadProps) {
  const [uploadSession, setUploadSession] = useLocalStorage<BulkUploadSession | null>('current-upload-session', null)
  const [dragState, setDragState] = useState<DragDropUploadState>({
    isDragActive: false,
    isDragAccept: false,
    isDragReject: false,
    files: [],
    rejectedFiles: []
  })
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)
  const { trackUserAction } = useTelemetry()
  
  // Initialize services
  const documentPreprocessor = createDocumentPreprocessor()
  const mlVerifier = createSimplifiedMLDocumentVerifier()

  // Supported file types
  const acceptedFileTypes = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'application/pdf'
  ]

  // Handle drag and drop events
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    setDragState(prev => ({
      ...prev,
      isDragActive: true
    }))
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Only set drag inactive if leaving the drop zone entirely
    if (!dropZoneRef.current?.contains(e.relatedTarget as Node)) {
      setDragState(prev => ({
        ...prev,
        isDragActive: false,
        isDragAccept: false,
        isDragReject: false
      }))
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const files = Array.from(e.dataTransfer.files)
    const validFiles = files.filter(file => 
      acceptedFileTypes.includes(file.type) && file.size <= maxFileSize
    )
    
    setDragState(prev => ({
      ...prev,
      isDragActive: true,
      isDragAccept: validFiles.length > 0 && files.length <= maxFiles,
      isDragReject: validFiles.length === 0 || files.length > maxFiles
    }))
  }, [acceptedFileTypes, maxFileSize, maxFiles])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)

    setDragState({
      isDragActive: false,
      isDragAccept: false,
      isDragReject: false,
      files: [],
      rejectedFiles: []
    })
  }, [])

  // Handle file selection
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    handleFiles(files)
  }, [])

  // Process selected files
  const handleFiles = useCallback((files: File[]) => {
    const validFiles: File[] = []
    const rejectedFiles: { file: File; errors: string[] }[] = []

    files.forEach(file => {
      const errors: string[] = []

      if (!acceptedFileTypes.includes(file.type)) {
        errors.push(`Unsupported file type: ${file.type}`)
      }

      if (file.size > maxFileSize) {
        errors.push(`File too large: ${(file.size / (1024 * 1024)).toFixed(1)}MB (max: ${maxFileSize / (1024 * 1024)}MB)`)
      }

      if (errors.length > 0) {
        rejectedFiles.push({ file, errors })
      } else {
        validFiles.push(file)
      }
    })

    if (validFiles.length + (uploadSession?.files.length || 0) > maxFiles) {
      toast.error(`Cannot upload more than ${maxFiles} files`)
      return
    }

    if (rejectedFiles.length > 0) {
      toast.error(`${rejectedFiles.length} file(s) rejected. Check the upload area for details.`)
    }

    if (validFiles.length > 0) {
      addFilesToSession(validFiles)
      trackUserAction('bulk_upload_files_added', 'upload', `${validFiles.length}_files`)
    }

    setDragState(prev => ({ ...prev, rejectedFiles }))
  }, [acceptedFileTypes, maxFileSize, maxFiles, uploadSession, trackUserAction])

  // Add files to upload session
  const addFilesToSession = useCallback((files: File[]) => {
    const sessionId = uploadSession?.id || `session_${Date.now()}`
    const bulkFiles: BulkUploadFile[] = files.map(file => ({
      id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      fileName: file.name,
      fileSize: file.size,
      status: 'pending'
    }))

    const newSession: BulkUploadSession = uploadSession ? {
      ...uploadSession,
      totalFiles: uploadSession.totalFiles + files.length,
      files: [...uploadSession.files, ...bulkFiles]
    } : {
      id: sessionId,
      userId: userProfile.id,
      totalFiles: files.length,
      processedFiles: 0,
      successfulUploads: 0,
      failedUploads: 0,
      status: 'initializing',
      startTime: Date.now(),
      files: bulkFiles
    }

    setUploadSession(newSession)

    // Initialize progress tracking
    const progressEntries: UploadProgress[] = files.map((file, index) => ({
      fileId: bulkFiles[index].id,
      fileName: file.name,
      progress: 0,
      status: 'uploading'
    }))

    setUploadProgress(prev => [...prev, ...progressEntries])

    // Store files for processing
    files.forEach((file, index) => {
      const fileKey = `upload_file_${bulkFiles[index].id}`
      // Note: In a real implementation, files would be stored in a proper file storage system
      // For this demo, we'll simulate the upload process
    })
  }, [uploadSession, userProfile.id])

  // Start bulk upload processing
  const startBulkUpload = useCallback(async () => {
    if (!uploadSession || uploadSession.files.length === 0) {
      toast.error('No files to upload')
      return
    }

    setIsProcessing(true)
    trackUserAction('bulk_upload_started', 'upload', `${uploadSession.files.length}_files`)

    try {
      // Update session status
      setUploadSession(prev => prev ? { ...prev, status: 'processing' } : null)

      let successCount = 0
      let failureCount = 0

      // Process files in batches
      for (let i = 0; i < uploadSession.files.length; i++) {
        const bulkFile = uploadSession.files[i]
        
        try {
          // Update progress
          setUploadProgress(prev => 
            prev.map(p => 
              p.fileId === bulkFile.id 
                ? { ...p, status: 'processing', progress: 50 }
                : p
            )
          )

          // Simulate file retrieval (in real implementation, get from storage)
          const mockFile = new File(['mock content'], bulkFile.fileName, { type: 'image/jpeg' })
          
          // Preprocess document
          const processingResult = await documentPreprocessor.preprocessDocument(mockFile)
          
          if (!processingResult.success) {
            throw new Error(processingResult.errors.join(', '))
          }

          // Create ML verification request
          const mlRequest: MLVerificationRequest = {
            documentId: bulkFile.id,
            documentType: getDocumentTypeFromFileName(bulkFile.fileName),
            extractedData: processingResult.extractedData!,
            metadata: processingResult.metadata!,
            userContext: {
              userId: userProfile.id,
              userType: userProfile.userType,
              previousVerifications: 0, // Would be fetched from user history
              riskLevel: 'low'
            }
          }

          // Perform ML verification
          const verificationResult = await mlVerifier.verifyDocument(mlRequest)

          // Update file status
          setUploadSession(prev => {
            if (!prev) return null
            return {
              ...prev,
              files: prev.files.map(f => 
                f.id === bulkFile.id 
                  ? { 
                      ...f, 
                      status: 'completed',
                      processingResult,
                      documentType: mlRequest.documentType
                    }
                  : f
              ),
              processedFiles: prev.processedFiles + 1,
              successfulUploads: prev.successfulUploads + 1
            }
          })

          setUploadProgress(prev => 
            prev.map(p => 
              p.fileId === bulkFile.id 
                ? { ...p, status: 'completed', progress: 100 }
                : p
            )
          )

          successCount++
          
          toast.success(`${bulkFile.fileName} processed successfully`)

        } catch (error) {
          console.error(`Failed to process ${bulkFile.fileName}:`, error)
          
          setUploadSession(prev => {
            if (!prev) return null
            return {
              ...prev,
              files: prev.files.map(f => 
                f.id === bulkFile.id 
                  ? { 
                      ...f, 
                      status: 'failed',
                      error: error instanceof Error ? error.message : 'Processing failed'
                    }
                  : f
              ),
              processedFiles: prev.processedFiles + 1,
              failedUploads: prev.failedUploads + 1
            }
          })

          setUploadProgress(prev => 
            prev.map(p => 
              p.fileId === bulkFile.id 
                ? { ...p, status: 'failed', progress: 0, error: error instanceof Error ? error.message : 'Failed' }
                : p
            )
          )

          failureCount++
          toast.error(`Failed to process ${bulkFile.fileName}`)
        }

        // Add delay between files to prevent overwhelming the system
        await new Promise(resolve => setTimeout(resolve, 1000))
      }

      // Complete session
      setUploadSession(prev => {
        if (!prev) return null
        return {
          ...prev,
          status: 'completed',
          endTime: Date.now()
        }
      })

      const finalSession = {
        ...uploadSession,
        status: 'completed' as const,
        endTime: Date.now(),
        successfulUploads: successCount,
        failedUploads: failureCount
      }

      onUploadComplete?.(finalSession)
      
      toast.success(
        `Bulk upload completed: ${successCount} successful, ${failureCount} failed`
      )

      trackUserAction('bulk_upload_completed', 'upload', `${successCount}_success_${failureCount}_failed`)

    } catch (error) {
      console.error('Bulk upload failed:', error)
      
      setUploadSession(prev => prev ? { ...prev, status: 'failed' } : null)
      
      const errorMessage = error instanceof Error ? error.message : 'Bulk upload failed'
      onUploadError?.(errorMessage)
      toast.error(errorMessage)
      
      trackUserAction('bulk_upload_failed', 'upload', errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }, [uploadSession, userProfile, documentPreprocessor, mlVerifier, onUploadComplete, onUploadError, trackUserAction])

  // Remove file from session
  const removeFile = useCallback((fileId: string) => {
    setUploadSession(prev => {
      if (!prev) return null
      return {
        ...prev,
        files: prev.files.filter(f => f.id !== fileId),
        totalFiles: prev.totalFiles - 1
      }
    })

    setUploadProgress(prev => prev.filter(p => p.fileId !== fileId))
    
    trackUserAction('bulk_upload_file_removed', 'upload', fileId)
  }, [trackUserAction])

  // Clear all files
  const clearAllFiles = useCallback(() => {
    setUploadSession(null)
    setUploadProgress([])
    setDragState(prev => ({ ...prev, rejectedFiles: [] }))
    
    trackUserAction('bulk_upload_cleared', 'upload')
  }, [trackUserAction])

  // Get document type from filename (simple heuristic)
  const getDocumentTypeFromFileName = (fileName: string): DocumentType => {
    const name = fileName.toLowerCase()
    
    if (name.includes('license') || name.includes('dl')) return 'drivers_license'
    if (name.includes('passport')) return 'passport'
    if (name.includes('id')) return 'government_id'
    if (name.includes('utility') || name.includes('bill')) return 'utility_bill'
    if (name.includes('bank') || name.includes('statement')) return 'bank_statement'
    
    return 'other'
  }

  // Get status icon for file
  const getFileStatusIcon = (status: BulkUploadFile['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-muted-foreground" />
      case 'processing':
        return <Upload className="h-4 w-4 text-blue-500 animate-pulse" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <Warning className="h-4 w-4 text-red-500" />
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />
    }
  }

  // Get status badge variant
  const getStatusVariant = (status: BulkUploadFile['status']) => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'failed':
        return 'destructive'
      case 'processing':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Bulk Document Upload
          </CardTitle>
          <CardDescription>
            Upload multiple documents at once for automated processing and verification. 
            Drag and drop files or click to select.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Drop Zone */}
          <div
            ref={dropZoneRef}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragState.isDragActive
                ? dragState.isDragAccept
                  ? 'border-green-500 bg-green-50'
                  : 'border-red-500 bg-red-50'
                : 'border-border bg-muted/30 hover:bg-muted/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={acceptedFileTypes.join(',')}
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={isProcessing}
            />
            
            <div className="space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Upload className="h-6 w-6 text-primary" />
              </div>
              
              <div>
                <h3 className="text-lg font-medium">
                  {dragState.isDragActive
                    ? dragState.isDragAccept
                      ? 'Drop files here'
                      : 'Some files cannot be uploaded'
                    : 'Drop files here or click to browse'
                  }
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Supports PDF, JPEG, PNG, GIF, BMP, TIFF up to {maxFileSize / (1024 * 1024)}MB each
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Maximum {maxFiles} files per upload
                </p>
              </div>

              {!dragState.isDragActive && (
                <Button 
                  variant="outline" 
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isProcessing}
                >
                  Select Files
                </Button>
              )}
            </div>
          </div>

          {/* Rejected Files Alert */}
          {dragState.rejectedFiles.length > 0 && (
            <Alert>
              <Warning className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">Some files were rejected:</p>
                  {dragState.rejectedFiles.map((rejectedFile, index) => (
                    <div key={index} className="text-sm">
                      <span className="font-medium">{rejectedFile.file.name}:</span>
                      <ul className="list-disc list-inside ml-2">
                        {rejectedFile.errors.map((error, errorIndex) => (
                          <li key={errorIndex}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Upload Session Status */}
          {uploadSession && uploadSession.files.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Upload Session</h3>
                <div className="flex gap-2">
                  {!isProcessing && uploadSession.status === 'initializing' && (
                    <Button onClick={startBulkUpload}>
                      Start Upload
                    </Button>
                  )}
                  <Button 
                    variant="outline" 
                    onClick={clearAllFiles}
                    disabled={isProcessing}
                  >
                    <X className="h-4 w-4 mr-2" />
                    Clear All
                  </Button>
                </div>
              </div>

              {/* Session Progress */}
              {uploadSession.status === 'processing' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Overall Progress</span>
                    <span>{uploadSession.processedFiles}/{uploadSession.totalFiles}</span>
                  </div>
                  <Progress 
                    value={(uploadSession.processedFiles / uploadSession.totalFiles) * 100} 
                    className="w-full" 
                  />
                </div>
              )}

              {/* File List */}
              <div className="space-y-3">
                <AnimatePresence>
                  {uploadSession.files.map((file) => {
                    const progress = uploadProgress.find(p => p.fileId === file.id)
                    
                    return (
                      <motion.div
                        key={file.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="flex items-center justify-between p-4 border rounded-lg bg-card"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          {getFileStatusIcon(file.status)}
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium truncate">
                                {file.fileName}
                              </p>
                              <Badge variant={getStatusVariant(file.status)}>
                                {file.status}
                              </Badge>
                            </div>
                            
                            <p className="text-xs text-muted-foreground">
                              {(file.fileSize / 1024).toFixed(1)} KB
                            </p>
                            
                            {file.error && (
                              <p className="text-xs text-red-500 mt-1">
                                {file.error}
                              </p>
                            )}
                            
                            {progress && progress.status === 'processing' && (
                              <div className="mt-2">
                                <Progress value={progress.progress} className="h-1" />
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {file.documentType && (
                            <Badge variant="outline" className="text-xs">
                              {file.documentType.replace('_', ' ')}
                            </Badge>
                          )}
                          
                          {!isProcessing && file.status === 'pending' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(file.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </motion.div>
                    )
                  })}
                </AnimatePresence>
              </div>

              {/* Session Summary */}
              {uploadSession.status === 'completed' && (
                <Card>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <p className="text-2xl font-bold text-green-600">
                          {uploadSession.successfulUploads}
                        </p>
                        <p className="text-sm text-muted-foreground">Successful</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-red-600">
                          {uploadSession.failedUploads}
                        </p>
                        <p className="text-sm text-muted-foreground">Failed</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-blue-600">
                          {uploadSession.endTime && uploadSession.startTime
                            ? Math.round((uploadSession.endTime - uploadSession.startTime) / 1000)
                            : 0}s
                        </p>
                        <p className="text-sm text-muted-foreground">Duration</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}