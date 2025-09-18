import { useState } from 'react'
import { VolunteerEvent } from '../App'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Badge } from './ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { Plus, Building, Calendar, Users } from '@phosphor-icons/react'

interface OrganizationDashboardProps {
  events: VolunteerEvent[]
  onAddEvent: (event: VolunteerEvent) => void
  onUpdateEvent: (event: VolunteerEvent) => void
}

const EVENT_CATEGORIES = [
  'Environment', 'Education', 'Health', 'Community', 'Animals',
  'Food & Nutrition', 'Youth', 'Seniors', 'Arts & Culture'
]

const SKILL_OPTIONS = [
  'Event Planning', 'Teaching', 'Construction', 'Gardening', 'Cooking',
  'Childcare', 'Elder Care', 'Animal Care', 'Technology', 'Transportation',
  'Administration', 'Fundraising', 'Marketing', 'Photography', 'Music'
]

export function OrganizationDashboard({ events, onAddEvent, onUpdateEvent }: OrganizationDashboardProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newEvent, setNewEvent] = useState({
    title: '',
    organization: 'Community Organization',
    description: '',
    date: '',
    time: '',
    location: '',
    volunteersNeeded: 1,
    category: '',
    skills: [] as string[]
  })

  const handleCreateEvent = () => {
    if (!newEvent.title || !newEvent.date || !newEvent.time || !newEvent.location) return

    const event: VolunteerEvent = {
      id: Date.now().toString(),
      ...newEvent,
      volunteersRegistered: 0,
      verified: true
    }

    onAddEvent(event)
    setShowCreateDialog(false)
    setNewEvent({
      title: '',
      organization: 'Community Organization',
      description: '',
      date: '',
      time: '',
      location: '',
      volunteersNeeded: 1,
      category: '',
      skills: []
    })
  }

  const handleSkillToggle = (skill: string) => {
    setNewEvent(current => ({
      ...current,
      skills: current.skills.includes(skill)
        ? current.skills.filter(s => s !== skill)
        : [...current.skills, skill]
    }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Organization Dashboard</h1>
          <p className="text-muted-foreground mt-2">Manage your volunteer events and coordination</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <Plus size={16} />
              Create Event
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Volunteer Event</DialogTitle>
              <DialogDescription>
                Set up a new volunteer opportunity for your community
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="event-title">Event Title</Label>
                  <Input
                    id="event-title"
                    value={newEvent.title}
                    onChange={(e) => setNewEvent(current => ({...current, title: e.target.value}))}
                    placeholder="Community Garden Cleanup"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="event-category">Category</Label>
                  <Select value={newEvent.category} onValueChange={(value) => 
                    setNewEvent(current => ({...current, category: value}))
                  }>
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {EVENT_CATEGORIES.map(category => (
                        <SelectItem key={category} value={category}>{category}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="event-description">Description</Label>
                <Textarea
                  id="event-description"
                  value={newEvent.description}
                  onChange={(e) => setNewEvent(current => ({...current, description: e.target.value}))}
                  placeholder="Describe what volunteers will be doing..."
                />
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="event-date">Date</Label>
                  <Input
                    id="event-date"
                    type="date"
                    value={newEvent.date}
                    onChange={(e) => setNewEvent(current => ({...current, date: e.target.value}))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="event-time">Time</Label>
                  <Input
                    id="event-time"
                    type="time"
                    value={newEvent.time}
                    onChange={(e) => setNewEvent(current => ({...current, time: e.target.value}))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="volunteers-needed">Volunteers Needed</Label>
                  <Input
                    id="volunteers-needed"
                    type="number"
                    min="1"
                    value={newEvent.volunteersNeeded}
                    onChange={(e) => setNewEvent(current => ({...current, volunteersNeeded: parseInt(e.target.value) || 1}))}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="event-location">Location</Label>
                <Input
                  id="event-location"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent(current => ({...current, location: e.target.value}))}
                  placeholder="123 Community St, Your City"
                />
              </div>

              <div className="space-y-3">
                <Label>Skills Needed (Optional)</Label>
                <div className="grid grid-cols-3 gap-2">
                  {SKILL_OPTIONS.map(skill => (
                    <Button
                      key={skill}
                      type="button"
                      variant={newEvent.skills.includes(skill) ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleSkillToggle(skill)}
                      className="text-xs h-8"
                    >
                      {skill}
                    </Button>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-4">
                <Button onClick={handleCreateEvent} className="flex-1">
                  Create Event
                </Button>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {events.length === 0 ? (
          <Card className="md:col-span-2 lg:col-span-3">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Building size={48} className="text-muted-foreground mb-4" />
              <CardTitle className="mb-2">No Events Created</CardTitle>
              <CardDescription className="text-center max-w-md">
                Create your first volunteer event to start connecting with community volunteers.
              </CardDescription>
            </CardContent>
          </Card>
        ) : (
          events.map(event => (
            <Card key={event.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg">{event.title}</CardTitle>
                  <Badge variant="outline">{event.category}</Badge>
                </div>
                <CardDescription className="flex items-center gap-2">
                  <Calendar size={14} />
                  {event.date} at {event.time}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {event.description}
                </p>
                
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-1">
                    <Users size={14} />
                    {event.volunteersRegistered}/{event.volunteersNeeded}
                  </span>
                  <Badge variant={event.volunteersRegistered >= event.volunteersNeeded ? "default" : "secondary"}>
                    {event.volunteersRegistered >= event.volunteersNeeded ? "Full" : "Open"}
                  </Badge>
                </div>

                {event.skills.length > 0 && (
                  <div>
                    <p className="text-xs font-medium mb-1">Skills:</p>
                    <div className="flex flex-wrap gap-1">
                      {event.skills.slice(0, 3).map(skill => (
                        <Badge key={skill} variant="secondary" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {event.skills.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{event.skills.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}