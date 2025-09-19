import { useState } from 'react'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { Dialog, DialogContent } from '../ui/dialog'
import { HandHeart, Users, Building, Shield } from '@phosphor-icons/react'
import { SignupFlow } from '../SignupFlow'
import { SignInForm } from '../auth/SignInForm'
import { UserProfile } from '../../types/profiles'

interface LandingPageProps {
  onSignupComplete: (profile: UserProfile) => void
}

export const LandingPage = ({ onSignupComplete }: LandingPageProps) => {
  const [activeTab, setActiveTab] = useState<'signup' | 'signin'>('signup')
  const [showAdminSignIn, setShowAdminSignIn] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <HandHeart size={48} className="text-primary mr-3" />
            <h1 className="text-4xl font-bold text-foreground">Voluntier</h1>
          </div>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Building stronger communities through coordinated volunteer efforts, 
            connecting individuals, organizations, and businesses.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="flex flex-col items-center p-6">
              <Users size={32} className="text-primary mb-3" />
              <h3 className="font-semibold mb-2">For Individuals</h3>
              <p className="text-sm text-muted-foreground text-center">
                Find meaningful volunteer opportunities and track your community impact
              </p>
            </div>
            <div className="flex flex-col items-center p-6">
              <HandHeart size={32} className="text-primary mb-3" />
              <h3 className="font-semibold mb-2">For Organizations</h3>
              <p className="text-sm text-muted-foreground text-center">
                Coordinate volunteers, manage events, and build community partnerships
              </p>
            </div>
            <div className="flex flex-col items-center p-6">
              <Building size={32} className="text-primary mb-3" />
              <h3 className="font-semibold mb-2">For Businesses</h3>
              <p className="text-sm text-muted-foreground text-center">
                Engage in corporate social responsibility and community investment
              </p>
            </div>
          </div>
        </div>

        {/* Sign Up/Sign In Section */}
        <div className="max-w-2xl mx-auto">
          <Card>
            <CardHeader>
              <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'signup' | 'signin')}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="signup">Join Community</TabsTrigger>
                  <TabsTrigger value="signin">Member Sign In</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab}>
                <TabsContent value="signup" className="space-y-6">
                  <div className="text-center">
                    <CardTitle className="mb-2">Join the Voluntier Community</CardTitle>
                    <CardDescription>
                      Create your account to start making a difference in your community
                    </CardDescription>
                  </div>
                  <SignupFlow onSignupComplete={onSignupComplete} />
                </TabsContent>
                
                <TabsContent value="signin" className="space-y-6">
                  <div className="text-center">
                    <CardTitle className="mb-2">Welcome Back</CardTitle>
                    <CardDescription>
                      Sign in to your account to continue your volunteer journey
                    </CardDescription>
                  </div>
                  <div className="text-center">
                    <p className="text-muted-foreground mb-4">
                      User authentication system is in development.
                    </p>
                    <p className="text-sm text-muted-foreground">
                      For now, please use the signup flow to access the platform.
                    </p>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Admin Access */}
          <div className="mt-8 text-center">
            <Button 
              variant="outline" 
              onClick={() => setShowAdminSignIn(true)}
              className="flex items-center gap-2 mx-auto"
            >
              <Shield size={16} />
              Administrator Access
            </Button>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6 text-center">
              <Shield size={32} className="text-primary mb-3 mx-auto" />
              <h3 className="font-semibold mb-2">Secure Platform</h3>
              <p className="text-sm text-muted-foreground">
                Multi-factor verification and comprehensive security monitoring
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <HandHeart size={32} className="text-primary mb-3 mx-auto" />
              <h3 className="font-semibold mb-2">Impact Tracking</h3>
              <p className="text-sm text-muted-foreground">
                Measure and visualize your community contribution
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <Users size={32} className="text-primary mb-3 mx-auto" />
              <h3 className="font-semibold mb-2">Community Network</h3>
              <p className="text-sm text-muted-foreground">
                Connect with local organizations and like-minded volunteers
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <Building size={32} className="text-primary mb-3 mx-auto" />
              <h3 className="font-semibold mb-2">Business Integration</h3>
              <p className="text-sm text-muted-foreground">
                Corporate volunteer programs and community partnerships
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Admin Sign In Dialog */}
      <Dialog open={showAdminSignIn} onOpenChange={setShowAdminSignIn}>
        <DialogContent className="sm:max-w-md">
          <SignInForm onClose={() => setShowAdminSignIn(false)} />
        </DialogContent>
      </Dialog>
    </div>
  )
}