/**
 * Temporal Workflow Integration Service
 * Provides a unified interface for frontend components to interact with Temporal workflows
 */

import { toast } from 'sonner'

interface WorkflowResponse {
  status: string
  data: any
  message: string
  workflow_id?: string
  timestamp: string
}

interface WorkflowError {
  detail: string
}

class TemporalWorkflowService {
  private baseUrl: string

  constructor(baseUrl: string = '/api/temporal') {
    this.baseUrl = baseUrl
  }

  /**
   * Generic method for making workflow API calls
   */
  private async callWorkflow(endpoint: string, data: any): Promise<WorkflowResponse> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData: WorkflowError = await response.json()
        throw new Error(errorData.detail || 'Workflow execution failed')
      }

      return await response.json()
    } catch (error) {
      console.error(`Workflow call failed for ${endpoint}:`, error)
      throw error
    }
  }

  /**
   * Authentication Workflows
   */
  async authenticateUser(credentials: {
    email: string
    password: string
    ipAddress?: string
    userAgent?: string
    rememberMe?: boolean
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/auth/authenticate', {
      email: credentials.email,
      password: credentials.password,
      ip_address: credentials.ipAddress || 'unknown',
      user_agent: credentials.userAgent || navigator.userAgent,
      remember_me: credentials.rememberMe || false,
      metadata: {
        timestamp: new Date().toISOString(),
      },
    })
  }

  async validateSession(sessionData: {
    sessionToken: string
    ipAddress?: string
    checkPrivileges?: boolean
    requiredPrivilege?: string
    requiredLevel?: string
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/auth/validate-session', {
      session_token: sessionData.sessionToken,
      ip_address: sessionData.ipAddress || 'unknown',
      check_privileges: sessionData.checkPrivileges || false,
      required_privilege: sessionData.requiredPrivilege,
      required_level: sessionData.requiredLevel || 'read',
    })
  }

  async checkUserPrivileges(privilegeData: {
    userId: string
    privilege: string
    level?: string
    resourceId?: string
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/auth/check-privileges', {
      user_id: privilegeData.userId,
      privilege: privilegeData.privilege,
      level: privilegeData.level || 'read',
      resource_id: privilegeData.resourceId,
      context: {
        timestamp: new Date().toISOString(),
      },
    })
  }

  /**
   * Document Processing Workflows
   */
  async uploadDocument(documentData: {
    userId: string
    documentType: string
    filename: string
    mimeType: string
    fileData: ArrayBuffer
    description?: string
  }): Promise<WorkflowResponse> {
    // Convert ArrayBuffer to base64 for JSON transport
    const base64Data = btoa(String.fromCharCode(...new Uint8Array(documentData.fileData)))
    
    return this.callWorkflow('/documents/upload', {
      user_id: documentData.userId,
      document_type: documentData.documentType,
      filename: documentData.filename,
      mime_type: documentData.mimeType,
      file_data: base64Data,
      description: documentData.description,
      metadata: {
        upload_timestamp: new Date().toISOString(),
        file_size: documentData.fileData.byteLength,
      },
    })
  }

  async bulkUploadDocuments(bulkData: {
    userId: string
    documents: Array<{
      documentType: string
      filename: string
      mimeType: string
      fileData: ArrayBuffer
      description?: string
    }>
    processingOptions?: any
  }): Promise<WorkflowResponse> {
    const processedDocuments = bulkData.documents.map((doc, index) => ({
      temp_id: `bulk_${index}_${Date.now()}`,
      user_id: bulkData.userId,
      document_type: doc.documentType,
      filename: doc.filename,
      mime_type: doc.mimeType,
      file_data: btoa(String.fromCharCode(...new Uint8Array(doc.fileData))),
      description: doc.description,
    }))

    return this.callWorkflow('/documents/bulk-upload', {
      user_id: bulkData.userId,
      documents: processedDocuments,
      processing_options: bulkData.processingOptions || {},
    })
  }

  /**
   * User Registration and Management Workflows
   */
  async registerVolunteer(registrationData: {
    profileData: any
    verificationLevel?: string
    source?: string
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/volunteers/register', {
      profile_data: registrationData.profileData,
      verification_level: registrationData.verificationLevel || 'basic',
      source: registrationData.source || 'web',
      metadata: {
        registration_timestamp: new Date().toISOString(),
      },
    })
  }

  /**
   * Event Management Workflows
   */
  async createEvent(eventData: {
    organizerId: string
    eventData: any
    autoPublish?: boolean
    notificationPreferences?: any
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/events/create', {
      organizer_id: eventData.organizerId,
      event_data: eventData.eventData,
      auto_publish: eventData.autoPublish || false,
      notification_preferences: eventData.notificationPreferences || {},
      metadata: {
        creation_timestamp: new Date().toISOString(),
      },
    })
  }

  /**
   * Notification Workflows
   */
  async sendNotification(notificationData: {
    userId: string
    type: string
    content: any
    deliveryMethod?: string
    priority?: string
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/notifications/send', {
      user_id: notificationData.userId,
      type: notificationData.type,
      content: notificationData.content,
      delivery_method: notificationData.deliveryMethod || 'email',
      priority: notificationData.priority || 'normal',
      metadata: {
        triggered_at: new Date().toISOString(),
      },
    })
  }

  /**
   * Telemetry Workflows
   */
  async trackTelemetryEvent(telemetryData: {
    userId?: string
    eventType: string
    category: string
    label?: string
    value?: number
    metadata?: any
  }): Promise<WorkflowResponse> {
    return this.callWorkflow('/telemetry/track', {
      user_id: telemetryData.userId,
      event_type: telemetryData.eventType,
      category: telemetryData.category,
      label: telemetryData.label,
      value: telemetryData.value,
      metadata: telemetryData.metadata || {},
      timestamp: new Date().toISOString(),
    })
  }

  /**
   * Workflow Status and Monitoring
   */
  async getWorkflowStatus(workflowId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/status/${workflowId}`)
      if (!response.ok) {
        throw new Error('Failed to get workflow status')
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to get workflow status:', error)
      throw error
    }
  }

  async listWorkflows(limit: number = 10): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/workflows/list?limit=${limit}`)
      if (!response.ok) {
        throw new Error('Failed to list workflows')
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to list workflows:', error)
      throw error
    }
  }

  /**
   * Convenience methods with error handling and notifications
   */
  async authenticateUserWithToast(credentials: {
    email: string
    password: string
    ipAddress?: string
    userAgent?: string
    rememberMe?: boolean
  }): Promise<WorkflowResponse | null> {
    try {
      const result = await this.authenticateUser(credentials)
      
      if (result.status === 'success' && result.data.authenticated) {
        toast.success('Authentication successful')
        return result
      } else {
        toast.error(result.data.reason || 'Authentication failed')
        return null
      }
    } catch (error) {
      toast.error(`Authentication failed: ${error.message}`)
      return null
    }
  }

  async uploadDocumentWithToast(documentData: {
    userId: string
    documentType: string
    filename: string
    mimeType: string
    fileData: ArrayBuffer
    description?: string
  }): Promise<WorkflowResponse | null> {
    try {
      toast.info('Starting document upload and processing...')
      
      const result = await this.uploadDocument(documentData)
      
      if (result.status === 'success' && result.data.success) {
        toast.success(`Document uploaded and processed successfully`)
        
        if (result.data.requires_human_review) {
          toast.info('Document requires human review - you will be notified when complete')
        }
        
        return result
      } else {
        const reason = result.data.reason || 'Unknown error'
        toast.error(`Document processing failed: ${reason}`)
        return null
      }
    } catch (error) {
      toast.error(`Document upload failed: ${error.message}`)
      return null
    }
  }

  async bulkUploadWithProgress(bulkData: {
    userId: string
    documents: Array<{
      documentType: string
      filename: string
      mimeType: string
      fileData: ArrayBuffer
      description?: string
    }>
    onProgress?: (completed: number, total: number) => void
    processingOptions?: any
  }): Promise<WorkflowResponse | null> {
    try {
      toast.info(`Starting bulk upload of ${bulkData.documents.length} documents...`)
      
      const result = await this.bulkUploadDocuments(bulkData)
      
      if (result.status === 'success' && result.data.success) {
        const { successful, failed, total_documents } = result.data
        
        if (failed === 0) {
          toast.success(`All ${total_documents} documents processed successfully`)
        } else {
          toast.warning(`${successful} documents processed successfully, ${failed} failed`)
        }
        
        return result
      } else {
        toast.error('Bulk upload failed')
        return null
      }
    } catch (error) {
      toast.error(`Bulk upload failed: ${error.message}`)
      return null
    }
  }

  async createEventWithToast(eventData: {
    organizerId: string
    eventData: any
    autoPublish?: boolean
    notificationPreferences?: any
  }): Promise<WorkflowResponse | null> {
    try {
      toast.info('Creating event...')
      
      const result = await this.createEvent(eventData)
      
      if (result.status === 'success' && result.data.status === 'success') {
        toast.success('Event created successfully')
        
        if (result.data.matches_found > 0) {
          toast.info(`Found ${result.data.matches_found} potential volunteer matches`)
        }
        
        return result
      } else {
        toast.error('Event creation failed')
        return null
      }
    } catch (error) {
      toast.error(`Event creation failed: ${error.message}`)
      return null
    }
  }

  /**
   * Silent telemetry tracking (no user feedback)
   */
  async trackEvent(eventType: string, category: string, label?: string, userId?: string): Promise<void> {
    try {
      await this.trackTelemetryEvent({
        userId,
        eventType,
        category,
        label,
        metadata: {
          url: window.location.href,
          timestamp: new Date().toISOString(),
        },
      })
    } catch (error) {
      // Silent failure for telemetry
      console.warn('Telemetry tracking failed:', error)
    }
  }
}

// Export singleton instance
export const temporalWorkflowService = new TemporalWorkflowService()

// Export the class for custom instances
export { TemporalWorkflowService }

// Export types
export type { WorkflowResponse, WorkflowError }