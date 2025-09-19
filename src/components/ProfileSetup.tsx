import { useState } from 'react'
import { UserProfile } from '../App'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Checkbox } from './ui/checkbox'
import { Badge } from './ui/badge'
import { UserCircle, CheckCircle } from '@phosphor-icons/react'

interface ProfileSetupProps {
  onProfileCreated: (profile: UserProfile) => void
}

const AVAILABLE_SKILLS = [
  'Event Planning', 'Teaching', 'Construction', 'Gardening', 'Cooking',
  'Childcare', 'Elder Care', 'Animal Care', 'Technology', 'Transportation',
  'Administration', 'Fundraising', 'Marketing', 'Photography', 'Music'
]

const AVAILABLE_INTERESTS = [
  'Environment', 'Education', 'Health', 'Animals', 'Community',
  'Arts & Culture', 'Sports', 'Technology', 'Food & Nutrition',
  'Seniors', 'Youth', 'Homelessness', 'Disability Services'
]

export function ProfileSetup({ onProfileCreated }: ProfileSetupProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [selectedSkills, setSelectedSkills] = useState<string[]>([])
  const [selectedInterests, setSelectedInterests] = useState<string[]>([])
  const [isOrganization, setIsOrganization] = useState(false)

  const handleSkillToggle = (skill: string) => {
    setSelectedSkills(current => 
      current.includes(skill) 
        ? current.filter(s => s !== skill)
        : [...current, skill]
    )
  }

  const handleInterestToggle = (interest: string) => {
    setSelectedInterests(current => 
      current.includes(interest) 
        ? current.filter(i => i !== interest)
        : [...current, interest]
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name || !email) return

    const profile: UserProfile = {
      id: Date.now().toString(),
      name,
      email,
      userType: 'individual',
      skills: selectedSkills,
      interests: selectedInterests,
      verified: false,
      verificationStatus: 'pending',
      hoursLogged: 0,
      eventsAttended: 0,
      isOrganization,
      securityScore: 0,
      flagged: false,
      createdAt: new Date().toISOString()
    }

    onProfileCreated(profile)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <UserCircle size={48} className="text-primary" />
          </div>
          <CardTitle className="text-2xl">Welcome to Voluntier</CardTitle>
          <CardDescription>
            Set up your profile to get started with volunteer opportunities in your community
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="organization"
                checked={isOrganization}
                onCheckedChange={(checked) => setIsOrganization(checked === true)}
              />
              <Label htmlFor="organization">
                I represent an organization
              </Label>
            </div>

            <div className="space-y-3">
              <Label>Skills & Abilities</Label>
              <p className="text-sm text-muted-foreground">
                Select skills you can contribute as a volunteer
              </p>
              <div className="grid grid-cols-3 gap-2">
                {AVAILABLE_SKILLS.map(skill => (
                  <Button
                    key={skill}
                    type="button"
                    variant={selectedSkills.includes(skill) ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleSkillToggle(skill)}
                    className="text-xs h-8"
                  >
                    {skill}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <Label>Interests</Label>
              <p className="text-sm text-muted-foreground">
                Select causes and areas you're passionate about
              </p>
              <div className="grid grid-cols-3 gap-2">
                {AVAILABLE_INTERESTS.map(interest => (
                  <Button
                    key={interest}
                    type="button"
                    variant={selectedInterests.includes(interest) ? "default" : "outline"}
                    size="sm"
                    onClick={() => handleInterestToggle(interest)}
                    className="text-xs h-8"
                  >
                    {interest}
                  </Button>
                ))}
              </div>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={!name || !email}
            >
              <CheckCircle size={16} className="mr-2" />
              Create Profile
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}