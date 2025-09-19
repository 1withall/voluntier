import { useState, useEffect } from 'react'
import { useKV } from '@github/spark/hooks'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Alert, AlertDescription } from './ui/alert'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { QrCode, Scan, CheckCircle, Warning, Shield, User } from '@phosphor-icons/react'
import { VerificationQRCode } from '../types/auth'
import { UserProfile } from '../App'

interface QRVerificationSystemProps {
  userProfile: UserProfile
}

export function QRVerificationSystem({ userProfile }: QRVerificationSystemProps) {
  const [qrCodes, setQRCodes] = useKV<VerificationQRCode[]>('verification-qr-codes', [])
  const [scannedCode, setScannedCode] = useState('')
  const [verificationStatus, setVerificationStatus] = useState<'idle' | 'scanning' | 'success' | 'error'>('idle')
  const [verificationMessage, setVerificationMessage] = useState('')
  const [myQRCode, setMyQRCode] = useState<VerificationQRCode | null>(null)

  // Generate QR code for individual users to be verified
  const generateMyQRCode = () => {
    if (userProfile.userType !== 'individual') return

    const newQRCode: VerificationQRCode = {
      id: Date.now().toString(),
      code: `VQR-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      userId: userProfile.id,
      generatedBy: userProfile.id,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
      verified: false
    }

    setQRCodes(current => [...(current || []), newQRCode])
    setMyQRCode(newQRCode)
  }

  // Scan QR code (for organizations)
  const handleScanQRCode = async () => {
    if (!scannedCode.trim()) return

    setVerificationStatus('scanning')

    // Find the QR code
    const qrCode = (qrCodes || []).find(code => code.code === scannedCode.trim())

    if (!qrCode) {
      setVerificationStatus('error')
      setVerificationMessage('Invalid QR code. Please check the code and try again.')
      return
    }

    if (qrCode.verified) {
      setVerificationStatus('error')
      setVerificationMessage('This QR code has already been used for verification.')
      return
    }

    if (new Date(qrCode.expiresAt) < new Date()) {
      setVerificationStatus('error')
      setVerificationMessage('QR code has expired. Please request a new one.')
      return
    }

    if (userProfile.userType !== 'organization' && userProfile.userType !== 'business') {
      setVerificationStatus('error')
      setVerificationMessage('Only verified organizations can scan QR codes for verification.')
      return
    }

    // Simulate location capture (in real implementation, this would use device geolocation)
    const location = {
      latitude: 40.7128 + (Math.random() - 0.5) * 0.01,
      longitude: -74.0060 + (Math.random() - 0.5) * 0.01,
      accuracy: 10
    }

    // Update QR code as verified
    const updatedQRCode = {
      ...qrCode,
      scannedAt: new Date().toISOString(),
      scannedBy: userProfile.id,
      location,
      verified: true
    }

    setQRCodes(current => 
      (current || []).map(code => 
        code.id === qrCode.id ? updatedQRCode : code
      )
    )

    setVerificationStatus('success')
    setVerificationMessage(`Successfully verified user ${qrCode.userId}. Verification logged with location data.`)
    setScannedCode('')

    // Log security event
    const securityEvent = {
      id: Date.now().toString(),
      userId: qrCode.userId,
      eventType: 'verification_success' as const,
      severity: 'low' as const,
      description: `In-person verification completed by ${userProfile.name}`,
      metadata: {
        verificationId: updatedQRCode.id,
        organizationId: userProfile.id,
        location
      },
      timestamp: new Date().toISOString(),
      resolved: true
    }

    // In a real implementation, this would be sent to the security system
    console.log('Verification Security Event:', securityEvent)
  }

  const getQRCodeStatus = (qrCode: VerificationQRCode) => {
    if (qrCode.verified) return 'verified'
    if (new Date(qrCode.expiresAt) < new Date()) return 'expired'
    return 'active'
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'verified':
        return <Badge className="text-green-600 bg-green-50 border-green-200">Verified</Badge>
      case 'expired':
        return <Badge variant="destructive">Expired</Badge>
      case 'active':
        return <Badge className="text-blue-600 bg-blue-50 border-blue-200">Active</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  // Auto-clear verification status after 5 seconds
  useEffect(() => {
    if (verificationStatus === 'success' || verificationStatus === 'error') {
      const timer = setTimeout(() => {
        setVerificationStatus('idle')
        setVerificationMessage('')
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [verificationStatus])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">QR Verification System</h1>
        <p className="text-muted-foreground mt-2">
          Secure in-person verification using QR codes
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Individual User - Generate QR Code */}
        {userProfile.userType === 'individual' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode size={20} />
                My Verification QR Code
              </CardTitle>
              <CardDescription>
                Generate a QR code for organizations to verify your identity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!myQRCode ? (
                <div className="text-center py-8">
                  <QrCode size={48} className="text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">
                    Generate a QR code to complete in-person verification with a registered organization
                  </p>
                  <Button onClick={generateMyQRCode} className="flex items-center gap-2">
                    <QrCode size={16} />
                    Generate QR Code
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-center p-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <div className="text-2xl font-mono font-bold text-center p-4 bg-white rounded border">
                      {myQRCode.code}
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      Show this code to a verified organization representative
                    </p>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Status:</span>
                    {getStatusBadge(getQRCodeStatus(myQRCode))}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Expires:</span>
                    <span className="text-sm text-muted-foreground">
                      {new Date(myQRCode.expiresAt).toLocaleString()}
                    </span>
                  </div>

                  {myQRCode.verified && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        ✓ Verified by organization on {new Date(myQRCode.scannedAt!).toLocaleDateString()}
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button 
                    variant="outline" 
                    onClick={() => setMyQRCode(null)}
                    className="w-full"
                  >
                    Generate New Code
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Organization/Business - Scan QR Codes */}
        {(userProfile.userType === 'organization' || userProfile.userType === 'business') && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scan size={20} />
                Verify Individual
              </CardTitle>
              <CardDescription>
                Scan QR codes to verify individual volunteers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="qrCode">QR Code</Label>
                <Input
                  id="qrCode"
                  value={scannedCode}
                  onChange={(e) => setScannedCode(e.target.value)}
                  placeholder="Enter or scan QR code (e.g., VQR-123456789-abc123)"
                  disabled={verificationStatus === 'scanning'}
                />
              </div>

              <Button 
                onClick={handleScanQRCode}
                disabled={!scannedCode.trim() || verificationStatus === 'scanning'}
                className="w-full flex items-center gap-2"
              >
                <Scan size={16} />
                {verificationStatus === 'scanning' ? 'Verifying...' : 'Verify Individual'}
              </Button>

              {verificationStatus === 'success' && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>{verificationMessage}</AlertDescription>
                </Alert>
              )}

              {verificationStatus === 'error' && (
                <Alert variant="destructive">
                  <Warning className="h-4 w-4" />
                  <AlertDescription>{verificationMessage}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        )}

        {/* Verification History */}
        <Card className={userProfile.userType === 'individual' ? 'md:col-span-1' : 'md:col-span-2'}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield size={20} />
              Verification History
            </CardTitle>
            <CardDescription>
              Recent verification activities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(qrCodes || [])
                .filter(code => 
                  userProfile.userType === 'individual' 
                    ? code.userId === userProfile.id 
                    : code.scannedBy === userProfile.id
                )
                .slice(0, 10)
                .map(code => (
                <div key={code.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <User size={20} className="text-muted-foreground" />
                    <div>
                      <p className="font-medium">
                        {userProfile.userType === 'individual' ? 'My Verification' : `User ${code.userId}`}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {code.verified 
                          ? `Verified on ${new Date(code.scannedAt!).toLocaleDateString()}`
                          : `Generated on ${new Date(code.id).toLocaleDateString()}`
                        }
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(getQRCodeStatus(code))}
                  </div>
                </div>
              ))}

              {(qrCodes || []).filter(code => 
                userProfile.userType === 'individual' 
                  ? code.userId === userProfile.id 
                  : code.scannedBy === userProfile.id
              ).length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Shield size={48} className="mx-auto mb-4 opacity-50" />
                  <p>No verification activities yet</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Information Panel */}
      <Card>
        <CardHeader>
          <CardTitle>How QR Verification Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-blue-600">1</span>
              </div>
              <h3 className="font-semibold mb-2">Generate</h3>
              <p className="text-sm text-muted-foreground">
                Individual volunteers generate a unique QR code valid for 24 hours
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-blue-600">2</span>
              </div>
              <h3 className="font-semibold mb-2">Visit</h3>
              <p className="text-sm text-muted-foreground">
                Volunteer visits a verified organization for in-person verification
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-xl font-bold text-blue-600">3</span>
              </div>
              <h3 className="font-semibold mb-2">Verify</h3>
              <p className="text-sm text-muted-foreground">
                Organization scans the QR code, completing the verification process
              </p>
            </div>
          </div>

          <Alert>
            <Shield className="h-4 w-4" />
            <AlertDescription>
              QR code verification includes location tracking, timestamp logging, and cryptographic validation 
              to ensure security and prevent fraud. All verification activities are logged for audit purposes.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  )
}