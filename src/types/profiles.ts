export interface BaseProfile {
  id: string
  createdAt: string
  updatedAt: string
  verificationStatus: 'pending' | 'in_progress' | 'verified' | 'rejected' | 'suspended'
  securityScore: number
  flagged: boolean
  lastActiveAt: string
  onboardingCompleted: boolean
  profileCompleteness: number
}

export interface IndividualProfile extends BaseProfile {
  userType: 'individual'
  personalInfo: {
    firstName: string
    lastName: string
    email: string
    phoneNumber: string
    dateOfBirth: string
    gender?: string
    pronouns?: string
  }
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
  preferences: {
    skills: string[]
    interests: string[]
    availability: {
      days: string[]
      timeSlots: string[]
      hoursPerWeek: number
      travelDistance: number
      transportation: string[]
    }
    communication: {
      emailNotifications: boolean
      smsNotifications: boolean
      preferredLanguage: string
      accessibility: {
        screenReader: boolean
        largeText: boolean
        highContrast: boolean
        captions: boolean
      }
    }
  }
  verification: {
    references: PersonalReference[]
    backgroundCheckStatus: 'pending' | 'in_progress' | 'completed' | 'failed'
    backgroundCheckConsent: boolean
    identityDocuments: VerificationDocument[]
    inPersonVerification: {
      completed: boolean
      verifiedBy?: string
      verificationDate?: string
      qrCodeUsed?: string
    }
  }
  volunteerHistory: {
    hoursLogged: number
    eventsAttended: number
    organizationsWorkedWith: string[]
    specialRecognitions: string[]
    currentCommitments: string[]
  }
  safety: {
    emergencyMedicalInfo?: string
    allergies?: string[]
    medications?: string[]
    medicalConditions?: string[]
    dietaryRestrictions?: string[]
  }
  gamification: {
    points: number
    badges: Badge[]
    level: number
    achievements: Achievement[]
    streaks: {
      current: number
      longest: number
    }
  }
}

export interface OrganizationProfile extends BaseProfile {
  userType: 'organization'
  organizationInfo: {
    legalName: string
    dbaName?: string
    ein: string
    organizationType: 'nonprofit' | 'charity' | 'religious' | 'educational' | 'government' | 'other'
    missionStatement: string
    description: string
    website?: string
    foundedYear: number
    numberOfEmployees: string
    annualBudget: string
  }
  contactInfo: {
    primaryEmail: string
    primaryPhone: string
    address: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
    mailingAddress?: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
  }
  leadership: {
    executiveDirector: ContactPerson
    boardChair?: ContactPerson
    volunteerCoordinator?: ContactPerson
    additionalContacts: ContactPerson[]
  }
  operations: {
    operatingHours: {
      [day: string]: {
        open: string
        close: string
        closed: boolean
      }
    }
    serviceAreas: string[]
    populationsServed: string[]
    programsOffered: string[]
    facilityCapacity: number
    accessibilityFeatures: string[]
  }
  verification: {
    legalStatus: VerificationDocument[]
    insurance: {
      generalLiability: VerificationDocument
      workersCompensation?: VerificationDocument
      volunteerAccident?: VerificationDocument
    }
    financialReports: VerificationDocument[]
    references: OrganizationReference[]
    facilityInspection: {
      completed: boolean
      inspectorId?: string
      inspectionDate?: string
      report?: VerificationDocument
    }
  }
  capabilities: {
    canVerifyVolunteers: boolean
    maxVolunteersPerEvent: number
    trainingPrograms: string[]
    equipmentAvailable: string[]
    specialCertifications: string[]
  }
  compliance: {
    backgroundCheckPolicy: boolean
    safeguardingPolicy: boolean
    dataProtectionCompliance: boolean
    volunteerAgreements: boolean
    incidentReportingProcess: boolean
  }
}

