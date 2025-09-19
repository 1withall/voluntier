/**
 * Secure Document Upload Component
 * Integrates document upload service with real-time notifications
 */

import { useState, useCallback, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Progress } from '../ui/progress'
import { Badge } from '../ui/badge'
import { Alert, AlertDescription } from '../ui/alert'
import { Textarea } from '../ui/textarea'
import { Separator } from '../ui/separator'
import { 
  Upload, 
  File, 
  Check, 
  X, 
  Warning, 
  Clock, 
  Shield,
  Eye,
  Trash
} from '@phosphor-icons/react'
import { documentUploadService, DocumentUploadService, DocumentType, DocumentMetadata, UploadProgress } from '../../services/documentUpload'
import { useNotifications } from '../../services/notifications'
import { UserProfile } from '../../types/profiles'
import { useKV } from '@github/spark/hooks'
import { useTelemetry } from '../../services/telemetry'

interface SecureDocumentUploadProps {
  userProfile: UserProfile
  documentType?: DocumentType
  onUploadComplete?: (document: DocumentMetadata) => void
  onUploadError?: (error: string) => void
}

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  government_id: 'Government ID',
  proof_of_address: 'Proof of Address',
  organization_registration: 'Organization Registration',
  business_license: 'Business License',
  reference_letter: 'Reference Letter',
  tax_exemption: 'Tax Exemption Certificate',
  insurance_certificate: 'Insurance Certificate',
  other: 'Other Document'
}

const DOCUMENT_TYPE_DESCRIPTIONS: Record<DocumentType, string> = {
  government_id: 'Driver\'s license, passport, or state-issued ID',
  proof_of_address: 'Utility bill, bank statement, or lease agreement',
  organization_registration: 'Articles of incorporation or nonprofit registration',
  business_license: 'Business registration or operating license',
  reference_letter: 'Character reference from a community member',
  tax_exemption: '501(c)(3) or other tax exemption documentation',
  insurance_certificate: 'General liability or professional insurance',
  other: 'Additional supporting documentation'
}

