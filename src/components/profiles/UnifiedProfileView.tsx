import { useState } from 'react'
import { UserProfile } from '../../types/profiles'
import { IndividualProfileView } from './IndividualProfileView'
import { OrganizationProfileView } from './OrganizationProfileView'
import { BusinessProfileView } from './BusinessProfileView'

interface UnifiedProfileViewProps {
  userProfile: UserProfile
  onUpdateProfile: (updatedProfile: UserProfile) => void
}

export function UnifiedProfileView({ userProfile, onUpdateProfile }: UnifiedProfileViewProps) {
  const renderProfileByType = () => {
    switch (userProfile.userType) {
      case 'individual':
        return (
          <IndividualProfileView 
            profile={userProfile}
            onUpdate={onUpdateProfile}
          />
        )
      case 'organization':
        return (
          <OrganizationProfileView 
            profile={userProfile}
            onUpdate={onUpdateProfile}
          />
        )
      case 'business':
        return (
          <BusinessProfileView 
            profile={userProfile}
            onUpdate={onUpdateProfile}
          />
        )
      default:
        return <div>Unknown user type</div>
    }
  }

  return (
    <div className="space-y-6">
      {renderProfileByType()}
    </div>
  )
}