export interface BusinessProfile extends BaseProfile {
  userType: 'business'
  businessInfo: {
    legalName: string
    dbaName?: string
    ein: string
    businessType: 'corporation' | 'llc' | 'partnership' | 'sole_proprietorship' | 'other'
    industry: string
    description: string
    website?: string
    foundedYear: number
    numberOfEmployees: string
    annualRevenue: string
  }
  contactInfo: {
    primaryEmail: string
    primaryPhone: string
    address: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
    mailingAddress?: {
      street: string
      city: string
      state: string
      zipCode: string
      country: string
    }
  }
  leadership: {
    ceo: ContactPerson
    csrDirector?: ContactPerson
    hrDirector?: ContactPerson
    communityRelations?: ContactPerson
    additionalContacts: ContactPerson[]
  }
  csrProgram: {
    hasEstablishedProgram: boolean
    programDescription?: string
    annualCSRBudget?: string
    employeeVolunteerPolicy?: string
    paidVolunteerTime?: boolean
    hoursPerEmployee?: number
    focusAreas: string[]
    partnershipHistory: string[]
  }
  verification: {
    businessLicense: VerificationDocument[]
    insurance: {
      generalLiability: VerificationDocument
      workersCompensation: VerificationDocument
      professionalLiability?: VerificationDocument
    }
    financialStanding: {
      creditReport?: VerificationDocument
      bankReference?: VerificationDocument
      taxCompliance?: VerificationDocument
    }
    references: BusinessReference[]
    ethicsCompliance: {
      codeOfConduct: VerificationDocument
      ethicsTraining: boolean
      complianceOfficer?: ContactPerson
    }
  }
  offerings: {
    skillBasedVolunteering: string[]
    mentorshipPrograms: string[]
    trainingResources: string[]
    equipmentDonations: string[]
    venueSpaces: string[]
    financialSupport: {
      grants: boolean
      sponsorships: boolean
      matchingGifts: boolean
    }
  }
  employeeEngagement: {
    volunteerProgram: boolean
    teamBuildingEvents: boolean
    skillSharingInitiatives: boolean
    communityPartnershipEvents: boolean
    employeeVolunteerTracking: boolean
  }
}

export interface ContactPerson {
  name: string
  title: string
  email: string
  phoneNumber: string
  department?: string
  isPrimary: boolean
}

export interface PersonalReference {
  id: string
  name: string
  relationship: string
  email: string
  phoneNumber: string
  yearsKnown: number
  verificationStatus: 'pending' | 'contacted' | 'verified' | 'failed'
  verificationDate?: string
  verificationNotes?: string
}

export interface OrganizationReference {
  id: string
  organizationName: string
  contactPerson: ContactPerson
  relationship: string
  yearsWorkedWith: number
  verificationStatus: 'pending' | 'contacted' | 'verified' | 'failed'
  verificationDate?: string
  verificationNotes?: string
}

export interface BusinessReference {
  id: string
  companyName: string
  contactPerson: ContactPerson
  relationship: string
  yearsWorkedWith: number
  verificationStatus: 'pending' | 'contacted' | 'verified' | 'failed'
  verificationDate?: string
  verificationNotes?: string
}

export interface VerificationDocument {
  id: string
  type: string
  fileName: string
  uploadDate: string
  status: 'pending' | 'under_review' | 'approved' | 'rejected'
  expirationDate?: string
  reviewNotes?: string
}

export interface Badge {
  id: string
  name: string
  description: string
  iconUrl: string
  earnedDate: string
  category: string
}

export interface Achievement {
  id: string
  name: string
  description: string
  requirements: string
  progress: number
  completed: boolean
  completedDate?: string
  category: string
}

export interface OnboardingStep {
  id: string
  title: string
  description: string
  completed: boolean
  required: boolean
  order: number
  estimatedTime: string
}

export interface OnboardingProgress {
  currentStep: number
  totalSteps: number
  completedSteps: string[]
  percentComplete: number
  estimatedTimeRemaining: string
}

export type UserProfile = IndividualProfile | OrganizationProfile | BusinessProfile