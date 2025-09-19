# Frontend Architecture Documentation

## Overview

The Voluntier frontend is a modern React application built with TypeScript, designed for accessibility, performance, and maintainability. It serves as both a development interface within GitHub Spark and a production-ready web application.

## Technology Stack

### Core Framework
- **React 18**: Modern React with concurrent features and improved performance
- **TypeScript**: Strict typing for enhanced developer experience and code reliability
- **Vite**: Fast build tool with hot module replacement and optimized production builds

### Styling & Design System
- **Tailwind CSS**: Utility-first CSS framework with custom design tokens
- **Shadcn/ui**: High-quality, accessible component library built on Radix UI
- **Custom Theme**: Comprehensive color palette and spacing system
- **Responsive Design**: Mobile-first approach with flexible grid layouts

### State Management
- **GitHub Spark KV**: Persistent storage for user data and application state
- **React State**: Local component state for UI interactions
- **Custom Hooks**: Reusable stateful logic and data fetching

### Icons & Assets
- **Phosphor Icons**: Consistent, modern icon set
- **Asset Management**: Explicit imports with Vite asset handling
- **Image Optimization**: Automatic optimization and lazy loading

## Project Structure

```
src/
├── components/              # React components organized by feature
│   ├── ui/                 # Base shadcn/ui components
│   ├── signup/             # User registration components
│   ├── profiles/           # User profile management
│   ├── onboarding/         # Guided user setup
│   ├── upload/             # Document upload system
│   ├── notifications/      # Real-time notifications
│   └── verification/       # Identity verification
├── services/               # Business logic and API interfaces
├── types/                  # TypeScript type definitions
├── data/                   # Sample data and test utilities
├── hooks/                  # Custom React hooks
├── lib/                    # Utility functions and helpers
├── styles/                 # CSS files and theme definitions
├── App.tsx                 # Main application component
└── main.tsx               # Application entry point
```

## Component Architecture

### Design Principles

1. **Composition over Inheritance**: Components built using composition patterns
2. **Single Responsibility**: Each component has a focused, well-defined purpose
3. **Accessibility First**: WCAG 2.1 AA compliance built into all components
4. **Type Safety**: Comprehensive TypeScript interfaces for all props and state
5. **Reusability**: Components designed for reuse across different contexts

### Component Categories

#### Base UI Components (`/components/ui/`)
Pre-built, accessible components from shadcn/ui:
- Form controls (Input, Button, Select, etc.)
- Layout components (Card, Dialog, Sheet, etc.)
- Navigation components (Tabs, Breadcrumb, etc.)
- Feedback components (Alert, Toast, Progress, etc.)

#### Feature Components
Application-specific components organized by domain:

**Authentication & Onboarding**
```typescript
// Signup forms for different user types
signup/
├── IndividualSignupForm.tsx    # Personal volunteer registration
├── OrganizationSignupForm.tsx  # Non-profit organization registration
└── BusinessSignupForm.tsx      # Business registration

// Guided onboarding processes
onboarding/
├── IndividualOnboarding.tsx    # Personal setup workflow
├── OrganizationOnboarding.tsx  # Organization configuration
├── BusinessOnboarding.tsx      # Business setup process
└── OnboardingProgressTracker.tsx # Progress visualization
```

**User Management**
```typescript
// Profile management components
profiles/
├── IndividualProfileView.tsx   # Personal profile display
├── OrganizationProfileView.tsx # Organization profile
├── BusinessProfileView.tsx     # Business profile
└── UnifiedProfileView.tsx      # Dynamic profile router
```

**Document Management**
```typescript
// Document upload and verification
upload/
├── SecureDocumentUpload.tsx    # Secure file upload
├── BulkDocumentUpload.tsx      # Multi-file upload
└── EnhancedDocumentUpload.tsx  # Advanced upload features

verification/
└── DocumentVerification.tsx    # Document verification UI
```

### State Management Patterns

#### Persistent State with useKV
```typescript
import { useKV } from '@github/spark/hooks'

// For data that should persist between sessions
const [userProfile, setUserProfile] = useKV<UserProfile | null>('user-profile', null)
const [events, setEvents] = useKV<VolunteerEvent[]>('volunteer-events', [])

// Always use functional updates to avoid stale closure issues
setEvents(currentEvents => [...currentEvents, newEvent])
```

#### Local State with useState
```typescript
import { useState } from 'react'

// For temporary UI state that doesn't need persistence
const [isLoading, setIsLoading] = useState(false)
const [selectedTab, setSelectedTab] = useState('overview')
const [formData, setFormData] = useState(initialFormData)
```

#### Custom Hooks Pattern
```typescript
// Example: useTelemetry hook for analytics
export const useTelemetry = () => {
  const [userId, setUserId] = useState<string | null>(null)
  
  const trackUserAction = useCallback((action: string, category: string, label?: string) => {
    // Implementation
  }, [userId])
  
  return { trackUserAction, trackPageView, setUserId }
}
```

## Services Layer

### Service Organization
Services handle business logic, API communication, and data processing:

```typescript
// services/telemetry.ts - Analytics and user tracking
export interface TelemetryService {
  trackUserAction(action: string, category: string, label?: string): void
  trackPageView(page: string): void
  setUserId(userId: string): void
}

// services/documentUpload.ts - Document processing
export interface DocumentUploadService {
  uploadDocument(file: File, documentType: string): Promise<UploadResult>
  processDocument(document: ProcessedDocument): Promise<VerificationResult>
}

// services/notifications.ts - Real-time notifications
export interface NotificationService {
  sendNotification(notification: NotificationData): Promise<void>
  subscribeToNotifications(userId: string): Observable<Notification>
}
```

