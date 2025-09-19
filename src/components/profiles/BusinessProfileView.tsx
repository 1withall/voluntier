import { useState } from 'react'
import { BusinessProfile } from '../../types/profiles'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Separator } from '../ui/separator'
import { 
  Briefcase, 
  Shield, 
  Phone, 
  MapPin, 
  Users, 
  PencilSimple,
  Envelope,
  Globe,
  HandHeart,
  Star,
  TrendUp,
  CheckCircle
} from '@phosphor-icons/react'

interface BusinessProfileViewProps {
  profile: BusinessProfile
  onUpdate: (updatedProfile: BusinessProfile) => void
}

export function BusinessProfileView({ profile, onUpdate }: BusinessProfileViewProps) {
  const [isEditing, setIsEditing] = useState(false)

  const getVerificationStatusColor = (status: string) => {
    switch (status) {
      case 'verified': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      case 'suspended': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            {profile.businessInfo?.legalName}
          </h1>
          <p className="text-muted-foreground">
            Corporate Partner - {profile.businessInfo?.industry}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge 
            className={getVerificationStatusColor(profile.verificationStatus)}
            variant="secondary"
          >
            <Shield size={14} className="mr-1" />
            {profile.verificationStatus.replace('_', ' ').toUpperCase()}
          </Badge>
          <Button variant="outline" onClick={() => setIsEditing(!isEditing)}>
            <PencilSimple size={16} className="mr-2" />
            {isEditing ? 'Cancel' : 'Edit Profile'}
          </Button>
        </div>
      </div>

      {/* Profile Completeness */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase size={20} />
            Profile Completion
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Profile Completeness</span>
              <span className="text-sm text-muted-foreground">{profile.profileCompleteness}%</span>
            </div>
            <Progress value={profile.profileCompleteness} className="w-full" />
            {profile.profileCompleteness < 100 && (
              <p className="text-sm text-muted-foreground">
                Complete your business profile to unlock all partnership features.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Business Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase size={20} />
              Business Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">EIN:</p>
              <p className="text-sm text-muted-foreground">{profile.businessInfo?.ein}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Business Type:</p>
              <p className="text-sm text-muted-foreground">
                {profile.businessInfo?.businessType?.replace('_', ' ').toUpperCase()}
              </p>
            </div>
            {profile.businessInfo?.dbaName && (
              <div>
                <p className="text-sm font-medium">DBA Name:</p>
                <p className="text-sm text-muted-foreground">{profile.businessInfo.dbaName}</p>
              </div>
            )}
            <div>
              <p className="text-sm font-medium">Founded:</p>
              <p className="text-sm text-muted-foreground">{profile.businessInfo?.foundedYear}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Employees:</p>
              <p className="text-sm text-muted-foreground">{profile.businessInfo?.numberOfEmployees}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Annual Revenue:</p>
              <p className="text-sm text-muted-foreground">{profile.businessInfo?.annualRevenue}</p>
            </div>
            {profile.businessInfo?.website && (
              <div className="flex items-center gap-2">
                <Globe size={16} className="text-muted-foreground" />
                <a 
                  href={profile.businessInfo.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:underline"
                >
                  {profile.businessInfo.website}
                </a>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Envelope size={20} />
              Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <Envelope size={16} className="text-muted-foreground" />
              <span className="text-sm">{profile.contactInfo?.primaryEmail}</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone size={16} className="text-muted-foreground" />
              <span className="text-sm">{profile.contactInfo?.primaryPhone}</span>
            </div>
            <div className="flex items-start gap-2">
              <MapPin size={16} className="text-muted-foreground mt-0.5" />
              <div className="text-sm">
                {profile.contactInfo?.address?.street}<br />
                {profile.contactInfo?.address?.city}, {profile.contactInfo?.address?.state} {profile.contactInfo?.address?.zipCode}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Business Description */}
      <Card>
        <CardHeader>
          <CardTitle>About Our Business</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{profile.businessInfo?.description}</p>
        </CardContent>
      </Card>

      {/* CSR Program */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HandHeart size={20} />
            Corporate Social Responsibility
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle 
              size={16} 
              className={profile.csrProgram?.hasEstablishedProgram ? 'text-green-600' : 'text-gray-400'} 
            />
            <span className="text-sm font-medium">
              {profile.csrProgram?.hasEstablishedProgram ? 'Established CSR Program' : 'Developing CSR Program'}
            </span>
          </div>
          
          {profile.csrProgram?.programDescription && (
            <div>
              <p className="text-sm font-medium mb-2">Program Description</p>
              <p className="text-sm text-muted-foreground">{profile.csrProgram.programDescription}</p>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm font-medium">Annual CSR Budget</p>
              <p className="text-sm text-muted-foreground">{profile.csrProgram?.annualCSRBudget || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Volunteer Hours/Employee</p>
              <p className="text-sm text-muted-foreground">{profile.csrProgram?.hoursPerEmployee || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Paid Volunteer Time</p>
              <p className="text-sm text-muted-foreground">
                {profile.csrProgram?.paidVolunteerTime ? 'Yes' : 'No'}
              </p>
            </div>
          </div>

          {(profile.csrProgram?.focusAreas || []).length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Focus Areas</p>
              <div className="flex flex-wrap gap-1">
                {(profile.csrProgram.focusAreas || []).map(area => (
                  <Badge key={area} variant="secondary">{area}</Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Leadership Team */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users size={20} />
            Leadership Team
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {profile.leadership?.ceo && (
              <div className="border rounded-lg p-3">
                <p className="font-medium">{profile.leadership.ceo.name}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.ceo.title}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.ceo.email}</p>
              </div>
            )}
            {profile.leadership?.csrDirector && (
              <div className="border rounded-lg p-3">
                <p className="font-medium">{profile.leadership.csrDirector.name}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.csrDirector.title}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.csrDirector.email}</p>
              </div>
            )}
            {profile.leadership?.hrDirector && (
              <div className="border rounded-lg p-3">
                <p className="font-medium">{profile.leadership.hrDirector.name}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.hrDirector.title}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.hrDirector.email}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Offerings & Capabilities */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star size={20} />
              Community Offerings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">Skill-Based Volunteering</p>
              <div className="flex flex-wrap gap-1">
                {(profile.offerings?.skillBasedVolunteering || []).map(skill => (
                  <Badge key={skill} variant="secondary">{skill}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Training Resources</p>
              <div className="flex flex-wrap gap-1">
                {(profile.offerings?.trainingResources || []).map(resource => (
                  <Badge key={resource} variant="outline">{resource}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Financial Support Options</p>
              <div className="space-y-1">
                {profile.offerings?.financialSupport?.grants && (
                  <Badge variant="secondary">Grants</Badge>
                )}
                {profile.offerings?.financialSupport?.sponsorships && (
                  <Badge variant="secondary">Sponsorships</Badge>
                )}
                {profile.offerings?.financialSupport?.matchingGifts && (
                  <Badge variant="secondary">Matching Gifts</Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendUp size={20} />
              Employee Engagement
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Volunteer Program</span>
              <Badge variant={profile.employeeEngagement?.volunteerProgram ? 'default' : 'secondary'}>
                {profile.employeeEngagement?.volunteerProgram ? 'Active' : 'Not Active'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Team Building Events</span>
              <Badge variant={profile.employeeEngagement?.teamBuildingEvents ? 'default' : 'secondary'}>
                {profile.employeeEngagement?.teamBuildingEvents ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Skill Sharing</span>
              <Badge variant={profile.employeeEngagement?.skillSharingInitiatives ? 'default' : 'secondary'}>
                {profile.employeeEngagement?.skillSharingInitiatives ? 'Yes' : 'No'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Volunteer Tracking</span>
              <Badge variant={profile.employeeEngagement?.employeeVolunteerTracking ? 'default' : 'secondary'}>
                {profile.employeeEngagement?.employeeVolunteerTracking ? 'Yes' : 'No'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Verification Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield size={20} />
            Verification Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">Business License</span>
              <Badge variant={
                (profile.verification?.businessLicense || []).length > 0 ? 'default' : 'secondary'
              }>
                {(profile.verification?.businessLicense || []).length > 0 ? 'Verified' : 'Pending'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Insurance Documentation</span>
              <Badge variant={
                profile.verification?.insurance?.generalLiability ? 'default' : 'secondary'
              }>
                {profile.verification?.insurance?.generalLiability ? 'Verified' : 'Pending'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Financial Standing</span>
              <Badge variant={
                profile.verification?.financialStanding?.creditReport ? 'default' : 'secondary'
              }>
                {profile.verification?.financialStanding?.creditReport ? 'Verified' : 'Pending'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Ethics Compliance</span>
              <Badge variant={
                profile.verification?.ethicsCompliance?.codeOfConduct ? 'default' : 'secondary'
              }>
                {profile.verification?.ethicsCompliance?.codeOfConduct ? 'Verified' : 'Pending'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}