import { UserProfile } from '../App'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { HandHeart, Users, Calendar, ChartBar, Shield, QrCode, Activity } from '@phosphor-icons/react'

interface HeaderProps {
  userProfile: UserProfile | null
  currentView: 'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry'
  onViewChange: (view: 'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry') => void
}

export function Header({ userProfile, currentView, onViewChange }: HeaderProps) {
  const navItems = [
    { id: 'events' as const, label: 'Events', icon: Calendar },
    { id: 'profile' as const, label: 'Profile', icon: Users },
    { id: 'organization' as const, label: 'Organizations', icon: HandHeart },
    { id: 'impact' as const, label: 'Impact', icon: ChartBar },
    { id: 'verification' as const, label: 'Verification', icon: QrCode },
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
              <Badge variant={userProfile.verified ? "default" : "secondary"}>
                {userProfile.verified ? "Verified" : "Pending"}
              </Badge>
              <div className="text-right">
                <p className="text-sm font-medium">{userProfile.name}</p>
                <p className="text-xs text-muted-foreground">{userProfile.hoursLogged}h logged</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}