### Integration Patterns

#### Backend Integration
```typescript
// Services designed to integrate with FastAPI backend
const apiClient = {
  baseURL: process.env.VITE_API_URL || 'http://localhost:8080/api/v1',
  
  async uploadDocument(file: File, metadata: DocumentMetadata) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('metadata', JSON.stringify(metadata))
    
    return fetch(`${this.baseURL}/documents/upload`, {
      method: 'POST',
      body: formData,
      headers: { Authorization: `Bearer ${token}` }
    })
  }
}
```

#### LLM Integration via Spark
```typescript
// Using Spark's LLM capabilities for enhanced features
const analyzeDocument = async (documentContent: string) => {
  const prompt = spark.llmPrompt`
    Analyze this document for completeness and accuracy:
    ${documentContent}
    
    Return a JSON object with validation results.
  `
  
  const result = await spark.llm(prompt, 'gpt-4o', true)
  return JSON.parse(result)
}
```

## Type System

### Type Organization
```typescript
// types/auth.ts - Authentication and authorization
export interface UserCredentials {
  email: string
  password: string
}

export interface AuthenticationResult {
  user: UserProfile
  token: string
  refreshToken: string
}

// types/profiles.ts - User profile definitions
export interface BaseProfile {
  id: string
  email: string
  userType: 'individual' | 'organization' | 'business'
  verificationStatus: VerificationStatus
  createdAt: string
  updatedAt: string
}

export interface IndividualProfile extends BaseProfile {
  userType: 'individual'
  firstName: string
  lastName: string
  skills: string[]
  availability: AvailabilitySchedule
  references: PersonalReference[]
}

// types/documents.ts - Document handling
export interface DocumentMetadata {
  documentType: DocumentType
  fileName: string
  fileSize: number
  uploadedAt: string
  verificationStatus: 'pending' | 'verified' | 'rejected'
}
```

### Strict Type Enforcement
- All components use TypeScript strict mode
- Comprehensive interfaces for all props and state
- Type guards for runtime type checking
- Generic types for reusable components

## Styling System

### Design Tokens
```css
/* Custom CSS variables for consistent theming */
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.2 0.05 240);
  --primary: oklch(0.6 0.15 240);
  --secondary: oklch(0.95 0.01 240);
  --accent: oklch(0.65 0.18 60);
  --success: oklch(0.7 0.12 150);
  --destructive: oklch(0.65 0.2 25);
  --radius: 0.5rem;
}
```

### Component Styling Patterns
```typescript
// Using Tailwind classes with shadcn/ui components
<Button 
  variant="primary" 
  size="lg"
  className="w-full bg-primary hover:bg-primary/90"
>
  Register as Volunteer
</Button>

// Responsive design with mobile-first approach
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  {events.map(event => (
    <EventCard key={event.id} event={event} />
  ))}
</div>
```

### Accessibility Features
- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Focus management

## Performance Optimization

### Bundle Optimization
- Tree shaking for unused code elimination
- Code splitting with dynamic imports
- Asset optimization with Vite
- Modern JavaScript output targeting

### Runtime Performance
- React.memo for expensive components
- useCallback and useMemo for optimization
- Lazy loading for routes and components
- Virtualization for large lists

### Loading States
```typescript
// Consistent loading patterns across components
const [isLoading, setIsLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

const handleSubmit = async (data: FormData) => {
  setIsLoading(true)
  setError(null)
  
  try {
    await submitForm(data)
  } catch (err) {
    setError(err.message)
  } finally {
    setIsLoading(false)
  }
}
```

## Testing Strategy

### Testing Approach
- Unit tests for utility functions and hooks
- Component testing with React Testing Library
- Integration tests for user workflows
- E2E tests for critical user journeys

### Testing Patterns
```typescript
// Example component test
import { render, screen, fireEvent } from '@testing-library/react'
import { IndividualSignupForm } from './IndividualSignupForm'

test('submits form with valid data', async () => {
  const onSubmit = jest.fn()
  render(<IndividualSignupForm onSubmit={onSubmit} />)
  
  fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'test@example.com' }
  })
  
  fireEvent.click(screen.getByRole('button', { name: 'Register' }))
  
  await waitFor(() => {
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ email: 'test@example.com' })
    )
  })
})
```

## Development Workflow

### Development Server
```bash
# Start development server with hot reload
npm run dev

# Run with specific port
npm run dev -- --port 3000

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality
- ESLint for code quality and consistency
- Prettier for code formatting
- TypeScript compiler for type checking
- Automated testing in CI/CD pipeline

### Development Best Practices
1. **Component First**: Build components in isolation
2. **Type Driven**: Define types before implementation
3. **Test Coverage**: Maintain high test coverage
4. **Documentation**: Document complex components and patterns
5. **Performance**: Monitor and optimize performance metrics

## Integration with Backend

### API Integration Strategy
- RESTful API design with consistent patterns
- Error handling with user-friendly messages
- Loading states and optimistic updates
- Offline capability with service workers (planned)

### Real-time Features
- WebSocket integration for live notifications
- Event-driven updates for collaborative features
- Optimistic UI updates for better UX

## Future Enhancements

### Planned Features
- Progressive Web App (PWA) capabilities
- Offline-first architecture
- Advanced accessibility features
- Mobile application (React Native)
- Enhanced animations and micro-interactions

### Scalability Considerations
- Micro-frontend architecture evaluation
- CDN integration for asset delivery
- Advanced caching strategies
- Performance monitoring and optimization

---

This architecture provides a solid foundation for building a scalable, maintainable, and user-friendly volunteer coordination platform that can grow with the community's needs.