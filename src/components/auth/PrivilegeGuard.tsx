import { ReactNode } from 'react'
import { useAuth } from '../../services/auth'
import { AllPrivileges, PrivilegeLevel } from '../../types/privileges'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Alert, AlertDescription } from '../ui/alert'
import { Lock, Shield, AlertTriangle } from '@phosphor-icons/react'
import { motion } from 'framer-motion'

interface PrivilegeGuardProps {
  children: ReactNode
  requiredPrivilege: AllPrivileges
  requiredLevel?: PrivilegeLevel
  fallbackMessage?: string
  showSignIn?: boolean
  onSignInClick?: () => void
}

export const PrivilegeGuard = ({ 
  children, 
  requiredPrivilege, 
  requiredLevel = 'read',
  fallbackMessage,
  showSignIn = true,
  onSignInClick
}: PrivilegeGuardProps) => {
  const { isAuthenticated, hasPrivilege, currentUser } = useAuth()

  const privilegeCheck = hasPrivilege(requiredPrivilege, requiredLevel)

  // If user has the required privilege, show the content
  if (privilegeCheck.hasPrivilege) {
    return <>{children}</>
  }

  // Determine the appropriate message and icon
  let icon = <Lock size={48} className="text-muted-foreground mb-4" />
  let title = 'Access Restricted'
  let description = fallbackMessage || 'You do not have permission to access this section.'
  let alertVariant: 'default' | 'destructive' = 'default'

  if (!isAuthenticated) {
    icon = <Shield size={48} className="text-muted-foreground mb-4" />
    title = 'Authentication Required'
    description = 'Please sign in to access administrative features.'
  } else if (privilegeCheck.reason === 'Privilege has expired') {
    icon = <AlertTriangle size={48} className="text-destructive mb-4" />
    title = 'Access Expired'
    description = `Your access to this feature expired on ${new Date(privilegeCheck.expiresAt!).toLocaleDateString()}.`
    alertVariant = 'destructive'
  } else if (privilegeCheck.reason?.includes('Insufficient privilege level')) {
    icon = <Lock size={48} className="text-muted-foreground mb-4" />
    title = 'Insufficient Privileges'
    description = `This feature requires ${requiredLevel} level access. You currently have ${privilegeCheck.level} level access.`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full"
    >
      <Card className="max-w-2xl mx-auto">
        <CardContent className="flex flex-col items-center justify-center py-12">
          {icon}
          <CardTitle className="mb-2">{title}</CardTitle>
          <CardDescription className="text-center max-w-md mb-6">
            {description}
          </CardDescription>

          {privilegeCheck.reason && (
            <Alert variant={alertVariant} className="mb-6 max-w-md">
              <AlertDescription>
                <strong>Reason:</strong> {privilegeCheck.reason}
              </AlertDescription>
            </Alert>
          )}

          {!isAuthenticated && showSignIn && (
            <Button onClick={onSignInClick} className="mb-4">
              Sign In as Administrator
            </Button>
          )}

          {isAuthenticated && currentUser && (
            <div className="text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                Signed in as: <span className="font-medium">{currentUser.email}</span>
              </p>
              <p className="text-xs text-muted-foreground">
                Required privilege: <span className="font-mono">{requiredPrivilege}</span> ({requiredLevel})
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

// Convenience hook for checking privileges in components
export const usePrivilege = (privilege: AllPrivileges, level: PrivilegeLevel = 'read') => {
  const { hasPrivilege } = useAuth()
  return hasPrivilege(privilege, level)
}

// Higher-order component for protecting entire pages
export const withPrivilege = (
  Component: React.ComponentType<any>,
  requiredPrivilege: AllPrivileges,
  requiredLevel: PrivilegeLevel = 'read'
) => {
  return function ProtectedComponent(props: any) {
    return (
      <PrivilegeGuard 
        requiredPrivilege={requiredPrivilege} 
        requiredLevel={requiredLevel}
      >
        <Component {...props} />
      </PrivilegeGuard>
    )
  }
}