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
import { Building, Shield, Phone, MapPin, Users, Clock, FileText, Warning } from '@phosphor-icons/react'

interface OrganizationSignupFormProps {
  onComplete: (data: any) => void
  onBack: () => void
}

export function OrganizationSignupForm({ onComplete, onBack }: OrganizationSignupFormProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<any>({})
  
  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm()
  
  const totalSteps = 4
  const progress = (currentStep / totalSteps) * 100

  const organizationTypes = [
    { value: 'nonprofit', label: 'Non-Profit Organization' },
    { value: 'government', label: 'Government Agency' },
    { value: 'religious', label: 'Religious Organization' },
    { value: 'educational', label: 'Educational Institution' },
    { value: 'community', label: 'Community Group' }
  ]

  const servicesOffered = [
    'Volunteer Coordination', 'Community Events', 'Educational Programs', 'Healthcare Services',
    'Food Services', 'Housing Assistance', 'Youth Programs', 'Senior Services',
    'Environmental Programs', 'Arts & Culture', 'Emergency Response', 'Other'
  ]

  const targetPopulations = [
    'Children & Youth', 'Seniors', 'Families', 'Individuals with Disabilities',
    'Veterans', 'Homeless Population', 'Low-Income Families', 'Immigrants',
    'General Community', 'Other'
  ]

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

  const onStepSubmit = (data: any) => {
    setFormData(prev => ({ ...prev, ...data }))
    
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    } else {
      // Final submission
      onComplete({
        ...formData,
        ...data,
        userType: 'organization',
        securityScore: 0,
        flagged: false
      })
    }
  }

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Building size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Organization Details</h2>
        <p className="text-muted-foreground">Tell us about your organization</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="organizationName">Organization Name *</Label>
          <Input
            id="organizationName"
            {...register('organizationName', { required: 'Organization name is required' })}
            placeholder="Enter your organization's full legal name"
          />
          {errors.organizationName && (
            <p className="text-sm text-destructive">{errors.organizationName.message?.toString()}</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="organizationType">Organization Type *</Label>
            <Select onValueChange={(value) => setValue('organizationType', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select organization type" />
              </SelectTrigger>
              <SelectContent>
                {organizationTypes.map(type => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.organizationType && (
              <p className="text-sm text-destructive">{errors.organizationType.message?.toString()}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="registrationNumber">Registration Number</Label>
            <Input
              id="registrationNumber"
              {...register('registrationNumber')}
              placeholder="EIN, State Registration, etc."
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="taxExemptStatus">Tax Exempt Status</Label>
          <Input
            id="taxExemptStatus"
            {...register('taxExemptStatus')}
            placeholder="e.g., 501(c)(3), if applicable"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="website">Website</Label>
          <Input
            id="website"
            type="url"
            {...register('website')}
            placeholder="https://your-organization.org"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="mission">Mission Statement *</Label>
          <Textarea
            id="mission"
            {...register('mission', { required: 'Mission statement is required' })}
            placeholder="Describe your organization's mission and purpose"
            rows={3}
          />
          {errors.mission && (
            <p className="text-sm text-destructive">{errors.mission.message?.toString()}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Organization Description *</Label>
          <Textarea
            id="description"
            {...register('description', { required: 'Description is required' })}
            placeholder="Provide a detailed description of your organization's activities and programs"
            rows={4}
          />
          {errors.description && (
            <p className="text-sm text-destructive">{errors.description.message?.toString()}</p>
          )}
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <MapPin size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Location & Contact Information</h2>
        <p className="text-muted-foreground">Where can people find and reach you?</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Organization Address</h3>
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
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Phone size={20} />
            Contact Information
          </h3>
          
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="primaryContactName">Primary Contact Name *</Label>
                <Input
                  id="primaryContactName"
                  {...register('contactInfo.primaryContact.name', { required: 'Primary contact name is required' })}
                  placeholder="Full name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="primaryContactTitle">Title/Position *</Label>
                <Input
                  id="primaryContactTitle"
                  {...register('contactInfo.primaryContact.title', { required: 'Title is required' })}
                  placeholder="e.g., Executive Director, Program Manager"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="primaryContactEmail">Primary Contact Email *</Label>
                <Input
                  id="primaryContactEmail"
                  type="email"
                  {...register('contactInfo.primaryContact.email', { 
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address'
                    }
                  })}
                  placeholder="contact@organization.org"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="primaryContactPhone">Primary Contact Phone *</Label>
                <Input
                  id="primaryContactPhone"
                  type="tel"
                  {...register('contactInfo.primaryContact.phoneNumber', { required: 'Phone number is required' })}
                  placeholder="(555) 123-4567"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="publicEmail">Public Email *</Label>
                <Input
                  id="publicEmail"
                  type="email"
                  {...register('contactInfo.publicEmail', { required: 'Public email is required' })}
                  placeholder="info@organization.org"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="publicPhone">Public Phone *</Label>
                <Input
                  id="publicPhone"
                  type="tel"
                  {...register('contactInfo.publicPhone', { required: 'Public phone is required' })}
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Users size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Services & Operations</h2>
        <p className="text-muted-foreground">What services do you provide?</p>
      </div>

      <div className="space-y-6">
        <div>
          <Label className="text-base font-semibold">Services Offered (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What services does your organization provide?</p>
          <div className="grid gap-2 md:grid-cols-3">
            {servicesOffered.map(service => (
              <div key={service} className="flex items-center space-x-2">
                <Checkbox 
                  id={`service-${service}`}
                  onCheckedChange={(checked) => {
                    const currentServices = watch('servicesOffered') || []
                    if (checked) {
                      setValue('servicesOffered', [...currentServices, service])
                    } else {
                      setValue('servicesOffered', currentServices.filter((s: string) => s !== service))
                    }
                  }}
                />
                <Label htmlFor={`service-${service}`} className="text-sm">{service}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-semibold">Target Population (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">Who does your organization primarily serve?</p>
          <div className="grid gap-2 md:grid-cols-3">
            {targetPopulations.map(population => (
              <div key={population} className="flex items-center space-x-2">
                <Checkbox 
                  id={`population-${population}`}
                  onCheckedChange={(checked) => {
                    const currentPopulations = watch('targetPopulation') || []
                    if (checked) {
                      setValue('targetPopulation', [...currentPopulations, population])
                    } else {
                      setValue('targetPopulation', currentPopulations.filter((p: string) => p !== population))
                    }
                  }}
                />
                <Label htmlFor={`population-${population}`} className="text-sm">{population}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock size={20} />
            Operating Hours
          </h3>
          
          <div className="space-y-3">
            {daysOfWeek.map(day => (
              <div key={day} className="flex items-center gap-4">
                <div className="w-24">
                  <Label className="text-sm font-medium">{day}</Label>
                </div>
                <div className="flex items-center gap-2 flex-1">
                  <Input
                    placeholder="9:00 AM"
                    {...register(`operatingHours.${day}.open`)}
                    className="max-w-32"
                  />
                  <span className="text-muted-foreground">to</span>
                  <Input
                    placeholder="5:00 PM"
                    {...register(`operatingHours.${day}.close`)}
                    className="max-w-32"
                  />
                  <span className="text-sm text-muted-foreground ml-2">
                    (Leave blank if closed)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Organizational Capacity</h3>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="volunteersNeeded">Volunteers Needed Monthly</Label>
              <Input
                id="volunteersNeeded"
                type="number"
                {...register('capacity.volunteersNeeded')}
                placeholder="0"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="eventsPerMonth">Events Per Month</Label>
              <Input
                id="eventsPerMonth"
                type="number"
                {...register('capacity.eventsPerMonth')}
                placeholder="0"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="participantsServed">Participants Served Monthly</Label>
              <Input
                id="participantsServed"
                type="number"
                {...register('capacity.participantsServed')}
                placeholder="0"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep4 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Shield size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Verification & Legal</h2>
        <p className="text-muted-foreground">Complete verification requirements</p>
      </div>

      <Alert>
        <Warning className="h-4 w-4" />
        <AlertDescription>
          Organizations must undergo comprehensive verification including legal status verification, 
          leadership team verification, insurance documentation, and facility inspection before 
          gaining full platform access.
        </AlertDescription>
      </Alert>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Required Documentation</h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox id="articles" />
              <Label htmlFor="articles" className="text-sm">
                Articles of Incorporation / Organizational Charter
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="taxExempt" />
              <Label htmlFor="taxExempt" className="text-sm">
                Tax Exempt Determination Letter (if applicable)
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="insurance" />
              <Label htmlFor="insurance" className="text-sm">
                General Liability Insurance Certificate
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="financials" />
              <Label htmlFor="financials" className="text-sm">
                Recent Financial Statements or Annual Report
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="boardList" />
              <Label htmlFor="boardList" className="text-sm">
                Board of Directors List with Contact Information
              </Label>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Platform Permissions Requested</h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="createEvents"
                {...register('permissions.createEvents')}
              />
              <Label htmlFor="createEvents" className="text-sm">
                Create and manage volunteer events
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="verifyIndividuals"
                {...register('permissions.verifyIndividuals')}
              />
              <Label htmlFor="verifyIndividuals" className="text-sm">
                Verify individual volunteers through QR code scanning
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="postTraining"
                {...register('permissions.postTrainingMaterials')}
              />
              <Label htmlFor="postTraining" className="text-sm">
                Post training materials and resources
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="accessReporting"
                {...register('permissions.accessReporting')}
              />
              <Label htmlFor="accessReporting" className="text-sm">
                Access volunteer analytics and reporting
              </Label>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="backgroundChecks"
              {...register('backgroundCheckPolicy', { required: 'Background check policy is required' })}
            />
            <Label htmlFor="backgroundChecks" className="text-sm">
              Our organization has a background check policy for volunteers in sensitive roles *
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="safetyProtocols"
              {...register('safetyProtocols', { required: 'Safety protocols confirmation is required' })}
            />
            <Label htmlFor="safetyProtocols" className="text-sm">
              We have established safety protocols and emergency procedures *
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
              Our organization agrees to follow the Community Code of Conduct *
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="dataProtection"
              {...register('dataProtectionAgreement', { required: 'Data protection agreement is required' })}
            />
            <Label htmlFor="dataProtection" className="text-sm">
              We agree to protect volunteer data and maintain confidentiality *
            </Label>
          </div>
        </div>

        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Next Steps After Submission</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Document review and verification (3-5 business days)</li>
            <li>• Reference checks with board members and community partners</li>
            <li>• Facility inspection scheduling (if applicable)</li>
            <li>• Final approval and platform access activation</li>
          </ul>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Organization Registration</h1>
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
          
          <Button type="submit">
            {currentStep === totalSteps ? 'Complete Registration' : 'Next Step'}
          </Button>
        </div>
      </form>
    </div>
  )
}