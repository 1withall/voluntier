import { useState, useEffect } from 'react'
import { VolunteerEvent } from '../App'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Badge } from './ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Switch } from './ui/switch'
import { Separator } from './ui/separator'
import { Alert, AlertDescription } from './ui/alert'
import { Plus, Building, Calendar, Users, Download, FileText, CheckCircle, AlertTriangle, Shield } from '@phosphor-icons/react'
import { useTelemetry } from '../services/telemetry'
import { usePrivilege } from './auth/PrivilegeGuard'
import { ProjectManagementPDFGenerator, EventProjectData } from '../services/pdfGenerator'
import { UserProfile } from '../types/profiles'
import { toast } from 'sonner'

interface OrganizationDashboardProps {
  events: VolunteerEvent[]
  onAddEvent: (event: VolunteerEvent) => void
  onUpdateEvent: (event: VolunteerEvent) => void
  userProfile?: UserProfile
}

const EVENT_CATEGORIES = [
  'Environment', 'Education', 'Health', 'Community', 'Animals',
  'Food & Nutrition', 'Youth', 'Seniors', 'Arts & Culture',
  'Emergency Response', 'Social Services', 'Technology', 'Sports & Recreation'
]

const SKILL_OPTIONS = [
  'Event Planning', 'Teaching', 'Construction', 'Gardening', 'Cooking',
  'Childcare', 'Elder Care', 'Animal Care', 'Technology', 'Transportation',
  'Administration', 'Fundraising', 'Marketing', 'Photography', 'Music',
  'First Aid', 'Project Management', 'Public Speaking', 'Data Entry',
  'Translation', 'Legal', 'Financial', 'Mentoring', 'Tutoring'
]

const EVENT_TYPES = [
  'One-time Event', 'Recurring Weekly', 'Recurring Monthly', 
  'Seasonal', 'Emergency Response', 'Ongoing Project'
]

const ACCESSIBILITY_FEATURES = [
  'Wheelchair Accessible', 'Sign Language Interpreter', 'Audio Description',
  'Braille Materials', 'Large Print', 'Accessible Parking', 'Accessible Restrooms',
  'Sensory-Friendly Environment', 'Transportation Assistance'
]

const SAFETY_REQUIREMENTS = [
  'Background Check Required', 'Training Required', 'Physical Fitness Required',
  'Age Restriction (18+)', 'Age Restriction (16+)', 'Parental Consent Required',
  'Safety Equipment Provided', 'Insurance Coverage', 'Emergency Contact Required'
]

// Enhanced event interface for comprehensive form
interface EnhancedEventForm {
  title: string
  organization: string
  description: string
  detailedDescription: string
  date: string
  endDate: string
  time: string
  endTime: string
  location: string
  exactAddress: string
  volunteersNeeded: number
  category: string
  eventType: string
  skills: string[]
  accessibilityFeatures: string[]
  safetyRequirements: string[]
  contactEmail: string
  contactPhone: string
  registrationDeadline: string
  specialInstructions: string
  equipmentProvided: string
  whatToBring: string
  parkingInfo: string
  publicTransport: string
  remoteOption: boolean
  virtualMeetingLink: string
  ageMinimum: number
  ageMaximum: number
  requiresApplication: boolean
  applicationDeadline: string
  estimatedHours: number
  impactDescription: string
  organizationWebsite: string
  socialMediaHandle: string
  eventImage: string
  additionalResources: string[]
}

