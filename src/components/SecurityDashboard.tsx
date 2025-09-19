import React, { useState, useEffect } from 'react'
import { useKV } from '@github/spark/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Alert, AlertDescription } from './ui/alert'
import { 
  Shield, 
  Warning, 
  Lock, 
  Eye, 
  TrendUp, 
  Activity,
  Users,
  Lightning,
  Target,
  Brain,
  Globe,
  ChartBar
} from '@phosphor-icons/react'

interface SecurityMetrics {
  threatLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  activeThreats: number
  blockedAttacks: number
  honeypotHits: number
  uniqueAttackers: number
  detectionRate: number
  falsePositiveRate: number
  systemStatus: 'HEALTHY' | 'WARNING' | 'CRITICAL'
  lastUpdated: string
}

interface SecurityEvent {
  id: string
  type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  description: string
  timestamp: string
  sourceIp: string
  status: 'ACTIVE' | 'RESOLVED' | 'INVESTIGATING'
}

interface ThreatIntelligence {
  totalIndicators: number
  activeThreats: number
  newThreatsToday: number
  topThreatTypes: Array<{ type: string; count: number }>
}

export function SecurityDashboard() {
  const [securityMetrics, setSecurityMetrics] = useKV<SecurityMetrics | null>('security-metrics', null)
  const [recentEvents, setRecentEvents] = useKV<SecurityEvent[]>('recent-security-events', [])
  const [threatIntel, setThreatIntel] = useKV<ThreatIntelligence | null>('threat-intelligence', null)
  const [isLoading, setIsLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  // Simulate real-time security data
  useEffect(() => {
    const generateMockMetrics = (): SecurityMetrics => {
      const threatLevels: SecurityMetrics['threatLevel'][] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
      const currentLevel = threatLevels[Math.floor(Math.random() * threatLevels.length)]
      
      return {
        threatLevel: currentLevel,
        activeThreats: Math.floor(Math.random() * 10) + 1,
        blockedAttacks: Math.floor(Math.random() * 50) + 10,
        honeypotHits: Math.floor(Math.random() * 20) + 5,
        uniqueAttackers: Math.floor(Math.random() * 25) + 3,
        detectionRate: Math.random() * 0.3 + 0.7, // 70-100%
        falsePositiveRate: Math.random() * 0.05, // 0-5%
        systemStatus: currentLevel === 'CRITICAL' ? 'CRITICAL' : 
                     currentLevel === 'HIGH' ? 'WARNING' : 'HEALTHY',
        lastUpdated: new Date().toISOString()
      }
    }

    const generateMockEvents = (): SecurityEvent[] => {
      const eventTypes = ['BRUTE_FORCE', 'SQL_INJECTION', 'XSS_ATTEMPT', 'HONEYPOT_HIT', 'ANOMALY_DETECTED']
      const severities: SecurityEvent['severity'][] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
      const statuses: SecurityEvent['status'][] = ['ACTIVE', 'RESOLVED', 'INVESTIGATING']
      
      return Array.from({ length: 5 }, (_, i) => ({
        id: `event-${i + 1}`,
        type: eventTypes[Math.floor(Math.random() * eventTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        description: `Security event detected from suspicious activity`,
        timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        sourceIp: `192.168.1.${Math.floor(Math.random() * 255)}`,
        status: statuses[Math.floor(Math.random() * statuses.length)]
      }))
    }

    const generateMockThreatIntel = (): ThreatIntelligence => {
      const threatTypes = ['Malware', 'Botnet', 'Phishing', 'Scanner', 'APT']
      
      return {
        totalIndicators: Math.floor(Math.random() * 1000) + 500,
        activeThreats: Math.floor(Math.random() * 50) + 10,
        newThreatsToday: Math.floor(Math.random() * 10) + 1,
        topThreatTypes: threatTypes.map(type => ({
          type,
          count: Math.floor(Math.random() * 20) + 1
        })).sort((a, b) => b.count - a.count)
      }
    }

    // Initial load
    setSecurityMetrics(generateMockMetrics())
    setRecentEvents(generateMockEvents())
    setThreatIntel(generateMockThreatIntel())
    setIsLoading(false)

    // Simulate real-time updates
    const interval = setInterval(() => {
      setSecurityMetrics(generateMockMetrics())
      setRecentEvents(generateMockEvents())
      setThreatIntel(generateMockThreatIntel())
      setLastRefresh(new Date())
    }, 10000) // Update every 10 seconds

    return () => clearInterval(interval)
  }, [])

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-green-600 bg-green-50'
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-50'
      case 'HIGH': return 'text-orange-600 bg-orange-50'
      case 'CRITICAL': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'LOW': return <Activity size={16} className="text-green-600" />
      case 'MEDIUM': return <Eye size={16} className="text-yellow-600" />
      case 'HIGH': return <Warning size={16} className="text-orange-600" />
      case 'CRITICAL': return <Lightning size={16} className="text-red-600" />
      default: return <Activity size={16} className="text-gray-600" />
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Shield size={24} className="text-primary" />
          <h1 className="text-3xl font-bold text-foreground">Security Dashboard</h1>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse space-y-2">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-8 bg-muted rounded w-1/2"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={24} className="text-primary" />
          <h1 className="text-3xl font-bold text-foreground">Security Dashboard</h1>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="outline" className="flex items-center gap-1">
            <Activity size={12} />
            Last updated: {lastRefresh.toLocaleTimeString()}
          </Badge>
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
            Refresh
          </Button>
        </div>
      </div>

      {/* System Status Alert */}
      {securityMetrics?.systemStatus === 'CRITICAL' && (
        <Alert className="border-red-200 bg-red-50">
          <Warning className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            Critical security threats detected. Immediate attention required.
          </AlertDescription>
        </Alert>
      )}

      {/* Overview Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Threat Level</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Badge className={getThreatLevelColor(securityMetrics?.threatLevel || 'LOW')}>
              {securityMetrics?.threatLevel}
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">
              Current security threat assessment
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Threats</CardTitle>
            <Warning className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {securityMetrics?.activeThreats || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Threats being monitored
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Blocked Attacks</CardTitle>
            <Lock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {securityMetrics?.blockedAttacks || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Attacks prevented today
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Detection Rate</CardTitle>
            <TrendUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {((securityMetrics?.detectionRate || 0) * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              ML threat detection accuracy
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Security Events */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye size={20} />
              Recent Security Events
            </CardTitle>
            <CardDescription>
              Latest security events and threats detected
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(recentEvents || []).map((event) => (
                <div key={event.id} className="flex items-start justify-between p-3 border rounded-lg">
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(event.severity)}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{event.type.replace('_', ' ')}</span>
                        <Badge variant="outline" className="text-xs">
                          {event.severity}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {event.description}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>IP: {event.sourceIp}</span>
                        <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                  <Badge 
                    variant={event.status === 'RESOLVED' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {event.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Threat Intelligence */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain size={20} />
              Threat Intelligence
            </CardTitle>
            <CardDescription>
              Current threat landscape and intelligence
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-foreground">
                    {threatIntel?.totalIndicators || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">Total Indicators</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {threatIntel?.activeThreats || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">Active Threats</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {threatIntel?.newThreatsToday || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">New Today</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-sm">Top Threat Types</h4>
                {threatIntel?.topThreatTypes.slice(0, 3).map((threat, index) => (
                  <div key={threat.type} className="flex items-center justify-between p-2 bg-muted rounded">
                    <span className="text-sm">{threat.type}</span>
                    <Badge variant="outline">{threat.count}</Badge>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Security Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target size={20} />
              Honeypot Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {securityMetrics?.honeypotHits || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Honeypot interactions detected
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users size={20} />
              Unique Attackers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {securityMetrics?.uniqueAttackers || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Distinct threat actors identified
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChartBar size={20} />
              False Positive Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {((securityMetrics?.falsePositiveRate || 0) * 100).toFixed(2)}%
            </div>
            <p className="text-xs text-muted-foreground">
              Detection accuracy metric
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}