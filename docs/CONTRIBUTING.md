# Contributing to Voluntier

Welcome to the Voluntier project! We appreciate your interest in contributing to this community-driven volunteer coordination platform. This guide will help you get started with contributing effectively.

## 🌟 Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- **Be Respectful**: Treat all community members with respect and kindness
- **Be Inclusive**: Welcome newcomers and help them feel part of the community
- **Be Collaborative**: Work together to solve problems and share knowledge
- **Be Professional**: Maintain professional standards in all interactions
- **Be Constructive**: Provide helpful feedback and suggestions

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Node.js** 18+ with npm
- **Python** 3.12+ with uv package manager
- **Docker** and Docker Compose
- **Git** for version control
- Basic understanding of React, TypeScript, and Python

### Development Environment Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/voluntier.git
   cd voluntier
   ```

2. **Frontend Setup**
   ```bash
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

3. **Backend Setup**
   ```bash
   # Navigate to backend
   cd backend
   
   # Run setup script
   ./scripts/setup.sh
   
   # Start services
   docker-compose up -d
   uv run uvicorn voluntier.api.main:app --reload
   ```

4. **Verify Installation**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8080/docs
   - All tests passing: `npm test` and `cd backend && uv run pytest`

## 🎯 How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **🐛 Bug Reports**: Help us identify and fix issues
2. **✨ Feature Requests**: Suggest new functionality
3. **📝 Documentation**: Improve or add documentation
4. **🔧 Code Contributions**: Bug fixes and new features
5. **🧪 Testing**: Improve test coverage and quality
6. **🎨 Design**: UI/UX improvements and accessibility

### Contribution Workflow

1. **Check Existing Issues**
   - Review open issues to avoid duplication
   - Comment on issues you'd like to work on
   - Ask for clarification if needed

2. **Create an Issue** (for new contributions)
   - Use appropriate issue templates
   - Provide detailed descriptions
   - Include acceptance criteria for features

3. **Branch Strategy**
   ```bash
   # Create feature branch from main
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   
   # Or for bug fixes
   git checkout -b fix/issue-description
   ```

4. **Make Changes**
   - Follow coding standards (see below)
   - Write tests for new functionality
   - Update documentation as needed
   - Commit with descriptive messages

5. **Test Your Changes**
   ```bash
   # Frontend tests
   npm test
   npm run lint
   npm run type-check
   
   # Backend tests
   cd backend
   uv run pytest
   uv run mypy src/
   uv run black --check src/
   ```

6. **Submit Pull Request**
   - Use the PR template
   - Reference related issues
   - Provide detailed description of changes
   - Include screenshots for UI changes

## 📋 Coding Standards

### General Principles

