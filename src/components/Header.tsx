import { UserProfile } from '../types/profiles'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { HandHeart, Users, Calendar, ChartBar, Shield, QrCode, Activity, FileText, ChartLine, Bell } from '@phosphor-icons/react'

interface HeaderProps {
  userProfile: UserProfile | null
  currentView: 'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry' | 'document-verification' | 'notifications' | 'onboarding'
  onViewChange: (view: 'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry' | 'document-verification' | 'notifications' | 'onboarding') => void
}

export function Header({ userProfile, currentView, onViewChange }: HeaderProps) {
  const getUserName = (profile: UserProfile | null): string => {
    if (!profile) return ''
    switch (profile.userType) {
      case 'individual':
        return `${profile.personalInfo?.firstName || ''} ${profile.personalInfo?.lastName || ''}`.trim()
      case 'organization':
        return profile.organizationInfo?.legalName || ''
      case 'business':
        return profile.businessInfo?.legalName || ''
      default:
        return ''
    }
  }

  const getVolunteerHours = (profile: UserProfile | null): number => {
    if (!profile || profile.userType !== 'individual') return 0
    return profile.volunteerHistory?.hoursLogged || 0
  }

  const isVerified = (profile: UserProfile | null): boolean => {
    if (!profile) return false
    return profile.verificationStatus === 'verified'
  }
  const navItems = [
    { id: 'events' as const, label: 'Events', icon: Calendar },
    { id: 'profile' as const, label: 'Profile', icon: Users },
    { id: 'organization' as const, label: 'Organizations', icon: HandHeart },
    { id: 'impact' as const, label: 'Impact', icon: ChartBar },
    { id: 'verification' as const, label: 'QR Verification', icon: QrCode },
    { id: 'document-verification' as const, label: 'Documents', icon: FileText },
    { id: 'notifications' as const, label: 'Notifications', icon: Bell },
    { id: 'onboarding' as const, label: 'Onboarding', icon: ChartLine },
    { id: 'security' as const, label: 'Security', icon: Shield },
    { id: 'telemetry' as const, label: 'Analytics', icon: Activity },
  ]

  return (
    <header className="border-b bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/50">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <HandHeart size={24} className="text-primary" />
              <h1 className="text-xl font-bold text-foreground">Voluntier</h1>
            </div>
          </div>

          {userProfile && (
            <nav className="flex items-center space-x-1">
              {navItems.map(({ id, label, icon: Icon }) => (
                <Button
                  key={id}
                  variant={currentView === id ? "default" : "ghost"}
                  size="sm"
                  onClick={() => onViewChange(id)}
                  className="flex items-center gap-2"
                >
                  <Icon size={16} />
                  {label}
                </Button>
              ))}
            </nav>
          )}

          {userProfile && (
            <div className="flex items-center space-x-3">
              <Badge variant={isVerified(userProfile) ? "default" : "secondary"}>
                {isVerified(userProfile) ? "Verified" : "Pending"}
              </Badge>
              <div className="text-right">
                <p className="text-sm font-medium">{getUserName(userProfile)}</p>
                <p className="text-xs text-muted-foreground">{getVolunteerHours(userProfile)}h logged</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}