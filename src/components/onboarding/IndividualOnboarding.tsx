import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { IndividualProfile, OnboardingStep, OnboardingProgress } from '../../types/profiles'
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
  User, 
  Shield, 
  Phone, 
  MapPin, 
  Heart, 
  Clock, 
  FileText, 
  Warning,
  CheckCircle,
  Camera,
  Upload,
  Globe,
  Star,
  Trophy
} from '@phosphor-icons/react'

interface IndividualOnboardingProps {
  onComplete: (profile: Partial<IndividualProfile>) => void
  onBack: () => void
  existingProfile?: Partial<IndividualProfile>
}

export function IndividualOnboarding({ onComplete, onBack, existingProfile }: IndividualOnboardingProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [profileData, setProfileData] = useState<Partial<IndividualProfile>>(existingProfile || {})
  const [uploadedDocuments, setUploadedDocuments] = useState<File[]>([])
  
  const { register, handleSubmit, formState: { errors }, watch, setValue, reset } = useForm()

  const onboardingSteps: OnboardingStep[] = [
    {
      id: 'personal-info',
      title: 'Personal Information',
      description: 'Basic details and contact information',
      completed: false,
      required: true,
      order: 1,
      estimatedTime: '5 minutes'
    },
    {
      id: 'address-contact',
      title: 'Address & Emergency Contact',
      description: 'Where you live and emergency contact details',
      completed: false,
      required: true,
      order: 2,
      estimatedTime: '3 minutes'
    },
    {
      id: 'skills-interests',
      title: 'Skills & Interests',
      description: 'Your skills and areas of interest for volunteering',
      completed: false,
      required: true,
      order: 3,
      estimatedTime: '4 minutes'
    },
    {
      id: 'availability',
      title: 'Availability & Preferences',
      description: 'When and how you prefer to volunteer',
      completed: false,
      required: true,
      order: 4,
      estimatedTime: '3 minutes'
    },
    {
      id: 'safety-accessibility',
      title: 'Safety & Accessibility',
      description: 'Medical information and accessibility needs',
      completed: false,
      required: false,
      order: 5,
      estimatedTime: '3 minutes'
    },
    {
      id: 'verification-documents',
      title: 'Verification Documents',
      description: 'Upload required identification and documents',
      completed: false,
      required: true,
      order: 6,
      estimatedTime: '5 minutes'
    },
    {
      id: 'references',
      title: 'Personal References',
      description: 'Provide contacts who can verify your identity',
      completed: false,
      required: true,
      order: 7,
      estimatedTime: '8 minutes'
    },
    {
      id: 'agreements',
      title: 'Agreements & Policies',
      description: 'Review and accept terms, policies, and code of conduct',
      completed: false,
      required: true,
      order: 8,
      estimatedTime: '5 minutes'
    }
  ]

  const totalSteps = onboardingSteps.length
  const progress = (currentStep / totalSteps) * 100

  const skillOptions = [
    'Teaching/Education', 'Healthcare/Medical', 'Construction/Building', 'Technology/IT', 'Arts & Crafts',
    'Cooking/Food Service', 'Gardening/Agriculture', 'Translation/Languages', 'Event Planning', 'Photography',
    'Social Media/Marketing', 'Fundraising', 'Mentoring/Coaching', 'Administrative/Office', 'Legal Services',
    'Accounting/Finance', 'Childcare', 'Elder Care', 'Animal Care', 'Environmental Science',
    'Music/Performance', 'Writing/Journalism', 'Research', 'Project Management', 'Other'
  ]

  const interestOptions = [
    'Children & Youth Development', 'Senior Citizens', 'Animal Welfare', 'Environmental Conservation',
    'Education & Literacy', 'Healthcare & Medical', 'Homelessness & Housing', 'Food Security & Nutrition',
    'Community Development', 'Arts & Culture', 'Sports & Recreation', 'Emergency Response & Disaster Relief',
    'Mental Health Support', 'Disability Services', 'Immigration & Refugee Services', 'Veterans Support',
    'LGBTQ+ Support', 'Racial Equity & Justice', 'Women\'s Empowerment', 'Religious/Faith-based Services',
    'International Development', 'Technology for Good', 'Other'
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
      const completeProfile: Partial<IndividualProfile> = {
        ...profileData,
        ...data,
        userType: 'individual',
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
      'personalInfo.firstName',
      'personalInfo.lastName', 
      'personalInfo.email',
      'personalInfo.phoneNumber',
      'personalInfo.dateOfBirth',
      'address.street',
      'address.city',
      'address.state',
      'address.zipCode',
      'emergencyContact.name',
      'emergencyContact.phoneNumber',
      'preferences.skills',
      'preferences.interests',
      'verification.references'
    ]
    
    let completed = 0
    requiredFields.forEach(field => {
      const value = field.split('.').reduce((obj, key) => obj?.[key], profile)
      if (value && (Array.isArray(value) ? value.length > 0 : true)) {
        completed++
      }
    })
    
    return Math.round((completed / requiredFields.length) * 100)
  }

  const renderPersonalInfo = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <User size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Personal Information</h2>
        <p className="text-muted-foreground">Let's start with your basic details</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="firstName">First Name *</Label>
          <Input
            id="firstName"
            {...register('firstName', { required: 'First name is required' })}
            placeholder="Enter your first name"
          />
          {errors.firstName && (
            <p className="text-sm text-destructive">{String(errors.firstName.message || 'First name is required')}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="lastName">Last Name *</Label>
          <Input
            id="lastName"
            {...register('lastName', { required: 'Last name is required' })}
            placeholder="Enter your last name"
          />
          {errors.lastName && (
            <p className="text-sm text-destructive">{String(errors.lastName.message || 'Last name is required')}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email Address *</Label>
          <Input
            id="email"
            type="email"
            {...register('email', { 
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address'
              }
            })}
            placeholder="your.email@example.com"
          />
          {errors.email && (
            <p className="text-sm text-destructive">{String(errors.email.message || 'Email is required')}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="phoneNumber">Phone Number *</Label>
          <Input
            id="phoneNumber"
            type="tel"
            {...register('phoneNumber', { required: 'Phone number is required' })}
            placeholder="(555) 123-4567"
          />
          {errors.phoneNumber && (
            <p className="text-sm text-destructive">{String(errors.phoneNumber.message || 'Phone number is required')}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="dateOfBirth">Date of Birth *</Label>
          <Input
            id="dateOfBirth"
            type="date"
            {...register('dateOfBirth', { required: 'Date of birth is required' })}
          />
          {errors.dateOfBirth && (
            <p className="text-sm text-destructive">{String(errors.dateOfBirth.message || 'Date of birth is required')}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="gender">Gender (Optional)</Label>
          <Select onValueChange={(value) => setValue('gender', value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select gender" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="female">Female</SelectItem>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="non-binary">Non-binary</SelectItem>
              <SelectItem value="prefer-not-to-say">Prefer not to say</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="pronouns">Pronouns (Optional)</Label>
          <Input
            id="pronouns"
            {...register('pronouns')}
            placeholder="e.g., they/them, she/her, he/him"
          />
        </div>
      </div>
    </div>
  )

  const renderAddressContact = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <MapPin size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Address & Emergency Contact</h2>
        <p className="text-muted-foreground">Where can we reach you?</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Your Address</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="street">Street Address *</Label>
              <Input
                id="street"
                {...register('street', { required: 'Street address is required' })}
                placeholder="123 Main St"
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

        <Separator />

        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Phone size={20} />
            Emergency Contact
          </h3>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="emergencyName">Emergency Contact Name *</Label>
              <Input
                id="emergencyName"
                {...register('emergencyName', { required: 'Emergency contact name is required' })}
                placeholder="Full name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergencyRelationship">Relationship *</Label>
              <Select onValueChange={(value) => setValue('emergencyRelationship', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select relationship" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="spouse">Spouse/Partner</SelectItem>
                  <SelectItem value="parent">Parent</SelectItem>
                  <SelectItem value="sibling">Sibling</SelectItem>
                  <SelectItem value="child">Child</SelectItem>
                  <SelectItem value="friend">Friend</SelectItem>
                  <SelectItem value="relative">Other Relative</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergencyPhone">Emergency Contact Phone *</Label>
              <Input
                id="emergencyPhone"
                type="tel"
                {...register('emergencyPhone', { required: 'Emergency contact phone is required' })}
                placeholder="(555) 123-4567"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergencyEmail">Emergency Contact Email</Label>
              <Input
                id="emergencyEmail"
                type="email"
                {...register('emergencyEmail')}
                placeholder="emergency@example.com"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderSkillsInterests = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Heart size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Skills & Interests</h2>
        <p className="text-muted-foreground">Help us match you with the right opportunities</p>
      </div>

      <div className="space-y-6">
        <div>
          <Label className="text-base font-semibold">Skills (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-4">What skills can you offer to the community?</p>
          <div className="grid gap-3 md:grid-cols-3">
            {skillOptions.map(skill => (
              <div key={skill} className="flex items-center space-x-2">
                <Checkbox 
                  id={`skill-${skill}`}
                  onCheckedChange={(checked) => {
                    const currentSkills = watch('skills') || []
                    if (checked) {
                      setValue('skills', [...currentSkills, skill])
                    } else {
                      setValue('skills', currentSkills.filter((s: string) => s !== skill))
                    }
                  }}
                />
                <Label htmlFor={`skill-${skill}`} className="text-sm leading-relaxed">{skill}</Label>
              </div>
            ))}
          </div>
        </div>

        <Separator />

        <div>
          <Label className="text-base font-semibold">Areas of Interest (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-4">What causes are you passionate about?</p>
          <div className="grid gap-3 md:grid-cols-2">
            {interestOptions.map(interest => (
              <div key={interest} className="flex items-center space-x-2">
                <Checkbox 
                  id={`interest-${interest}`}
                  onCheckedChange={(checked) => {
                    const currentInterests = watch('interests') || []
                    if (checked) {
                      setValue('interests', [...currentInterests, interest])
                    } else {
                      setValue('interests', currentInterests.filter((i: string) => i !== interest))
                    }
                  }}
                />
                <Label htmlFor={`interest-${interest}`} className="text-sm leading-relaxed">{interest}</Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  // Continue with remaining render methods...
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
            <h1 className="text-2xl font-bold">Individual Volunteer Onboarding</h1>
            <p className="text-muted-foreground">Complete your profile to start volunteering</p>
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
            {currentStep === 1 && renderPersonalInfo()}
            {currentStep === 2 && renderAddressContact()}
            {currentStep === 3 && renderSkillsInterests()}
            {/* Additional steps would be implemented here */}
          </CardContent>
        </Card>

        {renderNavigation()}
      </form>
    </div>
  )
}