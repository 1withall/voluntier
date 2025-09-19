// Authentication and privilege management service
import { useLocalStorage } from '../hooks/useLocalStorage'
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

  // Zero-trust crypto utilities
  static async generateSecurePassword(length: number = 21): Promise<string> {
    const chars = {
      lowercase: 'abcdefghijklmnopqrstuvwxyz',
      uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
      numbers: '0123456789',
      symbols: '!@#$%^&*()_+-=[]{}|;:,.<>?'
    }
    
    const allChars = chars.lowercase + chars.uppercase + chars.numbers + chars.symbols
    
    // Ensure at least one of each type
    let password = 
      chars.lowercase[Math.floor(Math.random() * chars.lowercase.length)] +
      chars.uppercase[Math.floor(Math.random() * chars.uppercase.length)] +
      chars.numbers[Math.floor(Math.random() * chars.numbers.length)] +
      chars.symbols[Math.floor(Math.random() * chars.symbols.length)]
    
    // Fill remaining length
    for (let i = 4; i < length; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)]
    }
    
    // Shuffle the password
    return password.split('').sort(() => Math.random() - 0.5).join('')
  }

  static generateDeviceFingerprint(): string {
    const components = [
      navigator.userAgent,
      navigator.language,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset().toString(),
      navigator.platform,
      navigator.hardwareConcurrency?.toString() || 'unknown',
      navigator.deviceMemory?.toString() || 'unknown'
    ]
    
    const fingerprint = components.join('|')
    
    // Simple hash
    let hash = 0
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    
    return Math.abs(hash).toString(36)
  }

  static async encryptData(data: string, key: string): Promise<string> {
    const encoder = new TextEncoder()
    const dataBuffer = encoder.encode(data)
    const keyBuffer = encoder.encode(key)
    
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyBuffer,
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    )
    
    const iv = crypto.getRandomValues(new Uint8Array(12))
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      dataBuffer
    )
    
    const combined = new Uint8Array(iv.length + encrypted.byteLength)
    combined.set(iv)
    combined.set(new Uint8Array(encrypted), iv.length)
    
    return btoa(String.fromCharCode(...combined))
  }

  static async decryptData(encryptedData: string, key: string): Promise<string> {
    const encrypted = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0))
    const iv = encrypted.slice(0, 12)
    const data = encrypted.slice(12)
    
    const encoder = new TextEncoder()
    const keyBuffer = encoder.encode(key)
    
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyBuffer,
      { name: 'AES-GCM' },
      false,
      ['decrypt']
    )
    
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      data
    )
    
    const decoder = new TextDecoder()
    return decoder.decode(decrypted)
  }
}

// WebAuthn/FIDO2 Manager
class WebAuthnManager {
  static async isAvailable(): Promise<boolean> {
    return typeof PublicKeyCredential !== 'undefined' &&
           typeof PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable === 'function'
  }

  static async generateRegistrationChallenge(userId: string): Promise<any> {
    // Generate a challenge for WebAuthn registration
    const challenge = new Uint8Array(32)
    crypto.getRandomValues(challenge)
    
    return {
      challenge: btoa(String.fromCharCode(...challenge)),
      rp: {
        name: 'Voluntier Platform',
        id: window.location.hostname
      },
      user: {
        id: btoa(userId),
        name: `user_${userId}`,
        displayName: `User ${userId}`
      },
      pubKeyCredParams: [
        { alg: -7, type: 'public-key' }, // ES256
        { alg: -257, type: 'public-key' } // RS256
      ],
      timeout: 60000,
      attestation: 'direct'
    }
  }

  static async registerCredential(challenge: any): Promise<PublicKeyCredential> {
    const publicKeyCredentialCreationOptions = {
      ...challenge,
      challenge: Uint8Array.from(atob(challenge.challenge), c => c.charCodeAt(0)),
      user: {
        ...challenge.user,
        id: Uint8Array.from(atob(challenge.user.id), c => c.charCodeAt(0))
      }
    }
    
    return await navigator.credentials.create({
      publicKey: publicKeyCredentialCreationOptions
    }) as PublicKeyCredential
  }

