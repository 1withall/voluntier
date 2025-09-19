// Test accounts for each user type with predefined credentials
// Username pattern: test_<account_type>
// Password: 1Fake_passw0rd.

import { IndividualProfile, OrganizationProfile, BusinessProfile } from '../types/profiles'

export interface TestCredentials {
  username: string
  password: string
  userType: 'individual' | 'organization' | 'business'
}

export const testCredentials: TestCredentials[] = [
  {
    username: 'test_individual',
    password: '1Fake_passw0rd.',
    userType: 'individual'
  },
  {
    username: 'test_organization',
    password: '1Fake_passw0rd.',
    userType: 'organization'
  },
  {
    username: 'test_business',
    password: '1Fake_passw0rd.',
    userType: 'business'
  }
]

export const testIndividualProfile: IndividualProfile = {
  id: 'test-individual-001',
  userType: 'individual',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  verificationStatus: 'verified',
  securityScore: 85,
  flagged: false,
  lastActiveAt: new Date().toISOString(),
  onboardingCompleted: true,
  profileCompleteness: 95,
  personalInfo: {
    firstName: 'Test',
    lastName: 'Individual',
    email: 'test.individual@example.com',
    phoneNumber: '+1-555-0101',
    dateOfBirth: '1990-05-15',
    gender: 'prefer-not-to-say',
    pronouns: 'they/them'
  },
  address: {
    street: '123 Test Street',
    city: 'Testville',
    state: 'TS',
    zipCode: '12345',
    country: 'United States'
  },
  emergencyContact: {
    name: 'Emergency Contact',
    relationship: 'Friend',
    phoneNumber: '+1-555-0102',
    email: 'emergency.contact@example.com'
  },
  preferences: {
    skills: ['Customer Service', 'Teaching', 'Organization', 'Technology'],
    interests: ['Education', 'Community Support', 'Environment', 'Youth Development'],
    availability: {
      days: ['Saturday', 'Sunday'],
      timeSlots: ['Morning', 'Afternoon'],
      hoursPerWeek: 8,
      travelDistance: 15,
      transportation: ['Personal Vehicle', 'Public Transit']
    },
    communication: {
      emailNotifications: true,
      smsNotifications: false,
      preferredLanguage: 'English',
      accessibility: {
        screenReader: false,
        largeText: false,
        highContrast: false,
        captions: false
      }
    }
  },
  verification: {
    references: [
      {
        id: 'ref-001',
        name: 'John Reference',
        relationship: 'Former Supervisor',
        email: 'john.reference@example.com',
        phoneNumber: '+1-555-0103',
        yearsKnown: 3,
        verificationStatus: 'verified',
        verificationDate: new Date().toISOString(),
        verificationNotes: 'Excellent character and work ethic'
      },
      {
        id: 'ref-002',
        name: 'Jane Character',
        relationship: 'Friend',
        email: 'jane.character@example.com',
        phoneNumber: '+1-555-0104',
        yearsKnown: 5,
        verificationStatus: 'verified',
        verificationDate: new Date().toISOString(),
        verificationNotes: 'Trustworthy and reliable volunteer'
      }
    ],
    backgroundCheckStatus: 'completed',
    backgroundCheckConsent: true,
    identityDocuments: [
      {
        id: 'doc-001',
        type: 'Driver License',
        fileName: 'drivers_license.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2028-05-15',
        reviewNotes: 'Valid state-issued ID verified'
      }
    ],
    inPersonVerification: {
      completed: true,
      verifiedBy: 'org-001',
      verificationDate: new Date().toISOString(),
      qrCodeUsed: 'QR-TEST-001'
    }
  },
  volunteerHistory: {
    hoursLogged: 45,
    eventsAttended: 8,
    organizationsWorkedWith: ['Local Food Bank', 'Green Earth Society'],
    specialRecognitions: ['Volunteer of the Month'],
    currentCommitments: ['Community Food Drive']
  },
  safety: {
    emergencyMedicalInfo: 'No known allergies or medical conditions',
    allergies: [],
    medications: [],
    medicalConditions: [],
    dietaryRestrictions: []
  },
  gamification: {
    points: 1250,
    badges: [
      {
        id: 'badge-001',
        name: 'First Timer',
        description: 'Completed first volunteer event',
        iconUrl: '/badges/first-timer.svg',
        earnedDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'Milestone'
      },
      {
        id: 'badge-002',
        name: 'Team Player',
        description: 'Volunteered with 3+ organizations',
        iconUrl: '/badges/team-player.svg',
        earnedDate: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'Collaboration'
      }
    ],
    level: 3,
    achievements: [
      {
        id: 'achievement-001',
        name: '50 Hour Club',
        description: 'Log 50 hours of volunteer service',
        requirements: 'Complete 50 volunteer hours',
        progress: 90,
        completed: false,
        category: 'Service Hours'
      }
    ],
    streaks: {
      current: 4,
      longest: 7
    }
  }
}

