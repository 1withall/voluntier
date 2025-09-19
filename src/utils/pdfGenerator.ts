import { jsPDF } from 'jspdf'
import { VolunteerEvent } from '../App'

/**
 * Project Management PDF Templates Generator
 * Generates editable PDF documents based on current PM best practices
 * Documents are designed for download/print, not database storage
 */

interface ProjectManagementTemplate {
  title: string
  description: string
  sections: string[]
  fields: Record<string, string>
}

// Project Management Templates based on PMBOK Guide and Agile practices
const PM_TEMPLATES: Record<string, ProjectManagementTemplate> = {
  charter: {
    title: 'Event Project Charter',
    description: 'Define project scope, objectives, and stakeholder alignment',
    sections: [
      'Project Overview',
      'Objectives & Success Criteria',
      'Scope & Deliverables',
      'Stakeholder Identification',
      'Resource Requirements',
      'Timeline & Milestones',
      'Risks & Assumptions',
      'Budget Overview',
      'Approval & Sign-off'
    ],
    fields: {
      'Project Name': '',
      'Project Manager': '',
      'Start Date': '',
      'End Date': '',
      'Budget': '',
      'Sponsor': '',
      'Key Stakeholders': '',
      'Success Metrics': ''
    }
  },
  
  scope: {
    title: 'Scope Management Plan',
    description: 'Define what is and is not included in the project',
    sections: [
      'Scope Statement',
      'Work Breakdown Structure (WBS)',
      'Deliverables',
      'Acceptance Criteria',
      'Exclusions',
      'Constraints',
      'Assumptions',
      'Change Control Process'
    ],
    fields: {
      'Project Scope': '',
      'Major Deliverables': '',
      'Out of Scope': '',
      'Constraints': '',
      'Assumptions': '',
      'Change Request Process': ''
    }
  },
  
  risk: {
    title: 'Risk Management Plan',
    description: 'Identify, assess, and plan responses to project risks',
    sections: [
      'Risk Identification',
      'Risk Assessment Matrix',
      'Risk Response Strategies',
      'Contingency Plans',
      'Risk Monitoring',
      'Communication Plan',
      'Review Schedule'
    ],
    fields: {
      'Risk Owner': '',
      'Review Frequency': '',
      'Escalation Process': '',
      'Risk Tolerance': '',
      'Monitoring Tools': ''
    }
  },
  
  communication: {
    title: 'Communication Management Plan',
    description: 'Define how project information will be managed and distributed',
    sections: [
      'Stakeholder Analysis',
      'Communication Requirements',
      'Communication Methods',
      'Frequency & Schedule',
      'Roles & Responsibilities',
      'Information Distribution',
      'Performance Reporting',
      'Issue Escalation'
    ],
    fields: {
      'Communication Lead': '',
      'Primary Channels': '',
      'Meeting Schedule': '',
      'Reporting Format': '',
      'Escalation Path': ''
    }
  },
  
  stakeholder: {
    title: 'Stakeholder Management Plan',
    description: 'Identify and engage project stakeholders effectively',
    sections: [
      'Stakeholder Register',
      'Influence/Interest Matrix',
      'Engagement Strategy',
      'Communication Preferences',
      'Expectations Management',
      'Feedback Mechanisms',
      'Conflict Resolution',
      'Relationship Building'
    ],
    fields: {
      'Primary Stakeholders': '',
      'Secondary Stakeholders': '',
      'Key Influencers': '',
      'Engagement Frequency': '',
      'Feedback Channels': ''
    }
  },
  
  timeline: {
    title: 'Schedule Management Plan',
    description: 'Plan and control project timeline and milestones',
    sections: [
      'Work Breakdown Structure',
      'Activity Sequencing',
      'Duration Estimates',
      'Critical Path Analysis',
      'Milestone Schedule',
      'Resource Calendar',
      'Schedule Control',
      'Change Management'
    ],
    fields: {
      'Project Duration': '',
      'Key Milestones': '',
      'Critical Path': '',
      'Resource Availability': '',
      'Buffer Time': ''
    }
  },
  
  budget: {
    title: 'Cost Management Plan',
    description: 'Plan, estimate, and control project costs',
    sections: [
      'Cost Estimation',
      'Budget Baseline',
      'Cost Categories',
      'Funding Sources',
      'Cost Control Process',
      'Variance Analysis',
      'Change Control',
      'Financial Reporting'
    ],
    fields: {
      'Total Budget': '',
      'Funding Sources': '',
      'Cost Categories': '',
      'Contingency Fund': '',
      'Approval Limits': ''
    }
  },
  
  quality: {
    title: 'Quality Management Plan',
    description: 'Define quality standards and assurance processes',
    sections: [
      'Quality Standards',
      'Quality Assurance',
      'Quality Control',
      'Metrics & KPIs',
      'Testing Procedures',
      'Review Process',
      'Continuous Improvement',
      'Lessons Learned'
    ],
    fields: {
      'Quality Standards': '',
      'Success Metrics': '',
      'Review Criteria': '',
      'Testing Methods': '',
      'Improvement Process': ''
    }
  },
  
  closure: {
    title: 'Project Closure Checklist',
    description: 'Ensure proper project completion and knowledge transfer',
    sections: [
      'Deliverable Acceptance',
      'Stakeholder Sign-off',
      'Resource Release',
      'Documentation Archive',
      'Lessons Learned',
      'Financial Closure',
      'Contract Closure',
      'Celebration & Recognition'
    ],
    fields: {
      'Final Deliverables': '',
      'Outstanding Issues': '',
      'Knowledge Transfer': '',
      'Archive Location': '',
      'Team Recognition': ''
    }
  }
}

