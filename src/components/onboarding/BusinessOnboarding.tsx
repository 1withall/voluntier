import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { BusinessProfile, OnboardingStep } from '../../types/profiles'
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
  Briefcase, 
  Shield, 
  Phone, 
  MapPin, 
  Users, 
  FileText, 
  Warning,
  CheckCircle,
  Upload,
  Globe,
  HandHeart,
  Star
} from '@phosphor-icons/react'

interface BusinessOnboardingProps {
  onComplete: (profile: Partial<BusinessProfile>) => void
  onBack: () => void
  existingProfile?: Partial<BusinessProfile>
}

export function BusinessOnboarding({ onComplete, onBack, existingProfile }: BusinessOnboardingProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [profileData, setProfileData] = useState<Partial<BusinessProfile>>(existingProfile || {})
  
  const { register, handleSubmit, formState: { errors }, watch, setValue, reset } = useForm()

  const onboardingSteps: OnboardingStep[] = [
    {
      id: 'business-info',
      title: 'Business Information',
      description: 'Basic details about your business',
      completed: false,
      required: true,
      order: 1,
      estimatedTime: '8 minutes'
    },
    {
      id: 'contact-address',
      title: 'Contact & Address',
      description: 'How people can reach your business',
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
      estimatedTime: '8 minutes'
    },
    {
      id: 'csr-program',
      title: 'Corporate Social Responsibility',
      description: 'Your CSR program and community involvement',
      completed: false,
      required: true,
      order: 4,
      estimatedTime: '10 minutes'
    },
    {
      id: 'offerings-capabilities',
      title: 'Offerings & Capabilities',
      description: 'What you can offer to the community',
      completed: false,
      required: true,
      order: 5,
      estimatedTime: '8 minutes'
    },
    {
      id: 'verification-docs',
      title: 'Business Verification',
      description: 'Upload required business and financial documents',
      completed: false,
      required: true,
      order: 6,
      estimatedTime: '10 minutes'
    },
    {
      id: 'agreements',
      title: 'Partnership Agreements',
      description: 'Review and accept partnership terms and ethics code',
      completed: false,
      required: true,
      order: 7,
      estimatedTime: '5 minutes'
    }
  ]

  const totalSteps = onboardingSteps.length
  const progress = (currentStep / totalSteps) * 100

  const businessTypes = [
    'corporation',
    'llc',
    'partnership',
    'sole_proprietorship',
    'other'
  ]

  const industries = [
    'Technology',
    'Healthcare',
    'Finance',
    'Manufacturing',
    'Retail',
    'Professional Services',
    'Construction',
    'Education',
    'Real Estate',
    'Transportation',
    'Energy',
    'Media & Entertainment',
    'Agriculture',
    'Other'
  ]

  const csrFocusAreas = [
    'Education & Literacy',
    'Environmental Sustainability',
    'Healthcare & Wellness',
    'Economic Development',
    'Youth Development',
    'Senior Services',
    'Arts & Culture',
    'Technology Access',
    'Food Security',
    'Housing & Homelessness',
    'Disaster Relief',
    'Veterans Support',
    'Diversity & Inclusion',
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
      const completeProfile: Partial<BusinessProfile> = {
        ...profileData,
        ...data,
        userType: 'business',
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
      'businessType',
      'industry',
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

  const renderBusinessInfo = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Briefcase size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Business Information</h2>
        <p className="text-muted-foreground">Tell us about your business</p>
      </div>

      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="legalName">Legal Business Name *</Label>
            <Input
              id="legalName"
              {...register('legalName', { required: 'Legal name is required' })}
              placeholder="Official registered business name"
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
            <Label htmlFor="businessType">Business Type *</Label>
            <Select onValueChange={(value) => setValue('businessType', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select business type" />
              </SelectTrigger>
              <SelectContent>
                {businessTypes.map(type => (
                  <SelectItem key={type} value={type}>
                    {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="industry">Industry *</Label>
            <Select onValueChange={(value) => setValue('industry', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select industry" />
              </SelectTrigger>
              <SelectContent>
                {industries.map(industry => (
                  <SelectItem key={industry} value={industry}>
                    {industry}
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
            <Label htmlFor="website">Company Website</Label>
            <Input
              id="website"
              type="url"
              {...register('website')}
              placeholder="https://www.yourcompany.com"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Business Description *</Label>
          <Textarea
            id="description"
            {...register('description', { required: 'Business description is required' })}
            placeholder="Describe your business, products, services, and market focus..."
            rows={4}
          />
          {errors.description && (
            <p className="text-sm text-destructive">{String(errors.description.message || 'Business description is required')}</p>
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
                <SelectItem value="1-10">1-10 employees</SelectItem>
                <SelectItem value="11-50">11-50 employees</SelectItem>
                <SelectItem value="51-100">51-100 employees</SelectItem>
                <SelectItem value="101-500">101-500 employees</SelectItem>
                <SelectItem value="501-1000">501-1000 employees</SelectItem>
                <SelectItem value="1000+">1000+ employees</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="annualRevenue">Annual Revenue</Label>
            <Select onValueChange={(value) => setValue('annualRevenue', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select revenue range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="under-1m">Under $1M</SelectItem>
                <SelectItem value="1m-5m">$1M - $5M</SelectItem>
                <SelectItem value="5m-10m">$5M - $10M</SelectItem>
                <SelectItem value="10m-50m">$10M - $50M</SelectItem>
                <SelectItem value="50m-100m">$50M - $100M</SelectItem>
                <SelectItem value="100m+">$100M+</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  )

  const renderCSRProgram = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <HandHeart size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Corporate Social Responsibility</h2>
        <p className="text-muted-foreground">Tell us about your community involvement</p>
      </div>

      <div className="space-y-6">
        <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg">
          <Checkbox 
            id="hasCSRProgram"
            onCheckedChange={(checked) => setValue('hasEstablishedProgram', checked)}
          />
          <div>
            <Label htmlFor="hasCSRProgram" className="font-medium">
              We have an established CSR program
            </Label>
            <p className="text-sm text-muted-foreground">
              Check if your company has formal corporate social responsibility initiatives
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="programDescription">CSR Program Description</Label>
          <Textarea
            id="programDescription"
            {...register('programDescription')}
            placeholder="Describe your current CSR initiatives, community partnerships, and social impact goals..."
            rows={4}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="annualCSRBudget">Annual CSR Budget</Label>
            <Select onValueChange={(value) => setValue('annualCSRBudget', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select budget range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="under-10k">Under $10,000</SelectItem>
                <SelectItem value="10k-25k">$10,000 - $25,000</SelectItem>
                <SelectItem value="25k-50k">$25,000 - $50,000</SelectItem>
                <SelectItem value="50k-100k">$50,000 - $100,000</SelectItem>
                <SelectItem value="100k-250k">$100,000 - $250,000</SelectItem>
                <SelectItem value="250k+">$250,000+</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="hoursPerEmployee">Volunteer Hours per Employee (annually)</Label>
            <Select onValueChange={(value) => setValue('hoursPerEmployee', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select hours range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">No formal program</SelectItem>
                <SelectItem value="1-8">1-8 hours</SelectItem>
                <SelectItem value="9-16">9-16 hours</SelectItem>
                <SelectItem value="17-24">17-24 hours</SelectItem>
                <SelectItem value="25-40">25-40 hours</SelectItem>
                <SelectItem value="40+">40+ hours</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Checkbox 
            id="paidVolunteerTime"
            onCheckedChange={(checked) => setValue('paidVolunteerTime', checked)}
          />
          <Label htmlFor="paidVolunteerTime" className="text-sm">
            We provide paid time off for employee volunteer work
          </Label>
        </div>

        <div>
          <Label className="text-base font-semibold">CSR Focus Areas (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What causes does your company prioritize?</p>
          <div className="grid gap-3 md:grid-cols-2">
            {csrFocusAreas.map(area => (
              <div key={area} className="flex items-center space-x-2">
                <Checkbox 
                  id={`csr-${area}`}
                  onCheckedChange={(checked) => {
                    const currentAreas = watch('focusAreas') || []
                    if (checked) {
                      setValue('focusAreas', [...currentAreas, area])
                    } else {
                      setValue('focusAreas', currentAreas.filter((a: string) => a !== area))
                    }
                  }}
                />
                <Label htmlFor={`csr-${area}`} className="text-sm leading-relaxed">{area}</Label>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="partnershipHistory">Previous Community Partnerships</Label>
          <Textarea
            id="partnershipHistory"
            {...register('partnershipHistory')}
            placeholder="List any previous partnerships with nonprofits, community organizations, or volunteer programs..."
            rows={3}
          />
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
            <h1 className="text-2xl font-bold">Business Partnership Registration</h1>
            <p className="text-muted-foreground">Join as a corporate community partner</p>
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
            {currentStep === 1 && renderBusinessInfo()}
            {currentStep === 4 && renderCSRProgram()}
            {/* Additional steps would be implemented here */}
          </CardContent>
        </Card>

        {renderNavigation()}
      </form>
    </div>
  )
}