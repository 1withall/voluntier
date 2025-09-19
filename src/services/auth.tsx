// Authentication and privilege management service
import { useKV } from '@github/spark/hooks'
import { useState, useEffect, createContext, useContext, ReactNode } from 'react'
import { 
  AdminUser, 
  AuthenticationResult, 
  PrivilegeCheckResult,
  AllPrivileges,
  PrivilegeLevel,
  SYSTEM_ROLES,
  ActiveSession
} from '../types/privileges'
import { UserProfile } from '../types/profiles'
import { temporalWorkflowService } from './temporalWorkflowService'

// Crypto utilities for password hashing
class AuthCrypto {
  static async generateSalt(): Promise<string> {
    const array = new Uint8Array(16)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  static async hashPassword(password: string, salt: string): Promise<string> {
    const encoder = new TextEncoder()
    const data = encoder.encode(password + salt)
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = new Uint8Array(hashBuffer)
    return Array.from(hashArray, byte => byte.toString(16).padStart(2, '0')).join('')
  }

  static async verifyPassword(password: string, hash: string, salt: string): Promise<boolean> {
    const computedHash = await this.hashPassword(password, salt)
    return computedHash === hash
  }

  static generateSessionToken(): string {
    const array = new Uint8Array(32)
    crypto.getRandomValues(array)
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
  }
}

interface AuthContextType {
  currentUser: AdminUser | null
  currentSession: ActiveSession | null
  regularUser: UserProfile | null
  isAuthenticated: boolean
  isLoading: boolean
  signIn: (email: string, password: string) => Promise<AuthenticationResult>
  signOut: () => Promise<void>
  hasPrivilege: (privilege: AllPrivileges, requiredLevel?: PrivilegeLevel) => PrivilegeCheckResult
  refreshSession: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [currentUser, setCurrentUser] = useState<AdminUser | null>(null)
  const [currentSession, setCurrentSession] = useState<ActiveSession | null>(null)
  const [regularUser, setRegularUser] = useKV<UserProfile | null>('user-profile', null)
  const [isLoading, setIsLoading] = useState(true)
  const [adminUsers, setAdminUsers] = useKV<AdminUser[]>('admin-users', [])
  const [sessionData, setSessionData] = useKV<Record<string, ActiveSession>>('active-sessions', {})
  const [adminInitialized, setAdminInitialized] = useState(false)
  const [sessionChecked, setSessionChecked] = useState(false)

  // Initialize system admin account
  useEffect(() => {
    if (adminInitialized) return
    
    const initializeSystemAdmin = async () => {
      try {
        if (!adminUsers || adminUsers.length === 0) {
          const salt = await AuthCrypto.generateSalt()
          const passwordHash = await AuthCrypto.hashPassword('1Fake_passw0rd.', salt)
          
          const systemAdmin: AdminUser = {
            id: 'system-admin-001',
            email: 'gy0d84t5bdk2h@proton.me',
            passwordHash,
            salt,
            isSystem: true,
            isSuperAdmin: true,
            roles: [SYSTEM_ROLES.SUPER_ADMIN.id],
            privileges: SYSTEM_ROLES.SUPER_ADMIN.privileges.map(priv => ({
              privilege: priv as AllPrivileges,
              level: 'super_admin' as PrivilegeLevel,
              grantedAt: new Date().toISOString(),
              grantedBy: 'system'
            })),
            createdAt: new Date().toISOString(),
            loginAttempts: 0,
            twoFactorEnabled: false,
            sessionTokens: []
          }
          
          setAdminUsers([systemAdmin])
        }
        setAdminInitialized(true)
      } catch (error) {
        console.error('Failed to initialize system admin:', error)
      } finally {
        setIsLoading(false)
      }
    }

    // Add a small delay to prevent initialization conflicts
    const timer = setTimeout(initializeSystemAdmin, 100)
    return () => clearTimeout(timer)
  }, [])