/**
 * Generate a fillable PDF form for project management
 */
export function generateProjectManagementPDF(
  templateType: keyof typeof PM_TEMPLATES,
  event: VolunteerEvent,
  organizationName: string
): void {
  try {
    const template = PM_TEMPLATES[templateType]
    if (!template) {
      throw new Error(`Template ${templateType} not found`)
    }

    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 20
    const contentWidth = pageWidth - (margin * 2)
    
    // Header
    doc.setFontSize(20)
    doc.setFont('helvetica', 'bold')
    doc.text(template.title, margin, margin + 10)
    
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    doc.text(`Event: ${event.title}`, margin, margin + 25)
    doc.text(`Organization: ${organizationName}`, margin, margin + 35)
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, margin, margin + 45)
    
    // Description
    doc.setFontSize(10)
    doc.setFont('helvetica', 'italic')
    const descriptionLines = doc.splitTextToSize(template.description, contentWidth)
    doc.text(descriptionLines, margin, margin + 60)
    
    let yPosition = margin + 80
    
    // Instructions
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(100, 100, 100)
    const instructions = [
      'INSTRUCTIONS:',
      '• Fill out this form completely before and during your event planning',
      '• Save a copy to your organization\'s project management system',
      '• Review and update regularly throughout the project lifecycle',
      '• Use this as a living document - not a one-time exercise'
    ]
    
    instructions.forEach(instruction => {
      doc.text(instruction, margin, yPosition)
      yPosition += 12
    })
    
    yPosition += 10
    doc.setTextColor(0, 0, 0)
    
    // Event-specific pre-filled fields
    const eventFields = {
      'Event Name': event.title,
      'Event Date': event.date,
      'Event Time': event.time,
      'Location': event.location,
      'Category': event.category,
      'Volunteers Needed': event.volunteersNeeded.toString(),
      'Description': event.description,
      'Skills Required': event.skills.join(', ')
    }
    
    // Add event information section
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('EVENT INFORMATION', margin, yPosition)
    yPosition += 15
    
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    
    Object.entries(eventFields).forEach(([key, value]) => {
      if (yPosition > pageHeight - 40) {
        doc.addPage()
        yPosition = margin
      }
      
      doc.setFont('helvetica', 'bold')
      doc.text(`${key}:`, margin, yPosition)
      doc.setFont('helvetica', 'normal')
      
      const valueText = value || '_'.repeat(50)
      const lines = doc.splitTextToSize(valueText, contentWidth - 80)
      doc.text(lines, margin + 80, yPosition)
      yPosition += Math.max(12, lines.length * 10)
    })
    
    yPosition += 15
    
    // Template sections
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('PROJECT MANAGEMENT SECTIONS', margin, yPosition)
    yPosition += 15
    
    template.sections.forEach((section, index) => {
      if (yPosition > pageHeight - 80) {
        doc.addPage()
        yPosition = margin
      }
      
      // Section header
      doc.setFontSize(12)
      doc.setFont('helvetica', 'bold')
      doc.text(`${index + 1}. ${section}`, margin, yPosition)
      yPosition += 15
      
      // Section content area (fillable lines)
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(10)
      
      for (let i = 0; i < 5; i++) {
        doc.line(margin, yPosition + 5, pageWidth - margin, yPosition + 5)
        yPosition += 12
      }
      
      yPosition += 10
    })
    
    // Template-specific fields
    if (Object.keys(template.fields).length > 0) {
      if (yPosition > pageHeight - 100) {
        doc.addPage()
        yPosition = margin
      }
      
      doc.setFontSize(14)
      doc.setFont('helvetica', 'bold')
      doc.text('KEY FIELDS', margin, yPosition)
      yPosition += 15
      
      Object.entries(template.fields).forEach(([key, defaultValue]) => {
        if (yPosition > pageHeight - 40) {
          doc.addPage()
          yPosition = margin
        }
        
        doc.setFontSize(10)
        doc.setFont('helvetica', 'bold')
        doc.text(`${key}:`, margin, yPosition)
        yPosition += 10
        
        // Create fillable area
        for (let i = 0; i < 2; i++) {
          doc.line(margin, yPosition + 5, pageWidth - margin, yPosition + 5)
          yPosition += 12
        }
        yPosition += 5
      })
    }
    
    // Footer
    const totalPages = doc.getNumberOfPages()
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)
      doc.setFontSize(8)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(100, 100, 100)
      doc.text(
        `Voluntier Project Management Template - Page ${i} of ${totalPages}`,
        margin,
        pageHeight - 10
      )
      doc.text(
        'For organizational use only - Do not store in application database',
        pageWidth - 120,
        pageHeight - 10
      )
    }
    
    // Save the PDF
    const filename = `${templateType}_${event.title.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.pdf`
    doc.save(filename)
    
    // Track download
    console.log(`PDF generated: ${filename}`)
    
  } catch (error) {
    console.error('Error generating PDF:', error)
    throw new Error('Failed to generate project management PDF')
  }
}

