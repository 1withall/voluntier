import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Progress } from '../ui/progress'
import { Badge } from '../ui/badge'
import { Alert, AlertDescription } from '../ui/alert'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Textarea } from '../ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs'
import { DocumentVerificationService, ReferenceVerificationService } from '../../services/verificationWorkflow'
import { DocumentVerificationRequest, ReferenceVerificationRequest } from '../../types/verification'
import { UserProfile } from '../../types/profiles'
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Eye, 
  Warning,
  Users,
  Envelope,
  Phone
} from '@phosphor-icons/react'

interface DocumentVerificationProps {
  userProfile: UserProfile
}

export function DocumentVerification({ userProfile }: DocumentVerificationProps) {
  const [documentRequests, setDocumentRequests] = useState<DocumentVerificationRequest[]>([])
  const [referenceRequests, setReferenceRequests] = useState<ReferenceVerificationRequest[]>([])
  const [uploading, setUploading] = useState(false)
  const [activeTab, setActiveTab] = useState('documents')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedDocType, setSelectedDocType] = useState<DocumentVerificationRequest['documentType']>('government_id')
  
  // Reference form state
  const [referenceForm, setReferenceForm] = useState({
    referenceType: 'personal' as ReferenceVerificationRequest['referenceType'],
    referenceName: '',
    referenceEmail: '',
    referencePhone: '',
    relationship: '',
    yearsKnown: 1
  })

  const documentService = DocumentVerificationService.getInstance()
  const referenceService = ReferenceVerificationService.getInstance()

  useEffect(() => {
    loadVerificationData()
  }, [userProfile.id])

  const loadVerificationData = async () => {
    try {
      const [documents, references] = await Promise.all([
        documentService.getUserVerificationRequests(userProfile.id),
        referenceService.getUserReferenceRequests(userProfile.id)
      ])
      setDocumentRequests(documents)
      setReferenceRequests(references)
    } catch (error) {
      console.error('Failed to load verification data:', error)
    }
  }

  const handleFileUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    try {
      await documentService.submitDocument(userProfile.id, selectedDocType, selectedFile)
      setSelectedFile(null)
      await loadVerificationData()
    } catch (error) {
      console.error('Failed to upload document:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleReferenceSubmit = async () => {
    if (!referenceForm.referenceName || !referenceForm.referenceEmail) return

    try {
      await referenceService.submitReference(userProfile.id, referenceForm)
      setReferenceForm({
        referenceType: 'personal',
        referenceName: '',
        referenceEmail: '',
        referencePhone: '',
        relationship: '',
        yearsKnown: 1
      })
      await loadVerificationData()
    } catch (error) {
      console.error('Failed to submit reference:', error)
    }
  }

  const getStatusColor = (status: DocumentVerificationRequest['status'] | ReferenceVerificationRequest['status']) => {
    switch (status) {
      case 'verified': return 'bg-green-100 text-green-800'
      case 'rejected': case 'failed': return 'bg-red-100 text-red-800'
      case 'processing': case 'sent': return 'bg-blue-100 text-blue-800'
      case 'requires_human_review': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: DocumentVerificationRequest['status'] | ReferenceVerificationRequest['status']) => {
    switch (status) {
      case 'verified': return <CheckCircle size={16} className="text-green-600" />
      case 'rejected': case 'failed': return <XCircle size={16} className="text-red-600" />
      case 'processing': case 'sent': return <Clock size={16} className="text-blue-600" />
      case 'requires_human_review': return <Eye size={16} className="text-yellow-600" />
      default: return <Clock size={16} className="text-gray-600" />
    }
  }

  const getRequiredDocuments = () => {
    const baseRequirements = ['government_id', 'proof_of_address']
    
    if (userProfile.userType === 'organization') {
      return [...baseRequirements, 'organization_license']
    }
    
    if (userProfile.userType === 'business') {
      return [...baseRequirements, 'business_registration']
    }
    
    return baseRequirements
  }

  const getVerificationProgress = () => {
    const requiredDocs = getRequiredDocuments()
    const verifiedDocs = documentRequests.filter(r => 
      requiredDocs.includes(r.documentType) && r.status === 'verified'
    ).length
    
    const requiredRefs = userProfile.userType === 'organization' ? 3 : 2
    const verifiedRefs = referenceRequests.filter(r => r.status === 'verified').length
    
    const totalRequired = requiredDocs.length + requiredRefs
    const totalVerified = verifiedDocs + Math.min(verifiedRefs, requiredRefs)
    
    return {
      percentage: Math.round((totalVerified / totalRequired) * 100),
      verified: totalVerified,
      total: totalRequired,
      documentsComplete: verifiedDocs === requiredDocs.length,
      referencesComplete: verifiedRefs >= requiredRefs
    }
  }

  const progress = getVerificationProgress()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Document Verification</h1>
          <p className="text-muted-foreground mt-2">
            Complete your verification to access all platform features
          </p>
        </div>
        <Card className="w-64">
          <CardContent className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress.verified}/{progress.total}</span>
              </div>
              <Progress value={progress.percentage} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {progress.percentage}% complete
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="documents" className="flex items-center gap-2">
            <FileText size={16} />
            Documents
          </TabsTrigger>
          <TabsTrigger value="references" className="flex items-center gap-2">
            <Users size={16} />
            References
          </TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload size={20} />
                Upload Documents
              </CardTitle>
              <CardDescription>
                Upload required documents for automated verification
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Document Type</Label>
                  <Select 
                    value={selectedDocType} 
                    onValueChange={(value) => setSelectedDocType(value as DocumentVerificationRequest['documentType'])}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="government_id">Government ID</SelectItem>
                      <SelectItem value="proof_of_address">Proof of Address</SelectItem>
                      {userProfile.userType === 'organization' && (
                        <SelectItem value="organization_license">Organization License</SelectItem>
                      )}
                      {userProfile.userType === 'business' && (
                        <SelectItem value="business_registration">Business Registration</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>File</Label>
                  <Input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  />
                </div>
              </div>
              
              <Button 
                onClick={handleFileUpload}
                disabled={!selectedFile || uploading}
                className="w-full"
              >
                {uploading ? 'Uploading...' : 'Upload Document'}
              </Button>
            </CardContent>
          </Card>

          <div className="grid gap-4">
            {documentRequests.map((request) => (
              <Card key={request.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText size={20} className="text-muted-foreground" />
                      <div>
                        <p className="font-medium">
                          {request.documentType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Uploaded {new Date(request.uploadedAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {request.metadata.confidenceScore && (
                        <Badge variant="outline">
                          {Math.round(request.metadata.confidenceScore * 100)}% confidence
                        </Badge>
                      )}
                      <Badge className={getStatusColor(request.status)}>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(request.status)}
                          {request.status.replace('_', ' ')}
                        </div>
                      </Badge>
                    </div>
                  </div>
                  
                  {request.rejectionReason && (
                    <Alert className="mt-3">
                      <Warning size={16} />
                      <AlertDescription>
                        {request.rejectionReason}
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {request.verificationResults?.complianceChecks && (
                    <div className="mt-3 space-y-1">
                      <p className="text-sm font-medium">Compliance Checks:</p>
                      <div className="grid grid-cols-2 gap-2">
                        {request.verificationResults.complianceChecks.map((check, index) => (
                          <div key={index} className="flex items-center gap-2 text-sm">
                            {check.passed ? (
                              <CheckCircle size={14} className="text-green-600" />
                            ) : (
                              <XCircle size={14} className="text-red-600" />
                            )}
                            <span className={check.passed ? 'text-green-700' : 'text-red-700'}>
                              {check.check.replace('_', ' ')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="references" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users size={20} />
                Add Reference
              </CardTitle>
              <CardDescription>
                Provide references who can vouch for your character and reliability
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Reference Type</Label>
                  <Select 
                    value={referenceForm.referenceType} 
                    onValueChange={(value) => setReferenceForm(prev => ({ 
                      ...prev, 
                      referenceType: value as ReferenceVerificationRequest['referenceType']
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="personal">Personal</SelectItem>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="organization">Organization</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    value={referenceForm.referenceName}
                    onChange={(e) => setReferenceForm(prev => ({ 
                      ...prev, 
                      referenceName: e.target.value 
                    }))}
                    placeholder="Reference's full name"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={referenceForm.referenceEmail}
                    onChange={(e) => setReferenceForm(prev => ({ 
                      ...prev, 
                      referenceEmail: e.target.value 
                    }))}
                    placeholder="reference@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone (Optional)</Label>
                  <Input
                    type="tel"
                    value={referenceForm.referencePhone}
                    onChange={(e) => setReferenceForm(prev => ({ 
                      ...prev, 
                      referencePhone: e.target.value 
                    }))}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Relationship</Label>
                  <Input
                    value={referenceForm.relationship}
                    onChange={(e) => setReferenceForm(prev => ({ 
                      ...prev, 
                      relationship: e.target.value 
                    }))}
                    placeholder="e.g., Friend, Colleague, Supervisor"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Years Known</Label>
                  <Input
                    type="number"
                    min="1"
                    max="50"
                    value={referenceForm.yearsKnown}
                    onChange={(e) => setReferenceForm(prev => ({ 
                      ...prev, 
                      yearsKnown: parseInt(e.target.value) || 1 
                    }))}
                  />
                </div>
              </div>

              <Button 
                onClick={handleReferenceSubmit}
                disabled={!referenceForm.referenceName || !referenceForm.referenceEmail}
                className="w-full"
              >
                Submit Reference
              </Button>
            </CardContent>
          </Card>

          <div className="grid gap-4">
            {referenceRequests.map((request) => (
              <Card key={request.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Users size={20} className="text-muted-foreground" />
                      <div>
                        <p className="font-medium">{request.referenceName}</p>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Envelope size={14} />
                            {request.referenceEmail}
                          </span>
                          {request.referencePhone && (
                            <span className="flex items-center gap-1">
                              <Phone size={14} />
                              {request.referencePhone}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {request.relationship} • {request.yearsKnown} years
                        </p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(request.status)}>
                      <div className="flex items-center gap-1">
                        {getStatusIcon(request.status)}
                        {request.status.replace('_', ' ')}
                      </div>
                    </Badge>
                  </div>
                  
                  {request.response && (
                    <div className="mt-3 p-3 bg-muted rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Trustworthiness:</span>
                          <div className="flex items-center gap-1 mt-1">
                            {Array.from({ length: 5 }, (_, i) => (
                              <div
                                key={i}
                                className={`w-2 h-2 rounded-full ${
                                  i < (request.response?.trustworthiness || 0) ? 'bg-primary' : 'bg-muted-foreground/20'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                        <div>
                          <span className="font-medium">Reliability:</span>
                          <div className="flex items-center gap-1 mt-1">
                            {Array.from({ length: 5 }, (_, i) => (
                              <div
                                key={i}
                                className={`w-2 h-2 rounded-full ${
                                  i < (request.response?.reliability || 0) ? 'bg-primary' : 'bg-muted-foreground/20'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                      {request.response.comments && (
                        <div className="mt-2">
                          <span className="font-medium text-sm">Comments:</span>
                          <p className="text-sm text-muted-foreground mt-1">
                            {request.response.comments}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}