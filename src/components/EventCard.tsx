import { VolunteerEvent } from '../App'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Calendar, MapPin, Users, Clock } from '@phosphor-icons/react'

interface EventCardProps {
  event: VolunteerEvent
  isRegistered: boolean
  onRegister: () => void
  onUnregister: () => void
}

export function EventCard({ event, isRegistered, onRegister, onUnregister }: EventCardProps) {
  const spotsRemaining = event.volunteersNeeded - event.volunteersRegistered

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">{event.title}</CardTitle>
            <CardDescription className="flex items-center gap-1">
              <Users size={14} />
              {event.organization}
              {event.verified && (
                <Badge variant="default" className="ml-2">Verified</Badge>
              )}
            </CardDescription>
          </div>
          <Badge variant="outline">{event.category}</Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground line-clamp-3">
          {event.description}
        </p>
        
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar size={14} />
            {event.date} at {event.time}
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin size={14} />
            {event.location}
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock size={14} />
            {event.volunteersRegistered}/{event.volunteersNeeded} volunteers
          </div>
        </div>

        {event.skills.length > 0 && (
          <div>
            <p className="text-xs font-medium mb-2">Skills needed:</p>
            <div className="flex flex-wrap gap-1">
              {event.skills.map(skill => (
                <Badge key={skill} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="pt-2">
          {isRegistered ? (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onUnregister}
              className="w-full"
            >
              Unregister
            </Button>
          ) : (
            <Button 
              size="sm" 
              onClick={onRegister}
              disabled={spotsRemaining <= 0}
              className="w-full"
            >
              {spotsRemaining <= 0 ? 'Event Full' : 'Register'}
            </Button>
          )}
          {spotsRemaining > 0 && spotsRemaining <= 3 && (
            <p className="text-xs text-muted-foreground mt-1 text-center">
              Only {spotsRemaining} spots remaining
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}