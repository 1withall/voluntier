/**
 * Enhanced Document Upload with AI Preprocessing
 * Combines single and bulk upload capabilities with intelligent document analysis
 */

import React, { useState, useCallback } from 'react'
import { useKV } from '@github/spark/hooks'
import { useTelemetry } from '../../services/telemetry'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Upload, FileText, Brain, Shield, CheckCircle } from '@phosphor-icons/react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { SecureDocumentUpload } from './SecureDocumentUpload'
import { BulkDocumentUpload } from './BulkDocumentUpload'
import { UserProfile } from '../../types/profiles'
import { DocumentUpload, BulkUploadSession } from '../../types/documents'

interface EnhancedDocumentUploadProps {
  userProfile: UserProfile
  onUploadComplete?: (documents: DocumentUpload[] | BulkUploadSession) => void
  onUploadError?: (error: string) => void
}

export function EnhancedDocumentUpload({
  userProfile,
  onUploadComplete,
  onUploadError
}: EnhancedDocumentUploadProps) {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single')
  const [uploadStats, setUploadStats] = useKV<{
    totalUploads: number
    successfulUploads: number
    failedUploads: number
    lastUploadTime: number
  }>('upload-stats', {
    totalUploads: 0,
    successfulUploads: 0,
    failedUploads: 0,
    lastUploadTime: 0
  })
  
  const { trackUserAction } = useTelemetry()

  const handleSingleUploadComplete = useCallback((doc: DocumentUpload) => {
    setUploadStats(current => {
      const stats = current || { totalUploads: 0, successfulUploads: 0, failedUploads: 0, lastUploadTime: 0 }
      return {
        totalUploads: stats.totalUploads + 1,
        successfulUploads: stats.successfulUploads + 1,
        failedUploads: stats.failedUploads,
        lastUploadTime: Date.now()
      }
    })
    
    trackUserAction('single_document_upload_complete', 'upload', doc.documentType)
    onUploadComplete?.([doc])
  }, [onUploadComplete, trackUserAction])

  const handleBulkUploadComplete = useCallback((session: BulkUploadSession) => {
    setUploadStats(current => {
      const stats = current || { totalUploads: 0, successfulUploads: 0, failedUploads: 0, lastUploadTime: 0 }
      return {
        totalUploads: stats.totalUploads + session.totalFiles,
        successfulUploads: stats.successfulUploads + session.successfulUploads,
        failedUploads: stats.failedUploads + session.failedUploads,
        lastUploadTime: Date.now()
      }
    })
    
    trackUserAction('bulk_document_upload_complete', 'upload', `${session.successfulUploads}_success`)
    onUploadComplete?.(session)
  }, [onUploadComplete, trackUserAction])

  const handleUploadError = useCallback((error: string) => {
    setUploadStats(current => {
      const stats = current || { totalUploads: 0, successfulUploads: 0, failedUploads: 0, lastUploadTime: 0 }
      return {
        totalUploads: stats.totalUploads + 1,
        successfulUploads: stats.successfulUploads,
        failedUploads: stats.failedUploads + 1,
        lastUploadTime: Date.now()
      }
    })
    
    trackUserAction('document_upload_error', 'upload', error)
    onUploadError?.(error)
  }, [onUploadError, trackUserAction])

  return (
    <div className="space-y-6">
      {/* Upload Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Document Upload Center
          </CardTitle>
          <CardDescription>
            Secure document upload with AI-powered preprocessing and verification
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">{uploadStats?.totalUploads || 0}</p>
              <p className="text-sm text-muted-foreground">Total Uploads</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{uploadStats?.successfulUploads || 0}</p>
              <p className="text-sm text-muted-foreground">Successful</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{uploadStats?.failedUploads || 0}</p>
              <p className="text-sm text-muted-foreground">Failed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {uploadStats && uploadStats.totalUploads > 0 
                  ? Math.round((uploadStats.successfulUploads / uploadStats.totalUploads) * 100)
                  : 0
                }%
              </p>
              <p className="text-sm text-muted-foreground">Success Rate</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Features Overview */}
      <Card>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-3 gap-6">
            <motion.div 
              className="text-center space-y-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Brain className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-semibold">AI Preprocessing</h3>
              <p className="text-sm text-muted-foreground">
                Intelligent text extraction, image enhancement, and quality optimization
              </p>
            </motion.div>

            <motion.div 
              className="text-center space-y-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-semibold">ML Verification</h3>
              <p className="text-sm text-muted-foreground">
                Automated document authenticity and fraud detection using machine learning
              </p>
            </motion.div>

            <motion.div 
              className="text-center space-y-2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="mx-auto w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <Shield className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="font-semibold">Security First</h3>
              <p className="text-sm text-muted-foreground">
                End-to-end encryption, malware scanning, and secure document handling
              </p>
            </motion.div>
          </div>
        </CardContent>
      </Card>

      {/* Upload Interface */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Choose between single document upload or bulk processing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'single' | 'bulk')}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="single" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Single Upload
              </TabsTrigger>
              <TabsTrigger value="bulk" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Bulk Upload
              </TabsTrigger>
            </TabsList>

            <TabsContent value="single" className="mt-6">
              <SecureDocumentUpload
                userProfile={userProfile}
                onUploadComplete={(document) => {
                  // Convert DocumentMetadata from upload service to DocumentUpload
                  const docUpload: DocumentUpload = {
                    id: document.id,
                    userId: userProfile.id,
                    fileName: document.originalName,
                    fileSize: document.size,
                    mimeType: document.mimeType,
                    uploadTimestamp: new Date(document.uploadedAt).getTime(),
                    status: document.verified ? 'verified' : 'pending',
                    documentType: document.documentType as any // Type conversion needed
                  }
                  handleSingleUploadComplete(docUpload)
                }}
                onUploadError={handleUploadError}
              />
            </TabsContent>

            <TabsContent value="bulk" className="mt-6">
              <BulkDocumentUpload
                userProfile={userProfile}
                onUploadComplete={handleBulkUploadComplete}
                onUploadError={handleUploadError}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Processing Features */}
      <Card>
        <CardHeader>
          <CardTitle>AI Processing Features</CardTitle>
          <CardDescription>
            Advanced document processing capabilities powered by locally-hosted ML models
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Document Preprocessing
              </h4>
              <ul className="text-sm text-muted-foreground space-y-2">
                <li>• Optical Character Recognition (OCR)</li>
                <li>• Image quality enhancement</li>
                <li>• Text extraction and parsing</li>
                <li>• Document structure analysis</li>
                <li>• Metadata extraction</li>
              </ul>
            </div>

            <div className="space-y-4">
              <h4 className="font-semibold flex items-center gap-2">
                <Shield className="h-4 w-4" />
                ML Verification
              </h4>
              <ul className="text-sm text-muted-foreground space-y-2">
                <li>• Document authenticity verification</li>
                <li>• Fraud detection and analysis</li>
                <li>• Data consistency validation</li>
                <li>• Security feature detection</li>
                <li>• Risk assessment scoring</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security & Privacy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-2">Data Protection</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• End-to-end encryption during upload</li>
                <li>• Secure file storage with access controls</li>
                <li>• Automated malware scanning</li>
                <li>• GDPR-compliant data handling</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Processing Security</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Locally-hosted ML models (no cloud processing)</li>
                <li>• Sandboxed document processing environment</li>
                <li>• Audit logging for all operations</li>
                <li>• Zero-trust security architecture</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}