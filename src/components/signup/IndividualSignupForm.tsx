import { useState } from 'react'
import { useForm } from 'react-hook-form'
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
import { User, Shield, Phone, MapPin, Heart, Clock, FileText, Warning } from '@phosphor-icons/react'
import { PersonalReference } from '../../types/auth'

interface IndividualSignupFormProps {
  onComplete: (data: any) => void
  onBack: () => void
}

export function IndividualSignupForm({ onComplete, onBack }: IndividualSignupFormProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [references, setReferences] = useState<PersonalReference[]>([])
  const [formData, setFormData] = useState<any>({})
  
  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm()
  
  const totalSteps = 5
  const progress = (currentStep / totalSteps) * 100

  const availabilityDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  const timeSlots = ['Morning (6AM-12PM)', 'Afternoon (12PM-6PM)', 'Evening (6PM-10PM)', 'Flexible']
  
  const skillOptions = [
    'Teaching/Education', 'Healthcare', 'Construction', 'Technology', 'Arts & Crafts',
    'Cooking', 'Gardening', 'Translation', 'Event Planning', 'Photography',
    'Social Media', 'Fundraising', 'Mentoring', 'Administrative', 'Other'
  ]

  const interestOptions = [
    'Children & Youth', 'Seniors', 'Animals', 'Environment', 'Education',
    'Healthcare', 'Homelessness', 'Food Security', 'Community Development',
    'Arts & Culture', 'Sports & Recreation', 'Emergency Response', 'Other'
  ]

  const addReference = () => {
    if (references.length < 3) {
      setReferences([...references, {
        id: Date.now().toString(),
        name: '',
        relationship: '',
        email: '',
        phoneNumber: '',
        yearsKnown: 0,
        verificationStatus: 'pending'
      }])
    }
  }

  const updateReference = (id: string, field: string, value: any) => {
    setReferences(refs => refs.map(ref => 
      ref.id === id ? { ...ref, [field]: value } : ref
    ))
  }

  const removeReference = (id: string) => {
    setReferences(refs => refs.filter(ref => ref.id !== id))
  }

  const onStepSubmit = (data: any) => {
    setFormData(prev => ({ ...prev, ...data, references }))
    
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    } else {
      // Final submission
      onComplete({
        ...formData,
        ...data,
        references,
        userType: 'individual',
        securityScore: 0,
        flagged: false
      })
    }
  }

  const renderStep1 = () => (
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
            <p className="text-sm text-destructive">{errors.firstName.message?.toString()}</p>
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
            <p className="text-sm text-destructive">{errors.lastName.message?.toString()}</p>
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
            <p className="text-sm text-destructive">{errors.email.message?.toString()}</p>
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
            <p className="text-sm text-destructive">{errors.phoneNumber.message?.toString()}</p>
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
            <p className="text-sm text-destructive">{errors.dateOfBirth.message?.toString()}</p>
          )}
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <MapPin size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Address & Contact</h2>
        <p className="text-muted-foreground">Where can we reach you?</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="street">Street Address *</Label>
          <Input
            id="street"
            {...register('address.street', { required: 'Street address is required' })}
            placeholder="123 Main St"
          />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="city">City *</Label>
            <Input
              id="city"
              {...register('address.city', { required: 'City is required' })}
              placeholder="City"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="state">State *</Label>
            <Input
              id="state"
              {...register('address.state', { required: 'State is required' })}
              placeholder="ST"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="zipCode">ZIP Code *</Label>
            <Input
              id="zipCode"
              {...register('address.zipCode', { required: 'ZIP code is required' })}
              placeholder="12345"
            />
          </div>
        </div>

        <h3 className="text-lg font-semibold mt-6 mb-4 flex items-center gap-2">
          <Phone size={20} />
          Emergency Contact
        </h3>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="emergencyName">Emergency Contact Name *</Label>
            <Input
              id="emergencyName"
              {...register('emergencyContact.name', { required: 'Emergency contact name is required' })}
              placeholder="Full name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="emergencyRelationship">Relationship *</Label>
            <Select onValueChange={(value) => setValue('emergencyContact.relationship', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select relationship" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="spouse">Spouse</SelectItem>
                <SelectItem value="parent">Parent</SelectItem>
                <SelectItem value="sibling">Sibling</SelectItem>
                <SelectItem value="child">Child</SelectItem>
                <SelectItem value="friend">Friend</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="emergencyPhone">Emergency Contact Phone *</Label>
            <Input
              id="emergencyPhone"
              type="tel"
              {...register('emergencyContact.phoneNumber', { required: 'Emergency contact phone is required' })}
              placeholder="(555) 123-4567"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="emergencyEmail">Emergency Contact Email</Label>
            <Input
              id="emergencyEmail"
              type="email"
              {...register('emergencyContact.email')}
              placeholder="emergency@example.com"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Heart size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Skills & Interests</h2>
        <p className="text-muted-foreground">Help us match you with the right opportunities</p>
      </div>

      <div className="space-y-6">
        <div>
          <Label className="text-base font-semibold">Skills (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What skills can you offer to the community?</p>
          <div className="grid gap-2 md:grid-cols-3">
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
                <Label htmlFor={`skill-${skill}`} className="text-sm">{skill}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-semibold">Areas of Interest (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What causes are you passionate about?</p>
          <div className="grid gap-2 md:grid-cols-3">
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
                <Label htmlFor={`interest-${interest}`} className="text-sm">{interest}</Label>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep4 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Clock size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Availability</h2>
        <p className="text-muted-foreground">When are you available to volunteer?</p>
      </div>

      <div className="space-y-6">
        <div>
          <Label className="text-base font-semibold">Available Days (Select all that apply)</Label>
          <div className="grid gap-2 md:grid-cols-4 mt-3">
            {availabilityDays.map(day => (
              <div key={day} className="flex items-center space-x-2">
                <Checkbox 
                  id={`day-${day}`}
                  onCheckedChange={(checked) => {
                    const currentDays = watch('availability.days') || []
                    if (checked) {
                      setValue('availability.days', [...currentDays, day])
                    } else {
                      setValue('availability.days', currentDays.filter((d: string) => d !== day))
                    }
                  }}
                />
                <Label htmlFor={`day-${day}`} className="text-sm">{day}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-semibold">Preferred Time Slots (Select all that apply)</Label>
          <div className="grid gap-2 md:grid-cols-2 mt-3">
            {timeSlots.map(slot => (
              <div key={slot} className="flex items-center space-x-2">
                <Checkbox 
                  id={`slot-${slot}`}
                  onCheckedChange={(checked) => {
                    const currentSlots = watch('availability.timeSlots') || []
                    if (checked) {
                      setValue('availability.timeSlots', [...currentSlots, slot])
                    } else {
                      setValue('availability.timeSlots', currentSlots.filter((s: string) => s !== slot))
                    }
                  }}
                />
                <Label htmlFor={`slot-${slot}`} className="text-sm">{slot}</Label>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="hoursPerWeek">Hours per week you can volunteer</Label>
          <Select onValueChange={(value) => setValue('availability.hoursPerWeek', parseInt(value))}>
            <SelectTrigger>
              <SelectValue placeholder="Select hours per week" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">1-2 hours</SelectItem>
              <SelectItem value="3">3-5 hours</SelectItem>
              <SelectItem value="6">6-10 hours</SelectItem>
              <SelectItem value="11">11-15 hours</SelectItem>
              <SelectItem value="16">16+ hours</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  )

  const renderStep5 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Shield size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">References & Verification</h2>
        <p className="text-muted-foreground">Provide references to help verify your identity</p>
      </div>

      <Alert>
        <Warning className="h-4 w-4" />
        <AlertDescription>
          You must provide at least 2 personal references who have known you for at least 1 year. 
          References cannot be family members and will be contacted for verification.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Personal References ({references.length}/3)</h3>
          {references.length < 3 && (
            <Button type="button" variant="outline" onClick={addReference}>
              Add Reference
            </Button>
          )}
        </div>

        {references.map((reference, index) => (
          <Card key={reference.id}>
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                Reference {index + 1}
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => removeReference(reference.id)}
                >
                  Remove
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Full Name *</Label>
                  <Input
                    value={reference.name}
                    onChange={(e) => updateReference(reference.id, 'name', e.target.value)}
                    placeholder="Reference full name"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Relationship *</Label>
                  <Input
                    value={reference.relationship}
                    onChange={(e) => updateReference(reference.id, 'relationship', e.target.value)}
                    placeholder="e.g., Former colleague, Teacher, Coach"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Email Address *</Label>
                  <Input
                    type="email"
                    value={reference.email}
                    onChange={(e) => updateReference(reference.id, 'email', e.target.value)}
                    placeholder="reference@example.com"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Phone Number *</Label>
                  <Input
                    type="tel"
                    value={reference.phoneNumber}
                    onChange={(e) => updateReference(reference.id, 'phoneNumber', e.target.value)}
                    placeholder="(555) 123-4567"
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label>Years Known *</Label>
                  <Select onValueChange={(value) => updateReference(reference.id, 'yearsKnown', parseInt(value))}>
                    <SelectTrigger>
                      <SelectValue placeholder="How long have they known you?" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1-2 years</SelectItem>
                      <SelectItem value="3">3-5 years</SelectItem>
                      <SelectItem value="6">6-10 years</SelectItem>
                      <SelectItem value="11">11+ years</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {references.length < 2 && (
          <Alert>
            <Warning className="h-4 w-4" />
            <AlertDescription>
              You need at least 2 references to proceed. Please add more references above.
            </AlertDescription>
          </Alert>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox 
            id="backgroundCheck"
            {...register('backgroundCheckConsent', { required: 'Background check consent is required' })}
          />
          <Label htmlFor="backgroundCheck" className="text-sm">
            I consent to a background check as part of the verification process *
          </Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox 
            id="terms"
            {...register('termsAccepted', { required: 'Terms acceptance is required' })}
          />
          <Label htmlFor="terms" className="text-sm">
            I agree to the Terms of Service and Privacy Policy *
          </Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox 
            id="codeOfConduct"
            {...register('codeOfConductAccepted', { required: 'Code of conduct acceptance is required' })}
          />
          <Label htmlFor="codeOfConduct" className="text-sm">
            I agree to follow the Community Code of Conduct *
          </Label>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Individual Volunteer Registration</h1>
          <Badge variant="outline">Step {currentStep} of {totalSteps}</Badge>
        </div>
        <Progress value={progress} className="w-full" />
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onStepSubmit)}>
        <Card>
          <CardContent className="p-6">
            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
            {currentStep === 4 && renderStep4()}
            {currentStep === 5 && renderStep5()}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <Button 
            type="button" 
            variant="outline" 
            onClick={currentStep === 1 ? onBack : () => setCurrentStep(currentStep - 1)}
          >
            {currentStep === 1 ? 'Back to Selection' : 'Previous'}
          </Button>
          
          <Button 
            type="submit"
            disabled={currentStep === 5 && references.length < 2}
          >
            {currentStep === totalSteps ? 'Complete Registration' : 'Next Step'}
          </Button>
        </div>
      </form>
    </div>
  )
}