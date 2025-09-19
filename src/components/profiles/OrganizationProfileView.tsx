import { useState } from 'react'
import { OrganizationProfile } from '../../types/profiles'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Separator } from '../ui/separator'
import { 
  Building, 
  Shield, 
  Phone, 
  MapPin, 
  Users, 
  PencilSimple,
  Envelope,
  Globe,
  Calendar,
  Clock,
  CheckCircle
} from '@phosphor-icons/react'

interface OrganizationProfileViewProps {
  profile: OrganizationProfile
  onUpdate: (updatedProfile: OrganizationProfile) => void
}

export function OrganizationProfileView({ profile, onUpdate }: OrganizationProfileViewProps) {
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
            {profile.organizationInfo?.legalName}
          </h1>
          <p className="text-muted-foreground">
            {profile.organizationInfo?.organizationType?.replace('_', ' ').toUpperCase()} Organization
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
            <Building size={20} />
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
                Complete your organization profile to unlock all platform features.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Organization Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building size={20} />
              Organization Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">EIN:</p>
              <p className="text-sm text-muted-foreground">{profile.organizationInfo?.ein}</p>
            </div>
            {profile.organizationInfo?.dbaName && (
              <div>
                <p className="text-sm font-medium">DBA Name:</p>
                <p className="text-sm text-muted-foreground">{profile.organizationInfo.dbaName}</p>
              </div>
            )}
            <div>
              <p className="text-sm font-medium">Founded:</p>
              <p className="text-sm text-muted-foreground">{profile.organizationInfo?.foundedYear}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Employees:</p>
              <p className="text-sm text-muted-foreground">{profile.organizationInfo?.numberOfEmployees}</p>
            </div>
            {profile.organizationInfo?.website && (
              <div className="flex items-center gap-2">
                <Globe size={16} className="text-muted-foreground" />
                <a 
                  href={profile.organizationInfo.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:underline"
                >
                  {profile.organizationInfo.website}
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

      {/* Mission & Description */}
      <Card>
        <CardHeader>
          <CardTitle>Mission & Purpose</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">Mission Statement</p>
            <p className="text-sm text-muted-foreground">{profile.organizationInfo?.missionStatement}</p>
          </div>
          <Separator />
          <div>
            <p className="text-sm font-medium mb-2">Description</p>
            <p className="text-sm text-muted-foreground">{profile.organizationInfo?.description}</p>
          </div>
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
            {profile.leadership?.executiveDirector && (
              <div className="border rounded-lg p-3">
                <p className="font-medium">{profile.leadership.executiveDirector.name}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.executiveDirector.title}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.executiveDirector.email}</p>
              </div>
            )}
            {profile.leadership?.boardChair && (
              <div className="border rounded-lg p-3">
                <p className="font-medium">{profile.leadership.boardChair.name}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.boardChair.title}</p>
                <p className="text-sm text-muted-foreground">{profile.leadership.boardChair.email}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Operations */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock size={20} />
              Operating Hours
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(profile.operations?.operatingHours || {}).map(([day, hours]) => (
                <div key={day} className="flex justify-between text-sm">
                  <span className="font-medium">{day}</span>
                  <span className="text-muted-foreground">
                    {hours.closed ? 'Closed' : `${hours.open} - ${hours.close}`}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Service Areas & Programs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">Service Areas</p>
              <div className="flex flex-wrap gap-1">
                {(profile.operations?.serviceAreas || []).map(area => (
                  <Badge key={area} variant="secondary">{area}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Programs Offered</p>
              <div className="flex flex-wrap gap-1">
                {(profile.operations?.programsOffered || []).map(program => (
                  <Badge key={program} variant="outline">{program}</Badge>
                ))}
              </div>
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
              <span className="font-medium">Legal Status Documents</span>
              <Badge variant={
                (profile.verification?.legalStatus || []).length > 0 ? 'default' : 'secondary'
              }>
                {(profile.verification?.legalStatus || []).length > 0 ? 'Submitted' : 'Pending'}
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
              <span className="font-medium">Facility Inspection</span>
              <Badge variant={
                profile.verification?.facilityInspection?.completed ? 'default' : 'secondary'
              }>
                {profile.verification?.facilityInspection?.completed ? 'Completed' : 'Pending'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Capabilities */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {profile.capabilities?.maxVolunteersPerEvent || 0}
              </div>
              <div className="text-sm text-muted-foreground">Max Volunteers per Event</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {profile.capabilities?.canVerifyVolunteers ? 'Yes' : 'No'}
              </div>
              <div className="text-sm text-muted-foreground">Can Verify Volunteers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {(profile.capabilities?.trainingPrograms || []).length}
              </div>
              <div className="text-sm text-muted-foreground">Training Programs</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}