  static async generateAuthenticationChallenge(credentialIds: string[]): Promise<any> {
    const challenge = new Uint8Array(32)
    crypto.getRandomValues(challenge)
    
    return {
      challenge: btoa(String.fromCharCode(...challenge)),
      allowCredentials: credentialIds.map(id => ({
        id: Uint8Array.from(atob(id), c => c.charCodeAt(0)),
        type: 'public-key'
      })),
      timeout: 60000,
      userVerification: 'preferred'
    }
  }

  static async authenticateWithCredential(challenge: any): Promise<PublicKeyCredential> {
    const publicKeyCredentialRequestOptions = {
      ...challenge,
      challenge: Uint8Array.from(atob(challenge.challenge), c => c.charCodeAt(0))
    }
    
    return await navigator.credentials.get({
      publicKey: publicKeyCredentialRequestOptions
    }) as PublicKeyCredential
  }
}

// Biometric Manager
class BiometricManager {
  static async isAvailable(): Promise<boolean> {
    return typeof PublicKeyCredential !== 'undefined' &&
           await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
  }

  static async enrollBiometric(userId: string, biometricType: string): Promise<any> {
    // For demonstration - in real implementation, this would capture actual biometric data
    // This is a placeholder that simulates biometric enrollment
    const mockBiometricData = {
      type: biometricType,
      data: btoa(Math.random().toString()),
      quality: 0.85,
      timestamp: new Date().toISOString()
    }
    
    return mockBiometricData
  }

  static async verifyBiometric(userId: string, biometricType: string): Promise<any> {
    // For demonstration - in real implementation, this would verify against stored biometric data
    const mockVerification = {
      verified: Math.random() > 0.1, // 90% success rate for demo
      confidence: Math.random() * 0.3 + 0.7, // 0.7-1.0 confidence
      timestamp: new Date().toISOString()
    }
    
    return mockVerification
  }
}