1. **Code Quality**
   - Write clean, readable, and maintainable code
   - Follow DRY (Don't Repeat Yourself) principles
   - Use meaningful variable and function names
   - Add comments for complex logic

2. **Security First**
   - Follow security best practices
   - Validate all inputs
   - Never commit secrets or API keys
   - Review security implications of changes

3. **Accessibility**
   - Ensure WCAG 2.1 AA compliance
   - Test with screen readers
   - Provide keyboard navigation
   - Use semantic HTML

### Frontend Standards

#### TypeScript/React
```typescript
// ✅ Good: Type-safe component with clear interface
interface UserProfileProps {
  user: UserProfile
  onUpdate: (user: UserProfile) => void
  isLoading?: boolean
}

export const UserProfile: React.FC<UserProfileProps> = ({ 
  user, 
  onUpdate, 
  isLoading = false 
}) => {
  // Component implementation
}

// ❌ Avoid: Untyped props and unclear naming
export const Profile = ({ data, fn, loading }) => {
  // Implementation
}
```

#### State Management
```typescript
// ✅ Good: Proper useKV usage for persistent data
const [userProfile, setUserProfile] = useKV<UserProfile | null>('user-profile', null)

// Functional updates to avoid stale closures
setUserProfile(currentProfile => ({
  ...currentProfile,
  skills: [...currentProfile.skills, newSkill]
}))

// ✅ Good: useState for temporary UI state
const [isEditing, setIsEditing] = useState(false)
const [formErrors, setFormErrors] = useState<string[]>([])
```

#### Component Structure
```typescript
// ✅ Good: Well-organized component structure
import React, { useState, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { UserProfile } from '@/types/profiles'

interface ComponentProps {
  // Props interface
}

export const ComponentName: React.FC<ComponentProps> = ({ prop1, prop2 }) => {
  // State and hooks
  const [localState, setLocalState] = useState(initialValue)
  
  // Event handlers
  const handleClick = useCallback(() => {
    // Implementation
  }, [dependencies])
  
  // Render
  return (
    <Card>
      <CardHeader>
        <CardTitle>Title</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content */}
      </CardContent>
    </Card>
  )
}
```

#### Styling Guidelines
```typescript
// ✅ Good: Tailwind classes with semantic organization
<Button 
  variant="primary" 
  size="lg"
  className="w-full bg-primary hover:bg-primary/90 focus:ring-2 focus:ring-ring"
  disabled={isLoading}
>
  {isLoading ? 'Processing...' : 'Submit'}
</Button>

// ✅ Good: Responsive design with mobile-first
<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
  {items.map(item => (
    <ItemCard key={item.id} item={item} />
  ))}
</div>
```

### Backend Standards

#### Python Code Style
```python
# ✅ Good: Type hints and clear function signatures
from typing import List, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    id: str
    email: str
    user_type: str
    verification_status: str
    created_at: datetime

async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> Optional[UserProfile]:
    """Retrieve user profile by ID with error handling."""
    try:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return UserProfile.from_orm(user) if user else None
    except Exception as e:
        logger.error(f"Error retrieving user profile {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

#### API Design
```python
# ✅ Good: RESTful API with proper error handling
@router.post("/users", response_model=UserProfile, status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """Create a new user with validation and security checks."""
    
    # Validate input
    if await email_exists(user_data.email, db):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_service.create_user(user_data, db)
    
    # Log activity
    await audit_service.log_user_creation(user.id, current_user.id)
    
    return UserProfile.from_orm(user)
```

### Documentation Standards

#### Code Documentation
```typescript
/**
 * Handles secure document upload with validation and preprocessing
 * 
 * @param file - The file to upload (PDF, DOC, or image)
 * @param documentType - Type of document (ID, certificate, etc.)
 * @param userId - ID of the user uploading the document
 * @returns Promise resolving to upload result with verification status
 * 
 * @throws {ValidationError} When file format is not supported
 * @throws {SecurityError} When file contains malicious content
 * 
 * @example
 * ```typescript
 * const result = await uploadDocument(
 *   file,
 *   'government_id',
 *   'user123'
 * )
 * 
 * if (result.success) {
 *   console.log('Document uploaded:', result.documentId)
 * }
 * ```
 */
export async function uploadDocument(
  file: File,
  documentType: DocumentType,
  userId: string
): Promise<DocumentUploadResult> {
  // Implementation
}
```

#### README Updates
- Keep README current with new features
- Update setup instructions for new dependencies
- Document breaking changes clearly
- Include migration guides for major updates

### Testing Standards

#### Frontend Tests
```typescript
// ✅ Good: Comprehensive component test
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UserProfileForm } from './UserProfileForm'

describe('UserProfileForm', () => {
  const mockProps = {
    user: mockUserProfile,
    onSubmit: jest.fn(),
    onCancel: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders all form fields correctly', () => {
    render(<UserProfileForm {...mockProps} />)
    
    expect(screen.getByLabelText('First Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Last Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('validates required fields', async () => {
    render(<UserProfileForm {...mockProps} />)
    
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    
    await waitFor(() => {
      expect(screen.getByText('First name is required')).toBeInTheDocument()
    })
    
    expect(mockProps.onSubmit).not.toHaveBeenCalled()
  })

  it('submits form with valid data', async () => {
    render(<UserProfileForm {...mockProps} />)
    
    fireEvent.change(screen.getByLabelText('First Name'), {
      target: { value: 'John' }
    })
    
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    
    await waitFor(() => {
      expect(mockProps.onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ firstName: 'John' })
      )
    })
  })
})
```

#### Backend Tests
```python
# ✅ Good: Comprehensive API test
import pytest
from httpx import AsyncClient
from tests.factories import UserFactory, DocumentFactory

class TestDocumentUpload:
    @pytest.mark.asyncio
    async def test_upload_valid_document(
        self,
        client: AsyncClient,
        authenticated_user: User,
        sample_pdf: bytes
    ):
        """Test successful document upload with valid file."""
        
        # Arrange
        files = {"file": ("test.pdf", sample_pdf, "application/pdf")}
        data = {"document_type": "government_id"}
        
        # Act
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {authenticated_user.token}"}
        )
        
        # Assert
        assert response.status_code == 201
        result = response.json()
        assert result["document_type"] == "government_id"
        assert result["verification_status"] == "pending"
        assert "document_id" in result

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(
        self,
        client: AsyncClient,
        authenticated_user: User
    ):
        """Test upload rejection for invalid file types."""
        
        # Arrange
        files = {"file": ("test.exe", b"invalid", "application/octet-stream")}
        data = {"document_type": "government_id"}
        
        # Act
        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {authenticated_user.token}"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
```

## 🔍 Review Process

### Pull Request Guidelines

#### PR Title and Description
```
feat: Add bulk document upload functionality

## Summary
Implements bulk document upload with drag-and-drop interface and progress tracking.