export function OrganizationDashboard({ events, onAddEvent, onUpdateEvent, userProfile }: OrganizationDashboardProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [currentTab, setCurrentTab] = useState('basic')
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { trackUserAction } = useTelemetry()
  
  // Check privileges for organization operations
  const createEventsPrivilege = usePrivilege('create_events')
  const manageEventsPrivilege = usePrivilege('manage_events')

  // Check if user is verified organization
  const isVerifiedOrganization = userProfile?.userType === 'organization' && userProfile?.verificationStatus === 'verified'
  
  const [newEvent, setNewEvent] = useState<EnhancedEventForm>({
    title: '',
    organization: userProfile?.organizationInfo?.legalName || userProfile?.organizationInfo?.dbaName || 'Community Organization',
    description: '',
    detailedDescription: '',
    date: '',
    endDate: '',
    time: '',
    endTime: '',
    location: '',
    exactAddress: '',
    volunteersNeeded: 1,
    category: '',
    eventType: '',
    skills: [],
    accessibilityFeatures: [],
    safetyRequirements: [],
    contactEmail: userProfile?.contactInfo?.primaryEmail || '',
    contactPhone: userProfile?.contactInfo?.primaryPhone || '',
    registrationDeadline: '',
    specialInstructions: '',
    equipmentProvided: '',
    whatToBring: '',
    parkingInfo: '',
    publicTransport: '',
    remoteOption: false,
    virtualMeetingLink: '',
    ageMinimum: 0,
    ageMaximum: 99,
    requiresApplication: false,
    applicationDeadline: '',
    estimatedHours: 1,
    impactDescription: '',
    organizationWebsite: userProfile?.organizationInfo?.website || '',
    socialMediaHandle: '',
    eventImage: '',
    additionalResources: []
  })

  // Security validation for form inputs
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    
    // Required field validation
    if (!newEvent.title.trim()) errors.title = 'Event title is required'
    if (!newEvent.description.trim()) errors.description = 'Description is required'
    if (!newEvent.date) errors.date = 'Event date is required'
    if (!newEvent.time) errors.time = 'Event time is required'
    if (!newEvent.location.trim()) errors.location = 'Location is required'
    if (!newEvent.category) errors.category = 'Category is required'
    if (!newEvent.eventType) errors.eventType = 'Event type is required'
    if (!newEvent.contactEmail.trim()) errors.contactEmail = 'Contact email is required'
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (newEvent.contactEmail && !emailRegex.test(newEvent.contactEmail)) {
      errors.contactEmail = 'Valid email address is required'
    }
    
    // Phone validation (basic)
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/
    if (newEvent.contactPhone && !phoneRegex.test(newEvent.contactPhone.replace(/[\s\-\(\)]/g, ''))) {
      errors.contactPhone = 'Valid phone number is required'
    }
    
    // Date validation
    const eventDate = new Date(newEvent.date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    if (eventDate < today) {
      errors.date = 'Event date cannot be in the past'
    }
    
    if (newEvent.endDate) {
      const endDate = new Date(newEvent.endDate)
      if (endDate < eventDate) {
        errors.endDate = 'End date cannot be before start date'
      }
    }
    
    // Registration deadline validation
    if (newEvent.registrationDeadline) {
      const regDeadline = new Date(newEvent.registrationDeadline)
      if (regDeadline > eventDate) {
        errors.registrationDeadline = 'Registration deadline must be before event date'
      }
    }
    
    // Age validation
    if (newEvent.ageMinimum < 0 || newEvent.ageMinimum > 100) {
      errors.ageMinimum = 'Minimum age must be between 0 and 100'
    }
    if (newEvent.ageMaximum < newEvent.ageMinimum || newEvent.ageMaximum > 100) {
      errors.ageMaximum = 'Maximum age must be greater than minimum age and less than 100'
    }
    
    // URL validation for website and virtual meeting links
    const urlRegex = /^https?:\/\/.+/
    if (newEvent.organizationWebsite && !urlRegex.test(newEvent.organizationWebsite)) {
      errors.organizationWebsite = 'Website must be a valid URL starting with http:// or https://'
    }
    if (newEvent.virtualMeetingLink && !urlRegex.test(newEvent.virtualMeetingLink)) {
      errors.virtualMeetingLink = 'Virtual meeting link must be a valid URL'
    }
    
    // Security checks for potential XSS or injection
    const dangerousPatterns = /<script|javascript:|data:/i
    const textFields = [
      'title', 'description', 'detailedDescription', 'location', 'exactAddress',
      'specialInstructions', 'equipmentProvided', 'whatToBring', 'parkingInfo',
      'publicTransport', 'impactDescription', 'socialMediaHandle'
    ]
    
    textFields.forEach(field => {
      const value = newEvent[field as keyof EnhancedEventForm] as string
      if (value && dangerousPatterns.test(value)) {
        errors[field] = 'Invalid characters detected. Please remove any script tags or javascript: links'
      }
    })
    
    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleCreateEvent = async () => {
    if (!validateForm()) {
      toast.error('Please fix the form errors before submitting')
      return
    }
    
    setIsSubmitting(true)
    trackUserAction('event_creation_started', 'organization', newEvent.category)
    
    try {
      // Simulate processing delay for security checks
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const event: VolunteerEvent = {
        id: Date.now().toString(),
        title: newEvent.title.trim(),
        organization: newEvent.organization.trim(),
        description: newEvent.description.trim(),
        date: newEvent.date,
        time: newEvent.time,
        location: newEvent.location.trim(),
        volunteersNeeded: newEvent.volunteersNeeded,
        volunteersRegistered: 0,
        skills: newEvent.skills,
        category: newEvent.category,
        verified: true
      }

      onAddEvent(event)
      setShowCreateDialog(false)
      resetForm()
      
      trackUserAction('event_created', 'organization', newEvent.category)
      toast.success('Event created successfully!')
      
    } catch (error) {
      console.error('Error creating event:', error)
      trackUserAction('event_creation_failed', 'organization', 'error')
      toast.error('Failed to create event. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setNewEvent({
      title: '',
      organization: userProfile?.organizationInfo?.legalName || userProfile?.organizationInfo?.dbaName || 'Community Organization',
      description: '',
      detailedDescription: '',
      date: '',
      endDate: '',
      time: '',
      endTime: '',
      location: '',
      exactAddress: '',
      volunteersNeeded: 1,
      category: '',
      eventType: '',
      skills: [],
      accessibilityFeatures: [],
      safetyRequirements: [],
      contactEmail: userProfile?.contactInfo?.primaryEmail || '',
      contactPhone: userProfile?.contactInfo?.primaryPhone || '',
      registrationDeadline: '',
      specialInstructions: '',
      equipmentProvided: '',
      whatToBring: '',
      parkingInfo: '',
      publicTransport: '',
      remoteOption: false,
      virtualMeetingLink: '',
      ageMinimum: 0,
      ageMaximum: 99,
      requiresApplication: false,
      applicationDeadline: '',
      estimatedHours: 1,
      impactDescription: '',
      organizationWebsite: userProfile?.organizationInfo?.website || '',
      socialMediaHandle: '',
      eventImage: '',
      additionalResources: []
    })
    setFormErrors({})
    setCurrentTab('basic')
  }

  const handleSkillToggle = (skill: string) => {
    setNewEvent(current => ({
      ...current,
      skills: current.skills.includes(skill)
        ? current.skills.filter(s => s !== skill)
        : [...current.skills, skill]
    }))
  }

  const handleAccessibilityToggle = (feature: string) => {
    setNewEvent(current => ({
      ...current,
      accessibilityFeatures: current.accessibilityFeatures.includes(feature)
        ? current.accessibilityFeatures.filter(f => f !== feature)
        : [...current.accessibilityFeatures, feature]
    }))
  }

  const handleSafetyToggle = (requirement: string) => {
    setNewEvent(current => ({
      ...current,
      safetyRequirements: current.safetyRequirements.includes(requirement)
        ? current.safetyRequirements.filter(r => r !== requirement)
        : [...current.safetyRequirements, requirement]
    }))
  }

  const handleDownloadProjectTemplate = async (templateType: string) => {
    if (!events.length) {
      toast.error('Please create an event first before downloading project management templates')
      return
    }
    
    try {
      trackUserAction('pm_template_download', 'organization', templateType)
      
      // Use the most recent event for template generation
      const recentEvent = events[events.length - 1]
      const { generateProjectManagementPDF } = await import('../utils/pdfGenerator')
      
      generateProjectManagementPDF(
        templateType as any,
        recentEvent,
        userProfile?.organizationInfo?.legalName || userProfile?.organizationInfo?.dbaName || 'Organization'
      )
      
      toast.success(`${templateType} template downloaded successfully`)
    } catch (error) {
      console.error('Error generating PDF:', error)
      toast.error('Failed to generate PDF template')
    }
  }

  const handleDownloadEventChecklist = async () => {
    if (!events.length) {
      toast.error('Please create an event first before downloading the planning checklist')
      return
    }
    
    try {
      trackUserAction('event_checklist_download', 'organization', 'checklist')
      
      const recentEvent = events[events.length - 1]
      const { generateEventPlanningChecklist } = await import('../utils/pdfGenerator')
      
      generateEventPlanningChecklist(
        recentEvent,
        userProfile?.organizationInfo?.legalName || userProfile?.organizationInfo?.dbaName || 'Organization'
      )
      
      toast.success('Event planning checklist downloaded successfully')
    } catch (error) {
      console.error('Error generating checklist:', error)
      toast.error('Failed to generate event checklist')
    }
  }

  // Enhanced PDF Generation Functions for Project Management
  const generateProjectPDFs = (event: VolunteerEvent) => {
    try {
      const projectData: EventProjectData = {
        eventId: event.id,
        eventTitle: event.title,
        organization: event.organization,
        projectManager: userProfile?.leadership?.executiveDirector?.name || 'Project Manager',
        startDate: event.date,
        endDate: event.date, // Single day event, same end date
        description: event.description,
        objectives: [
          'Successfully execute volunteer event',
          'Ensure volunteer safety and satisfaction',
          'Achieve measurable community impact',
          'Build organizational reputation'
        ],
        deliverables: [
          'Completed volunteer event',
          'Volunteer feedback collection',
          'Impact measurement report',
          'Event documentation'
        ],
        timeline: [
          { milestone: 'Event Planning Complete', date: event.date, status: 'pending' },
          { milestone: 'Volunteer Recruitment', date: event.date, status: 'pending' },
          { milestone: 'Event Execution', date: event.date, status: 'pending' },
          { milestone: 'Impact Assessment', date: event.date, status: 'pending' }
        ],
        team: [
          { 
            name: userProfile?.leadership?.executiveDirector?.name || 'Project Manager', 
            role: 'Project Manager', 
            contact: userProfile?.contactInfo?.primaryEmail || '' 
          },
          { 
            name: userProfile?.leadership?.volunteerCoordinator?.name || 'Volunteer Coordinator', 
            role: 'Volunteer Coordinator', 
            contact: userProfile?.leadership?.volunteerCoordinator?.email || '' 
          }
        ],
        budget: [
          { item: 'Event Materials', amount: 500, category: 'Supplies' },
          { item: 'Volunteer Recognition', amount: 200, category: 'Recognition' },
          { item: 'Safety Equipment', amount: 150, category: 'Safety' },
          { item: 'Miscellaneous', amount: 100, category: 'Other' }
        ],
        risks: [
          { 
            risk: 'Insufficient volunteer turnout', 
            probability: 'medium', 
            impact: 'high', 
            mitigation: 'Robust recruitment campaign with backup volunteers' 
          },
          { 
            risk: 'Weather-related cancellation', 
            probability: 'low', 
            impact: 'high', 
            mitigation: 'Indoor backup venue or postponement plan' 
          },
          { 
            risk: 'Volunteer safety incident', 
            probability: 'low', 
            impact: 'high', 
            mitigation: 'Comprehensive safety briefing and first aid availability' 
          }
        ],
        stakeholders: [
          { name: 'Event Volunteers', role: 'Primary Participants', influence: 'high' },
          { name: 'Community Members', role: 'Beneficiaries', influence: 'medium' },
          { name: 'Organization Board', role: 'Oversight', influence: 'high' },
          { name: 'Local Partners', role: 'Support', influence: 'medium' }
        ]
      }

      return projectData
    } catch (error) {
      console.error('Error generating project data:', error)
      toast.error('Failed to generate project management data')
      return null
    }
  }

  const handleDownloadProjectCharter = (event: VolunteerEvent) => {
    const projectData = generateProjectPDFs(event)
    if (projectData) {
      ProjectManagementPDFGenerator.generateProjectCharter(projectData)
      trackUserAction('project_charter_downloaded', 'organization', event.id)
      toast.success('Project Charter downloaded successfully')
    }
  }

  const handleDownloadTimeline = (event: VolunteerEvent) => {
    const projectData = generateProjectPDFs(event)
    if (projectData) {
      ProjectManagementPDFGenerator.generateProjectTimeline(projectData)
      trackUserAction('project_timeline_downloaded', 'organization', event.id)
      toast.success('Project Timeline downloaded successfully')
    }
  }

  const handleDownloadRiskAssessment = (event: VolunteerEvent) => {
    const projectData = generateProjectPDFs(event)
    if (projectData) {
      ProjectManagementPDFGenerator.generateRiskAssessment(projectData)
      trackUserAction('risk_assessment_downloaded', 'organization', event.id)
      toast.success('Risk Assessment downloaded successfully')
    }
  }

  const handleDownloadResourcePlan = (event: VolunteerEvent) => {
    const projectData = generateProjectPDFs(event)
    if (projectData) {
      ProjectManagementPDFGenerator.generateResourcePlan(projectData)
      trackUserAction('resource_plan_downloaded', 'organization', event.id)
      toast.success('Resource Plan downloaded successfully')
    }
  }

  const handleDownloadCommunicationPlan = (event: VolunteerEvent) => {
    const projectData = generateProjectPDFs(event)
    if (projectData) {
      ProjectManagementPDFGenerator.generateCommunicationPlan(projectData)
      trackUserAction('communication_plan_downloaded', 'organization', event.id)
      toast.success('Communication Plan downloaded successfully')
    }
  }

  const handleDownloadClosureReport = (event: VolunteerEvent) => {
    const projectData = generateProjectPDFs(event)
    if (projectData) {
      ProjectManagementPDFGenerator.generateClosureReport(projectData)
      trackUserAction('closure_report_downloaded', 'organization', event.id)
      toast.success('Closure Report downloaded successfully')
    }
  }

  return (
    <div className="space-y-6">
      {/* Access Control Alert */}
      {!isVerifiedOrganization && (
        <Alert variant="destructive">
          <AlertTriangle size={16} />
          <AlertDescription>
            Organization verification required. Only verified organizations can create and manage events.
          </AlertDescription>
        </Alert>
      )}

      {!createEventsPrivilege.hasPrivilege && (
        <Alert>
          <Shield size={16} />
          <AlertDescription>
            Event creation privileges required. Contact your administrator for access.
          </AlertDescription>
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Organization Dashboard</h1>
          <p className="text-muted-foreground mt-2">Manage your volunteer events and coordination</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button 
                className="flex items-center gap-2"
                disabled={!isVerifiedOrganization || !createEventsPrivilege.hasPrivilege}
              >
                <Plus size={16} />
                Create Event
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Shield size={20} />
                  Create New Volunteer Event
                </DialogTitle>
                <DialogDescription>
                  Set up a comprehensive volunteer opportunity with security validation and project management integration
                </DialogDescription>
              </DialogHeader>
              
              <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="logistics">Logistics</TabsTrigger>
                  <TabsTrigger value="requirements">Requirements</TabsTrigger>
                  <TabsTrigger value="contact">Contact</TabsTrigger>
                </TabsList>

                <TabsContent value="basic" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="event-title">Event Title *</Label>
                      <Input
                        id="event-title"
                        value={newEvent.title}
                        onChange={(e) => setNewEvent(current => ({...current, title: e.target.value}))}
                        placeholder="Community Garden Cleanup"
                        className={formErrors.title ? 'border-destructive' : ''}
                      />
                      {formErrors.title && (
                        <p className="text-sm text-destructive">{formErrors.title}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="event-category">Category *</Label>
                      <Select value={newEvent.category} onValueChange={(value) => 
                        setNewEvent(current => ({...current, category: value}))
                      }>
                        <SelectTrigger className={formErrors.category ? 'border-destructive' : ''}>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {EVENT_CATEGORIES.map(category => (
                            <SelectItem key={category} value={category}>{category}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {formErrors.category && (
                        <p className="text-sm text-destructive">{formErrors.category}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="event-type">Event Type *</Label>
                      <Select value={newEvent.eventType} onValueChange={(value) => 
                        setNewEvent(current => ({...current, eventType: value}))
                      }>
                        <SelectTrigger className={formErrors.eventType ? 'border-destructive' : ''}>
                          <SelectValue placeholder="Select event type" />
                        </SelectTrigger>
                        <SelectContent>
                          {EVENT_TYPES.map(type => (
                            <SelectItem key={type} value={type}>{type}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {formErrors.eventType && (
                        <p className="text-sm text-destructive">{formErrors.eventType}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="volunteers-needed">Volunteers Needed *</Label>
                      <Input
                        id="volunteers-needed"
                        type="number"
                        min="1"
                        max="500"
                        value={newEvent.volunteersNeeded}
                        onChange={(e) => setNewEvent(current => ({...current, volunteersNeeded: parseInt(e.target.value) || 1}))}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="event-description">Brief Description *</Label>
                    <Textarea
                      id="event-description"
                      value={newEvent.description}
                      onChange={(e) => setNewEvent(current => ({...current, description: e.target.value}))}
                      placeholder="Brief overview of what volunteers will be doing..."
                      className={formErrors.description ? 'border-destructive' : ''}
                      rows={3}
                    />
                    {formErrors.description && (
                      <p className="text-sm text-destructive">{formErrors.description}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="detailed-description">Detailed Description</Label>
                    <Textarea
                      id="detailed-description"
                      value={newEvent.detailedDescription}
                      onChange={(e) => setNewEvent(current => ({...current, detailedDescription: e.target.value}))}
                      placeholder="Detailed information about the event, goals, and expectations..."
                      rows={4}
                    />
                  </div>
                </TabsContent>

                <TabsContent value="details" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="event-date">Start Date *</Label>
                      <Input
                        id="event-date"
                        type="date"
                        value={newEvent.date}
                        onChange={(e) => setNewEvent(current => ({...current, date: e.target.value}))}
                        className={formErrors.date ? 'border-destructive' : ''}
                      />
                      {formErrors.date && (
                        <p className="text-sm text-destructive">{formErrors.date}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="event-end-date">End Date (if multi-day)</Label>
                      <Input
                        id="event-end-date"
                        type="date"
                        value={newEvent.endDate}
                        onChange={(e) => setNewEvent(current => ({...current, endDate: e.target.value}))}
                        className={formErrors.endDate ? 'border-destructive' : ''}
                      />
                      {formErrors.endDate && (
                        <p className="text-sm text-destructive">{formErrors.endDate}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="event-time">Start Time *</Label>
                      <Input
                        id="event-time"
                        type="time"
                        value={newEvent.time}
                        onChange={(e) => setNewEvent(current => ({...current, time: e.target.value}))}
                        className={formErrors.time ? 'border-destructive' : ''}
                      />
                      {formErrors.time && (
                        <p className="text-sm text-destructive">{formErrors.time}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="event-end-time">End Time</Label>
                      <Input
                        id="event-end-time"
                        type="time"
                        value={newEvent.endTime}
                        onChange={(e) => setNewEvent(current => ({...current, endTime: e.target.value}))}
                      />
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="estimated-hours">Estimated Hours</Label>
                      <Input
                        id="estimated-hours"
                        type="number"
                        min="0.5"
                        max="24"
                        step="0.5"
                        value={newEvent.estimatedHours}
                        onChange={(e) => setNewEvent(current => ({...current, estimatedHours: parseFloat(e.target.value) || 1}))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="registration-deadline">Registration Deadline</Label>
                      <Input
                        id="registration-deadline"
                        type="date"
                        value={newEvent.registrationDeadline}
                        onChange={(e) => setNewEvent(current => ({...current, registrationDeadline: e.target.value}))}
                        className={formErrors.registrationDeadline ? 'border-destructive' : ''}
                      />
                      {formErrors.registrationDeadline && (
                        <p className="text-sm text-destructive">{formErrors.registrationDeadline}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Skills Needed (Optional)</Label>
                    <div className="grid grid-cols-3 gap-2 max-h-32 overflow-y-auto p-2 border rounded">
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

                  <div className="space-y-2">
                    <Label htmlFor="impact-description">Expected Impact & Outcomes</Label>
                    <Textarea
                      id="impact-description"
                      value={newEvent.impactDescription}
                      onChange={(e) => setNewEvent(current => ({...current, impactDescription: e.target.value}))}
                      placeholder="Describe the expected impact and outcomes of this volunteer event..."
                      rows={3}
                    />
                  </div>
                </TabsContent>

                <TabsContent value="logistics" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="event-location">Location Name *</Label>
                    <Input
                      id="event-location"
                      value={newEvent.location}
                      onChange={(e) => setNewEvent(current => ({...current, location: e.target.value}))}
                      placeholder="Community Center Main Hall"
                      className={formErrors.location ? 'border-destructive' : ''}
                    />
                    {formErrors.location && (
                      <p className="text-sm text-destructive">{formErrors.location}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="exact-address">Exact Address</Label>
                    <Input
                      id="exact-address"
                      value={newEvent.exactAddress}
                      onChange={(e) => setNewEvent(current => ({...current, exactAddress: e.target.value}))}
                      placeholder="123 Community St, Your City, State 12345"
                    />
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="parking-info">Parking Information</Label>
                      <Textarea
                        id="parking-info"
                        value={newEvent.parkingInfo}
                        onChange={(e) => setNewEvent(current => ({...current, parkingInfo: e.target.value}))}
                        placeholder="Free parking available in adjacent lot..."
                        rows={2}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="public-transport">Public Transportation</Label>
                      <Textarea
                        id="public-transport"
                        value={newEvent.publicTransport}
                        onChange={(e) => setNewEvent(current => ({...current, publicTransport: e.target.value}))}
                        placeholder="Bus routes 15, 23 stop nearby..."
                        rows={2}
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="remote-option"
                      checked={newEvent.remoteOption}
                      onCheckedChange={(checked) => setNewEvent(current => ({...current, remoteOption: checked}))}
                    />
                    <Label htmlFor="remote-option">This event has remote/virtual participation options</Label>
                  </div>

                  {newEvent.remoteOption && (
                    <div className="space-y-2">
                      <Label htmlFor="virtual-meeting-link">Virtual Meeting Link</Label>
                      <Input
                        id="virtual-meeting-link"
                        value={newEvent.virtualMeetingLink}
                        onChange={(e) => setNewEvent(current => ({...current, virtualMeetingLink: e.target.value}))}
                        placeholder="https://zoom.us/j/..."
                        className={formErrors.virtualMeetingLink ? 'border-destructive' : ''}
                      />
                      {formErrors.virtualMeetingLink && (
                        <p className="text-sm text-destructive">{formErrors.virtualMeetingLink}</p>
                      )}
                    </div>
                  )}

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="equipment-provided">Equipment/Materials Provided</Label>
                      <Textarea
                        id="equipment-provided"
                        value={newEvent.equipmentProvided}
                        onChange={(e) => setNewEvent(current => ({...current, equipmentProvided: e.target.value}))}
                        placeholder="Tools, gloves, safety equipment..."
                        rows={3}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="what-to-bring">What Volunteers Should Bring</Label>
                      <Textarea
                        id="what-to-bring"
                        value={newEvent.whatToBring}
                        onChange={(e) => setNewEvent(current => ({...current, whatToBring: e.target.value}))}
                        placeholder="Water bottle, sun hat, comfortable clothes..."
                        rows={3}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="special-instructions">Special Instructions</Label>
                    <Textarea
                      id="special-instructions"
                      value={newEvent.specialInstructions}
                      onChange={(e) => setNewEvent(current => ({...current, specialInstructions: e.target.value}))}
                      placeholder="Meeting point, check-in procedures, etc..."
                      rows={3}
                    />
                  </div>
                </TabsContent>

                <TabsContent value="requirements" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="age-minimum">Minimum Age</Label>
                      <Input
                        id="age-minimum"
                        type="number"
                        min="0"
                        max="100"
                        value={newEvent.ageMinimum}
                        onChange={(e) => setNewEvent(current => ({...current, ageMinimum: parseInt(e.target.value) || 0}))}
                        className={formErrors.ageMinimum ? 'border-destructive' : ''}
                      />
                      {formErrors.ageMinimum && (
                        <p className="text-sm text-destructive">{formErrors.ageMinimum}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="age-maximum">Maximum Age</Label>
                      <Input
                        id="age-maximum"
                        type="number"
                        min="0"
                        max="100"
                        value={newEvent.ageMaximum}
                        onChange={(e) => setNewEvent(current => ({...current, ageMaximum: parseInt(e.target.value) || 99}))}
                        className={formErrors.ageMaximum ? 'border-destructive' : ''}
                      />
                      {formErrors.ageMaximum && (
                        <p className="text-sm text-destructive">{formErrors.ageMaximum}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Safety Requirements & Restrictions</Label>
                    <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto p-2 border rounded">
                      {SAFETY_REQUIREMENTS.map(requirement => (
                        <Button
                          key={requirement}
                          type="button"
                          variant={newEvent.safetyRequirements.includes(requirement) ? "default" : "outline"}
                          size="sm"
                          onClick={() => handleSafetyToggle(requirement)}
                          className="text-xs h-8 justify-start"
                        >
                          {requirement}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Accessibility Features</Label>
                    <div className="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto p-2 border rounded">
                      {ACCESSIBILITY_FEATURES.map(feature => (
                        <Button
                          key={feature}
                          type="button"
                          variant={newEvent.accessibilityFeatures.includes(feature) ? "default" : "outline"}
                          size="sm"
                          onClick={() => handleAccessibilityToggle(feature)}
                          className="text-xs h-8 justify-start"
                        >
                          {feature}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="requires-application"
                      checked={newEvent.requiresApplication}
                      onCheckedChange={(checked) => setNewEvent(current => ({...current, requiresApplication: checked}))}
                    />
                    <Label htmlFor="requires-application">Requires application/screening process</Label>
                  </div>

                  {newEvent.requiresApplication && (
                    <div className="space-y-2">
                      <Label htmlFor="application-deadline">Application Deadline</Label>
                      <Input
                        id="application-deadline"
                        type="date"
                        value={newEvent.applicationDeadline}
                        onChange={(e) => setNewEvent(current => ({...current, applicationDeadline: e.target.value}))}
                      />
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="contact" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="contact-email">Contact Email *</Label>
                      <Input
                        id="contact-email"
                        type="email"
                        value={newEvent.contactEmail}
                        onChange={(e) => setNewEvent(current => ({...current, contactEmail: e.target.value}))}
                        placeholder="contact@organization.org"
                        className={formErrors.contactEmail ? 'border-destructive' : ''}
                      />
                      {formErrors.contactEmail && (
                        <p className="text-sm text-destructive">{formErrors.contactEmail}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="contact-phone">Contact Phone</Label>
                      <Input
                        id="contact-phone"
                        type="tel"
                        value={newEvent.contactPhone}
                        onChange={(e) => setNewEvent(current => ({...current, contactPhone: e.target.value}))}
                        placeholder="(555) 123-4567"
                        className={formErrors.contactPhone ? 'border-destructive' : ''}
                      />
                      {formErrors.contactPhone && (
                        <p className="text-sm text-destructive">{formErrors.contactPhone}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="organization-website">Organization Website</Label>
                      <Input
                        id="organization-website"
                        type="url"
                        value={newEvent.organizationWebsite}
                        onChange={(e) => setNewEvent(current => ({...current, organizationWebsite: e.target.value}))}
                        placeholder="https://yourorganization.org"
                        className={formErrors.organizationWebsite ? 'border-destructive' : ''}
                      />
                      {formErrors.organizationWebsite && (
                        <p className="text-sm text-destructive">{formErrors.organizationWebsite}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="social-media">Social Media Handle</Label>
                      <Input
                        id="social-media"
                        value={newEvent.socialMediaHandle}
                        onChange={(e) => setNewEvent(current => ({...current, socialMediaHandle: e.target.value}))}
                        placeholder="@yourorganization"
                      />
                    </div>
                  </div>

                  {Object.keys(formErrors).length > 0 && (
                    <Alert variant="destructive">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Please review and fix the validation errors before submitting the form.
                      </AlertDescription>
                    </Alert>
                  )}

                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      All information will be validated for security. Events undergo automated screening before publication.
                    </AlertDescription>
                  </Alert>
                </TabsContent>
              </Tabs>

              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={handleCreateEvent} 
                  className="flex-1"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Creating Event...' : 'Create Event'}
                </Button>
                <Button variant="outline" onClick={() => {
                  setShowCreateDialog(false)
                  resetForm()
                }}>
                  Cancel
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Project Management Tools Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText size={20} />
            Project Management Tools
          </CardTitle>
          <CardDescription>
            Download professional project management templates (PDF format) for your event planning.
            These documents are designed for offline use and should be stored in your organization's systems.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Button
              variant="outline"
              onClick={() => handleDownloadProjectTemplate('charter')}
              className="flex items-center gap-2 h-auto p-4 flex-col"
              disabled={events.length === 0}
            >
              <Download size={20} />
              <div className="text-center">
                <div className="font-medium">Project Charter</div>
                <div className="text-xs text-muted-foreground">Define scope & objectives</div>
              </div>
            </Button>

            <Button
              variant="outline"
              onClick={() => handleDownloadProjectTemplate('timeline')}
              className="flex items-center gap-2 h-auto p-4 flex-col"
              disabled={events.length === 0}
            >
              <Download size={20} />
              <div className="text-center">
                <div className="font-medium">Schedule Plan</div>
                <div className="text-xs text-muted-foreground">Timeline & milestones</div>
              </div>
            </Button>

            <Button
              variant="outline"
              onClick={() => handleDownloadProjectTemplate('risk')}
              className="flex items-center gap-2 h-auto p-4 flex-col"
              disabled={events.length === 0}
            >
              <Download size={20} />
              <div className="text-center">
                <div className="font-medium">Risk Management</div>
                <div className="text-xs text-muted-foreground">Identify & mitigate risks</div>
              </div>
            </Button>

            <Button
              variant="outline"
              onClick={() => handleDownloadProjectTemplate('stakeholder')}
              className="flex items-center gap-2 h-auto p-4 flex-col"
              disabled={events.length === 0}
            >
              <Download size={20} />
              <div className="text-center">
                <div className="font-medium">Stakeholder Plan</div>
                <div className="text-xs text-muted-foreground">Manage relationships</div>
              </div>
            </Button>

            <Button
              variant="outline"
              onClick={() => handleDownloadProjectTemplate('communication')}
              className="flex items-center gap-2 h-auto p-4 flex-col"
              disabled={events.length === 0}
            >
              <Download size={20} />
              <div className="text-center">
                <div className="font-medium">Communication Plan</div>
                <div className="text-xs text-muted-foreground">Information flow strategy</div>
              </div>
            </Button>

            <Button
              variant="outline"
              onClick={handleDownloadEventChecklist}
              className="flex items-center gap-2 h-auto p-4 flex-col"
              disabled={events.length === 0}
            >
              <Download size={20} />
              <div className="text-center">
                <div className="font-medium">Event Checklist</div>
                <div className="text-xs text-muted-foreground">Comprehensive planning list</div>
              </div>
            </Button>
          </div>

          {events.length === 0 && (
            <Alert className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Create your first event to unlock project management templates
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Separator />

      {/* Events List */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {events.length === 0 ? (
          <Card className="md:col-span-2 lg:col-span-3">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Building size={48} className="text-muted-foreground mb-4" />
              <CardTitle className="mb-2">No Events Created</CardTitle>
              <CardDescription className="text-center max-w-md">
                Create your first volunteer event to start connecting with community volunteers and access project management tools.
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

                {/* Project Management Downloads */}
                <Separator />
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Project Management Tools:</p>
                  <div className="grid grid-cols-2 gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadProjectCharter(event)}
                      className="text-xs h-8"
                      disabled={!isVerifiedOrganization}
                    >
                      <FileText size={12} className="mr-1" />
                      Charter
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadTimeline(event)}
                      className="text-xs h-8"
                      disabled={!isVerifiedOrganization}
                    >
                      <Calendar size={12} className="mr-1" />
                      Timeline
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadRiskAssessment(event)}
                      className="text-xs h-8"
                      disabled={!isVerifiedOrganization}
                    >
                      <AlertTriangle size={12} className="mr-1" />
                      Risk Plan
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadResourcePlan(event)}
                      className="text-xs h-8"
                      disabled={!isVerifiedOrganization}
                    >
                      <Users size={12} className="mr-1" />
                      Resources
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadCommunicationPlan(event)}
                      className="text-xs h-8"
                      disabled={!isVerifiedOrganization}
                    >
                      <Shield size={12} className="mr-1" />
                      Comms
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadClosureReport(event)}
                      className="text-xs h-8"
                      disabled={!isVerifiedOrganization}
                    >
                      <CheckCircle size={12} className="mr-1" />
                      Closure
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}