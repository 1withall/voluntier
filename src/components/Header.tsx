import { useState, useEffect } from 'react'
import { UserProfile } from '../types/profiles'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from './ui/dropdown-menu'
import { Dialog, DialogContent } from './ui/dialog'
import { HandHeart, Users, Calendar, ChartBar, Shield, QrCode, Activity, FileText, ChartLine, Bell, SignOut, SignIn, User, ChevronDown } from '@phosphor-icons/react'
import { useAuth } from '../services/auth'
import { usePrivilege } from './auth/PrivilegeGuard'
import { SignInForm } from './auth/SignInForm'

interface HeaderProps {
  userProfile: UserProfile | null
  currentView: 'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry' | 'document-verification' | 'notifications' | 'onboarding'
  onViewChange: (view: 'events' | 'profile' | 'organization' | 'impact' | 'security' | 'verification' | 'telemetry' | 'document-verification' | 'notifications' | 'onboarding') => void
}

export function Header({ userProfile, currentView, onViewChange }: HeaderProps) {
  const { isAuthenticated, currentUser, signOut } = useAuth()
  const [showSignInDialog, setShowSignInDialog] = useState(false)
  
  // Check privileges for admin features
  const securityPrivilege = usePrivilege('view_security_dashboard')
  const telemetryPrivilege = usePrivilege('view_telemetry')
  const analyticsPrivilege = usePrivilege('view_analytics')

  // Listen for admin sign-in requests from privilege guards
  useEffect(() => {
    const handleShowAdminSignIn = () => {
      setShowSignInDialog(true)
    }

    window.addEventListener('show-admin-signin', handleShowAdminSignIn)
    return () => {
      window.removeEventListener('show-admin-signin', handleShowAdminSignIn)
    }
  }, [])

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

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Sign out failed:', error)
    }
  }

  // Filter navigation items based on privileges
  const getVisibleNavItems = () => {
    const baseItems = [
      { id: 'events' as const, label: 'Events', icon: Calendar },
      { id: 'profile' as const, label: 'Profile', icon: Users },
      { id: 'organization' as const, label: 'Organizations', icon: HandHeart },
      { id: 'impact' as const, label: 'Impact', icon: ChartBar },
      { id: 'verification' as const, label: 'QR Verification', icon: QrCode },
      { id: 'document-verification' as const, label: 'Documents', icon: FileText },
      { id: 'notifications' as const, label: 'Notifications', icon: Bell },
      { id: 'onboarding' as const, label: 'Onboarding', icon: ChartLine },
    ]

    const adminItems = []
    
    // Only show security dashboard if user has the privilege
    if (securityPrivilege.hasPrivilege) {
      adminItems.push({ id: 'security' as const, label: 'Security', icon: Shield })
    }
    
    // Only show telemetry/analytics if user has the privilege
    if (telemetryPrivilege.hasPrivilege || analyticsPrivilege.hasPrivilege) {
      adminItems.push({ id: 'telemetry' as const, label: 'Analytics', icon: Activity })
    }

    return [...baseItems, ...adminItems]
  }

  const navItems = getVisibleNavItems()

  return (
    <>
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

            <div className="flex items-center space-x-3">
              {/* Regular user profile info */}
              {userProfile && (
                <>
                  <Badge variant={isVerified(userProfile) ? "default" : "secondary"}>
                    {isVerified(userProfile) ? "Verified" : "Pending"}
                  </Badge>
                  <div className="text-right">
                    <p className="text-sm font-medium">{getUserName(userProfile)}</p>
                    <p className="text-xs text-muted-foreground">{getVolunteerHours(userProfile)}h logged</p>
                  </div>
                </>
              )}

              {/* Admin authentication controls */}
              <div className="flex items-center space-x-2">
                {isAuthenticated && currentUser ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm" className="flex items-center gap-2">
                        <Shield size={16} className="text-primary" />
                        <span className="hidden sm:inline">Admin</span>
                        <ChevronDown size={14} />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <div className="px-2 py-1.5">
                        <p className="text-sm font-medium">{currentUser.email}</p>
                        <p className="text-xs text-muted-foreground">
                          {currentUser.isSuperAdmin ? 'Super Administrator' : 'Administrator'}
                        </p>
                      </div>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleSignOut} className="text-destructive">
                        <SignOut size={16} className="mr-2" />
                        Sign Out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setShowSignInDialog(true)}
                    className="flex items-center gap-2"
                  >
                    <SignIn size={16} />
                    <span className="hidden sm:inline">Admin Sign In</span>
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sign In Dialog */}
      <Dialog open={showSignInDialog} onOpenChange={setShowSignInDialog}>
        <DialogContent className="sm:max-w-md">
          <SignInForm onClose={() => setShowSignInDialog(false)} />
        </DialogContent>
      </Dialog>
    </>
  )
}