/**
 * Generate a comprehensive event planning checklist PDF
 */
export function generateEventPlanningChecklist(event: VolunteerEvent, organizationName: string): void {
  try {
    const doc = new jsPDF()
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 20
    
    // Header
    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.text('Event Planning Checklist', margin, margin + 10)
    
    doc.setFontSize(12)
    doc.text(`Event: ${event.title}`, margin, margin + 25)
    doc.text(`Organization: ${organizationName}`, margin, margin + 35)
    doc.text(`Date: ${event.date} at ${event.time}`, margin, margin + 45)
    
    let yPosition = margin + 65
    
    const checklistSections = [
      {
        title: '6-8 Weeks Before Event',
        items: [
          'Define event goals and objectives',
          'Secure event date and venue',
          'Create event budget',
          'Identify required permits and insurance',
          'Develop marketing and communication plan',
          'Create volunteer recruitment strategy',
          'Set up registration system',
          'Plan event logistics (setup, breakdown, etc.)'
        ]
      },
      {
        title: '4-6 Weeks Before Event',
        items: [
          'Finalize volunteer roles and responsibilities',
          'Order necessary supplies and equipment',
          'Confirm catering/refreshments if applicable',
          'Create volunteer training materials',
          'Set up communication channels',
          'Finalize safety and emergency procedures',
          'Create event timeline and run-of-show',
          'Prepare backup plans for weather/emergencies'
        ]
      },
      {
        title: '2-4 Weeks Before Event',
        items: [
          'Conduct volunteer orientation/training',
          'Confirm all vendor arrangements',
          'Finalize volunteer assignments',
          'Test all equipment and technology',
          'Prepare volunteer check-in materials',
          'Create signage and wayfinding',
          'Coordinate with local authorities if needed',
          'Send reminder communications to volunteers'
        ]
      },
      {
        title: '1 Week Before Event',
        items: [
          'Final volunteer count confirmation',
          'Prepare volunteer packets/materials',
          'Confirm weather contingency plans',
          'Final equipment and supply check',
          'Prepare day-of emergency contacts list',
          'Set up online check-in systems',
          'Brief team leaders and supervisors',
          'Prepare thank you materials for volunteers'
        ]
      },
      {
        title: 'Day of Event',
        items: [
          'Arrive early for setup',
          'Conduct volunteer check-in',
          'Brief all volunteers on safety procedures',
          'Distribute tools and materials',
          'Monitor volunteer performance and safety',
          'Take photos/document the event',
          'Manage volunteer break schedules',
          'Coordinate event breakdown and cleanup'
        ]
      },
      {
        title: 'After Event',
        items: [
          'Collect and clean equipment',
          'Gather volunteer feedback',
          'Thank volunteers personally',
          'Document lessons learned',
          'Submit impact reports',
          'Process any incident reports',
          'Plan follow-up communications',
          'Evaluate event success against goals'
        ]
      }
    ]
    
    checklistSections.forEach(section => {
      if (yPosition > pageHeight - 100) {
        doc.addPage()
        yPosition = margin
      }
      
      // Section title
      doc.setFontSize(14)
      doc.setFont('helvetica', 'bold')
      doc.text(section.title, margin, yPosition)
      yPosition += 15
      
      // Checklist items
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      
      section.items.forEach(item => {
        if (yPosition > pageHeight - 30) {
          doc.addPage()
          yPosition = margin
        }
        
        // Checkbox
        doc.rect(margin, yPosition - 3, 4, 4)
        
        // Item text
        const lines = doc.splitTextToSize(item, pageWidth - margin - 20)
        doc.text(lines, margin + 10, yPosition)
        yPosition += Math.max(8, lines.length * 6)
      })
      
      yPosition += 10
    })
    
    // Save the PDF
    const filename = `event_checklist_${event.title.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.pdf`
    doc.save(filename)
    
  } catch (error) {
    console.error('Error generating checklist PDF:', error)
    throw new Error('Failed to generate event planning checklist')
  }
}

/**
 * Get available project management templates
 */
export function getAvailableTemplates(): Array<{key: string, title: string, description: string}> {
  return Object.entries(PM_TEMPLATES).map(([key, template]) => ({
    key,
    title: template.title,
    description: template.description
  }))
}