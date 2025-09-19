/**
 * Notification Center Component
 * Real-time notification display and management
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { ScrollArea } from '../ui/scroll-area'
import { Separator } from '../ui/separator'
import { Switch } from '../ui/switch'
import { Label } from '../ui/label'
import { 
  Bell, 
  BellRinging, 
  Check, 
  CheckCircle, 
  Warning, 
  Clock, 
  Shield,
  X,
  Gear
} from '@phosphor-icons/react'
import { useNotifications, NotificationData } from '../../services/notifications'
import { UserProfile } from '../../types/profiles'

interface NotificationCenterProps {
  userProfile: UserProfile
}

export function NotificationCenter({ userProfile }: NotificationCenterProps) {
  const [filter, setFilter] = useState<'all' | 'unread' | 'verification' | 'security'>('all')

  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications(userProfile.id)

  const getNotificationIcon = (notification: NotificationData) => {
    switch (notification.type) {
      case 'verification_approved':
        return <CheckCircle className="text-success" size={20} />
      case 'verification_rejected':
        return <X className="text-destructive" size={20} />
      case 'verification_started':
      case 'verification_requires_action':
        return <Clock className="text-accent" size={20} />
      case 'security_alert':
        return <Shield className="text-destructive" size={20} />
      case 'document_uploaded':
      case 'document_processed':
        return <Check className="text-muted-foreground" size={20} />
      default:
        return <Bell className="text-muted-foreground" size={20} />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'destructive'
      case 'high':
        return 'default'
      case 'medium':
        return 'secondary'
      case 'low':
        return 'outline'
      default:
        return 'secondary'
    }
  }

  const filteredNotifications = (notifications || []).filter(notification => {
    switch (filter) {
      case 'unread':
        return !notification.read
      case 'verification':
        return notification.category === 'verification'
      case 'security':
        return notification.category === 'security'
      default:
        return true
    }
  })

  const handleUpdatePreferences = async (updates: any) => {
    // Simplified - no preferences management for now
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <BellRinging size={24} className="text-primary" />
            {(unreadCount || 0) > 0 && (
              <Badge className="absolute -top-2 -right-2 h-5 w-5 rounded-full text-xs flex items-center justify-center">
                {(unreadCount || 0) > 99 ? '99+' : (unreadCount || 0)}
              </Badge>
            )}
          </div>
          <div>
            <h1 className="text-2xl font-bold">Notifications</h1>
            <p className="text-muted-foreground">
              {(unreadCount || 0) === 0 
                ? 'You\'re all caught up!' 
                : `${unreadCount || 0} unread notification${(unreadCount || 0) !== 1 ? 's' : ''}`
              }
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {(unreadCount || 0) > 0 && (
            <Button variant="outline" onClick={markAllAsRead}>
              Mark All Read
            </Button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {[
          { key: 'all', label: 'All' },
          { key: 'unread', label: 'Unread' },
          { key: 'verification', label: 'Verification' },
          { key: 'security', label: 'Security' }
        ].map(({ key, label }) => (
          <Button
            key={key}
            variant={filter === key ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setFilter(key as any)}
          >
            {label}
            {key === 'unread' && (unreadCount || 0) > 0 && (
              <Badge variant="secondary" className="ml-2 h-4 w-4 rounded-full text-xs">
                {unreadCount || 0}
              </Badge>
            )}
          </Button>
        ))}
      </div>

      {/* Notifications List */}
      <Card>
        <CardContent className="p-0">
          {filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Bell size={48} className="text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No notifications</h3>
              <p className="text-muted-foreground">
                {filter === 'all' 
                  ? 'You don\'t have any notifications yet.'
                  : `No ${filter} notifications found.`
                }
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="divide-y">
                {filteredNotifications.map((notification, index) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-muted/50 transition-colors cursor-pointer ${
                      !notification.read ? 'bg-primary/5 border-l-4 border-l-primary' : ''
                    }`}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-0.5">
                        {getNotificationIcon(notification)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className={`font-medium ${!notification.read ? 'text-foreground' : 'text-muted-foreground'}`}>
                                {notification.title}
                              </h4>
                              <Badge variant={getPriorityColor(notification.priority) as any} className="text-xs">
                                {notification.priority}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">
                              {notification.message}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span>{new Date(notification.timestamp).toLocaleString()}</span>
                              <Badge variant="outline" className="text-xs">
                                {notification.category}
                              </Badge>
                            </div>
                          </div>
                          
                          {!notification.read && (
                            <div className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-2" />
                          )}
                        </div>
                        
                        {notification.actionUrl && (
                          <div className="mt-3">
                            <Button variant="outline" size="sm">
                              View Details
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  )
}