import { useState } from 'react'
import { useAuth } from '../../services/auth'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Alert, AlertDescription } from '../ui/alert'
import { Eye, EyeSlash, Lock, User } from '@phosphor-icons/react'
import { motion } from 'framer-motion'

interface SignInFormProps {
  onClose?: () => void
  className?: string
}

export const SignInForm = ({ onClose, className }: SignInFormProps) => {
  const { signIn, isLoading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [remainingAttempts, setRemainingAttempts] = useState<number | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setRemainingAttempts(null)

    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password')
      return
    }

    try {
      const result = await signIn(email.trim(), password)
      
      if (result.success) {
        onClose?.()
        setEmail('')
        setPassword('')
      } else {
        setError(result.error || 'Sign in failed')
        if (typeof result.remainingAttempts === 'number') {
          setRemainingAttempts(result.remainingAttempts)
        }
      }
    } catch (err) {
      setError('An unexpected error occurred')
      console.error('Sign in error:', err)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.2 }}
      className={className}
    >
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Administrator Sign In
          </CardTitle>
          <CardDescription className="text-center">
            Access the administrative dashboard
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>
                  {error}
                  {remainingAttempts !== null && (
                    <div className="mt-1 text-sm">
                      {remainingAttempts > 0 
                        ? `${remainingAttempts} attempts remaining` 
                        : 'Account temporarily locked'
                      }
                    </div>
                  )}
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="admin-email">Email Address</Label>
              <div className="relative">
                <User 
                  size={20} 
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" 
                />
                <Input
                  id="admin-email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                  disabled={isLoading}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-password">Password</Label>
              <div className="relative">
                <Lock 
                  size={20} 
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" 
                />
                <Input
                  id="admin-password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 pr-12"
                  disabled={isLoading}
                  autoComplete="current-password"
                  required
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 h-auto"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeSlash size={16} className="text-muted-foreground" />
                  ) : (
                    <Eye size={16} className="text-muted-foreground" />
                  )}
                </Button>
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                type="submit"
                className="flex-1"
                disabled={isLoading || !email.trim() || !password.trim()}
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </Button>
              {onClose && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
              )}
            </div>
          </form>

          <div className="mt-6 pt-4 border-t text-center">
            <p className="text-sm text-muted-foreground">
              Administrative access only
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Contact system administrator for access
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}