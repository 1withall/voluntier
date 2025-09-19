import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Progress } from '../ui/progress'
import { Badge } from '../ui/badge'
import { Alert, AlertDescription } from '../ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { OnboardingAnalyticsService } from '../../services/onboardingAnalytics'
import { OnboardingProgress, OnboardingAnalytics, OnboardingStep } from '../../types/onboarding'
import { UserProfile } from '../../types/profiles'
import {
  CheckCircle,
  XCircle,
  Clock,
  Play,
  SkipForward,
  ChartBar,
  TrendUp,
  Warning,
  Users,
  Timer,
  Target
} from '@phosphor-icons/react'

interface OnboardingProgressTrackerProps {
  userProfile: UserProfile
}

export function OnboardingProgressTracker({ userProfile }: OnboardingProgressTrackerProps) {
  const [onboardingProgress, setOnboardingProgress] = useState<OnboardingProgress | null>(null)
  const [analytics, setAnalytics] = useState<OnboardingAnalytics[]>([])
  const [aggregatedStats, setAggregatedStats] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('progress')
  const [loading, setLoading] = useState(true)

  const analyticsService = OnboardingAnalyticsService.getInstance()

  useEffect(() => {
    loadOnboardingData()
  }, [userProfile.id])

  const loadOnboardingData = async () => {
    setLoading(true)
    try {
      // Initialize progress if it doesn't exist
      let progress = await analyticsService.getOnboardingProgress(userProfile.id)
      if (!progress) {
        progress = await analyticsService.initializeOnboardingProgress(userProfile.id, userProfile.userType)
      }

      const { analytics: userAnalytics } = await analyticsService.getUserAnalytics(userProfile.id)
      const aggregated = await analyticsService.getAggregatedAnalytics(userProfile.userType)

      setOnboardingProgress(progress)
      setAnalytics(userAnalytics)
      setAggregatedStats(aggregated)
    } catch (error) {
      console.error('Failed to load onboarding data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartOnboarding = async () => {
    if (onboardingProgress && onboardingProgress.status === 'not_started') {
      try {
        const updatedProgress = await analyticsService.startOnboarding(userProfile.id)
        setOnboardingProgress(updatedProgress)
      } catch (error) {
        console.error('Failed to start onboarding:', error)
      }
    }
  }

  const handleCompleteStep = async (stepId: string) => {
    if (!onboardingProgress) return
    
    try {
      const startTime = Date.now()
      const duration = 5000 + Math.random() * 15000 // Simulate 5-20 seconds
      
      const updatedProgress = await analyticsService.completeStep(
        userProfile.id, 
        stepId, 
        duration,
        { simulatedCompletion: true }
      )
      setOnboardingProgress(updatedProgress)
      await loadOnboardingData() // Refresh analytics
    } catch (error) {
      console.error('Failed to complete step:', error)
    }
  }

  const handleSkipStep = async (stepId: string) => {
    if (!onboardingProgress) return
    
    try {
      const updatedProgress = await analyticsService.skipStep(
        userProfile.id, 
        stepId, 
        'Optional step skipped by user'
      )
      setOnboardingProgress(updatedProgress)
      await loadOnboardingData()
    } catch (error) {
      console.error('Failed to skip step:', error)
    }
  }

  const getStepStatus = (stepId: string): 'completed' | 'failed' | 'skipped' | 'current' | 'pending' => {
    if (!onboardingProgress) return 'pending'
    
    if (onboardingProgress.completedSteps.some(s => s.stepId === stepId)) return 'completed'
    if (onboardingProgress.failedSteps.some(s => s.stepId === stepId)) return 'failed'
    if (onboardingProgress.skippedSteps.some(s => s.stepId === stepId)) return 'skipped'
    if (onboardingProgress.currentStepId === stepId) return 'current'
    return 'pending'
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle size={20} className="text-green-600" />
      case 'failed': return <XCircle size={20} className="text-red-600" />
      case 'skipped': return <SkipForward size={20} className="text-yellow-600" />
      case 'current': return <Play size={20} className="text-blue-600" />
      default: return <Clock size={20} className="text-gray-400" />
    }
  }

  const getStepBadgeColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'skipped': return 'bg-yellow-100 text-yellow-800'
      case 'current': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-600'
    }
  }

  const formatDuration = (minutes: number): string => {
    if (minutes < 1) return '< 1 min'
    if (minutes < 60) return `${Math.round(minutes)} min`
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = Math.round(minutes % 60)
    return `${hours}h ${remainingMinutes}m`
  }

  const getTemplate = () => {
    // Mock template based on user type
    const templates = {
      individual: [
        { id: 'personal_info', name: 'Personal Information', required: true, estimatedDuration: 5 },
        { id: 'document_upload', name: 'Document Upload', required: true, estimatedDuration: 10 },
        { id: 'references', name: 'References', required: true, estimatedDuration: 8 },
        { id: 'verification', name: 'In-Person Verification', required: true, estimatedDuration: 30 }
      ],
      organization: [
        { id: 'org_info', name: 'Organization Info', required: true, estimatedDuration: 10 },
        { id: 'legal_docs', name: 'Legal Documents', required: true, estimatedDuration: 15 },
        { id: 'leadership', name: 'Leadership Team', required: true, estimatedDuration: 12 },
        { id: 'verification', name: 'Verification', required: true, estimatedDuration: 45 }
      ],
      business: [
        { id: 'business_info', name: 'Business Information', required: true, estimatedDuration: 8 },
        { id: 'registration_docs', name: 'Registration Docs', required: true, estimatedDuration: 12 },
        { id: 'verification', name: 'Verification', required: false, estimatedDuration: 20 }
      ]
    }
    return templates[userProfile.userType] || []
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-1/3 mb-2" />
          <div className="h-4 bg-muted rounded w-2/3" />
        </div>
      </div>
    )
  }

  const template = getTemplate()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Onboarding Progress</h1>
          <p className="text-muted-foreground mt-2">
            Track your completion progress and view detailed analytics
          </p>
        </div>
        {onboardingProgress && (
          <Card className="w-80">
            <CardContent className="p-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Overall Progress</span>
                  <Badge className={onboardingProgress.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}>
                    {onboardingProgress.status.replace('_', ' ')}
                  </Badge>
                </div>
                <Progress value={onboardingProgress.analytics.progressPercentage} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{onboardingProgress.analytics.completedSteps}/{onboardingProgress.analytics.totalSteps} steps</span>
                  <span>{onboardingProgress.analytics.progressPercentage}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="flex items-center gap-1">
                    <Timer size={12} />
                    {formatDuration(onboardingProgress.analytics.totalTimeSpent)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Target size={12} />
                    {formatDuration(onboardingProgress.analytics.estimatedTimeRemaining)} left
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="progress" className="flex items-center gap-2">
            <CheckCircle size={16} />
            Progress
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <ChartBar size={16} />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="insights" className="flex items-center gap-2">
            <TrendUp size={16} />
            Insights
          </TabsTrigger>
        </TabsList>

        <TabsContent value="progress" className="space-y-6">
          {onboardingProgress?.status === 'not_started' && (
            <Alert>
              <Play size={16} />
              <AlertDescription className="flex items-center justify-between">
                <span>Ready to begin your onboarding journey?</span>
                <Button onClick={handleStartOnboarding} size="sm">
                  Start Onboarding
                </Button>
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4">
            {template.map((step, index) => {
              const status = getStepStatus(step.id)
              const stepData = onboardingProgress?.completedSteps.find(s => s.stepId === step.id)
              
              return (
                <Card key={step.id} className={status === 'current' ? 'ring-2 ring-primary' : ''}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStepIcon(status)}
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{step.name}</p>
                            {step.required && <Badge variant="outline" className="text-xs">Required</Badge>}
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Estimated time: {step.estimatedDuration} minutes
                          </p>
                          {stepData && (
                            <p className="text-xs text-muted-foreground">
                              Completed in {Math.round(stepData.duration / 60)}m {stepData.duration % 60}s
                              {stepData.attempts > 1 && ` (${stepData.attempts} attempts)`}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getStepBadgeColor(status)}>
                          {status}
                        </Badge>
                        {status === 'current' && (
                          <div className="flex gap-1">
                            <Button 
                              size="sm" 
                              onClick={() => handleCompleteStep(step.id)}
                              className="h-8 px-3"
                            >
                              Complete
                            </Button>
                            {!step.required && (
                              <Button 
                                size="sm" 
                                variant="outline" 
                                onClick={() => handleSkipStep(step.id)}
                                className="h-8 px-3"
                              >
                                Skip
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          {onboardingProgress && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Time Spent</p>
                      <p className="text-2xl font-bold">
                        {formatDuration(onboardingProgress.analytics.totalTimeSpent)}
                      </p>
                    </div>
                    <Timer size={24} className="text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Avg Step Time</p>
                      <p className="text-2xl font-bold">
                        {formatDuration(onboardingProgress.analytics.averageStepDuration)}
                      </p>
                    </div>
                    <ChartBar size={24} className="text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Retry Attempts</p>
                      <p className="text-2xl font-bold">
                        {onboardingProgress.analytics.retryAttempts}
                      </p>
                    </div>
                    <XCircle size={24} className="text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Completion Rate</p>
                      <p className="text-2xl font-bold">
                        {onboardingProgress.analytics.progressPercentage}%
                      </p>
                    </div>
                    <Target size={24} className="text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Step-by-Step Analytics</CardTitle>
              <CardDescription>
                Detailed breakdown of your progress through each onboarding step
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {template.map((step) => {
                  const stepAnalytics = analytics.filter(a => a.stepId === step.id)
                  const completedStep = onboardingProgress?.completedSteps.find(s => s.stepId === step.id)
                  const failedStep = onboardingProgress?.failedSteps.find(s => s.stepId === step.id)
                  
                  return (
                    <div key={step.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        {getStepIcon(getStepStatus(step.id))}
                        <div>
                          <p className="font-medium">{step.name}</p>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span>Events: {stepAnalytics.length}</span>
                            {completedStep && (
                              <span>Duration: {Math.round(completedStep.duration / 60)}m {completedStep.duration % 60}s</span>
                            )}
                            {failedStep && (
                              <span className="text-red-600">Attempts: {failedStep.attempts}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-6">
          {aggregatedStats && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users size={20} />
                      Cohort Performance
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Total Started:</span>
                        <span className="font-medium">{aggregatedStats.performanceMetrics.totalStarted}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Completed:</span>
                        <span className="font-medium">{aggregatedStats.performanceMetrics.totalCompleted}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Success Rate:</span>
                        <span className="font-medium">
                          {Math.round(aggregatedStats.performanceMetrics.overallCompletionRate * 100)}%
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Warning size={20} />
                      Common Issues
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {aggregatedStats.errorPatterns.slice(0, 3).map((error, index) => (
                        <div key={index} className="text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">{error.errorType}:</span>
                            <span className="font-medium">{error.frequency}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendUp size={20} />
                      Optimization
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Avg Completion:</span>
                        <span className="font-medium">
                          {formatDuration(aggregatedStats.averageCompletionTime)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Your Time:</span>
                        <span className="font-medium">
                          {onboardingProgress ? formatDuration(onboardingProgress.analytics.totalTimeSpent) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {aggregatedStats.commonDropoffPoints.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Common Dropoff Points</CardTitle>
                    <CardDescription>
                      Steps where users most commonly abandon the onboarding process
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {aggregatedStats.commonDropoffPoints.map((dropoff, index) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                          <span className="font-medium">
                            {template.find(s => s.id === dropoff.stepId)?.name || dropoff.stepId}
                          </span>
                          <div className="flex items-center gap-2">
                            <Progress value={dropoff.dropoffRate * 100} className="w-24 h-2" />
                            <span className="text-sm text-muted-foreground">
                              {Math.round(dropoff.dropoffRate * 100)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}