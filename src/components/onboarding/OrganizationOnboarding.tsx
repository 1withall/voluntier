import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { OrganizationProfile, OnboardingStep } from '../../types/profiles'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Textarea } from '../ui/textarea'
import { Checkbox } from '../ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Alert, AlertDescription } from '../ui/alert'
import { Separator } from '../ui/separator'
import { 
  Building, 
  Shield, 
  Phone, 
  MapPin, 
  Users, 
  FileText, 
  Warning,
  CheckCircle,
  Upload,
  Globe,
  Clock,
  Heart
} from '@phosphor-icons/react'

interface OrganizationOnboardingProps {
  onComplete: (profile: Partial<OrganizationProfile>) => void
  onBack: () => void
  existingProfile?: Partial<OrganizationProfile>
}

export function OrganizationOnboarding({ onComplete, onBack, existingProfile }: OrganizationOnboardingProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [profileData, setProfileData] = useState<Partial<OrganizationProfile>>(existingProfile || {})
  const [contacts, setContacts] = useState<any[]>([])
  
  const { register, handleSubmit, formState: { errors }, watch, setValue, reset } = useForm()

  const onboardingSteps: OnboardingStep[] = [
    {
      id: 'organization-info',
      title: 'Organization Information',
      description: 'Basic details about your organization',
      completed: false,
      required: true,
      order: 1,
      estimatedTime: '8 minutes'
    },
    {
      id: 'contact-address',
      title: 'Contact & Address',
      description: 'How people can reach your organization',
      completed: false,
      required: true,
      order: 2,
      estimatedTime: '5 minutes'
    },
    {
      id: 'leadership-team',
      title: 'Leadership Team',
      description: 'Key contacts and leadership information',
      completed: false,
      required: true,
      order: 3,
      estimatedTime: '10 minutes'
    },
    {
      id: 'operations',
      title: 'Operations & Capabilities',
      description: 'How your organization operates and what you offer',
      completed: false,
      required: true,
      order: 4,
      estimatedTime: '8 minutes'
    },
    {
      id: 'verification-docs',
      title: 'Legal & Verification Documents',
      description: 'Upload required legal and insurance documents',
      completed: false,
      required: true,
      order: 5,
      estimatedTime: '10 minutes'
    },
    {
      id: 'compliance-policies',
      title: 'Compliance & Policies',
      description: 'Confirm compliance with safety and legal requirements',
      completed: false,
      required: true,
      order: 6,
      estimatedTime: '5 minutes'
    },
    {
      id: 'agreements',
      title: 'Platform Agreements',
      description: 'Review and accept platform terms and policies',
      completed: false,
      required: true,
      order: 7,
      estimatedTime: '3 minutes'
    }
  ]

  const totalSteps = onboardingSteps.length
  const progress = (currentStep / totalSteps) * 100

  const organizationTypes = [
    'nonprofit',
    'charity', 
    'religious',
    'educational',
    'government',
    'other'
  ]

  const serviceAreas = [
    'Child & Youth Services',
    'Senior Services', 
    'Healthcare',
    'Education',
    'Environmental',
    'Food Security',
    'Housing & Homelessness',
    'Mental Health',
    'Disability Services',
    'Disaster Relief',
    'Community Development',
    'Arts & Culture',
    'Other'
  ]

  const saveStepData = (stepData: any) => {
    setProfileData(prev => ({
      ...prev,
      ...stepData,
      updatedAt: new Date().toISOString()
    }))
  }

  const onStepSubmit = (data: any) => {
    saveStepData(data)
    
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
      reset()
    } else {
      // Final submission
      const completeProfile: Partial<OrganizationProfile> = {
        ...profileData,
        ...data,
        userType: 'organization',
        onboardingCompleted: true,
        profileCompleteness: calculateProfileCompleteness({ ...profileData, ...data }),
        createdAt: existingProfile?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      onComplete(completeProfile)
    }
  }

  const calculateProfileCompleteness = (profile: any): number => {
    const requiredFields = [
      'legalName',
      'ein',
      'organizationType',
      'missionStatement',
      'primaryEmail',
      'primaryPhone',
      'street',
      'city',
      'state',
      'zipCode'
    ]
    
    let completed = 0
    requiredFields.forEach(field => {
      if (profile[field]) completed++
    })
    
    return Math.round((completed / requiredFields.length) * 100)
  }

  const renderOrganizationInfo = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Building size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Organization Information</h2>
        <p className="text-muted-foreground">Tell us about your organization</p>
      </div>

      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="legalName">Legal Organization Name *</Label>
            <Input
              id="legalName"
              {...register('legalName', { required: 'Legal name is required' })}
              placeholder="Official registered name"
            />
            {errors.legalName && (
              <p className="text-sm text-destructive">{String(errors.legalName.message || 'Legal name is required')}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="dbaName">DBA Name (if different)</Label>
            <Input
              id="dbaName"
              {...register('dbaName')}
              placeholder="Doing business as..."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ein">EIN (Tax ID) *</Label>
            <Input
              id="ein"
              {...register('ein', { 
                required: 'EIN is required',
                pattern: {
                  value: /^\d{2}-\d{7}$/,
                  message: 'EIN must be in format XX-XXXXXXX'
                }
              })}
              placeholder="XX-XXXXXXX"
            />
            {errors.ein && (
              <p className="text-sm text-destructive">{String(errors.ein.message || 'EIN is required')}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="organizationType">Organization Type *</Label>
            <Select onValueChange={(value) => setValue('organizationType', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select organization type" />
              </SelectTrigger>
              <SelectContent>
                {organizationTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="foundedYear">Founded Year *</Label>
            <Input
              id="foundedYear"
              type="number"
              {...register('foundedYear', { 
                required: 'Founded year is required',
                min: { value: 1800, message: 'Year must be after 1800' },
                max: { value: new Date().getFullYear(), message: 'Year cannot be in the future' }
              })}
              placeholder="YYYY"
            />
            {errors.foundedYear && (
              <p className="text-sm text-destructive">{String(errors.foundedYear.message || 'Founded year is required')}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              type="url"
              {...register('website')}
              placeholder="https://www.yourorg.org"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="missionStatement">Mission Statement *</Label>
          <Textarea
            id="missionStatement"
            {...register('missionStatement', { required: 'Mission statement is required' })}
            placeholder="Describe your organization's mission and purpose..."
            rows={3}
          />
          {errors.missionStatement && (
            <p className="text-sm text-destructive">{String(errors.missionStatement.message || 'Mission statement is required')}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Organization Description *</Label>
          <Textarea
            id="description"
            {...register('description', { required: 'Description is required' })}
            placeholder="Provide a detailed description of your organization, programs, and services..."
            rows={4}
          />
          {errors.description && (
            <p className="text-sm text-destructive">{String(errors.description.message || 'Description is required')}</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="numberOfEmployees">Number of Employees</Label>
            <Select onValueChange={(value) => setValue('numberOfEmployees', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select employee count" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1-5">1-5 employees</SelectItem>
                <SelectItem value="6-10">6-10 employees</SelectItem>
                <SelectItem value="11-25">11-25 employees</SelectItem>
                <SelectItem value="26-50">26-50 employees</SelectItem>
                <SelectItem value="51-100">51-100 employees</SelectItem>
                <SelectItem value="101+">101+ employees</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="annualBudget">Annual Budget</Label>
            <Select onValueChange={(value) => setValue('annualBudget', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select budget range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="under-50k">Under $50,000</SelectItem>
                <SelectItem value="50k-100k">$50,000 - $100,000</SelectItem>
                <SelectItem value="100k-250k">$100,000 - $250,000</SelectItem>
                <SelectItem value="250k-500k">$250,000 - $500,000</SelectItem>
                <SelectItem value="500k-1m">$500,000 - $1,000,000</SelectItem>
                <SelectItem value="1m+">$1,000,000+</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  )

  const renderContactAddress = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <MapPin size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Contact & Address Information</h2>
        <p className="text-muted-foreground">How can people reach your organization?</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Primary Contact Information</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="primaryEmail">Primary Email *</Label>
              <Input
                id="primaryEmail"
                type="email"
                {...register('primaryEmail', { 
                  required: 'Primary email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                placeholder="contact@yourorg.org"
              />
              {errors.primaryEmail && (
                <p className="text-sm text-destructive">{String(errors.primaryEmail.message || 'Primary email is required')}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="primaryPhone">Primary Phone *</Label>
              <Input
                id="primaryPhone"
                type="tel"
                {...register('primaryPhone', { required: 'Primary phone is required' })}
                placeholder="(555) 123-4567"
              />
              {errors.primaryPhone && (
                <p className="text-sm text-destructive">{String(errors.primaryPhone.message || 'Primary phone is required')}</p>
              )}
            </div>
          </div>
        </div>

        <Separator />

        <div>
          <h3 className="text-lg font-semibold mb-4">Physical Address</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="street">Street Address *</Label>
              <Input
                id="street"
                {...register('street', { required: 'Street address is required' })}
                placeholder="123 Organization Way"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  {...register('city', { required: 'City is required' })}
                  placeholder="City"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="state">State *</Label>
                <Input
                  id="state"
                  {...register('state', { required: 'State is required' })}
                  placeholder="ST"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="zipCode">ZIP Code *</Label>
                <Input
                  id="zipCode"
                  {...register('zipCode', { required: 'ZIP code is required' })}
                  placeholder="12345"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="country">Country *</Label>
              <Input
                id="country"
                {...register('country', { required: 'Country is required' })}
                defaultValue="United States"
                placeholder="Country"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox 
            id="differentMailing"
            onCheckedChange={(checked) => setValue('differentMailingAddress', checked)}
          />
          <Label htmlFor="differentMailing" className="text-sm">
            Mailing address is different from physical address
          </Label>
        </div>
      </div>
    </div>
  )

  const renderNavigation = () => (
    <div className="flex justify-between mt-6">
      <Button 
        type="button" 
        variant="outline" 
        onClick={currentStep === 1 ? onBack : () => setCurrentStep(currentStep - 1)}
      >
        {currentStep === 1 ? 'Back to Selection' : 'Previous'}
      </Button>
      
      <div className="flex gap-2">
        <Button variant="ghost" type="button">
          Save Progress
        </Button>
        <Button type="submit">
          {currentStep === totalSteps ? 'Complete Onboarding' : 'Next Step'}
        </Button>
      </div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Organization Registration</h1>
            <p className="text-muted-foreground">Complete your organization profile</p>
          </div>
          <Badge variant="outline">Step {currentStep} of {totalSteps}</Badge>
        </div>
        <Progress value={progress} className="w-full" />
        <div className="text-sm text-muted-foreground text-center">
          Estimated time remaining: {onboardingSteps.slice(currentStep - 1).reduce((acc, step) => acc + parseInt(step.estimatedTime), 0)} minutes
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onStepSubmit)}>
        <Card>
          <CardContent className="p-6">
            {currentStep === 1 && renderOrganizationInfo()}
            {currentStep === 2 && renderContactAddress()}
            {/* Additional steps would be implemented here */}
          </CardContent>
        </Card>

        {renderNavigation()}
      </form>
    </div>
  )
}