export const testOrganizationProfile: OrganizationProfile = {
  id: 'test-organization-001',
  userType: 'organization',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  verificationStatus: 'verified',
  securityScore: 92,
  flagged: false,
  lastActiveAt: new Date().toISOString(),
  onboardingCompleted: true,
  profileCompleteness: 98,
  organizationInfo: {
    legalName: 'Test Community Foundation',
    dbaName: 'Test Foundation',
    ein: '12-3456789',
    organizationType: 'nonprofit',
    missionStatement: 'To strengthen our community through volunteer coordination and support services.',
    description: 'A test nonprofit organization dedicated to community service and volunteer management.',
    website: 'https://testfoundation.org',
    foundedYear: 2015,
    numberOfEmployees: '10-25',
    annualBudget: '$500K-$1M'
  },
  contactInfo: {
    primaryEmail: 'info@testfoundation.org',
    primaryPhone: '+1-555-0201',
    address: {
      street: '456 Foundation Lane',
      city: 'Testville',
      state: 'TS',
      zipCode: '12345',
      country: 'United States'
    },
    mailingAddress: {
      street: 'PO Box 789',
      city: 'Testville',
      state: 'TS',
      zipCode: '12346',
      country: 'United States'
    }
  },
  leadership: {
    executiveDirector: {
      name: 'Sarah Director',
      title: 'Executive Director',
      email: 'sarah.director@testfoundation.org',
      phoneNumber: '+1-555-0202',
      department: 'Executive',
      isPrimary: true
    },
    boardChair: {
      name: 'Michael Chair',
      title: 'Board Chair',
      email: 'michael.chair@testfoundation.org',
      phoneNumber: '+1-555-0203',
      department: 'Board',
      isPrimary: false
    },
    volunteerCoordinator: {
      name: 'Lisa Coordinator',
      title: 'Volunteer Coordinator',
      email: 'lisa.coordinator@testfoundation.org',
      phoneNumber: '+1-555-0204',
      department: 'Programs',
      isPrimary: false
    },
    additionalContacts: []
  },
  operations: {
    operatingHours: {
      'Monday': { open: '09:00', close: '17:00', closed: false },
      'Tuesday': { open: '09:00', close: '17:00', closed: false },
      'Wednesday': { open: '09:00', close: '17:00', closed: false },
      'Thursday': { open: '09:00', close: '17:00', closed: false },
      'Friday': { open: '09:00', close: '17:00', closed: false },
      'Saturday': { open: '10:00', close: '14:00', closed: false },
      'Sunday': { open: '', close: '', closed: true }
    },
    serviceAreas: ['Community Support', 'Education', 'Environment', 'Health & Wellness'],
    populationsServed: ['All Ages', 'Families', 'Seniors', 'Youth'],
    programsOffered: ['Volunteer Coordination', 'Community Events', 'Skills Training', 'Resource Distribution'],
    facilityCapacity: 150,
    accessibilityFeatures: ['Wheelchair Accessible', 'Accessible Parking', 'Audio Loop System', 'Large Print Materials']
  },
  verification: {
    legalStatus: [
      {
        id: 'doc-org-001',
        type: '501(c)(3) Determination Letter',
        fileName: 'irs_determination_letter.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        reviewNotes: 'Valid nonprofit status confirmed'
      }
    ],
    insurance: {
      generalLiability: {
        id: 'doc-org-002',
        type: 'General Liability Insurance',
        fileName: 'general_liability_certificate.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2025-12-31',
        reviewNotes: '$2M coverage verified'
      },
      volunteerAccident: {
        id: 'doc-org-003',
        type: 'Volunteer Accident Insurance',
        fileName: 'volunteer_accident_policy.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2025-12-31',
        reviewNotes: 'Adequate volunteer coverage'
      }
    },
    financialReports: [
      {
        id: 'doc-org-004',
        type: 'Annual Financial Report',
        fileName: 'annual_financial_2023.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        reviewNotes: 'Financial transparency verified'
      }
    ],
    references: [
      {
        id: 'org-ref-001',
        organizationName: 'State Nonprofit Association',
        contactPerson: {
          name: 'David Reference',
          title: 'Membership Director',
          email: 'david.reference@statenonprofits.org',
          phoneNumber: '+1-555-0205',
          isPrimary: true
        },
        relationship: 'Member Organization',
        yearsWorkedWith: 5,
        verificationStatus: 'verified',
        verificationDate: new Date().toISOString(),
        verificationNotes: 'Active member in good standing'
      }
    ],
    facilityInspection: {
      completed: true,
      inspectorId: 'inspector-001',
      inspectionDate: new Date().toISOString(),
      report: {
        id: 'doc-org-005',
        type: 'Facility Safety Inspection',
        fileName: 'facility_inspection_report.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        reviewNotes: 'All safety requirements met'
      }
    }
  },
  capabilities: {
    canVerifyVolunteers: true,
    maxVolunteersPerEvent: 50,
    trainingPrograms: ['Volunteer Orientation', 'Safety Training', 'First Aid Certification'],
    equipmentAvailable: ['Tables', 'Chairs', 'Sound System', 'Projector', 'Laptops'],
    specialCertifications: ['First Aid Certified Staff', 'Background Check Certified']
  },
  compliance: {
    backgroundCheckPolicy: true,
    safeguardingPolicy: true,
    dataProtectionCompliance: true,
    volunteerAgreements: true,
    incidentReportingProcess: true
  }
}