  // Check for existing session on load
  useEffect(() => {
    if (sessionChecked || !adminInitialized) return
    
    const checkExistingSession = async () => {
      if (!adminUsers || adminUsers.length === 0 || !sessionData) return
      
      try {
        const sessionToken = localStorage.getItem('voluntier_session_token')
        if (sessionToken && sessionData[sessionToken]) {
          const session = sessionData[sessionToken]
          
          // Validate session through Temporal workflow
          const validationResult = await temporalWorkflowService.validateSession({
            sessionToken,
            ipAddress: 'localhost',
          })
          
          if (validationResult.status === 'success' && validationResult.data.valid) {
            const user = adminUsers.find(u => 
              u.sessionTokens.some(t => t.token === sessionToken)
            )
            
            if (user && !currentUser) {
              setCurrentUser(user)
              setCurrentSession(session)
              
              // Update last activity
              const updatedSession = {
                ...session,
                lastActivity: new Date().toISOString()
              }
              setSessionData(current => ({
                ...current,
                [sessionToken]: updatedSession
              }))
            }
          } else {
            // Session invalid - clean up
            localStorage.removeItem('voluntier_session_token')
            setSessionData(current => {
              const updated = { ...current }
              delete updated[sessionToken]
              return updated
            })
          }
        }
      } catch (error) {
        console.error('Failed to check existing session:', error)
      } finally {
        setSessionChecked(true)
      }
    }

    if (!isLoading && adminInitialized) {
      checkExistingSession()
    }
  }, [isLoading, adminInitialized, sessionChecked, adminUsers?.length, sessionData && Object.keys(sessionData).length, currentUser?.id])

  const signIn = async (email: string, password: string): Promise<AuthenticationResult> => {
    try {
      setIsLoading(true)
      
      // For admin users, first check local storage for rapid response
      const user = adminUsers?.find(u => u.email.toLowerCase() === email.toLowerCase())
      
      if (user) {
        // Handle admin authentication locally for speed
        if (user.lockedUntil && new Date(user.lockedUntil) > new Date()) {
          return {
            success: false,
            error: 'Account is temporarily locked due to failed login attempts'
          }
        }

        const isValidPassword = await AuthCrypto.verifyPassword(password, user.passwordHash, user.salt)
        
        if (!isValidPassword) {
          const updatedUser = {
            ...user,
            loginAttempts: user.loginAttempts + 1,
            lockedUntil: user.loginAttempts >= 4 ? 
              new Date(Date.now() + 15 * 60 * 1000).toISOString() :
              undefined
          }
          
          setAdminUsers(current => 
            current?.map(u => u.id === user.id ? updatedUser : u) || []
          )
          
          return {
            success: false,
            error: 'Invalid credentials',
            remainingAttempts: Math.max(0, 5 - updatedUser.loginAttempts)
          }
        }

        // Create session locally for admin
        const sessionToken = AuthCrypto.generateSessionToken()
        const session: ActiveSession = {
          token: sessionToken,
          createdAt: new Date().toISOString(),
          expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
          ipAddress: 'localhost',
          userAgent: navigator.userAgent,
          lastActivity: new Date().toISOString()
        }

        const updatedUser = {
          ...user,
          lastLoginAt: new Date().toISOString(),
          loginAttempts: 0,
          lockedUntil: undefined,
          sessionTokens: [...user.sessionTokens.filter(t => new Date(t.expiresAt) > new Date()), session]
        }

        localStorage.setItem('voluntier_session_token', sessionToken)
        setSessionData(current => ({
          ...current,
          [sessionToken]: session
        }))

        setAdminUsers(current => 
          current?.map(u => u.id === user.id ? updatedUser : u) || []
        )

        setCurrentUser(updatedUser)
        setCurrentSession(session)

        return {
          success: true,
          user: updatedUser,
          session
        }
      } else {
        // For regular users, use Temporal workflow
        const authResult = await temporalWorkflowService.authenticateUser({
          email,
          password,
          ipAddress: 'localhost',
          userAgent: navigator.userAgent,
        })

        if (authResult.status === 'success' && authResult.data.authenticated) {
          // Store session token for regular users
          localStorage.setItem('voluntier_session_token', authResult.data.session.session_token)
          
          return {
            success: true,
            user: authResult.data.user_data,
            session: authResult.data.session
          }
        } else {
          return {
            success: false,
            error: authResult.data.reason || 'Authentication failed'
          }
        }
      }
    } catch (error) {
      console.error('Sign in error:', error)
      return {
        success: false,
        error: 'An error occurred during sign in'
      }
    } finally {
      setIsLoading(false)
    }
  }

