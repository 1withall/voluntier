// Comprehensive privilege and role-based access control system

export type PrivilegeLevel = 'none' | 'read' | 'write' | 'admin' | 'super_admin'

export type SystemPrivilege = 
  | 'view_security_dashboard'
  | 'manage_security_settings'
  | 'view_telemetry'
  | 'manage_telemetry'
  | 'view_analytics'
  | 'manage_analytics'
  | 'manage_users'
  | 'manage_organizations'
  | 'manage_system_config'
  | 'view_audit_logs'
  | 'manage_audit_logs'
  | 'emergency_override'
  | 'system_maintenance'
  | 'data_export'
  | 'data_import'
  | 'manage_privileges'
  | 'view_financial_data'
  | 'manage_financial_data'

export type UserPrivilege =
  | 'create_events'
  | 'manage_events'
  | 'verify_individuals'
  | 'post_training_materials'
  | 'access_reporting'
  | 'sponsor_events'
  | 'offer_internships'
  | 'bulk_messaging'
  | 'view_participant_data'
  | 'manage_participant_data'

export type AllPrivileges = SystemPrivilege | UserPrivilege

export interface PrivilegeConfig {
  privilege: AllPrivileges
  level: PrivilegeLevel
  grantedAt: string
  grantedBy: string
  expiresAt?: string
  conditions?: PrivilegeCondition[]
}

export interface PrivilegeCondition {
  type: 'time_based' | 'location_based' | 'verification_level' | 'approval_required'
  parameters: Record<string, any>
}

export interface UserRole {
  id: string
  name: string
  description: string
  privileges: PrivilegeConfig[]
  isSystem: boolean
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface AdminUser {
  id: string
  email: string
  passwordHash: string
  salt: string
  isSystem: boolean
  isSuperAdmin: boolean
  roles: string[]
  privileges: PrivilegeConfig[]
  createdAt: string
  lastLoginAt?: string
  loginAttempts: number
  lockedUntil?: string
  twoFactorEnabled: boolean
  twoFactorSecret?: string
  sessionTokens: ActiveSession[]
}

export interface ActiveSession {
  token: string
  createdAt: string
  expiresAt: string
  ipAddress: string
  userAgent: string
  lastActivity: string
}

export interface AuthenticationResult {
  success: boolean
  user?: AdminUser
  session?: ActiveSession
  error?: string
  requiresTwoFactor?: boolean
  remainingAttempts?: number
}

export interface PrivilegeCheckResult {
  hasPrivilege: boolean
  level: PrivilegeLevel
  reason?: string
  conditions?: PrivilegeCondition[]
  expiresAt?: string
}

// Predefined system roles
export const SYSTEM_ROLES = {
  SUPER_ADMIN: {
    id: 'super_admin',
    name: 'Super Administrator',
    description: 'Full system access with all privileges',
    isSystem: true,
    privileges: [
      'view_security_dashboard',
      'manage_security_settings',
      'view_telemetry',
      'manage_telemetry',
      'view_analytics',
      'manage_analytics',
      'manage_users',
      'manage_organizations',
      'manage_system_config',
      'view_audit_logs',
      'manage_audit_logs',
      'emergency_override',
      'system_maintenance',
      'data_export',
      'data_import',
      'manage_privileges',
      'view_financial_data',
      'manage_financial_data'
    ]
  },
  SECURITY_ADMIN: {
    id: 'security_admin',
    name: 'Security Administrator',
    description: 'Security and audit management',
    isSystem: true,
    privileges: [
      'view_security_dashboard',
      'manage_security_settings',
      'view_audit_logs',
      'manage_audit_logs',
      'view_telemetry',
      'emergency_override'
    ]
  },
  ANALYTICS_ADMIN: {
    id: 'analytics_admin',
    name: 'Analytics Administrator',
    description: 'Analytics and reporting access',
    isSystem: true,
    privileges: [
      'view_analytics',
      'manage_analytics',
      'view_telemetry',
      'data_export',
      'access_reporting'
    ]
  },
  USER_ADMIN: {
    id: 'user_admin',
    name: 'User Administrator',
    description: 'User and organization management',
    isSystem: true,
    privileges: [
      'manage_users',
      'manage_organizations',
      'view_audit_logs',
      'access_reporting'
    ]
  }
} as const

// Default privileges by user type
export const DEFAULT_USER_PRIVILEGES: Record<string, UserPrivilege[]> = {
  individual: [],
  organization: [
    'create_events',
    'manage_events',
    'verify_individuals',
    'post_training_materials',
    'access_reporting'
  ],
  business: [
    'create_events',
    'manage_events',
    'post_training_materials',
    'sponsor_events',
    'offer_internships',
    'access_reporting'
  ]
}

export const PRIVILEGE_DESCRIPTIONS: Record<AllPrivileges, string> = {
  // System privileges
  view_security_dashboard: 'View security dashboard and monitoring data',
  manage_security_settings: 'Modify security configurations and policies',
  view_telemetry: 'Access telemetry and usage analytics',
  manage_telemetry: 'Configure telemetry collection and processing',
  view_analytics: 'View site analytics and performance metrics',
  manage_analytics: 'Configure analytics settings and reports',
  manage_users: 'Create, modify, and deactivate user accounts',
  manage_organizations: 'Manage organization accounts and verification',
  manage_system_config: 'Modify system-wide configuration settings',
  view_audit_logs: 'Access system audit trails and logs',
  manage_audit_logs: 'Configure audit logging and retention',
  emergency_override: 'Emergency system access during incidents',
  system_maintenance: 'Perform system maintenance operations',
  data_export: 'Export system data for backup or analysis',
  data_import: 'Import data into the system',
  manage_privileges: 'Grant and revoke user privileges',
  view_financial_data: 'Access financial and billing information',
  manage_financial_data: 'Modify financial settings and billing',

  // User privileges
  create_events: 'Create volunteer events and opportunities',
  manage_events: 'Modify and delete own events',
  verify_individuals: 'Verify individual user accounts',
  post_training_materials: 'Upload and share training content',
  access_reporting: 'Generate and view activity reports',
  sponsor_events: 'Sponsor events and provide funding',
  offer_internships: 'Post internship opportunities',
  bulk_messaging: 'Send messages to multiple users',
  view_participant_data: 'View participant information',
  manage_participant_data: 'Modify participant records'
}