export const testBusinessProfile: BusinessProfile = {
  id: 'test-business-001',
  userType: 'business',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  verificationStatus: 'verified',
  securityScore: 88,
  flagged: false,
  lastActiveAt: new Date().toISOString(),
  onboardingCompleted: true,
  profileCompleteness: 94,
  businessInfo: {
    legalName: 'Test Solutions Inc.',
    dbaName: 'TestSolutions',
    ein: '98-7654321',
    businessType: 'corporation',
    industry: 'Technology Services',
    description: 'A technology solutions company committed to community engagement and corporate social responsibility.',
    website: 'https://testsolutions.com',
    foundedYear: 2010,
    numberOfEmployees: '50-100',
    annualRevenue: '$5M-$10M'
  },
  contactInfo: {
    primaryEmail: 'community@testsolutions.com',
    primaryPhone: '+1-555-0301',
    address: {
      street: '789 Business Park Drive',
      city: 'Testville',
      state: 'TS',
      zipCode: '12347',
      country: 'United States'
    },
    mailingAddress: {
      street: '789 Business Park Drive',
      city: 'Testville',
      state: 'TS',
      zipCode: '12347',
      country: 'United States'
    }
  },
  leadership: {
    ceo: {
      name: 'Robert CEO',
      title: 'Chief Executive Officer',
      email: 'robert.ceo@testsolutions.com',
      phoneNumber: '+1-555-0302',
      department: 'Executive',
      isPrimary: true
    },
    csrDirector: {
      name: 'Amanda CSR',
      title: 'CSR Director',
      email: 'amanda.csr@testsolutions.com',
      phoneNumber: '+1-555-0303',
      department: 'Corporate Affairs',
      isPrimary: false
    },
    hrDirector: {
      name: 'Jennifer HR',
      title: 'HR Director',
      email: 'jennifer.hr@testsolutions.com',
      phoneNumber: '+1-555-0304',
      department: 'Human Resources',
      isPrimary: false
    },
    additionalContacts: []
  },
  csrProgram: {
    hasEstablishedProgram: true,
    programDescription: 'Comprehensive corporate social responsibility program focusing on education, technology access, and environmental sustainability.',
    annualCSRBudget: '$100K-$250K',
    employeeVolunteerPolicy: 'All employees receive 8 hours of paid volunteer time per year',
    paidVolunteerTime: true,
    hoursPerEmployee: 8,
    focusAreas: ['Education', 'Technology Access', 'Environmental Sustainability', 'Community Development'],
    partnershipHistory: ['Local School District', 'Digital Divide Coalition', 'Environmental Action Network']
  },
  verification: {
    businessLicense: [
      {
        id: 'doc-biz-001',
        type: 'Business License',
        fileName: 'business_license.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2025-06-30',
        reviewNotes: 'Valid state business license'
      }
    ],
    insurance: {
      generalLiability: {
        id: 'doc-biz-002',
        type: 'General Liability Insurance',
        fileName: 'general_liability_certificate.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2025-12-31',
        reviewNotes: '$5M coverage verified'
      },
      workersCompensation: {
        id: 'doc-biz-003',
        type: 'Workers Compensation Insurance',
        fileName: 'workers_comp_certificate.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2025-12-31',
        reviewNotes: 'State-required coverage confirmed'
      },
      professionalLiability: {
        id: 'doc-biz-004',
        type: 'Professional Liability Insurance',
        fileName: 'professional_liability_certificate.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        expirationDate: '2025-12-31',
        reviewNotes: 'Technology services coverage'
      }
    },
    financialStanding: {
      creditReport: {
        id: 'doc-biz-005',
        type: 'Business Credit Report',
        fileName: 'business_credit_report.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        reviewNotes: 'Excellent credit rating verified'
      },
      bankReference: {
        id: 'doc-biz-006',
        type: 'Bank Reference Letter',
        fileName: 'bank_reference_letter.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        reviewNotes: 'Strong banking relationship confirmed'
      }
    },
    references: [
      {
        id: 'biz-ref-001',
        companyName: 'Chamber of Commerce',
        contactPerson: {
          name: 'Patricia Chamber',
          title: 'Membership Director',
          email: 'patricia.chamber@testchamber.org',
          phoneNumber: '+1-555-0305',
          isPrimary: true
        },
        relationship: 'Member Business',
        yearsWorkedWith: 8,
        verificationStatus: 'verified',
        verificationDate: new Date().toISOString(),
        verificationNotes: 'Active chamber member with community involvement'
      }
    ],
    ethicsCompliance: {
      codeOfConduct: {
        id: 'doc-biz-007',
        type: 'Code of Conduct',
        fileName: 'code_of_conduct.pdf',
        uploadDate: new Date().toISOString(),
        status: 'approved',
        reviewNotes: 'Comprehensive ethics guidelines'
      },
      ethicsTraining: true,
      complianceOfficer: {
        name: 'Thomas Compliance',
        title: 'Chief Compliance Officer',
        email: 'thomas.compliance@testsolutions.com',
        phoneNumber: '+1-555-0306',
        department: 'Legal & Compliance',
        isPrimary: false
      }
    }
  },
  offerings: {
    skillBasedVolunteering: ['Web Development', 'Database Management', 'IT Support', 'Digital Marketing', 'Project Management'],
    mentorshipPrograms: ['Career Development', 'Technical Skills', 'Entrepreneurship'],
    trainingResources: ['Digital Literacy', 'Computer Skills', 'Professional Development'],
    equipmentDonations: ['Laptops', 'Tablets', 'Software Licenses', 'Network Equipment'],
    venueSpaces: ['Conference Rooms', 'Training Facilities', 'Event Space'],
    financialSupport: {
      grants: true,
      sponsorships: true,
      matchingGifts: true
    }
  },
  employeeEngagement: {
    volunteerProgram: true,
    teamBuildingEvents: true,
    skillSharingInitiatives: true,
    communityPartnershipEvents: true,
    employeeVolunteerTracking: true
  }
}

export const initializeTestAccounts = () => {
  // Store test credentials for login verification
  const existingCredentials = localStorage.getItem('voluntier_test-credentials')
  if (!existingCredentials) {
    localStorage.setItem('voluntier_test-credentials', JSON.stringify(testCredentials))
  }
  
  // Store test user profiles
  const existingIndividual = localStorage.getItem('voluntier_test-individual-profile')
  if (!existingIndividual) {
    localStorage.setItem('voluntier_test-individual-profile', JSON.stringify(testIndividualProfile))
  }
  
  const existingOrganization = localStorage.getItem('voluntier_test-organization-profile')
  if (!existingOrganization) {
    localStorage.setItem('voluntier_test-organization-profile', JSON.stringify(testOrganizationProfile))
  }
  
  const existingBusiness = localStorage.getItem('voluntier_test-business-profile')
  if (!existingBusiness) {
    localStorage.setItem('voluntier_test-business-profile', JSON.stringify(testBusinessProfile))
  }
}