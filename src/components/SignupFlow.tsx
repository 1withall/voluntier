import { useState } from 'react'
import { UserProfile } from '../types/profiles'
import { IndividualOnboarding } from './onboarding/IndividualOnboarding'
import { OrganizationOnboarding } from './onboarding/OrganizationOnboarding'
import { BusinessOnboarding } from './onboarding/BusinessOnboarding'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { User, Building, Briefcase, Shield, CheckCircle } from '@phosphor-icons/react'

interface SignupFlowProps {
  onSignupComplete: (userData: UserProfile) => void
}

type UserType = 'individual' | 'organization' | 'business'

export function SignupFlow({ onSignupComplete }: SignupFlowProps) {
  const [selectedUserType, setSelectedUserType] = useState<UserType | null>(null)
  const [currentStep, setCurrentStep] = useState<'select' | 'form' | 'verification'>('select')

  const userTypes = [
    {
      type: 'individual' as UserType,
      title: 'Individual Volunteer',
      description: 'Join as a community member looking to volunteer and make a difference',
      icon: User,
      features: [
        'Find volunteer opportunities',
        'Track your impact',
        'Connect with organizations',
        'Skill-based matching'
      ],
      verification: [
        'Personal references (2 required)',
        'In-person QR verification',
        'Background check consent',
        'Identity document upload'
      ]
    },
    {
      type: 'organization' as UserType,
      title: 'Non-Profit Organization',
      description: 'Register your organization to coordinate volunteers and manage events',
      icon: Building,
      features: [
        'Post volunteer opportunities',
        'Manage volunteer applications',
        'Verify individual volunteers',
        'Access impact analytics'
      ],
      verification: [
        'Legal status verification',
        'Leadership team verification',
        'Insurance documentation',
        'Physical facility inspection'
      ]
    },
    {
      type: 'business' as UserType,
      title: 'Corporate Partner',
      description: 'Partner with the community through corporate social responsibility',
      icon: Briefcase,
      features: [
        'Employee volunteer programs',
        'Sponsor community events',
        'Offer skill-based volunteering',
        'Provide training resources'
      ],
      verification: [
        'Business license verification',
        'Financial standing check',
        'CSR policy review',
        'Ethics compliance audit'
      ]
    }
  ]

  const handleUserTypeSelect = (userType: UserType) => {
    setSelectedUserType(userType)
    setCurrentStep('form')
  }

  const handleFormComplete = (userData: any) => {
    setCurrentStep('verification')
    onSignupComplete({
      ...userData,
      userType: selectedUserType,
      verificationStatus: 'pending'
    } as UserProfile)
  }

  const renderUserTypeSelection = () => (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center mb-6">
          <Shield size={48} className="text-primary mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-foreground">Join Voluntier</h1>
            <p className="text-muted-foreground">Choose your account type to get started</p>
          </div>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <Shield size={20} className="text-blue-600 mt-0.5" />
            <div className="text-left">
              <h3 className="font-semibold text-blue-900 mb-1">Security Notice</h3>
              <p className="text-sm text-blue-700">
                All accounts undergo comprehensive verification including identity validation, 
                reference checks, and in-person verification. This process ensures community safety 
                and trust. Only one account per individual or entity is permitted.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {userTypes.map((userType) => {
          const IconComponent = userType.icon
          return (
            <Card 
              key={userType.type}
              className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:border-primary/50"
              onClick={() => handleUserTypeSelect(userType.type)}
            >
              <CardHeader className="text-center">
                <div className="flex justify-center mb-3">
                  <IconComponent size={32} className="text-primary" />
                </div>
                <CardTitle className="text-lg">{userType.title}</CardTitle>
                <CardDescription className="text-sm">
                  {userType.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium text-sm text-foreground mb-2">Features:</h4>
                  <ul className="space-y-1">
                    {userType.features.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <CheckCircle size={12} className="text-green-600" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-sm text-foreground mb-2">Verification Required:</h4>
                  <ul className="space-y-1">
                    {userType.verification.map((item, index) => (
                      <li key={index} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Shield size={12} className="text-blue-600" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <Button className="w-full mt-4">
                  Select {userType.title}
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )

  const renderSignupForm = () => {
    if (!selectedUserType) return null

    const commonProps = {
      onComplete: handleFormComplete,
      onBack: () => {
        setSelectedUserType(null)
        setCurrentStep('select')
      }
    }

    switch (selectedUserType) {
      case 'individual':
        return <IndividualOnboarding {...commonProps} />
      case 'organization':
        return <OrganizationOnboarding {...commonProps} />
      case 'business':
        return <BusinessOnboarding {...commonProps} />
      default:
        return null
    }
  }

  const renderVerificationInstructions = () => (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <CheckCircle size={48} className="text-green-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-foreground mb-2">Account Created Successfully</h1>
        <p className="text-muted-foreground">
          Your account has been created and is now pending verification
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield size={20} />
            Verification Process
          </CardTitle>
          <CardDescription>
            Complete these steps to fully activate your account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
              <Badge variant="secondary">1</Badge>
              <div>
                <p className="font-medium">Document Review</p>
                <p className="text-sm text-muted-foreground">
                  Our security team will review your submitted documents (1-2 business days)
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
              <Badge variant="secondary">2</Badge>
              <div>
                <p className="font-medium">Reference Verification</p>
                <p className="text-sm text-muted-foreground">
                  {selectedUserType === 'individual' 
                    ? 'Your personal references will be contacted for verification'
                    : 'Leadership and organizational verification will be conducted'
                  }
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
              <Badge variant="secondary">3</Badge>
              <div>
                <p className="font-medium">In-Person Verification</p>
                <p className="text-sm text-muted-foreground">
                  {selectedUserType === 'individual'
                    ? 'Visit a verified organization to complete QR code verification'
                    : 'Facility inspection and final verification will be scheduled'
                  }
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-medium text-green-900 mb-2">What happens next?</h4>
            <ul className="text-sm text-green-700 space-y-1">
              <li>• You'll receive email updates on your verification progress</li>
              <li>• Check your dashboard for real-time status updates</li>
              <li>• Verification typically completes within 5-7 business days</li>
              <li>• Contact support if you have questions or need assistance</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      <div className="text-center">
        <Button 
          variant="outline" 
          onClick={() => {
            setCurrentStep('select')
            setSelectedUserType(null)
          }}
        >
          Return to Home
        </Button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4">
        {currentStep === 'select' && renderUserTypeSelection()}
        {currentStep === 'form' && renderSignupForm()}
        {currentStep === 'verification' && renderVerificationInstructions()}
      </div>
    </div>
  )
}