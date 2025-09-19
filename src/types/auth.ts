// Authentication and user management type definitions

export type UserType = 'individual' | 'organization' | 'business'

export type VerificationStatus = 'pending' | 'in_progress' | 'verified' | 'rejected' | 'suspended'

export interface BaseUser {
  id: string
  email: string
  userType: UserType
  verificationStatus: VerificationStatus
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
  securityScore: number
  flagged: boolean
  notes?: string
}

export interface IndividualUser extends BaseUser {
  userType: 'individual'
  profile: {
    firstName: string
    lastName: string
    dateOfBirth: string
    phoneNumber: string
    address: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
    emergencyContact: {
      name: string
      relationship: string
      phoneNumber: string
      email?: string
    }
    skills: string[]
    interests: string[]
    availability: {
      days: string[]
      timeSlots: string[]
      hoursPerWeek: number
    }
    references: PersonalReference[]
    backgroundCheckConsent: boolean
    communicationPreferences: {
      email: boolean
      sms: boolean
      push: boolean
    }
  }
  verification: {
    documentsUploaded: boolean
    referencesVerified: number
    inPersonVerificationComplete: boolean
    backgroundCheckComplete: boolean
    verificationCode?: string
    qrCodeScannedBy?: string
    verificationDate?: string
  }
}

export interface OrganizationUser extends BaseUser {
  userType: 'organization'
  profile: {
    organizationName: string
    organizationType: 'nonprofit' | 'government' | 'religious' | 'educational' | 'community'
    registrationNumber?: string
    taxExemptStatus?: string
    mission: string
    description: string
    website?: string
    address: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
    contactInfo: {
      primaryContact: {
        name: string
        title: string
        email: string
        phoneNumber: string
      }
      publicEmail: string
      publicPhone: string
    }
    servicesOffered: string[]
    targetPopulation: string[]
    operatingHours: {
      [day: string]: {
        open: string
        close: string
      }
    }
    capacity: {
      volunteersNeeded: number
      eventsPerMonth: number
      participantsServed: number
    }
  }
  verification: {
    documentsUploaded: boolean
    legalStatusVerified: boolean
    leadershipVerified: boolean
    insuranceVerified: boolean
    facilitiesInspected: boolean
    verificationOfficials: string[]
  }
  permissions: {
    createEvents: boolean
    verifyIndividuals: boolean
    postTrainingMaterials: boolean
    accessReporting: boolean
  }
}

export interface BusinessUser extends BaseUser {
  userType: 'business'
  profile: {
    businessName: string
    businessType: 'corporation' | 'llc' | 'partnership' | 'sole_proprietorship' | 'other'
    industry: string
    registrationNumber: string
    taxId: string
    description: string
    website?: string
    address: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
    contactInfo: {
      primaryContact: {
        name: string
        title: string
        email: string
        phoneNumber: string
      }
      publicEmail: string
      publicPhone: string
    }
    csrProgram: {
      description: string
      budget: number
      focusAreas: string[]
      goals: string[]
    }
    offerings: {
      volunteerPrograms: string[]
      skillBasedVolunteering: string[]
      financialSupport: string[]
      resourceDonations: string[]
      trainingPrograms: string[]
    }
    employeeVolunteering: {
      paidVolunteerTime: boolean
      hoursPerEmployee: number
      teamBuilding: boolean
    }
  }
  verification: {
    documentsUploaded: boolean
    businessLicenseVerified: boolean
    financialStandingVerified: boolean
    leadershipVerified: boolean
    csrPolicyVerified: boolean
    ethicsComplianceVerified: boolean
  }
  permissions: {
    createEvents: boolean
    postTrainingMaterials: boolean
    sponsorEvents: boolean
    accessReporting: boolean
    offerInternships: boolean
  }
}

export interface PersonalReference {
  id: string
  name: string
  relationship: string
  email: string
  phoneNumber: string
  yearsKnown: number
  verificationStatus: 'pending' | 'contacted' | 'verified' | 'failed'
  verificationCode?: string
  notes?: string
}

export interface SecurityEvent {
  id: string
  userId: string
  eventType: 'login_attempt' | 'verification_failure' | 'suspicious_activity' | 'data_breach' | 'system_alert'
  severity: 'low' | 'medium' | 'high' | 'critical'
  description: string
  metadata: Record<string, any>
  timestamp: string
  resolved: boolean
  resolvedBy?: string
  resolvedAt?: string
}

export interface VerificationQRCode {
  id: string
  code: string
  userId: string
  generatedBy: string
  expiresAt: string
  scannedAt?: string
  scannedBy?: string
  location?: {
    latitude: number
    longitude: number
    accuracy: number
  }
  verified: boolean
}