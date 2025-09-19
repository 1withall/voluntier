import { useState } from 'react'
import { useKV } from '@github/spark/hooks'
import { Header } from './components/Header'
import { EventCard } from './components/EventCard'
import { ProfileSetup } from './components/ProfileSetup'
import { OrganizationDashboard } from './components/OrganizationDashboard'
import { ImpactTracker } from './components/ImpactTracker'
import { SecurityDashboard } from './components/SecurityDashboard'
import { Button } from './components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Badge } from './components/ui/badge'
import { HandHeart, Users, Calendar, MapPin } from '@phosphor-icons/react'

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

export interface UserProfile {
  id: string
  name: string
  email: string
  skills: string[]
  interests: string[]
  verified: boolean
  hoursLogged: number
  eventsAttended: number
  isOrganization: boolean
}

function App() {
  const [userProfile, setUserProfile] = useKV<UserProfile | null>('user-profile', null)
  const [currentView, setCurrentView] = useState<'events' | 'profile' | 'organization' | 'impact' | 'security'>('events')
  const [events, setEvents] = useKV<VolunteerEvent[]>('volunteer-events', [])
  const [registrations, setRegistrations] = useKV<{[eventId: string]: boolean}>('user-registrations', {})

  const handleRegisterForEvent = (eventId: string) => {
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
      return <ProfileSetup onProfileCreated={setUserProfile} />
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
          <div className="space-y-6">
            <h1 className="text-3xl font-bold text-foreground">My Profile</h1>
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users size={20} />
                    Profile Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="font-medium">{userProfile.name}</p>
                    <p className="text-sm text-muted-foreground">{userProfile.email}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-2">Skills</p>
                    <div className="flex flex-wrap gap-1">
                      {userProfile.skills.map(skill => (
                        <Badge key={skill} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium mb-2">Interests</p>
                    <div className="flex flex-wrap gap-1">
                      {userProfile.interests.map(interest => (
                        <Badge key={interest} variant="outline">{interest}</Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HandHeart size={20} />
                    Volunteer Stats
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>Hours Logged:</span>
                    <span className="font-medium">{userProfile.hoursLogged}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Events Attended:</span>
                    <span className="font-medium">{userProfile.eventsAttended}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Verification Status:</span>
                    <Badge variant={userProfile.verified ? "default" : "secondary"}>
                      {userProfile.verified ? "Verified" : "Pending"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )

      case 'organization':
        return userProfile.isOrganization ? (
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
        return <SecurityDashboard />

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