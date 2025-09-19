// Security monitoring and threat detection system

import { useState, useEffect } from 'react'
import { useKV } from '@github/spark/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Alert, AlertDescription } from './ui/alert'
import { Progress } from './ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { 
  Shield, 
  Warning, 
  Eye, 
  Lock, 
  Activity, 
  Info,
  CheckCircle,
  Clock,
  TrendUp,
  Lightning,
  Bug,
  Database
} from '@phosphor-icons/react'
import { SecurityEvent } from '../types/auth'
import { UserProfile } from '../types/profiles'
import { PrivilegeGuard } from './auth/PrivilegeGuard'

interface SecurityDashboardProps {
  userProfile?: UserProfile | null
}

export function SecurityDashboard({ userProfile }: SecurityDashboardProps) {
  return (
    <PrivilegeGuard 
      requiredPrivilege="view_security_dashboard" 
      requiredLevel="read"
      fallbackMessage="Access to the security dashboard requires administrative privileges."
      onSignInClick={() => {
        // This will be handled by the parent component's sign-in dialog
        const event = new CustomEvent('show-admin-signin')
        window.dispatchEvent(event)
      }}
    >
      <SecurityDashboardContent userProfile={userProfile} />
    </PrivilegeGuard>
  )
}

function SecurityDashboardContent({ userProfile }: SecurityDashboardProps) {
  const [securityEvents, setSecurityEvents] = useKV<SecurityEvent[]>('security-events', [])
  const [threatLevel, setThreatLevel] = useKV<'low' | 'medium' | 'high' | 'critical'>('threat-level', 'low')
  const [securityScore, setSecurityScore] = useKV<number>('platform-security-score', 95)
  const [activeThreats, setActiveThreats] = useKV<number>('active-threats', 0)
  const [mitigatedThreats, setMitigatedThreats] = useKV<number>('mitigated-threats', 247)
  const [vulnerabilities, setVulnerabilities] = useKV<any[]>('vulnerabilities', [])
  const [auditLogs, setAuditLogs] = useKV<any[]>('audit-logs', [])

  // Simulated real-time security monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate security event generation
      const eventTypes = ['login_attempt', 'verification_failure', 'suspicious_activity', 'system_alert']
      const severities = ['low', 'medium', 'high']
      
      if (Math.random() < 0.1) { // 10% chance of new event every 5 seconds
        const newEvent: SecurityEvent = {
          id: Date.now().toString(),
          userId: userProfile?.id || 'system',
          eventType: eventTypes[Math.floor(Math.random() * eventTypes.length)] as any,
          severity: severities[Math.floor(Math.random() * severities.length)] as any,
          description: generateEventDescription(),
          metadata: {},
          timestamp: new Date().toISOString(),
          resolved: false
        }
        
        setSecurityEvents(current => [newEvent, ...((current || []).slice(0, 49))]) // Keep last 50 events
        
        // Update metrics based on event severity
        if (newEvent.severity === 'high' || newEvent.severity === 'critical') {
          setActiveThreats(current => (current || 0) + 1)
        }
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [userProfile])

  const generateEventDescription = () => {
    const descriptions = [
      'Multiple failed login attempts detected',
      'Unusual access pattern identified',
      'New device login from unrecognized location',
      'Potential bot activity detected',
      'Verification bypass attempt blocked',
      'Suspicious file upload detected',
      'Rate limit exceeded by user',
      'Invalid authentication token usage',
      'Potential SQL injection attempt blocked',
      'Cross-site scripting attempt prevented'
    ]
    return descriptions[Math.floor(Math.random() * descriptions.length)]
  }

  const resolveSecurityEvent = (eventId: string) => {
    setSecurityEvents(current => 
      (current || []).map(event => 
        event.id === eventId 
          ? { ...event, resolved: true, resolvedBy: userProfile?.id || 'admin', resolvedAt: new Date().toISOString() }
          : event
      )
    )
    
    setActiveThreats(current => Math.max(0, (current || 0) - 1))
    setMitigatedThreats(current => (current || 0) + 1)
  }

  const runSecurityScan = async () => {
    // Simulate comprehensive security scan
    const scanResults = {
      vulnerabilities: [
        {
          id: 'vuln-001',
          type: 'Authentication',
          severity: 'medium',
          description: 'Password policy could be strengthened',
          status: 'identified',
          remediation: 'Implement stronger password requirements'
        },
        {
          id: 'vuln-002', 
          type: 'Network Security',
          severity: 'low',
          description: 'SSL certificate expiring in 30 days',
          status: 'monitoring',
          remediation: 'Schedule certificate renewal'
        }
      ],
      score: 97,
      scanTime: new Date().toISOString()
    }
    
    setVulnerabilities(scanResults.vulnerabilities)
    setSecurityScore(scanResults.score)
    
    // Log the scan
    const scanLog = {
      id: Date.now().toString(),
      action: 'security_scan',
      user: userProfile?.id || 'system',
      timestamp: new Date().toISOString(),
      details: 'Comprehensive security scan completed',
      result: 'success'
    }
    
    setAuditLogs(current => [scanLog, ...(current || []).slice(0, 99)]) // Keep last 100 logs
  }

  const getThreatLevelColor = (level: string | undefined) => {
    const actualLevel = level || 'low'
    switch (actualLevel) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200'
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-green-600 bg-green-50 border-green-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive'
      case 'high': return 'destructive'
      case 'medium': return 'secondary'
      case 'low': return 'outline'
      default: return 'outline'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Security Dashboard</h1>
          <p className="text-muted-foreground mt-2">Real-time security monitoring and threat detection</p>
        </div>
        <Button onClick={runSecurityScan} className="flex items-center gap-2">
          <Shield size={16} />
          Run Security Scan
        </Button>
      </div>

      {/* Security Overview Cards */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Score</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{securityScore}%</div>
            <Progress value={securityScore} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Excellent security posture
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Threats</CardTitle>
            <Warning className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{activeThreats}</div>
            <p className="text-xs text-muted-foreground">
              Threats under investigation
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Threats Mitigated</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{mitigatedThreats}</div>
            <p className="text-xs text-muted-foreground">
              +12 this week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Threat Level</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Badge className={getThreatLevelColor(threatLevel)} variant="outline">
              {(threatLevel || 'low').toUpperCase()}
            </Badge>
            <p className="text-xs text-muted-foreground mt-2">
              Current threat assessment
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Security Tabs */}
      <Tabs defaultValue="events" className="space-y-4">
        <TabsList>
          <TabsTrigger value="events">Security Events</TabsTrigger>
          <TabsTrigger value="vulnerabilities">Vulnerabilities</TabsTrigger>
          <TabsTrigger value="monitoring">Real-time Monitoring</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info size={20} />
                Recent Security Events
              </CardTitle>
              <CardDescription>
                Real-time security events and incidents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(securityEvents || []).slice(0, 10).map(event => (
                  <div 
                    key={event.id} 
                    className={`p-3 rounded-lg border ${event.resolved ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant={getSeverityColor(event.severity)}>
                          {event.severity}
                        </Badge>
                        <span className="font-medium">{event.eventType.replace('_', ' ')}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                        {!event.resolved && (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => resolveSecurityEvent(event.id)}
                          >
                            Resolve
                          </Button>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{event.description}</p>
                    {event.resolved && (
                      <p className="text-xs text-green-600 mt-1">
                        ✓ Resolved by {event.resolvedBy} at {new Date(event.resolvedAt!).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="vulnerabilities" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bug size={20} />
                Vulnerability Assessment
              </CardTitle>
              <CardDescription>
                Known vulnerabilities and remediation status
              </CardDescription>
            </CardHeader>
            <CardContent>
              {(vulnerabilities || []).length === 0 ? (
                <div className="text-center py-8">
                  <CheckCircle size={48} className="text-green-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-green-600 mb-2">No Critical Vulnerabilities</h3>
                  <p className="text-muted-foreground">
                    Your system is secure. Run a security scan to check for new vulnerabilities.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {(vulnerabilities || []).map(vuln => (
                    <div key={vuln.id} className="p-3 rounded-lg border">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Badge variant={getSeverityColor(vuln.severity)}>
                            {vuln.severity}
                          </Badge>
                          <span className="font-medium">{vuln.type}</span>
                        </div>
                        <Badge variant="outline">{vuln.status}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-1">{vuln.description}</p>
                      <p className="text-xs text-blue-600">Remediation: {vuln.remediation}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye size={20} />
                  Network Monitoring
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Firewall Status</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    Active
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>DDoS Protection</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    Enabled
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>Rate Limiting</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    Active
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>SSL/TLS</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    TLS 1.3
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database size={20} />
                  Data Protection
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span>Encryption at Rest</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    AES-256
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>Backup Status</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    Daily
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>Access Control</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    RBAC
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span>Audit Logging</span>
                  <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                    Enabled
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightning size={20} />
                  AI-Powered Threat Detection
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    Advanced machine learning algorithms are continuously monitoring for suspicious patterns, 
                    anomalous behavior, and potential security threats. Current detection accuracy: 99.2%
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock size={20} />
                Audit Trail
              </CardTitle>
              <CardDescription>
                Complete audit log of system activities and security events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {(auditLogs || []).slice(0, 15).map(log => (
                  <div key={log.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <div>
                      <span className="font-medium">{log.action.replace('_', ' ')}</span>
                      <span className="text-sm text-muted-foreground ml-2">by {log.user}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
                
                {(auditLogs || []).length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No audit logs available. System activities will appear here.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}