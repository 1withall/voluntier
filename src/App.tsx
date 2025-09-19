import { useState, useEffect } from 'react'
import { useKV } from '@github/spark/hooks'
import { useTelemetry } from './services/telemetry'
import { initializeSampleData } from './data/sampleData'
import { Header } from './components/Header'
import { EventCard } from './components/EventCard'
import { OrganizationDashboard } from './components/OrganizationDashboard'
import { ImpactTracker } from './components/ImpactTracker'
import { SecurityDashboard } from './components/SecurityDashboard'
import { SignupFlow } from './components/SignupFlow'
import { QRVerificationSystem } from './components/QRVerificationSystem'
import { TelemetryDashboard } from './components/TelemetryDashboard'
import { UnifiedProfileView } from './components/profiles/UnifiedProfileView'
import { EnhancedDocumentUpload } from './components/upload/EnhancedDocumentUpload'
import { NotificationCenter } from './components/notifications/NotificationCenter'
import { OnboardingProgressTracker } from './components/onboarding/OnboardingProgressTracker'
import { Button } from './components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Badge } from './components/ui/badge'
import { HandHeart, Users, Calendar, MapPin } from '@phosphor-icons/react'
import { UserProfile } from './types/profiles'

export interface VolunteerEvent {
  id: string
  title: string
  organization: string
  description: string
  date: string
  time: string
  location: string
  volunteersNeeded: number
  volunteersRegistered: number
  skills: string[]
  category: string
  verified: boolean
}

function App() {
  const [userProfile, setUserProfile] = useKV<UserProfile | null>('user-profile', null)
  const [currentView, setCurrentView] = useState<'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry' | 'document-verification' | 'notifications' | 'onboarding'>('events')
  const [events, setEvents] = useKV<VolunteerEvent[]>('volunteer-events', [])
  const [registrations, setRegistrations] = useKV<{[eventId: string]: boolean}>('user-registrations', {})
  
  const { trackUserAction, trackPageView, setUserId } = useTelemetry()

  // Initialize sample data on first load
  useEffect(() => {
    initializeSampleData()
  }, [])

  // Track user identification and page views
  useEffect(() => {
    if (userProfile) {
      setUserId(userProfile.id)
      trackUserAction('user_profile_loaded', 'authentication', userProfile.userType)
    }
  }, [userProfile, setUserId, trackUserAction])

  useEffect(() => {
    trackPageView(currentView)
  }, [currentView, trackPageView])

  const handleRegisterForEvent = (eventId: string) => {
    trackUserAction('event_registration', 'events', `event_${eventId}`)
    
    setRegistrations(current => ({
      ...(current || {}),
      [eventId]: true
    }))
    
    setEvents(currentEvents => 
      (currentEvents || []).map(event => 
        event.id === eventId 
          ? { ...event, volunteersRegistered: event.volunteersRegistered + 1 }
          : event
      )
    )
  }

  const handleUnregisterFromEvent = (eventId: string) => {
    trackUserAction('event_unregistration', 'events', `event_${eventId}`)
    
    setRegistrations(current => {
      const updated = { ...(current || {}) }
      delete updated[eventId]
      return updated
    })
    
    setEvents(currentEvents => 
      (currentEvents || []).map(event => 
        event.id === eventId 
          ? { ...event, volunteersRegistered: Math.max(0, event.volunteersRegistered - 1) }
          : event
      )
    )
  }

  const renderContent = () => {
    if (!userProfile) {
      return <SignupFlow onSignupComplete={setUserProfile} />
    }

    switch (currentView) {
      case 'events':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground">Volunteer Opportunities</h1>
                <p className="text-muted-foreground mt-2">Find meaningful ways to help your community</p>
              </div>
              <div className="flex gap-2">
                <Badge variant="secondary" className="flex items-center gap-1">
                  <HandHeart size={16} />
                  {(events || []).filter(e => registrations?.[e.id]).length} Registered
                </Badge>
              </div>
            </div>

            {(events || []).length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Calendar size={48} className="text-muted-foreground mb-4" />
                  <CardTitle className="mb-2">No Events Yet</CardTitle>
                  <CardDescription className="text-center max-w-md">
                    Events will appear here as organizations post volunteer opportunities. 
                    Check back soon or encourage local organizations to join the platform!
                  </CardDescription>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {(events || []).map(event => (
                  <EventCard
                    key={event.id}
                    event={event}
                    isRegistered={!!(registrations || {})[event.id]}
                    onRegister={() => handleRegisterForEvent(event.id)}
                    onUnregister={() => handleUnregisterFromEvent(event.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )

      case 'profile':
        return (
          <UnifiedProfileView 
            userProfile={userProfile}
            onUpdateProfile={setUserProfile}
          />
        )

      case 'organization':
        return userProfile.userType === 'organization' ? (
          <OrganizationDashboard
            events={events || []}
            onAddEvent={(newEvent) => setEvents(current => [...(current || []), newEvent])}
            onUpdateEvent={(updatedEvent) => setEvents(current => 
              (current || []).map(event => event.id === updatedEvent.id ? updatedEvent : event)
            )}
          />
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Users size={48} className="text-muted-foreground mb-4" />
              <CardTitle className="mb-2">Organization Access Required</CardTitle>
              <CardDescription className="text-center max-w-md mb-4">
                This section is for verified organizations to manage volunteer events and coordination.
              </CardDescription>
              <Button variant="outline">Request Organization Access</Button>
            </CardContent>
          </Card>
        )

      case 'impact':
        return <ImpactTracker events={events || []} registrations={registrations || {}} />

      case 'security':
        return <SecurityDashboard userProfile={userProfile} />

      case 'verification':
        return <QRVerificationSystem userProfile={userProfile} />

      case 'telemetry':
        return <TelemetryDashboard />

      case 'document-verification':
        return (
          <EnhancedDocumentUpload 
            userProfile={userProfile}
            onUploadComplete={(docs) => {
              if (Array.isArray(docs)) {
                docs.forEach(doc => trackUserAction('document_uploaded', 'verification', doc.documentType))
              } else {
                trackUserAction('bulk_upload_completed', 'verification', `${docs.successfulUploads}_files`)
              }
            }}
            onUploadError={(error) => {
              trackUserAction('document_upload_failed', 'verification', error)
            }}
          />
        )

      case 'notifications':
        return <NotificationCenter userProfile={userProfile} />

      case 'onboarding':
        return <OnboardingProgressTracker userProfile={userProfile} />

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header 
        userProfile={userProfile || null}
        currentView={currentView}
        onViewChange={setCurrentView}
      />
      <main className="container mx-auto px-4 py-8">
        {renderContent()}
      </main>
    </div>
  )
}

export default App