// Risk Assessment Engine
class RiskAssessmentEngine {
  static assessRisk(context: {
    ipAddress: string
    userAgent: string
    deviceFingerprint: string
    location?: any
    behavioralData?: any
  }): number {
    let riskScore = 0.1 // Base risk
    
    // IP-based risk (simplified)
    if (context.ipAddress === 'unknown') {
      riskScore += 0.3
    }
    
    // Location-based risk
    if (context.location && context.location.country !== 'US') {
      riskScore += 0.2
    }
    
    // Time-based risk
    const hour = new Date().getHours()
    if (hour >= 2 && hour <= 6) {
      riskScore += 0.4
    }
    
    // Behavioral risk (simplified)
    if (context.behavioralData) {
      const keystrokeAnomalies = context.behavioralData.keystrokeAnomalies || 0
      riskScore += keystrokeAnomalies * 0.1
    }
    
    return Math.min(riskScore, 1.0)
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
  // Zero-trust methods
  zeroTrustSignIn?: (email: string, password: string, options?: any) => Promise<AuthenticationResult>
  registerHardwareToken?: (userId: string) => Promise<{ success: boolean; credential?: any; error?: string }>
  authenticateWithHardwareToken?: (userId: string) => Promise<{ success: boolean; error?: string }>
  enrollBiometric?: (userId: string, biometricType: string) => Promise<{ success: boolean; error?: string }>
  verifyBiometric?: (userId: string, biometricType: string) => Promise<{ success: boolean; confidence?: number; error?: string }>
  assessAuthenticationRisk?: (context?: any) => Promise<{ riskScore: number; riskLevel: string; recommendations: string[] }>
  generateSecurePassword?: (length?: number) => Promise<string>
  generateSecureCredentials?: (userId: string, options?: any) => Promise<{ success: boolean; credentials?: any; error?: string }>
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
  const [regularUser, setRegularUser] = useLocalStorage<UserProfile | null>('user-profile', null)
  const [isLoading, setIsLoading] = useState(true)
  const [adminUsers, setAdminUsers] = useLocalStorage<AdminUser[]>('admin-users', [])
  const [sessionData, setSessionData] = useLocalStorage<Record<string, ActiveSession>>('active-sessions', {})
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

  // Zero-trust authentication methods
  const zeroTrustSignIn = async (email: string, password: string, options?: {
    deviceFingerprint?: string
    location?: any
    behavioralData?: any
  }): Promise<AuthenticationResult> => {
    try {
      setIsLoading(true)

      const deviceFingerprint = options?.deviceFingerprint || AuthCrypto.generateDeviceFingerprint()
      const location = options?.location || {}
      const behavioralData = options?.behavioralData || {}

      // Use zero-trust authentication workflow
      const authResult = await temporalWorkflowService.zeroTrustAuthenticate({
        email,
        password,
        ipAddress: 'localhost', // In production, get real IP
        userAgent: navigator.userAgent,
        deviceFingerprint,
        location,
        behavioralData
      })

      if (authResult.status === 'success' && authResult.data.authenticated) {
        // Store session information
        localStorage.setItem('voluntier_session_token', authResult.data.session_id)
        localStorage.setItem('voluntier_risk_score', authResult.data.risk_score.toString())

        // Create session object
        const session: ActiveSession = {
          token: authResult.data.session_id,
          createdAt: new Date().toISOString(),
          expiresAt: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
          ipAddress: 'localhost',
          userAgent: navigator.userAgent,
          lastActivity: new Date().toISOString(),
          riskScore: authResult.data.risk_score,
          deviceFingerprint
        }

        setSessionData(current => ({
          ...current,
          [authResult.data.session_id]: session
        }))

        setCurrentSession(session)

        return {
          success: true,
          user: authResult.data.user_data,
          session,
          riskScore: authResult.data.risk_score,
          requiresAdditionalFactors: authResult.data.requires_additional_factors,
          additionalFactors: authResult.data.additional_factors
        }
      } else {
        return {
          success: false,
          error: authResult.data.message || 'Zero-trust authentication failed',
          riskScore: authResult.data.risk_score || 0
        }
      }
    } catch (error) {
      console.error('Zero-trust sign in error:', error)
      return {
        success: false,
        error: 'Zero-trust authentication service error'
      }
    } finally {
      setIsLoading(false)
    }
  }

  const registerHardwareToken = async (userId: string): Promise<{ success: boolean; credential?: any; error?: string }> => {
    try {
      // Check if WebAuthn is available
      if (!await WebAuthnManager.isAvailable()) {
        return { success: false, error: 'WebAuthn not supported' }
      }

      // Generate registration challenge
      const challenge = await WebAuthnManager.generateRegistrationChallenge(userId)

      // Register the credential
      const credential = await WebAuthnManager.registerCredential(challenge)

      // Send to backend for verification and storage
      const registrationResult = await temporalWorkflowService.registerHardwareToken({
        userId,
        challengeResponse: {
          id: credential.id,
          rawId: btoa(String.fromCharCode(...new Uint8Array(credential.rawId))),
          response: {
            clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(credential.response.clientDataJSON))),
            attestationObject: btoa(String.fromCharCode(...new Uint8Array(credential.response.attestationObject)))
          },
          type: credential.type
        }
      })

      if (registrationResult.status === 'success' && registrationResult.data.registered) {
        return { success: true, credential }
      } else {
        return { success: false, error: 'Hardware token registration failed' }
      }
    } catch (error) {
      console.error('Hardware token registration error:', error)
      return { success: false, error: 'Hardware token registration failed' }
    }
  }

  const authenticateWithHardwareToken = async (userId: string): Promise<{ success: boolean; error?: string }> => {
    try {
      // Get user's registered credentials (in production, fetch from backend)
      const credentials = ['dummy_credential_id'] // Placeholder

      // Generate authentication challenge
      const challenge = await WebAuthnManager.generateAuthenticationChallenge(credentials)

      // Authenticate with credential
      const assertion = await WebAuthnManager.authenticateWithCredential(challenge)

      // Verify with backend
      const authResult = await temporalWorkflowService.authenticateWithHardwareToken({
        userId,
        challengeResponse: {
          id: assertion.id,
          rawId: btoa(String.fromCharCode(...new Uint8Array(assertion.rawId))),
          response: {
            clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
            authenticatorData: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
            signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
            userHandle: assertion.response.userHandle ? 
              btoa(String.fromCharCode(...new Uint8Array(assertion.response.userHandle))) : null
          },
          type: assertion.type
        }
      })

      return {
        success: authResult.status === 'success' && authResult.data.authenticated
      }
    } catch (error) {
      console.error('Hardware token authentication error:', error)
      return { success: false, error: 'Hardware token authentication failed' }
    }
  }

  const enrollBiometric = async (userId: string, biometricType: string): Promise<{ success: boolean; error?: string }> => {
    try {
      // Check if biometric authentication is available
      if (!await BiometricManager.isAvailable()) {
        return { success: false, error: 'Biometric authentication not available' }
      }

      // Enroll biometric data
      const biometricData = await BiometricManager.enrollBiometric(userId, biometricType)

      // Send to backend
      const enrollmentResult = await temporalWorkflowService.enrollBiometric({
        userId,
        biometricType,
        biometricData: btoa(JSON.stringify(biometricData)),
        qualityScore: biometricData.quality
      })

      return {
        success: enrollmentResult.status === 'success' && enrollmentResult.data.enrolled
      }
    } catch (error) {
      console.error('Biometric enrollment error:', error)
      return { success: false, error: 'Biometric enrollment failed' }
    }
  }

  const verifyBiometric = async (userId: string, biometricType: string): Promise<{ success: boolean; confidence?: number; error?: string }> => {
    try {
      // Verify biometric data
      const verificationData = await BiometricManager.verifyBiometric(userId, biometricType)

      // Send to backend for verification
      const verifyResult = await temporalWorkflowService.verifyBiometric({
        userId,
        biometricType,
        biometricData: btoa(JSON.stringify(verificationData))
      })

      if (verifyResult.status === 'success') {
        return {
          success: verifyResult.data.verified,
          confidence: verifyResult.data.confidence_score
        }
      } else {
        return { success: false, error: 'Biometric verification failed' }
      }
    } catch (error) {
      console.error('Biometric verification error:', error)
      return { success: false, error: 'Biometric verification failed' }
    }
  }

  const assessAuthenticationRisk = async (context?: {
    ipAddress?: string
    userAgent?: string
    deviceFingerprint?: string
    location?: any
    behavioralData?: any
  }): Promise<{ riskScore: number; riskLevel: string; recommendations: string[] }> => {
    try {
      const assessmentContext = {
        ipAddress: context?.ipAddress || 'localhost',
        userAgent: context?.userAgent || navigator.userAgent,
        deviceFingerprint: context?.deviceFingerprint || AuthCrypto.generateDeviceFingerprint(),
        location: context?.location || {},
        behavioralData: context?.behavioralData || {}
      }

      // Local risk assessment
      const localRiskScore = RiskAssessmentEngine.assessRisk(assessmentContext)

      // Backend risk assessment
      const backendResult = await temporalWorkflowService.assessAuthenticationRisk({
        userId: currentUser?.id,
        sessionId: currentSession?.token,
        ...assessmentContext
      })

      if (backendResult.status === 'success') {
        return {
          riskScore: backendResult.data.risk_score,
          riskLevel: backendResult.data.risk_level,
          recommendations: backendResult.data.recommended_actions
        }
      } else {
        // Fallback to local assessment
        return {
          riskScore: localRiskScore,
          riskLevel: localRiskScore > 0.7 ? 'HIGH' : localRiskScore > 0.4 ? 'MEDIUM' : 'LOW',
          recommendations: localRiskScore > 0.7 ? ['require_mfa', 'notify_security'] : ['monitor_session']
        }
      }
    } catch (error) {
      console.error('Risk assessment error:', error)
      return {
        riskScore: 0.5,
        riskLevel: 'MEDIUM',
        recommendations: ['monitor_session']
      }
    }
  }

  const generateSecurePassword = async (length: number = 21): Promise<string> => {
    return await AuthCrypto.generateSecurePassword(length)
  }

  const generateSecureCredentials = async (userId: string, options?: {
    includePassword?: boolean
    includeRecoveryCodes?: boolean
    passwordLength?: number
  }): Promise<{ success: boolean; credentials?: any; error?: string }> => {
    try {
      const result = await temporalWorkflowService.generateSecureCredentials({
        userId,
        includePassword: options?.includePassword,
        includeRecoveryCodes: options?.includeRecoveryCodes,
        passwordLength: options?.passwordLength
      })

      if (result.status === 'success') {
        return { success: true, credentials: result.data }
      } else {
        return { success: false, error: 'Credential generation failed' }
      }
    } catch (error) {
      console.error('Credential generation error:', error)
      return { success: false, error: 'Credential generation failed' }
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
    refreshSession,
    // Zero-trust methods
    zeroTrustSignIn,
    registerHardwareToken,
    authenticateWithHardwareToken,
    enrollBiometric,
    verifyBiometric,
    assessAuthenticationRisk,
    generateSecurePassword,
    generateSecureCredentials
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}