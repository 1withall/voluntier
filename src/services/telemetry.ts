// Comprehensive telemetry and logging system for security and operational monitoring

import { useState, useEffect, useCallback } from 'react'
import { useKV } from '@github/spark/hooks'

export interface TelemetryEvent {
  id: string
  timestamp: string
  userId?: string
  sessionId: string
  eventType: 'user_action' | 'security_event' | 'system_event' | 'error_event' | 'performance_event'
  category: string
  action: string
  label?: string
  value?: number
  metadata: Record<string, any>
  severity: 'info' | 'warning' | 'error' | 'critical'
  source: 'client' | 'server' | 'system'
  environment: 'development' | 'staging' | 'production'
  userAgent?: string
  ipAddress?: string
  location?: {
    country?: string
    region?: string
    city?: string
  }
}

export interface TelemetryAnalytics {
  totalEvents: number
  eventsByType: Record<string, number>
  eventsBySeverity: Record<string, number>
  uniqueUsers: number
  averageSessionDuration: number
  errorRate: number
  securityIncidents: number
  performanceMetrics: {
    averageLoadTime: number
    averageResponseTime: number
    bounceRate: number
  }
}

class TelemetryService {
  private sessionId: string
  private userId?: string
  private telemetryQueue: TelemetryEvent[] = []
  private isOnline: boolean = navigator.onLine
  private batchSize: number = 50
  private flushInterval: number = 30000 // 30 seconds

  constructor() {
    this.sessionId = this.generateSessionId()
    this.initializeService()
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private initializeService() {
    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true
      this.flushTelemetry()
    })
    
    window.addEventListener('offline', () => {
      this.isOnline = false
    })

    // Set up periodic flushing
    setInterval(() => {
      this.flushTelemetry()
    }, this.flushInterval)

    // Flush on page unload
    window.addEventListener('beforeunload', () => {
      this.flushTelemetry()
    })

    // Track performance metrics
    if ('performance' in window) {
      window.addEventListener('load', () => {
        setTimeout(() => {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
          this.trackEvent({
            eventType: 'performance_event',
            category: 'page_load',
            action: 'load_complete',
            value: navigation.loadEventEnd - navigation.loadEventStart,
            metadata: {
              domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
              firstContentfulPaint: this.getFirstContentfulPaint(),
              networkType: (navigator as any).connection?.effectiveType
            },
            severity: 'info'
          })
        }, 0)
      })
    }

