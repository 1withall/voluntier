# Quick Development Guide

This guide provides essential information for developers to quickly understand and contribute to the Voluntier platform.

## 🚀 Quick Start (5 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/your-org/voluntier.git
cd voluntier

# 2. Frontend
npm install && npm run dev
# Open http://localhost:5173

# 3. Backend (optional for frontend-only development)
cd backend
./scripts/setup.sh
docker-compose up -d
uv run uvicorn voluntier.api.main:app --reload
```

## 📁 Key File Locations

### Frontend (`/src`)
```
src/
├── App.tsx              # Main application component
├── components/          # All React components
│   ├── ui/             # Base shadcn/ui components  
│   ├── signup/         # User registration forms
│   └── profiles/       # Profile management
├── services/           # Business logic (API calls, etc.)
├── types/              # TypeScript type definitions
└── hooks/              # Custom React hooks
```

### Backend (`/backend`)
```
backend/
├── src/voluntier/      # Main Python package
│   ├── api/           # FastAPI routes
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── temporal_workflows/ # Temporal workflows
├── config/            # Configuration files
└── tests/             # Test suite
```

### Documentation (`/docs`)
```
docs/
├── README.md          # Documentation index
├── SETUP.md           # Detailed setup guide
├── ARCHITECTURE.md    # System architecture
├── API.md             # API documentation
└── CONTRIBUTING.md    # Development guidelines
```

## 🛠️ Common Development Tasks

### Frontend Development
```bash
# Start development server
npm run dev

# Type checking
npm run type-check

# Linting and formatting
npm run lint
npm run format

# Testing
npm test
```

### Backend Development
```bash
cd backend

# Start API server
uv run uvicorn voluntier.api.main:app --reload

# Start Temporal worker
uv run voluntier worker

# Run tests
uv run pytest

# Type checking
uv run mypy src/
```

### Full Stack Development
```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend API
cd backend && uv run uvicorn voluntier.api.main:app --reload

# Terminal 3: Temporal worker
cd backend && uv run voluntier worker

# Terminal 4: Infrastructure
cd backend && docker-compose up -d
```

## 🎯 Development Workflow

### 1. Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow existing code patterns
- Add TypeScript types for new interfaces
- Write tests for new functionality
- Update documentation as needed

### 3. Test Changes
```bash
# Frontend
npm run lint && npm run type-check && npm test

# Backend
cd backend && uv run pytest && uv run mypy src/
```

### 4. Commit and Push
```bash
git add .
git commit -m "feat: descriptive commit message"
git push origin feature/your-feature-name
```

### 5. Create Pull Request
- Use the PR template
- Include screenshots for UI changes
- Reference related issues
- Wait for review and approval

## 📋 Code Standards

### TypeScript/React
```typescript
// ✅ Good: Proper typing and structure
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
  // Implementation
}
```

### State Management
```typescript
// ✅ Persistent data (survives page refresh)
const [userProfile, setUserProfile] = useKV<UserProfile | null>('user-profile', null)

// ✅ Temporary UI state (does not survive page refresh)
const [isLoading, setIsLoading] = useState(false)

// ✅ Always use functional updates for useKV
setUserProfile(current => ({ ...current, newField: 'value' }))
```

### Python/FastAPI
```python
# ✅ Good: Type hints and proper structure
from typing import List, Optional
from pydantic import BaseModel

class UserProfile(BaseModel):
    id: str
    email: str
    user_type: str

@router.get("/users/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """Get user profile with proper error handling."""
    # Implementation
```

## 🧪 Testing Patterns

### Frontend Tests
```typescript
import { render, screen, fireEvent } from '@testing-library/react'

test('component renders and handles user interaction', async () => {
  const onSubmit = jest.fn()
  render(<YourComponent onSubmit={onSubmit} />)
  
  fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
  
  expect(onSubmit).toHaveBeenCalled()
})
```

### Backend Tests
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_api_endpoint(client: AsyncClient, authenticated_user):
    response = await client.get(
        "/api/v1/users/profile",
        headers={"Authorization": f"Bearer {authenticated_user.token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == authenticated_user.email
```

## 🔧 Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using a port
lsof -i :5173
lsof -i :8080

# Kill process if needed
kill -9 <PID>
```

**Frontend not hot reloading:**
```bash
# Clear cache and restart
rm -rf node_modules/.vite
npm run dev
```

**Backend database issues:**
```bash
# Reset database
cd backend
docker-compose down
docker-compose up -d postgresql
uv run alembic upgrade head
```

**TypeScript errors:**
```bash
# Clear TypeScript cache
rm -rf node_modules/.tmp
npm run type-check
```

### Getting Help

1. **Check Documentation**: Start with relevant docs in `/docs`
2. **Search Issues**: Look for similar problems in GitHub issues
3. **Ask Questions**: Create a new issue with the "question" label
4. **Join Community**: Discord link in main README

## 🎨 UI/UX Guidelines

### Component Usage
```typescript
// ✅ Use shadcn/ui components
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

// ✅ Proper Tailwind classes
<Button 
  variant="primary" 
  size="lg"
  className="w-full"
>
  Submit
</Button>
```

### Responsive Design
```typescript
// ✅ Mobile-first responsive classes
<div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
  {items.map(item => <ItemCard key={item.id} item={item} />)}
</div>
```

### Accessibility
```typescript
// ✅ Proper ARIA labels and semantic HTML
<Button
  aria-label="Submit volunteer application"
  disabled={isLoading}
>
  {isLoading ? 'Submitting...' : 'Submit Application'}
</Button>
```

## 🔒 Security Guidelines

### Input Validation
```typescript
// ✅ Frontend validation
const emailSchema = z.string().email("Valid email required")

// ✅ Backend validation
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
```

### Authentication
```typescript
// ✅ Proper token handling
const token = localStorage.getItem('access_token')
if (token) {
  headers.Authorization = `Bearer ${token}`
}
```

### Data Handling
```typescript
// ✅ Never log sensitive data
console.log('User login attempt', { email: user.email }) // ✅ OK
console.log('User data', { password: user.password })   // ❌ Never
```

## 📊 Performance Tips

### Frontend Optimization
```typescript
// ✅ Memoize expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  return <ComplexVisualization data={data} />
})

// ✅ Use callbacks for event handlers
const handleSubmit = useCallback((data) => {
  // Handle submission
}, [dependency])
```

### Backend Optimization
```python
# ✅ Use database indexes
class User(Base):
    email = Column(String, index=True, unique=True)

# ✅ Async/await for I/O operations
async def get_user_profile(user_id: str) -> UserProfile:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

## 🚀 Deployment Notes

### Environment Configuration
```bash
# Development
ENVIRONMENT=development
DEBUG=true

# Production
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secure-secret-key
```

### Build Commands
```bash
# Frontend production build
npm run build
npm run preview

# Backend Docker build
cd backend
docker build -t voluntier-api .
```

## 📈 Monitoring

### Key Metrics to Watch
- **Frontend**: Page load times, user interactions, error rates
- **Backend**: API response times, database query performance, error rates
- **Security**: Failed login attempts, unusual access patterns, threat scores

### Logging Best Practices
```typescript
// ✅ Structured logging
logger.info('User action completed', {
  userId: user.id,
  action: 'event_registration',
  eventId: event.id,
  timestamp: new Date().toISOString()
})
```

This guide covers the essential information needed to start developing on the Voluntier platform. For detailed information, refer to the comprehensive documentation in the `/docs` directory.