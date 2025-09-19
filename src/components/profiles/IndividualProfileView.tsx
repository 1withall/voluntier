import { useState } from 'react'
import { IndividualProfile } from '../../types/profiles'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Separator } from '../ui/separator'
import { 
  User, 
  Shield, 
  Phone, 
  MapPin, 
  Heart, 
  Clock, 
  Star,
  Trophy,
  PencilSimple,
  Envelope,
  Calendar,
  CheckCircle
} from '@phosphor-icons/react'

interface IndividualProfileViewProps {
  profile: IndividualProfile
  onUpdate: (updatedProfile: IndividualProfile) => void
}

export function IndividualProfileView({ profile, onUpdate }: IndividualProfileViewProps) {
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

  const getLevelInfo = (points: number) => {
    const level = Math.floor(points / 100) + 1
    const pointsInLevel = points % 100
    const pointsToNext = 100 - pointsInLevel
    return { level, pointsInLevel, pointsToNext }
  }

  const levelInfo = getLevelInfo(profile.gamification?.points || 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            {profile.personalInfo?.firstName} {profile.personalInfo?.lastName}
          </h1>
          <p className="text-muted-foreground">Individual Volunteer</p>
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
            <User size={20} />
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
                Complete your profile to unlock all features and improve matching with opportunities.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User size={20} />
              Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4">
              <div className="flex items-center gap-2">
                <Envelope size={16} className="text-muted-foreground" />
                <span className="text-sm">{profile.personalInfo?.email}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone size={16} className="text-muted-foreground" />
                <span className="text-sm">{profile.personalInfo?.phoneNumber}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar size={16} className="text-muted-foreground" />
                <span className="text-sm">
                  Born {new Date(profile.personalInfo?.dateOfBirth || '').toLocaleDateString()}
                </span>
              </div>
              {profile.personalInfo?.pronouns && (
                <div>
                  <span className="text-sm font-medium">Pronouns:</span>
                  <span className="text-sm ml-2">{profile.personalInfo.pronouns}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Address Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin size={20} />
              Location
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className="text-sm">
                {profile.address?.street}<br />
                {profile.address?.city}, {profile.address?.state} {profile.address?.zipCode}
              </p>
              <div className="pt-2">
                <p className="text-xs font-medium text-muted-foreground">Emergency Contact:</p>
                <p className="text-sm">
                  {profile.emergencyContact?.name} ({profile.emergencyContact?.relationship})
                </p>
                <p className="text-sm text-muted-foreground">
                  {profile.emergencyContact?.phoneNumber}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Skills & Interests */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart size={20} />
              Skills & Interests
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">Skills</p>
              <div className="flex flex-wrap gap-1">
                {(profile.preferences?.skills || []).map(skill => (
                  <Badge key={skill} variant="secondary">{skill}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Interests</p>
              <div className="flex flex-wrap gap-1">
                {(profile.preferences?.interests || []).map(interest => (
                  <Badge key={interest} variant="outline">{interest}</Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Availability */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock size={20} />
              Availability
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium mb-2">Available Days</p>
              <div className="flex flex-wrap gap-1">
                {(profile.preferences?.availability?.days || []).map(day => (
                  <Badge key={day} variant="outline">{day}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-medium mb-2">Time Slots</p>
              <div className="flex flex-wrap gap-1">
                {(profile.preferences?.availability?.timeSlots || []).map(slot => (
                  <Badge key={slot} variant="outline">{slot}</Badge>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm">
                <span className="font-medium">Hours per week:</span> {profile.preferences?.availability?.hoursPerWeek || 0}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Volunteer History & Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy size={20} />
            Volunteer Impact
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {profile.volunteerHistory?.hoursLogged || 0}
              </div>
              <div className="text-sm text-muted-foreground">Hours Logged</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {profile.volunteerHistory?.eventsAttended || 0}
              </div>
              <div className="text-sm text-muted-foreground">Events Attended</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {profile.volunteerHistory?.organizationsWorkedWith?.length || 0}
              </div>
              <div className="text-sm text-muted-foreground">Organizations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {profile.gamification?.points || 0}
              </div>
              <div className="text-sm text-muted-foreground">Impact Points</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gamification & Achievements */}
      {profile.gamification && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star size={20} />
                Level & Progress
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">Level {levelInfo.level}</div>
                <p className="text-sm text-muted-foreground">Volunteer Level</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Progress to next level</span>
                  <span className="text-sm text-muted-foreground">
                    {levelInfo.pointsInLevel}/100 points
                  </span>
                </div>
                <Progress value={levelInfo.pointsInLevel} className="w-full" />
                <p className="text-xs text-muted-foreground text-center">
                  {levelInfo.pointsToNext} points to Level {levelInfo.level + 1}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm">
                  <span className="font-medium">Current Streak:</span> {profile.gamification.streaks?.current || 0} days
                </p>
                <p className="text-sm text-muted-foreground">
                  Best: {profile.gamification.streaks?.longest || 0} days
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy size={20} />
                Badges & Achievements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">Earned Badges ({(profile.gamification.badges || []).length})</p>
                  <div className="grid grid-cols-4 gap-2">
                    {(profile.gamification.badges || []).slice(0, 8).map(badge => (
                      <div key={badge.id} className="text-center">
                        <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-1">
                          <Trophy size={16} className="text-yellow-600" />
                        </div>
                        <p className="text-xs text-muted-foreground truncate">{badge.name}</p>
                      </div>
                    ))}
                  </div>
                </div>
                
                <Separator />
                
                <div>
                  <p className="text-sm font-medium mb-2">Recent Achievements</p>
                  <div className="space-y-2">
                    {(profile.gamification.achievements || [])
                      .filter(a => a.completed)
                      .slice(0, 3)
                      .map(achievement => (
                        <div key={achievement.id} className="flex items-center gap-2">
                          <CheckCircle size={16} className="text-green-600" />
                          <span className="text-sm">{achievement.name}</span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

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
              <span className="font-medium">Background Check</span>
              <Badge variant={profile.verification?.backgroundCheckStatus === 'completed' ? 'default' : 'secondary'}>
                {profile.verification?.backgroundCheckStatus || 'Pending'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">Personal References</span>
              <Badge variant={
                (profile.verification?.references || []).filter(r => r.verificationStatus === 'verified').length >= 2 
                  ? 'default' 
                  : 'secondary'
              }>
                {(profile.verification?.references || []).filter(r => r.verificationStatus === 'verified').length}/2 Verified
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="font-medium">In-Person Verification</span>
              <Badge variant={profile.verification?.inPersonVerification?.completed ? 'default' : 'secondary'}>
                {profile.verification?.inPersonVerification?.completed ? 'Completed' : 'Pending'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}