  const signOut = async (): Promise<void> => {
    try {
      const sessionToken = localStorage.getItem('voluntier_session_token')
      
      if (sessionToken && currentUser) {
        // Remove session from user's active sessions
        const updatedUser = {
          ...currentUser,
          sessionTokens: currentUser.sessionTokens.filter(t => t.token !== sessionToken)
        }
        
        setAdminUsers(current => 
          current?.map(u => u.id === currentUser.id ? updatedUser : u) || []
        )

        // Remove from session storage
        setSessionData(current => {
          const updated = { ...current }
          delete updated[sessionToken]
          return updated
        })
      }

      // Clear local state
      localStorage.removeItem('voluntier_session_token')
      setCurrentUser(null)
      setCurrentSession(null)
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  const hasPrivilege = (privilege: AllPrivileges, requiredLevel: PrivilegeLevel = 'read'): PrivilegeCheckResult => {
    if (!currentUser) {
      return {
        hasPrivilege: false,
        level: 'none',
        reason: 'Not authenticated'
      }
    }

    // Super admin has all privileges
    if (currentUser.isSuperAdmin) {
      return {
        hasPrivilege: true,
        level: 'super_admin'
      }
    }

    // Check user's specific privileges
    const userPrivilege = currentUser.privileges.find(p => p.privilege === privilege)
    if (!userPrivilege) {
      return {
        hasPrivilege: false,
        level: 'none',
        reason: 'Privilege not granted'
      }
    }

    // Check if privilege has expired
    if (userPrivilege.expiresAt && new Date(userPrivilege.expiresAt) < new Date()) {
      return {
        hasPrivilege: false,
        level: 'none',
        reason: 'Privilege has expired',
        expiresAt: userPrivilege.expiresAt
      }
    }

    // Check privilege level
    const privilegeLevels: PrivilegeLevel[] = ['none', 'read', 'write', 'admin', 'super_admin']
    const userLevelIndex = privilegeLevels.indexOf(userPrivilege.level)
    const requiredLevelIndex = privilegeLevels.indexOf(requiredLevel)

    if (userLevelIndex >= requiredLevelIndex) {
      return {
        hasPrivilege: true,
        level: userPrivilege.level,
        conditions: userPrivilege.conditions,
        expiresAt: userPrivilege.expiresAt
      }
    }

    return {
      hasPrivilege: false,
      level: userPrivilege.level,
      reason: `Insufficient privilege level (has ${userPrivilege.level}, requires ${requiredLevel})`
    }
  }

  const refreshSession = async (): Promise<boolean> => {
    try {
      const sessionToken = localStorage.getItem('voluntier_session_token')
      if (!sessionToken || !currentSession) {
        return false
      }

      // Validate current session through Temporal
      const validationResult = await temporalWorkflowService.validateSession({
        sessionToken,
        ipAddress: 'localhost',
      })

      if (validationResult.status === 'success' && validationResult.data.valid) {
        // Extend session by 8 hours
        const extendedSession = {
          ...currentSession,
          expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
          lastActivity: new Date().toISOString()
        }

        setSessionData(current => ({
          ...current,
          [sessionToken]: extendedSession
        }))

        setCurrentSession(extendedSession)
        return true
      } else {
        // Session invalid - sign out
        await signOut()
        return false
      }
    } catch (error) {
      console.error('Session refresh error:', error)
      return false
    }
  }

  const value: AuthContextType = {
    currentUser,
    currentSession,
    regularUser,
    isAuthenticated: !!currentUser,
    isLoading,
    signIn,
    signOut,
    hasPrivilege,
    refreshSession
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}