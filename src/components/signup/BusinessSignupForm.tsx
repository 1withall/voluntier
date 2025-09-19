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
import { Briefcase, Shield, Phone, MapPin, TrendUp, Handshake, FileText, Warning } from '@phosphor-icons/react'

interface BusinessSignupFormProps {
  onComplete: (data: any) => void
  onBack: () => void
}

export function BusinessSignupForm({ onComplete, onBack }: BusinessSignupFormProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<any>({})
  
  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm()
  
  const totalSteps = 4
  const progress = (currentStep / totalSteps) * 100

  const businessTypes = [
    { value: 'corporation', label: 'Corporation' },
    { value: 'llc', label: 'Limited Liability Company (LLC)' },
    { value: 'partnership', label: 'Partnership' },
    { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
    { value: 'other', label: 'Other' }
  ]

  const industries = [
    'Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing',
    'Construction', 'Real Estate', 'Professional Services', 'Education',
    'Hospitality', 'Transportation', 'Energy', 'Agriculture', 'Media',
    'Non-Profit', 'Government', 'Other'
  ]

  const csrFocusAreas = [
    'Education', 'Environmental Sustainability', 'Community Development',
    'Healthcare', 'Poverty Alleviation', 'Youth Development', 'Senior Care',
    'Arts & Culture', 'Technology Access', 'Disaster Relief', 'Other'
  ]

  const volunteerPrograms = [
    'Team Building Events', 'Skills-Based Volunteering', 'Board Service',
    'Pro Bono Services', 'Mentoring Programs', 'Community Cleanups',
    'Fundraising Events', 'Food Drives', 'Educational Workshops', 'Other'
  ]

  const skillBasedOfferings = [
    'Legal Services', 'Accounting/Finance', 'Marketing', 'IT Support',
    'Web Development', 'Graphic Design', 'Project Management',
    'Training & Development', 'Strategic Planning', 'Other'
  ]

  const onStepSubmit = (data: any) => {
    setFormData(prev => ({ ...prev, ...data }))
    
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    } else {
      // Final submission
      onComplete({
        ...formData,
        ...data,
        userType: 'business',
        securityScore: 0,
        flagged: false
      })
    }
  }

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Briefcase size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Business Information</h2>
        <p className="text-muted-foreground">Tell us about your business</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="businessName">Business Name *</Label>
          <Input
            id="businessName"
            {...register('businessName', { required: 'Business name is required' })}
            placeholder="Enter your business's full legal name"
          />
          {errors.businessName && (
            <p className="text-sm text-destructive">{errors.businessName.message?.toString()}</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="businessType">Business Type *</Label>
            <Select onValueChange={(value) => setValue('businessType', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select business type" />
              </SelectTrigger>
              <SelectContent>
                {businessTypes.map(type => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.businessType && (
              <p className="text-sm text-destructive">{errors.businessType.message?.toString()}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="industry">Industry *</Label>
            <Select onValueChange={(value) => setValue('industry', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select your industry" />
              </SelectTrigger>
              <SelectContent>
                {industries.map(industry => (
                  <SelectItem key={industry} value={industry}>
                    {industry}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.industry && (
              <p className="text-sm text-destructive">{errors.industry.message?.toString()}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="registrationNumber">Business Registration Number *</Label>
            <Input
              id="registrationNumber"
              {...register('registrationNumber', { required: 'Registration number is required' })}
              placeholder="State registration number"
            />
            {errors.registrationNumber && (
              <p className="text-sm text-destructive">{errors.registrationNumber.message?.toString()}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="taxId">Tax ID / EIN *</Label>
            <Input
              id="taxId"
              {...register('taxId', { required: 'Tax ID is required' })}
              placeholder="Federal Tax ID / EIN"
            />
            {errors.taxId && (
              <p className="text-sm text-destructive">{errors.taxId.message?.toString()}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="website">Company Website</Label>
          <Input
            id="website"
            type="url"
            {...register('website')}
            placeholder="https://your-company.com"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Business Description *</Label>
          <Textarea
            id="description"
            {...register('description', { required: 'Business description is required' })}
            placeholder="Describe your business, its products/services, and market presence"
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
          <h3 className="text-lg font-semibold mb-4">Business Address</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="street">Street Address *</Label>
              <Input
                id="street"
                {...register('address.street', { required: 'Street address is required' })}
                placeholder="123 Business Way"
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
                  placeholder="e.g., CEO, CSR Director, Community Relations"
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
                  placeholder="contact@company.com"
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
                  placeholder="community@company.com"
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
        <TrendUp size={32} className="text-primary mx-auto" />
        <h2 className="text-2xl font-bold">Corporate Social Responsibility</h2>
        <p className="text-muted-foreground">Share your CSR goals and community involvement plans</p>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">CSR Program Overview</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="csrDescription">CSR Program Description *</Label>
              <Textarea
                id="csrDescription"
                {...register('csrProgram.description', { required: 'CSR description is required' })}
                placeholder="Describe your corporate social responsibility initiatives and community involvement goals"
                rows={3}
              />
              {(errors as any)?.csrProgram?.description && (
                <p className="text-sm text-destructive">{(errors as any).csrProgram.description.message?.toString()}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="csrBudget">Annual CSR Budget (USD)</Label>
              <Input
                id="csrBudget"
                type="number"
                {...register('csrProgram.budget')}
                placeholder="50000"
              />
              <p className="text-xs text-muted-foreground">
                Optional: This helps us understand the scale of your community involvement
              </p>
            </div>
          </div>
        </div>

        <div>
          <Label className="text-base font-semibold">CSR Focus Areas (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What areas does your CSR program focus on?</p>
          <div className="grid gap-2 md:grid-cols-3">
            {csrFocusAreas.map(area => (
              <div key={area} className="flex items-center space-x-2">
                <Checkbox 
                  id={`csr-${area}`}
                  onCheckedChange={(checked) => {
                    const currentAreas = watch('csrProgram.focusAreas') || []
                    if (checked) {
                      setValue('csrProgram.focusAreas', [...currentAreas, area])
                    } else {
                      setValue('csrProgram.focusAreas', currentAreas.filter((a: string) => a !== area))
                    }
                  }}
                />
                <Label htmlFor={`csr-${area}`} className="text-sm">{area}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-semibold">Volunteer Programs (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What volunteer opportunities can you offer?</p>
          <div className="grid gap-2 md:grid-cols-2">
            {volunteerPrograms.map(program => (
              <div key={program} className="flex items-center space-x-2">
                <Checkbox 
                  id={`volunteer-${program}`}
                  onCheckedChange={(checked) => {
                    const currentPrograms = watch('offerings.volunteerPrograms') || []
                    if (checked) {
                      setValue('offerings.volunteerPrograms', [...currentPrograms, program])
                    } else {
                      setValue('offerings.volunteerPrograms', currentPrograms.filter((p: string) => p !== program))
                    }
                  }}
                />
                <Label htmlFor={`volunteer-${program}`} className="text-sm">{program}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label className="text-base font-semibold">Skill-Based Volunteering (Select all that apply)</Label>
          <p className="text-sm text-muted-foreground mb-3">What professional skills can your employees offer?</p>
          <div className="grid gap-2 md:grid-cols-2">
            {skillBasedOfferings.map(skill => (
              <div key={skill} className="flex items-center space-x-2">
                <Checkbox 
                  id={`skill-${skill}`}
                  onCheckedChange={(checked) => {
                    const currentSkills = watch('offerings.skillBasedVolunteering') || []
                    if (checked) {
                      setValue('offerings.skillBasedVolunteering', [...currentSkills, skill])
                    } else {
                      setValue('offerings.skillBasedVolunteering', currentSkills.filter((s: string) => s !== skill))
                    }
                  }}
                />
                <Label htmlFor={`skill-${skill}`} className="text-sm">{skill}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Employee Volunteering Program</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="paidVolunteerTime"
                {...register('employeeVolunteering.paidVolunteerTime')}
              />
              <Label htmlFor="paidVolunteerTime" className="text-sm">
                We offer paid volunteer time for employees
              </Label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="hoursPerEmployee">Volunteer Hours per Employee (Annual)</Label>
                <Input
                  id="hoursPerEmployee"
                  type="number"
                  {...register('employeeVolunteering.hoursPerEmployee')}
                  placeholder="40"
                />
              </div>

              <div className="flex items-center space-x-2 pt-6">
                <Checkbox 
                  id="teamBuilding"
                  {...register('employeeVolunteering.teamBuilding')}
                />
                <Label htmlFor="teamBuilding" className="text-sm">
                  Include volunteer activities in team building
                </Label>
              </div>
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
        <h2 className="text-2xl font-bold">Verification & Permissions</h2>
        <p className="text-muted-foreground">Complete verification requirements</p>
      </div>

      <Alert>
        <Warning className="h-4 w-4" />
        <AlertDescription>
          Business partners must undergo comprehensive verification including business license verification, 
          financial standing checks, leadership verification, and ethics compliance review before 
          gaining full platform access.
        </AlertDescription>
      </Alert>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Required Documentation</h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox id="businessLicense" />
              <Label htmlFor="businessLicense" className="text-sm">
                Business License and Registration Documents
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="taxDocuments" />
              <Label htmlFor="taxDocuments" className="text-sm">
                Tax Registration and Compliance Documents
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="insuranceCert" />
              <Label htmlFor="insuranceCert" className="text-sm">
                General Liability Insurance Certificate
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="financialStatements" />
              <Label htmlFor="financialStatements" className="text-sm">
                Recent Financial Statements or Annual Report
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="csrPolicy" />
              <Label htmlFor="csrPolicy" className="text-sm">
                Corporate Social Responsibility Policy Document
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox id="leadership" />
              <Label htmlFor="leadership" className="text-sm">
                Leadership Team Information and Verification
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
                Create and manage volunteer events and initiatives
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="sponsorEvents"
                {...register('permissions.sponsorEvents')}
              />
              <Label htmlFor="sponsorEvents" className="text-sm">
                Sponsor community events and provide funding
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="postTraining"
                {...register('permissions.postTrainingMaterials')}
              />
              <Label htmlFor="postTraining" className="text-sm">
                Post training materials and professional development resources
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="accessReporting"
                {...register('permissions.accessReporting')}
              />
              <Label htmlFor="accessReporting" className="text-sm">
                Access community impact analytics and reporting
              </Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="offerInternships"
                {...register('permissions.offerInternships')}
              />
              <Label htmlFor="offerInternships" className="text-sm">
                Offer internships and professional development opportunities
              </Label>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="ethicsCompliance"
              {...register('ethicsCompliance', { required: 'Ethics compliance is required' })}
            />
            <Label htmlFor="ethicsCompliance" className="text-sm">
              Our business operates in compliance with all applicable laws and ethical standards *
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="volunteerSafety"
              {...register('volunteerSafety', { required: 'Volunteer safety commitment is required' })}
            />
            <Label htmlFor="volunteerSafety" className="text-sm">
              We commit to providing safe environments for all volunteer activities *
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
              Our business agrees to follow the Community Code of Conduct *
            </Label>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="dataProtection"
              {...register('dataProtectionAgreement', { required: 'Data protection agreement is required' })}
            />
            <Label htmlFor="dataProtection" className="text-sm">
              We agree to protect community data and maintain confidentiality *
            </Label>
          </div>
        </div>

        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Next Steps After Submission</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Business documentation review and verification (3-5 business days)</li>
            <li>• Financial standing and compliance checks</li>
            <li>• Leadership team verification and reference checks</li>
            <li>• Ethics and CSR policy review</li>
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
          <h1 className="text-2xl font-bold">Business Partner Registration</h1>
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