## Changes
- Added BulkDocumentUpload component with drag-and-drop
- Implemented upload progress tracking
- Added batch processing for multiple files
- Updated DocumentUploadService to handle bulk operations

## Testing
- [ ] Unit tests for new components
- [ ] Integration tests for upload service
- [ ] Manual testing with various file types
- [ ] Accessibility testing with screen reader

## Breaking Changes
None

## Related Issues
Closes #123
References #456

## Screenshots
[Include relevant screenshots for UI changes]
```

#### Review Checklist

**Code Quality**
- [ ] Code follows project standards and conventions
- [ ] Functions and variables have clear, descriptive names
- [ ] Complex logic is properly documented
- [ ] No code duplication or unnecessary complexity

**Functionality**
- [ ] Feature works as described in requirements
- [ ] Edge cases are handled appropriately
- [ ] Error handling is comprehensive and user-friendly
- [ ] Performance implications are considered

**Security**
- [ ] Input validation is implemented
- [ ] Authentication and authorization are correct
- [ ] No sensitive data is exposed
- [ ] Security best practices are followed

**Testing**
- [ ] Adequate test coverage for new code
- [ ] All tests pass locally and in CI
- [ ] Integration tests cover main user flows
- [ ] Manual testing completed for UI changes

**Documentation**
- [ ] Code is properly documented
- [ ] README updated if needed
- [ ] API documentation updated
- [ ] Migration guide provided for breaking changes

### Feedback and Iteration

1. **Constructive Feedback**: Provide specific, actionable feedback
2. **Collaborative Discussion**: Be open to alternative approaches
3. **Timely Response**: Respond to reviews promptly
4. **Continuous Improvement**: Learn from feedback and apply to future contributions

## 🚨 Security Considerations

### Security Best Practices

1. **Input Validation**
   - Validate all user inputs on both frontend and backend
   - Sanitize data before processing or storage
   - Use parameterized queries to prevent SQL injection

2. **Authentication & Authorization**
   - Implement proper JWT token handling
   - Use role-based access control
   - Verify permissions for all operations

3. **Data Protection**
   - Encrypt sensitive data at rest and in transit
   - Follow GDPR and privacy regulations
   - Implement secure file upload handling

4. **Error Handling**
   - Don't expose sensitive information in error messages
   - Log security events for monitoring
   - Implement rate limiting and abuse protection

### Reporting Security Issues

If you discover a security vulnerability:

1. **Do not** create a public issue
2. Email security concerns to the maintainers
3. Provide detailed description of the vulnerability
4. Include steps to reproduce if possible
5. Allow time for investigation and patching

## 📈 Performance Guidelines

### Frontend Performance

1. **Component Optimization**
   - Use React.memo for expensive components
   - Implement useCallback and useMemo appropriately
   - Avoid unnecessary re-renders

2. **Bundle Optimization**
   - Code split large components
   - Optimize asset loading
   - Use appropriate image formats and sizes

3. **User Experience**
   - Implement loading states
   - Provide immediate feedback for user actions
   - Use optimistic updates where appropriate

### Backend Performance

1. **Database Optimization**
   - Use appropriate indexes
   - Implement connection pooling
   - Optimize query performance

2. **API Performance**
   - Implement caching strategies
   - Use pagination for large datasets
   - Optimize serialization

3. **Resource Management**
   - Monitor memory usage
   - Implement proper cleanup
   - Use async/await appropriately

## 🎯 Getting Help

### Resources

- **Documentation**: Check the `/docs` directory
- **API Docs**: Available at http://localhost:8080/docs when running
- **Examples**: Look at existing components for patterns
- **Issues**: Search existing issues for similar problems

### Community Support

- **GitHub Discussions**: For general questions and feature discussions
- **Issues**: For bug reports and specific problems
- **Pull Requests**: For code review and implementation discussion

### Mentorship

New contributors are welcome! If you're new to the project:

1. Start with "good first issue" labels
2. Ask questions in issue comments
3. Request code reviews from experienced contributors
4. Participate in discussions and provide feedback

## 🏆 Recognition

We appreciate all contributions to the Voluntier project:

- **Contributors** are listed in the project README
- **Significant contributions** are highlighted in release notes
- **Community members** are recognized for helpful participation

Thank you for contributing to Voluntier and helping build better tools for community volunteer coordination!

---

## Quick Reference

### Commands
```bash
# Frontend
npm run dev          # Start development server
npm test            # Run tests
npm run lint        # Lint code
npm run type-check  # TypeScript checking

# Backend
cd backend
uv run pytest              # Run tests
uv run mypy src/           # Type checking
uv run black src/          # Format code
uv run uvicorn voluntier.api.main:app --reload  # Start API
```

### Git Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature
# Make changes
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature
# Create PR on GitHub
```