import { useState, useEffect } from 'react'
import { UserProfile } from '../types/profiles'
import { TestCredentials, testIndividualProfile, testOrganizationProfile, testBusinessProfile } from '../data/testAccounts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Alert, AlertDescription } from './ui/alert'
import { Badge } from './ui/badge'
import { TestTube, User, Building, Briefcase, Shield, Eye, EyeClosed } from '@phosphor-icons/react'

interface TestAccountLoginProps {
  onLoginSuccess: (userProfile: UserProfile) => void
  onCancel: () => void
}

export function TestAccountLogin({ onLoginSuccess, onCancel }: TestAccountLoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [testCredentials, setTestCredentials] = useState<TestCredentials[]>([])

  useEffect(() => {
    // Load test credentials from localStorage
    const stored = localStorage.getItem('voluntier_test-credentials')
    if (stored) {
      setTestCredentials(JSON.parse(stored))
    }
  }, [])

  const handleLogin = () => {
    setError('')
    
    // Find matching credentials
    const matchedCredentials = testCredentials.find(
      cred => cred.username === username && cred.password === password
    )
    
    if (!matchedCredentials) {
      setError('Invalid username or password')
      return
    }

    // Load the appropriate test profile
    let userProfile: UserProfile
    switch (matchedCredentials.userType) {
      case 'individual':
        userProfile = testIndividualProfile
        break
      case 'organization':
        userProfile = testOrganizationProfile
        break
      case 'business':
        userProfile = testBusinessProfile
        break
      default:
        setError('Invalid user type')
        return
    }

    onLoginSuccess(userProfile)
  }

  const handleQuickLogin = (userType: 'individual' | 'organization' | 'business') => {
    const cred = testCredentials.find(c => c.userType === userType)
    if (cred) {
      setUsername(cred.username)
      setPassword(cred.password)
    }
  }

  const testAccounts = [
    {
      type: 'individual' as const,
      title: 'Individual Volunteer',
      icon: User,
      description: 'Verified volunteer with completed profile',
      features: ['45 volunteer hours', '8 events attended', 'Level 3 volunteer', '2 badges earned']
    },
    {
      type: 'organization' as const,
      title: 'Non-Profit Organization',
      icon: Building,
      description: 'Verified organization with active programs',
      features: ['Can verify volunteers', '501(c)(3) verified', 'Insurance approved', 'Facility inspected']
    },
    {
      type: 'business' as const,
      title: 'Corporate Partner',
      icon: Briefcase,
      description: 'Business with established CSR program',
      features: ['$100K+ CSR budget', '8 hours/employee volunteer time', 'Ethics compliance verified', 'Multiple partnerships']
    }
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center mb-6">
          <TestTube size={48} className="text-accent mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-foreground">Test Account Login</h1>
            <p className="text-muted-foreground">Login with pre-configured test accounts</p>
          </div>
        </div>
        
        <Alert className="bg-amber-50 border-amber-200">
          <Shield size={20} className="text-amber-600" />
          <AlertDescription className="text-amber-700">
            <strong>Development Mode:</strong> These are pre-configured test accounts for development and demonstration purposes. 
            Each account type has realistic data and verification status to showcase the platform's capabilities.
          </AlertDescription>
        </Alert>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Manual Login Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield size={20} />
              Manual Login
            </CardTitle>
            <CardDescription>
              Enter test account credentials manually
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="test_individual"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="1Fake_passw0rd."
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeClosed size={16} /> : <Eye size={16} />}
                </Button>
              </div>
            </div>

            {error && (
              <Alert className="bg-red-50 border-red-200">
                <AlertDescription className="text-red-700">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              <Button onClick={handleLogin} className="flex-1">
                Login
              </Button>
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            </div>

            <div className="text-xs text-muted-foreground space-y-1">
              <p><strong>Test Credentials:</strong></p>
              <p>• test_individual / 1Fake_passw0rd.</p>
              <p>• test_organization / 1Fake_passw0rd.</p>
              <p>• test_business / 1Fake_passw0rd.</p>
            </div>
          </CardContent>
        </Card>

        {/* Quick Login Options */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TestTube size={20} />
              Quick Login
            </CardTitle>
            <CardDescription>
              One-click login for each account type
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {testAccounts.map((account) => {
              const IconComponent = account.icon
              return (
                <div
                  key={account.type}
                  className="border rounded-lg p-4 space-y-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <IconComponent size={24} className="text-primary mt-1" />
                    <div className="flex-1">
                      <h3 className="font-medium">{account.title}</h3>
                      <p className="text-sm text-muted-foreground mb-2">
                        {account.description}
                      </p>
                      <div className="flex flex-wrap gap-1 mb-3">
                        {account.features.map((feature, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {feature}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleQuickLogin(account.type)}
                        >
                          Fill Credentials
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => {
                            handleQuickLogin(account.type)
                            setTimeout(handleLogin, 100)
                          }}
                        >
                          Quick Login
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>

      <div className="text-center">
        <Button variant="ghost" onClick={onCancel} className="text-muted-foreground">
          ← Back to Account Selection
        </Button>
      </div>
    </div>
  )
}