/**
 * Real-time Notification Service
 * Provides real-time notifications for verification status updates
 * - WebSocket-based real-time communication
 * - Push notification support
 * - In-app notification system
 * - Email notification fallback
 */

import { useKV } from '@github/spark/hooks'
import { useState, useEffect, useCallback } from 'react'

export interface NotificationData {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: string
  read: boolean
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: 'verification' | 'security' | 'system' | 'event'
  metadata?: Record<string, any>
  actionUrl?: string
  expiresAt?: string
}

export type NotificationType = 
  | 'verification_started'
  | 'verification_completed'
  | 'verification_approved'
  | 'verification_rejected'
  | 'verification_requires_action'
  | 'document_uploaded'
  | 'document_processed'
  | 'security_alert'
  | 'account_verified'
  | 'system_maintenance'

export interface VerificationStatusUpdate {
  documentId: string
  userId: string
  status: 'pending' | 'in_progress' | 'verified' | 'rejected'
  previousStatus: string
  notes?: string
  verifiedBy?: string
  timestamp: string
}

export interface NotificationPreferences {
  userId: string
  inApp: boolean
  email: boolean
  push: boolean
  verification: boolean
  security: boolean
  events: boolean
  marketing: boolean
}

export class NotificationService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private listeners: Map<string, Set<(data: any) => void>> = new Map()
  private connectionPromise: Promise<void> | null = null

  /**
   * Initialize WebSocket connection for real-time notifications
   */
  async connect(userId: string): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/notifications/ws?userId=${userId}`
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('Notification service connected')
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('Failed to parse notification message:', error)
          }
        }

        this.ws.onclose = () => {
          console.log('Notification service disconnected')
          this.connectionPromise = null
          this.attemptReconnect(userId)
        }

        this.ws.onerror = (error) => {
          console.error('Notification service error:', error)
          reject(error)
        }

      } catch (error) {
        reject(error)
      }
    })

    return this.connectionPromise
  }

  /**
   * Attempt to reconnect WebSocket
   */
  private async attemptReconnect(userId: string): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('Max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = Math.pow(2, this.reconnectAttempts) * 1000 // Exponential backoff

    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      this.connect(userId)
    }, delay)
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: any): void {
    const { type, payload } = data

    // Emit to specific listeners
    const typeListeners = this.listeners.get(type)
    if (typeListeners) {
      typeListeners.forEach(listener => listener(payload))
    }

    // Emit to general listeners
    const allListeners = this.listeners.get('*')
    if (allListeners) {
      allListeners.forEach(listener => listener(data))
    }

    // Handle verification status updates
    if (type === 'verification_status_update') {
      this.handleVerificationUpdate(payload)
    }

    // Handle security alerts
    if (type === 'security_alert') {
      this.handleSecurityAlert(payload)
    }
  }

  /**
   * Handle verification status updates
   */
  private handleVerificationUpdate(update: VerificationStatusUpdate): void {
    const notification: NotificationData = {
      id: crypto.randomUUID(),
      type: this.getNotificationTypeFromStatus(update.status),
      title: this.getVerificationTitle(update.status),
      message: this.getVerificationMessage(update),
      timestamp: new Date().toISOString(),
      read: false,
      priority: update.status === 'rejected' ? 'high' : 'medium',
      category: 'verification',
      metadata: {
        documentId: update.documentId,
        verificationUpdate: update
      },
      actionUrl: `/verification/document/${update.documentId}`
    }

    this.showInAppNotification(notification)
    this.sendPushNotification(notification)
  }

  /**
   * Handle security alerts
   */
  private handleSecurityAlert(alert: any): void {
    const notification: NotificationData = {
      id: crypto.randomUUID(),
      type: 'security_alert',
      title: 'Security Alert',
      message: alert.message,
      timestamp: new Date().toISOString(),
      read: false,
      priority: 'urgent',
      category: 'security',
      metadata: alert,
      actionUrl: '/security'
    }

    this.showInAppNotification(notification)
    this.sendPushNotification(notification)
  }

  /**
   * Subscribe to notification events
   */
  subscribe(type: string, listener: (data: any) => void): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set())
    }
    
    this.listeners.get(type)!.add(listener)

    // Return unsubscribe function
    return () => {
      const typeListeners = this.listeners.get(type)
      if (typeListeners) {
        typeListeners.delete(listener)
        if (typeListeners.size === 0) {
          this.listeners.delete(type)
        }
      }
    }
  }

  /**
   * Send push notification
   */
  private async sendPushNotification(notification: NotificationData): Promise<void> {
    if (!('Notification' in window)) {
      return // Browser doesn't support notifications
    }

    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: notification.id,
        requireInteraction: notification.priority === 'urgent'
      })
    } else if (Notification.permission === 'default') {
      const permission = await Notification.requestPermission()
      if (permission === 'granted') {
        this.sendPushNotification(notification)
      }
    }
  }

  /**
   * Show in-app notification
   */
  private showInAppNotification(notification: NotificationData): void {
    // Emit to in-app notification listeners
    const listeners = this.listeners.get('in_app_notification')
    if (listeners) {
      listeners.forEach(listener => listener(notification))
    }
  }

  /**
   * Get notification type from verification status
   */
  private getNotificationTypeFromStatus(status: string): NotificationType {
    switch (status) {
      case 'pending':
        return 'verification_started'
      case 'in_progress':
        return 'verification_started'
      case 'verified':
        return 'verification_approved'
      case 'rejected':
        return 'verification_rejected'
      default:
        return 'verification_started'
    }
  }

  /**
   * Get verification notification title
   */
  private getVerificationTitle(status: string): string {
    switch (status) {
      case 'pending':
        return 'Verification Started'
      case 'in_progress':
        return 'Verification In Progress'
      case 'verified':
        return 'Document Verified'
      case 'rejected':
        return 'Verification Failed'
      default:
        return 'Verification Update'
    }
  }

  /**
   * Get verification notification message
   */
  private getVerificationMessage(update: VerificationStatusUpdate): string {
    switch (update.status) {
      case 'pending':
        return 'Your document has been received and is pending verification.'
      case 'in_progress':
        return 'Your document is currently being reviewed by our verification team.'
      case 'verified':
        return 'Your document has been successfully verified.'
      case 'rejected':
        return update.notes || 'Your document could not be verified. Please check the requirements and resubmit.'
      default:
        return 'Your verification status has been updated.'
    }
  }

  /**
   * Send email notification
   */
  async sendEmailNotification(userId: string, notification: NotificationData): Promise<void> {
    try {
      await fetch('/api/notifications/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userId,
          notification
        })
      })
    } catch (error) {
      console.error('Failed to send email notification:', error)
    }
  }

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    try {
      await fetch(`/api/notifications/${notificationId}/read`, {
        method: 'PUT'
      })
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }

  /**
   * Get user notifications
   */
  async getNotifications(userId: string, limit = 50): Promise<NotificationData[]> {
    try {
      const response = await fetch(`/api/notifications/user/${userId}?limit=${limit}`)
      if (!response.ok) {
        throw new Error('Failed to fetch notifications')
      }
      return await response.json()
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
      return []
    }
  }

  /**
   * Update notification preferences
   */
  async updatePreferences(preferences: NotificationPreferences): Promise<void> {
    try {
      await fetch('/api/notifications/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(preferences)
      })
    } catch (error) {
      console.error('Failed to update notification preferences:', error)
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connectionPromise = null
    this.listeners.clear()
  }
}

// React hook for using notification service
export function useNotifications(userId?: string) {
  const [notifications, setNotifications] = useKV<NotificationData[]>(`notifications-${userId}`, [])
  const [unreadCount, setUnreadCount] = useKV<number>(`unread-count-${userId}`, 0)
  const [service] = useState(() => new NotificationService())

  useEffect(() => {
    if (!userId) return

    // Connect to notification service
    service.connect(userId)

    // Subscribe to in-app notifications
    const unsubscribe = service.subscribe('in_app_notification', (notification: NotificationData) => {
      setNotifications(current => [notification, ...(current || [])].slice(0, 100)) // Keep last 100
      setUnreadCount(current => (current || 0) + 1)
    })

    return () => {
      unsubscribe()
      service.disconnect()
    }
  }, [userId, service, setNotifications, setUnreadCount])

  const markAsRead = useCallback(async (notificationId: string) => {
    await service.markAsRead(notificationId)
    setNotifications(current => 
      (current || []).map(n => n.id === notificationId ? { ...n, read: true } : n)
    )
    setUnreadCount(current => Math.max(0, (current || 0) - 1))
  }, [service, setNotifications, setUnreadCount])

  const markAllAsRead = useCallback(async () => {
    const unreadNotifications = (notifications || []).filter(n => !n.read)
    await Promise.all(unreadNotifications.map(n => service.markAsRead(n.id)))
    setNotifications(current => (current || []).map(n => ({ ...n, read: true })))
    setUnreadCount(0)
  }, [notifications, service, setNotifications, setUnreadCount])

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    service
  }
}

// Export singleton instance for non-React usage
export const notificationService = new NotificationService()