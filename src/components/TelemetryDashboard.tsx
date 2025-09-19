import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { useTelemetry } from '../services/telemetry'
import { PrivilegeGuard } from './auth/PrivilegeGuard'
import { 
  Activity, 
  TrendUp, 
  Users, 
  Shield, 
  Clock, 
  Bug, 
  Database,
  Eye,
  ChartBar
} from '@phosphor-icons/react'

export function TelemetryDashboard() {
  return (
    <PrivilegeGuard 
      requiredPrivilege="view_telemetry" 
      requiredLevel="read"
      fallbackMessage="Access to telemetry and analytics requires administrative privileges."
      onSignInClick={() => {
        // This will be handled by the parent component's sign-in dialog
        const event = new CustomEvent('show-admin-signin')
        window.dispatchEvent(event)
      }}
    >
      <TelemetryDashboardContent />
    </PrivilegeGuard>
  )
}

function TelemetryDashboardContent() {
  const { analytics } = useTelemetry()

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  const formatPercentage = (num: number) => {
    return `${num.toFixed(1)}%`
  }

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'security_event': return 'text-red-600 bg-red-50 border-red-200'
      case 'error_event': return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'performance_event': return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'user_action': return 'text-green-600 bg-green-50 border-green-200'
      case 'system_event': return 'text-purple-600 bg-purple-50 border-purple-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive'
      case 'error': return 'destructive'
      case 'warning': return 'secondary'
      case 'info': return 'outline'
      default: return 'outline'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Telemetry & Analytics Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Real-time application monitoring and user analytics
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(analytics.totalEvents)}</div>
            <p className="text-xs text-muted-foreground">
              All telemetry events captured
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.uniqueUsers}</div>
            <p className="text-xs text-muted-foreground">
              Active platform users
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <Bug className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatPercentage(analytics.errorRate)}</div>
            <Progress value={analytics.errorRate} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Application error rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Incidents</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{analytics.securityIncidents}</div>
            <p className="text-xs text-muted-foreground">
              High/critical security events
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="events" className="space-y-4">
        <TabsList>
          <TabsTrigger value="events">Event Types</TabsTrigger>
          <TabsTrigger value="severity">Severity Analysis</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ChartBar size={20} />
                Events by Type
              </CardTitle>
              <CardDescription>
                Distribution of telemetry events by category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analytics.eventsByType).map(([eventType, count]) => {
                  const percentage = analytics.totalEvents > 0 ? (count / analytics.totalEvents) * 100 : 0
                  return (
                    <div key={eventType} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge className={getEventTypeColor(eventType)} variant="outline">
                            {eventType.replace('_', ' ')}
                          </Badge>
                          <span className="text-sm font-medium">{count} events</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {formatPercentage(percentage)}
                        </span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  )
                })}
                
                {Object.keys(analytics.eventsByType).length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Activity size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No events tracked yet. Start using the application to see analytics.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="severity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bug size={20} />
                Events by Severity
              </CardTitle>
              <CardDescription>
                Event severity distribution and error analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(analytics.eventsBySeverity).map(([severity, count]) => {
                  const percentage = analytics.totalEvents > 0 ? (count / analytics.totalEvents) * 100 : 0
                  return (
                    <div key={severity} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant={getSeverityColor(severity)}>
                            {severity.toUpperCase()}
                          </Badge>
                          <span className="text-sm font-medium">{count} events</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {formatPercentage(percentage)}
                        </span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  )
                })}
                
                {Object.keys(analytics.eventsBySeverity).length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Bug size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No severity data available yet.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock size={20} />
                  Load Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Average Load Time</span>
                  <span className="font-medium">
                    {analytics.performanceMetrics.averageLoadTime.toFixed(0)}ms
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Average Response Time</span>
                  <span className="font-medium">
                    {analytics.performanceMetrics.averageResponseTime.toFixed(0)}ms
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Bounce Rate</span>
                  <span className="font-medium">
                    {formatPercentage(analytics.performanceMetrics.bounceRate)}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendUp size={20} />
                  User Engagement
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Average Session</span>
                  <span className="font-medium">
                    {(analytics.averageSessionDuration / 60).toFixed(1)}min
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Total Users</span>
                  <span className="font-medium">{analytics.uniqueUsers}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Events per User</span>
                  <span className="font-medium">
                    {analytics.uniqueUsers > 0 
                      ? (analytics.totalEvents / analytics.uniqueUsers).toFixed(1)
                      : '0'
                    }
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye size={20} />
                  Health Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className={`p-3 rounded-lg ${analytics.errorRate < 1 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="flex items-center gap-2">
                    {analytics.errorRate < 1 ? (
                      <Badge className="text-green-600 bg-green-100 border-green-200">Healthy</Badge>
                    ) : (
                      <Badge variant="destructive">Needs Attention</Badge>
                    )}
                    <span className="text-sm font-medium">Application Health</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {analytics.errorRate < 1 
                      ? 'Error rate is within acceptable limits'
                      : 'Error rate is elevated and requires investigation'
                    }
                  </p>
                </div>

                <div className={`p-3 rounded-lg ${analytics.securityIncidents === 0 ? 'bg-green-50 border border-green-200' : 'bg-orange-50 border border-orange-200'}`}>
                  <div className="flex items-center gap-2">
                    {analytics.securityIncidents === 0 ? (
                      <Badge className="text-green-600 bg-green-100 border-green-200">Secure</Badge>
                    ) : (
                      <Badge className="text-orange-600 bg-orange-100 border-orange-200">Monitor</Badge>
                    )}
                    <span className="text-sm font-medium">Security Status</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {analytics.securityIncidents === 0
                      ? 'No security incidents detected'
                      : `${analytics.securityIncidents} security incidents require review`
                    }
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                  <div className="flex items-center gap-2">
                    <Badge className="text-blue-600 bg-blue-100 border-blue-200">Performance</Badge>
                    <span className="text-sm font-medium">Load Performance</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {analytics.performanceMetrics.averageLoadTime < 2000
                      ? 'Application is loading quickly'
                      : 'Consider optimizing load performance'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database size={20} />
                  Data Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center py-4">
                  <div className="text-3xl font-bold text-primary">{formatNumber(analytics.totalEvents)}</div>
                  <p className="text-sm text-muted-foreground">Total Events Collected</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-xl font-semibold">{analytics.uniqueUsers}</div>
                    <p className="text-xs text-muted-foreground">Users</p>
                  </div>
                  <div>
                    <div className="text-xl font-semibold">
                      {Object.keys(analytics.eventsByType).length}
                    </div>
                    <p className="text-xs text-muted-foreground">Event Types</p>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="text-xs text-muted-foreground text-center">
                    Real-time telemetry collection active
                    <br />
                    Data retention: 1000 events
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}