    // Track unhandled errors
    window.addEventListener('error', (event) => {
      this.trackEvent({
        eventType: 'error_event',
        category: 'javascript_error',
        action: 'unhandled_error',
        label: event.message,
        metadata: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          stack: event.error?.stack
        },
        severity: 'error'
      })
    })

    // Track unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.trackEvent({
        eventType: 'error_event',
        category: 'promise_rejection',
        action: 'unhandled_rejection',
        label: event.reason?.toString(),
        metadata: {
          reason: event.reason,
          stack: event.reason?.stack
        },
        severity: 'error'
      })
    })
  }

  private getFirstContentfulPaint(): number | undefined {
    try {
      const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0]
      return fcpEntry?.startTime
    } catch {
      return undefined
    }
  }

  setUserId(userId: string) {
    this.userId = userId
    this.trackEvent({
      eventType: 'user_action',
      category: 'authentication',
      action: 'user_identified',
      metadata: { userId },
      severity: 'info'
    })
  }

  trackEvent(eventData: Partial<TelemetryEvent>) {
    const event: TelemetryEvent = {
      id: `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      userId: this.userId,
      sessionId: this.sessionId,
      eventType: eventData.eventType || 'user_action',
      category: eventData.category || 'unknown',
      action: eventData.action || 'unknown',
      label: eventData.label,
      value: eventData.value,
      metadata: eventData.metadata || {},
      severity: eventData.severity || 'info',
      source: 'client',
      environment: process.env.NODE_ENV === 'production' ? 'production' : 'development',
      userAgent: navigator.userAgent,
      ipAddress: undefined, // Would be set by server
      location: undefined, // Would be set by server
      ...eventData
    }

    this.telemetryQueue.push(event)

    // Immediate flush for critical events
    if (event.severity === 'critical' || event.eventType === 'security_event') {
      this.flushTelemetry()
    }

    // Flush when batch size is reached
    if (this.telemetryQueue.length >= this.batchSize) {
      this.flushTelemetry()
    }
  }

  trackSecurityEvent(eventData: {
    action: string
    description: string
    metadata?: Record<string, any>
    severity?: 'info' | 'warning' | 'error' | 'critical'
  }) {
    this.trackEvent({
      eventType: 'security_event',
      category: 'security',
      action: eventData.action,
      label: eventData.description,
      metadata: {
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        ...eventData.metadata
      },
      severity: eventData.severity || 'warning'
    })
  }

  trackUserAction(action: string, category: string, label?: string, value?: number, metadata?: Record<string, any>) {
    this.trackEvent({
      eventType: 'user_action',
      category,
      action,
      label,
      value,
      metadata,
      severity: 'info'
    })
  }

  trackPageView(page: string, additionalData?: Record<string, any>) {
    this.trackEvent({
      eventType: 'user_action',
      category: 'navigation',
      action: 'page_view',
      label: page,
      metadata: {
        page,
        referrer: document.referrer,
        ...additionalData
      },
      severity: 'info'
    })
  }

  trackFormSubmission(formName: string, success: boolean, errors?: string[]) {
    this.trackEvent({
      eventType: 'user_action',
      category: 'form',
      action: success ? 'form_submit_success' : 'form_submit_error',
      label: formName,
      metadata: {
        formName,
        success,
        errors: errors || []
      },
      severity: success ? 'info' : 'warning'
    })
  }

  private async flushTelemetry() {
    if (this.telemetryQueue.length === 0 || !this.isOnline) {
      return
    }

    const eventsToFlush = [...this.telemetryQueue]
    this.telemetryQueue = []

    try {
      // In a real implementation, this would send to your analytics backend
      console.log('📊 Telemetry Batch:', {
        batchSize: eventsToFlush.length,
        events: eventsToFlush
      })

      // Store locally for demo purposes
      const existingEvents = JSON.parse(localStorage.getItem('voluntier_telemetry') || '[]')
      const allEvents = [...existingEvents, ...eventsToFlush].slice(-1000) // Keep last 1000 events
      localStorage.setItem('voluntier_telemetry', JSON.stringify(allEvents))

    } catch (error) {
      console.error('Failed to flush telemetry:', error)
      // Re-add events to queue for retry
      this.telemetryQueue.unshift(...eventsToFlush)
    }
  }

  getAnalytics(): TelemetryAnalytics {
    try {
      const events: TelemetryEvent[] = JSON.parse(localStorage.getItem('voluntier_telemetry') || '[]')
      
      const totalEvents = events.length
      const eventsByType = events.reduce((acc, event) => {
        acc[event.eventType] = (acc[event.eventType] || 0) + 1
        return acc
      }, {} as Record<string, number>)
      
      const eventsBySeverity = events.reduce((acc, event) => {
        acc[event.severity] = (acc[event.severity] || 0) + 1
        return acc
      }, {} as Record<string, number>)
      
      const uniqueUsers = new Set(events.filter(e => e.userId).map(e => e.userId)).size
      const uniqueSessions = new Set(events.map(e => e.sessionId))
      
      const errorEvents = events.filter(e => e.eventType === 'error_event')
      const errorRate = totalEvents > 0 ? (errorEvents.length / totalEvents) * 100 : 0
      
      const securityEvents = events.filter(e => e.eventType === 'security_event')
      const securityIncidents = securityEvents.filter(e => e.severity === 'error' || e.severity === 'critical').length
      
      const performanceEvents = events.filter(e => e.eventType === 'performance_event')
      const loadTimes = performanceEvents.filter(e => e.action === 'load_complete').map(e => e.value || 0)
      const averageLoadTime = loadTimes.length > 0 ? loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length : 0
      
      return {
        totalEvents,
        eventsByType,
        eventsBySeverity,
        uniqueUsers,
        averageSessionDuration: 0, // Would calculate from session events
        errorRate,
        securityIncidents,
        performanceMetrics: {
          averageLoadTime,
          averageResponseTime: 0, // Would calculate from API events
          bounceRate: 0 // Would calculate from navigation events
        }
      }
    } catch (error) {
      console.error('Failed to get analytics:', error)
      return {
        totalEvents: 0,
        eventsByType: {},
        eventsBySeverity: {},
        uniqueUsers: 0,
        averageSessionDuration: 0,
        errorRate: 0,
        securityIncidents: 0,
        performanceMetrics: {
          averageLoadTime: 0,
          averageResponseTime: 0,
          bounceRate: 0
        }
      }
    }
  }
}

// Global telemetry instance
export const telemetry = new TelemetryService()

// React hook for telemetry
export function useTelemetry() {
  const [analytics, setAnalytics] = useState<TelemetryAnalytics>(telemetry.getAnalytics())

  useEffect(() => {
    const interval = setInterval(() => {
      setAnalytics(telemetry.getAnalytics())
    }, 10000) // Update every 10 seconds

    return () => clearInterval(interval)
  }, [])

  // Use useCallback to prevent function reference changes on each render
  const trackEvent = useCallback((eventData: Partial<TelemetryEvent>) => {
    telemetry.trackEvent(eventData)
  }, [])

  const trackSecurityEvent = useCallback((eventData: {
    action: string
    description: string
    metadata?: Record<string, any>
    severity?: 'info' | 'warning' | 'error' | 'critical'
  }) => {
    telemetry.trackSecurityEvent(eventData)
  }, [])

  const trackUserAction = useCallback((action: string, category: string, label?: string, value?: number, metadata?: Record<string, any>) => {
    telemetry.trackUserAction(action, category, label, value, metadata)
  }, [])

  const trackPageView = useCallback((page: string, additionalData?: Record<string, any>) => {
    telemetry.trackPageView(page, additionalData)
  }, [])

  const trackFormSubmission = useCallback((formName: string, success: boolean, errors?: string[]) => {
    telemetry.trackFormSubmission(formName, success, errors)
  }, [])

  const setUserId = useCallback((userId: string) => {
    telemetry.setUserId(userId)
  }, [])

  return {
    analytics,
    trackEvent,
    trackSecurityEvent,
    trackUserAction,
    trackPageView,
    trackFormSubmission,
    setUserId
  }
}