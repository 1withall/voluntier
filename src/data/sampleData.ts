// Sample data initialization for demonstration

import { VolunteerEvent } from '../App'

export const sampleEvents: VolunteerEvent[] = [
  {
    id: 'event-001',
    title: 'Community Food Drive',
    organization: 'Local Food Bank',
    description: 'Help organize and distribute food to families in need. Tasks include sorting donations, packing bags, and greeting community members.',
    date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 week from now
    time: '09:00 AM - 1:00 PM',
    location: '123 Community Center Drive, Downtown',
    volunteersNeeded: 15,
    volunteersRegistered: 8,
    skills: ['Customer Service', 'Physical Labor', 'Organization'],
    category: 'Community Support',
    verified: true
  },
  {
    id: 'event-002',
    title: 'Senior Technology Workshop',
    organization: 'TechForGood',
    description: 'Teach seniors how to use smartphones and tablets. Help with basic navigation, email, video calls, and app usage.',
    date: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 10 days from now
    time: '2:00 PM - 4:00 PM',
    location: 'Senior Community Center, 456 Oak Street',
    volunteersNeeded: 8,
    volunteersRegistered: 3,
    skills: ['Technology', 'Teaching', 'Patience'],
    category: 'Education',
    verified: true
  },
  {
    id: 'event-003',
    title: 'Park Cleanup Initiative',
    organization: 'Green Earth Society',
    description: 'Join us for a community park cleanup. We\'ll provide all supplies including gloves, trash bags, and tools. Help make our community beautiful!',
    date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2 weeks from now
    time: '8:00 AM - 12:00 PM',
    location: 'Riverside Park, 789 River Road',
    volunteersNeeded: 25,
    volunteersRegistered: 18,
    skills: ['Physical Labor', 'Environmental Awareness'],
    category: 'Environment',
    verified: true
  },
  {
    id: 'event-004',
    title: 'Youth Mentoring Program',
    organization: 'Future Leaders Foundation',
    description: 'Mentor high school students in career planning and life skills. Share your professional experience and help guide the next generation.',
    date: new Date(Date.now() + 21 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3 weeks from now
    time: '6:00 PM - 8:00 PM',
    location: 'Lincoln High School, 321 Education Blvd',
    volunteersNeeded: 12,
    volunteersRegistered: 5,
    skills: ['Mentoring', 'Communication', 'Professional Experience'],
    category: 'Youth Development',
    verified: true
  },
  {
    id: 'event-005',
    title: 'Holiday Gift Wrapping',
    organization: 'Helping Hands Charity',
    description: 'Help wrap holiday gifts for underprivileged families. Create a magical holiday experience for children and families in our community.',
    date: new Date(Date.now() + 28 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 4 weeks from now
    time: '10:00 AM - 6:00 PM',
    location: 'Community Center Main Hall, 555 Main Street',
    volunteersNeeded: 20,
    volunteersRegistered: 12,
    skills: ['Arts & Crafts', 'Organization', 'Attention to Detail'],
    category: 'Holiday Support',
    verified: true
  },
  {
    id: 'event-006',
    title: 'Free Health Screening Event',
    organization: 'Community Health Alliance',
    description: 'Support healthcare professionals in providing free health screenings. Help with registration, patient guidance, and basic administrative tasks.',
    date: new Date(Date.now() + 35 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 weeks from now
    time: '9:00 AM - 3:00 PM',
    location: 'City Health Center, 777 Wellness Way',
    volunteersNeeded: 10,
    volunteersRegistered: 4,
    skills: ['Healthcare', 'Administrative', 'Customer Service'],
    category: 'Health & Wellness',
    verified: true
  }
]

export const initializeSampleData = () => {
  // Check if events already exist to avoid overwriting user data
  const existingEvents = localStorage.getItem('voluntier_volunteer-events')
  if (!existingEvents || JSON.parse(existingEvents).length === 0) {
    localStorage.setItem('voluntier_volunteer-events', JSON.stringify(sampleEvents))
  }
}