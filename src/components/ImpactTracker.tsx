import { VolunteerEvent } from '../App'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { ChartBar, Users, Clock, Calendar, TrendUp } from '@phosphor-icons/react'

interface ImpactTrackerProps {
  events: VolunteerEvent[]
  registrations: {[eventId: string]: boolean}
}

export function ImpactTracker({ events, registrations }: ImpactTrackerProps) {
  const totalEvents = events.length
  const totalVolunteersRegistered = events.reduce((sum, event) => sum + event.volunteersRegistered, 0)
  const myRegistrations = Object.keys(registrations).length
  const estimatedHoursPerEvent = 4
  const totalImpactHours = totalVolunteersRegistered * estimatedHoursPerEvent

  const categoryBreakdown = events.reduce((acc, event) => {
    acc[event.category] = (acc[event.category] || 0) + event.volunteersRegistered
    return acc
  }, {} as Record<string, number>)

  const topCategories = Object.entries(categoryBreakdown)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)

  const completionRate = totalEvents > 0 ? (events.filter(e => e.volunteersRegistered >= e.volunteersNeeded).length / totalEvents) * 100 : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Community Impact</h1>
        <p className="text-muted-foreground mt-2">Track the positive impact we're making together</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{totalEvents}</div>
            <p className="text-xs text-muted-foreground">
              Active volunteer opportunities
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Volunteers Engaged</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-accent">{totalVolunteersRegistered}</div>
            <p className="text-xs text-muted-foreground">
              Community members participating
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Impact Hours</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">{totalImpactHours}</div>
            <p className="text-xs text-muted-foreground">
              Estimated volunteer hours
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">My Participation</CardTitle>
            <TrendUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{myRegistrations}</div>
            <p className="text-xs text-muted-foreground">
              Events I'm registered for
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChartBar size={20} />
              Event Completion Rate
            </CardTitle>
            <CardDescription>
              How well we're filling volunteer positions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Events with full volunteer capacity</span>
                <span>{completionRate.toFixed(0)}%</span>
              </div>
              <Progress value={completionRate} className="h-2" />
            </div>
            <div className="text-sm text-muted-foreground">
              {events.filter(e => e.volunteersRegistered >= e.volunteersNeeded).length} of {totalEvents} events fully staffed
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users size={20} />
              Popular Categories
            </CardTitle>
            <CardDescription>
              Where volunteers are most active
            </CardDescription>
          </CardHeader>
          <CardContent>
            {topCategories.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data available yet</p>
            ) : (
              <div className="space-y-3">
                {topCategories.map(([category, count]) => (
                  <div key={category} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{category}</Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{count}</span>
                      <span className="text-xs text-muted-foreground">volunteers</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {totalEvents > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest volunteer opportunities and engagement</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {events.slice(0, 5).map(event => (
                <div key={event.id} className="flex items-center justify-between border-b pb-3 last:border-b-0">
                  <div className="space-y-1">
                    <p className="font-medium">{event.title}</p>
                    <p className="text-sm text-muted-foreground">{event.organization}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {event.volunteersRegistered}/{event.volunteersNeeded} volunteers
                    </p>
                    <Badge variant={event.volunteersRegistered >= event.volunteersNeeded ? "default" : "secondary"}>
                      {event.volunteersRegistered >= event.volunteersNeeded ? "Full" : "Open"}
                    </Badge>
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