export function SecureDocumentUpload({ 
  userProfile, 
  documentType,
  onUploadComplete,
  onUploadError 
}: SecureDocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedDocumentType, setSelectedDocumentType] = useState<DocumentType>(documentType || 'other')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({ loaded: 0, total: 0, percentage: 0 })
  const [error, setError] = useState<string | null>(null)
  const [uploadedDocuments, setUploadedDocuments] = useKV<DocumentMetadata[]>(`documents-${userProfile.id}`, [])
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { trackUserAction } = useTelemetry()
  const { notifications } = useNotifications(userProfile.id)

  // Initialize document upload service with telemetry
  const uploadService = new DocumentUploadService({
    trackUserAction,
    trackPageView: () => {},
    setUserId: () => {}
  })

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
      trackUserAction('document_selected', 'upload', selectedDocumentType)
    }
  }, [selectedDocumentType, trackUserAction])

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.stopPropagation()
  }, [])

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.stopPropagation()
    
    const files = event.dataTransfer.files
    if (files.length > 0) {
      setSelectedFile(files[0])
      setError(null)
      trackUserAction('document_dropped', 'upload', selectedDocumentType)
    }
  }, [selectedDocumentType, trackUserAction])

  const handleUpload = useCallback(async () => {
    if (!selectedFile) return

    setUploading(true)
    setError(null)
    setUploadProgress({ loaded: 0, total: selectedFile.size, percentage: 0 })

    try {
      const document = await uploadService.uploadDocument(
        selectedFile,
        {
          documentType: selectedDocumentType,
          description: description.trim() || undefined,
          isRequired: true
        },
        (progress) => {
          setUploadProgress(progress)
        }
      )

      // Update local state
      setUploadedDocuments(current => [document, ...(current || [])])
      
      // Reset form
      setSelectedFile(null)
      setDescription('')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      onUploadComplete?.(document)
      trackUserAction('document_upload_success', 'upload', selectedDocumentType)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed'
      setError(errorMessage)
      onUploadError?.(errorMessage)
      trackUserAction('document_upload_error', 'upload', errorMessage)
    } finally {
      setUploading(false)
    }
  }, [selectedFile, selectedDocumentType, description, uploadService, setUploadedDocuments, onUploadComplete, onUploadError, trackUserAction])

  const handleDelete = useCallback(async (documentId: string) => {
    try {
      await uploadService.deleteDocument(documentId)
      setUploadedDocuments(current => (current || []).filter(doc => doc.id !== documentId))
      trackUserAction('document_deleted', 'upload', documentId)
    } catch (err) {
      setError('Failed to delete document')
    }
  }, [uploadService, setUploadedDocuments, trackUserAction])

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return <Check className="text-success" size={16} />
      case 'rejected':
        return <X className="text-destructive" size={16} />
      case 'in_progress':
        return <Clock className="text-accent" size={16} />
      default:
        return <Clock className="text-muted-foreground" size={16} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'success'
      case 'rejected':
        return 'destructive'
      case 'in_progress':
        return 'default'
      default:
        return 'secondary'
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield size={20} />
            Secure Document Upload
          </CardTitle>
          <CardDescription>
            Upload documents securely with end-to-end encryption. All files are virus-scanned and verified.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Document Type Selection */}
          {!documentType && (
            <div className="space-y-2">
              <Label htmlFor="document-type">Document Type</Label>
              <Select value={selectedDocumentType} onValueChange={(value) => setSelectedDocumentType(value as DocumentType)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select document type" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(DOCUMENT_TYPE_LABELS).map(([type, label]) => (
                    <SelectItem key={type} value={type}>
                      <div>
                        <div className="font-medium">{label}</div>
                        <div className="text-sm text-muted-foreground">
                          {DOCUMENT_TYPE_DESCRIPTIONS[type as DocumentType]}
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* File Upload Area */}
          <div className="space-y-4">
            <Label>Select File</Label>
            
            {!selectedFile ? (
              <div
                className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={48} className="mx-auto mb-4 text-muted-foreground" />
                <div className="space-y-2">
                  <p className="text-lg font-medium">Choose a file or drag it here</p>
                  <p className="text-sm text-muted-foreground">
                    PDF, JPEG, PNG, or Word documents up to 50MB
                  </p>
                </div>
                <Input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
                  onChange={handleFileSelect}
                />
              </div>
            ) : (
              <div className="border rounded-lg p-4 bg-muted/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <File size={24} className="text-primary" />
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null)
                      if (fileInputRef.current) fileInputRef.current.value = ''
                    }}
                  >
                    <X size={16} />
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              placeholder="Add any additional context about this document..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          {/* Upload Progress */}
          {uploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress.percentage}%</span>
              </div>
              <Progress value={uploadProgress.percentage} className="w-full" />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <Warning size={16} />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="w-full"
          >
            {uploading ? 'Uploading...' : 'Upload Document'}
          </Button>
        </CardContent>
      </Card>

      {/* Uploaded Documents */}
      {uploadedDocuments && uploadedDocuments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Uploaded Documents</CardTitle>
            <CardDescription>
              Track the verification status of your uploaded documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {uploadedDocuments.map((doc, index) => (
                <div key={doc.id}>
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <File size={20} className="text-muted-foreground" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium">{doc.originalName}</p>
                          <Badge variant={getStatusColor(doc.verificationStatus) as any}>
                            <div className="flex items-center gap-1">
                              {getStatusIcon(doc.verificationStatus)}
                              {doc.verificationStatus.replace('_', ' ')}
                            </div>
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {DOCUMENT_TYPE_LABELS[doc.documentType]} • {formatFileSize(doc.size)} • 
                          Uploaded {new Date(doc.uploadedAt).toLocaleDateString()}
                        </p>
                        {doc.verificationNotes && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {doc.verificationNotes}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <Eye size={16} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(doc.id)}
                      >
                        <Trash size={16} />
                      </Button>
                    </div>
                  </div>
                  {index < uploadedDocuments.length - 1 && <Separator className="my-4" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Notifications */}
      {notifications && notifications.filter(n => n.category === 'verification').length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Verification Updates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {notifications
                .filter(n => n.category === 'verification')
                .slice(0, 5)
                .map((notification) => (
                  <div key={notification.id} className="flex items-start gap-3 p-3 border rounded-lg">
                    {getStatusIcon(notification.type)}
                    <div className="flex-1">
                      <p className="font-medium">{notification.title}</p>
                      <p className="text-sm text-muted-foreground">{notification.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(notification.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}